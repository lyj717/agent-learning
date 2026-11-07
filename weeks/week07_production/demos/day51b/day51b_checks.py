"""AI 维护的 Day51B 核心对照；只使用公共人工资料与离线回调。"""

import copy
import json
import math
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from pydantic import BaseModel, ValidationError

INTERNAL_MESSAGE = "INTERNAL_DEMO_MESSAGE_DO_NOT_RETURN"


def _finish(run_dir: Path, results: list[dict]) -> None:
    """先保存全部结果，再统一报告未通过项。"""
    (run_dir / "checks.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    passed = sum(row["passed"] for row in results)
    print(f"对照汇总：{passed}/{len(results)} 组通过")
    if passed != len(results):
        raise AssertionError("请对照本轮实际与期望，未全部通过")


def run_a(model: type[BaseModel], run_dir: Path) -> None:
    """检查严格字段、空字符串与业务空白的边界。"""
    if not model.model_fields:
        raise NotImplementedError("第 A 题的请求模型还没写")
    cases = [
        ("正常字段", {"session_id": "room-a", "question": "地点"}, True),
        ("空格在模型层合法", {"session_id": "  ", "question": "  "}, True),
        ("空 question", {"session_id": "room-a", "question": ""}, False),
        ("空 session_id", {"session_id": "", "question": "地点"}, False),
        ("session_id 类型错", {"session_id": 7, "question": "地点"}, False),
        ("question 类型错", {"session_id": "room-a", "question": 7}, False),
        ("缺 session_id", {"question": "地点"}, False),
        ("缺 question", {"session_id": "room-a"}, False),
        ("额外 top_k", {"session_id": "room-a", "question": "地点", "top_k": 2}, False),
    ]
    results = []
    for label, payload, accepted in cases:
        before = copy.deepcopy(payload)
        actual = None
        rejected = False
        try:
            actual = model.model_validate(payload).model_dump()
        except ValidationError:
            rejected = True
        expected = payload if accepted else "ValidationError"
        passed = (actual == expected if accepted else rejected) and payload == before
        row = {
            "case": label,
            "input": payload,
            "actual": actual if not rejected else "ValidationError",
            "expected": expected,
            "passed": bool(passed),
        }
        results.append(row)
        print("\n", label, "；输入：", payload)
        print(
            "实际：",
            row["actual"],
            "；期望：",
            expected,
            "；输入保持：",
            payload == before,
        )
        print("通过：", passed)
    _finish(run_dir, results)


def _checked(question: str) -> dict | None:
    """给出人工替身的期望内容，不判断任何真实模型回答。"""
    if question == "无资料":
        return None
    text = "周六十点开放。" if question == "时间" else "请到二楼取书。"
    return {"status": "answered", "answer": text, "cited_ids": ["public.md#L1-L1"]}


class _Fixture:
    """提供已实现的三项回调，保存调用次数、输入与实际事件。"""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.calls = {"retrieve": 0, "request": 0}
        self.events: list[dict] = []
        self.questions: list[str] = []
        self.inputs_ok = True

    def retrieve(self, question: str) -> list[Document]:
        """只返回人工证据或指定故障，不调用检索库。"""
        self.calls["retrieve"] += 1
        self.questions.append(question)
        if question == "检索超时":
            raise TimeoutError(INTERNAL_MESSAGE)
        if question == "无资料":
            return []
        checked = _checked(question)
        return [
            Document(
                id="public.md#L1-L1",
                page_content=checked["answer"],
                metadata={"source": "public.md", "line_start": 1, "line_end": 1},
            )
        ]

    def request(self, messages: list[dict[str, str]]) -> dict:
        """读取旧函数组装的两条消息，返回人工 JSON。"""
        self.calls["request"] += 1
        payload = json.loads(messages[1]["content"])
        question = payload["question"]
        self.inputs_ok = self.inputs_ok and (
            len(messages) == 2
            and [message["role"] for message in messages] == ["system", "user"]
            and set(payload) == {"question", "evidence"}
            and len(payload["evidence"]) == 1
            and payload["evidence"][0]["id"] == "public.md#L1-L1"
        )
        raw_text = json.dumps(_checked(question), ensure_ascii=False)
        return {"raw_text": raw_text, "finish_reason": "stop", "usage": None}

    def emit(self, event: dict) -> None:
        """只接事件字典；目录已经固定，保留 JSONL 与内存副本。"""
        copied = copy.deepcopy(event)
        self.events.append(copied)
        with (self.run_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(copied, ensure_ascii=False, allow_nan=False) + "\n")


def _events_ok(
    events: list[dict], pattern: list[tuple[str, str]], seen: set[str]
) -> bool:
    """核对旧阶段协议及新请求编号，不接受事件中夹带业务载荷。"""
    if len(events) != len(pattern):
        return False
    if not events:
        return True
    if any(not isinstance(event, dict) for event in events):
        return False
    request_id = events[0].get("request_id")
    try:
        valid_id = (
            isinstance(request_id, str)
            and UUID(request_id).hex == request_id
            and UUID(request_id).version == 4
        )
    except (ValueError, AttributeError):
        return False
    if not valid_id or request_id in seen:
        return False
    seen.add(request_id)
    for event, (stage, state) in zip(events, pattern, strict=True):
        fields = {"request_id", "stage", "state"}
        if state != "start":
            fields.add("elapsed_ms")
        if state == "error":
            fields.add("error_type")
        if (
            set(event) != fields
            or event["request_id"] != request_id
            or event["stage"] != stage
            or event["state"] != state
        ):
            return False
        if state != "start" and (
            not isinstance(event["elapsed_ms"], float)
            or not math.isfinite(event["elapsed_ms"])
            or event["elapsed_ms"] < 0
        ):
            return False
        if state == "error" and not isinstance(event["error_type"], str):
            return False
    return INTERNAL_MESSAGE not in json.dumps(events)


def run_b(factory: Callable, run_dir: Path) -> None:
    """按顺序检查会话历史、旧阶段协议、失败结果和应用边界。"""
    fixture = _Fixture(run_dir)
    app = factory(fixture.retrieve, fixture.request, fixture.emit)
    if not isinstance(app, FastAPI):
        raise TypeError("create_chat_app 必须返回 FastAPI 应用对象")
    histories: dict[str, list[dict]] = {}
    results = []
    seen_ids: set[str] = set()

    def check(
        client: TestClient,
        label: str,
        method: str,
        path: str,
        payload: dict | None,
        status: int,
        *,
        kind: str = "error",
        session: str = "",
        question: str = "",
        detail: str | None = None,
        failed_stage: str | None = None,
        error_type: str | None = None,
        isolated: bool = False,
        distinct: bool = True,
    ) -> None:
        """记录单次实际请求，所有可预期错误继续检查，不只报告第一处。"""
        before_calls = fixture.calls.copy()
        before_events = len(fixture.events)
        before_questions = len(fixture.questions)
        response = client.request(method, path, json=payload)
        try:
            body = response.json()
        except ValueError:
            body = {"unparsed_text": response.text}
        events = fixture.events[before_events:]
        calls = {
            name: fixture.calls[name] - before_calls[name] for name in fixture.calls
        }
        expected_calls = {"retrieve": 0, "request": 0}
        pattern: list[tuple[str, str]] = []
        if kind == "ask" or failed_stage is not None:
            expected_calls = {
                "retrieve": 1,
                "request": 0
                if question == "无资料" or failed_stage == "retrieve"
                else 1,
            }
            for stage in ["retrieve", "prepare", "generate", "validate"]:
                pattern.extend(
                    [
                        (stage, "start"),
                        (stage, "error" if stage == failed_stage else "ok"),
                    ]
                )
                if stage == failed_stage or question == "无资料":
                    break
        request_id = body.get("request_id") if isinstance(body, dict) else None
        if kind == "ask":
            expected = {
                "session_id": session,
                "request_id": request_id,
                "checked": _checked(question),
            }
            body_ok = (
                body == expected
                and bool(events)
                and request_id == events[0].get("request_id")
            )
            histories.setdefault(session, []).append(
                {
                    "question": question,
                    "request_id": request_id,
                    "checked": _checked(question),
                }
            )
        elif kind == "history":
            expected = {
                "session_id": session,
                "turns": [] if isolated else histories.get(session, []),
            }
            body_ok = body == expected and distinct
        elif kind == "health":
            expected = {"status": "ok", "mode": "offline"}
            body_ok = body == expected
        elif status == 500:
            expected = {"unparsed_text": "Internal Server Error"}
            body_ok = body == expected
        elif detail is not None:
            expected = {"detail": detail}
            body_ok = body == expected
        else:
            expected = "响应正文含 detail"
            body_ok = isinstance(body, dict) and "detail" in body
        protocol_ok = _events_ok(events, pattern, seen_ids)
        if error_type is not None:
            protocol_ok = (
                protocol_ok
                and bool(events)
                and events[-1].get("error_type") == error_type
            )
        input_ok = fixture.inputs_ok and (
            fixture.questions[before_questions:]
            == ([question] if expected_calls["retrieve"] else [])
        )
        safe = INTERNAL_MESSAGE not in json.dumps(body, ensure_ascii=False)
        passed = bool(
            response.status_code == status
            and body_ok
            and calls == expected_calls
            and protocol_ok
            and input_ok
            and safe
        )
        row = {
            "case": label,
            "method": method,
            "path": path,
            "input": payload,
            "status": response.status_code,
            "expected_status": status,
            "body": body,
            "expected_body": expected,
            "callbacks": calls,
            "request_ids": sorted(
                {
                    event["request_id"]
                    for event in events
                    if isinstance(event, dict)
                    and isinstance(event.get("request_id"), str)
                }
            ),
            "forwarded_questions": fixture.questions[before_questions:],
            "body_ok": body_ok,
            "stages_ok": protocol_ok,
            "input_ok": input_ok,
            "passed": passed,
        }
        with (run_dir / "requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        results.append(row)
        print("\n", label, "：", method, path, "；输入：", payload)
        print(
            "实际/期望状态码：",
            response.status_code,
            "/",
            status,
            "；回调次数：",
            calls,
        )
        print(
            "正文/历史：",
            body_ok,
            "；阶段：",
            protocol_ok,
            "；输入：",
            input_ok,
            "；通过：",
            passed,
        )
        if kind == "ask" and isinstance(body, dict):
            print(
                "返回会话：",
                body.get("session_id"),
                "；请求编号：",
                body.get("request_id"),
            )
            print("返回 checked：", body.get("checked"))
        if (
            kind == "history"
            and isinstance(body, dict)
            and isinstance(body.get("turns"), list)
        ):
            print(
                "实际/期望历史条数：", len(body["turns"]), "/", len(expected["turns"])
            )
            print(
                "实际问题顺序：",
                [
                    turn.get("question")
                    for turn in body["turns"]
                    if isinstance(turn, dict)
                ],
            )
        if events:
            print(
                "本次阶段：",
                [
                    (event.get("stage"), event.get("state"))
                    for event in events
                    if isinstance(event, dict)
                ],
            )
        if not body_ok:
            print("实际正文：", body, "；期望正文：", expected)

    # 与 Day51A 相同：普通代码异常显示 500，以便其余案例仍可检查。
    with TestClient(app, raise_server_exceptions=False) as client:
        check(client, "健康检查", "GET", "/health", None, 200, kind="health")
        check(
            client,
            "未知会话为空",
            "GET",
            "/sessions/room-a/history",
            None,
            200,
            kind="history",
            session="room-a",
        )
        check(
            client,
            "会话 A 首轮并清理空白",
            "POST",
            "/ask",
            {"session_id": " room-a ", "question": " 地点 "},
            200,
            kind="ask",
            session="room-a",
            question="地点",
        )
        check(
            client,
            "会话 B 首轮",
            "POST",
            "/ask",
            {"session_id": "room-b", "question": "地点"},
            200,
            kind="ask",
            session="room-b",
            question="地点",
        )
        check(
            client,
            "会话 A 第二轮",
            "POST",
            "/ask",
            {"session_id": "room-a", "question": "时间"},
            200,
            kind="ask",
            session="room-a",
            question="时间",
        )
        check(
            client,
            "A 的两轮按顺序并清理路径空白",
            "GET",
            "/sessions/%20room-a%20/history",
            None,
            200,
            kind="history",
            session="room-a",
        )
        check(
            client,
            "B 不混入 A",
            "GET",
            "/sessions/room-b/history",
            None,
            200,
            kind="history",
            session="room-b",
        )
        check(
            client,
            "空证据也是正常记录",
            "POST",
            "/ask",
            {"session_id": "room-a", "question": "无资料"},
            200,
            kind="ask",
            session="room-a",
            question="无资料",
        )
        check(
            client,
            "空白问题无回调",
            "POST",
            "/ask",
            {"session_id": "room-a", "question": "  "},
            400,
            detail="question 不能只有空白",
        )
        check(
            client,
            "空白会话无回调",
            "POST",
            "/ask",
            {"session_id": "  ", "question": "地点"},
            400,
            detail="session_id 不能只有空白",
        )
        check(client, "模型拒绝缺字段", "POST", "/ask", {"question": "地点"}, 422)
        check(client, "错误方法", "GET", "/ask", None, 405)
        check(client, "未知路径", "GET", "/unknown", None, 404)
        check(
            client,
            "历史路径的空白编号",
            "GET",
            "/sessions/%20%20/history",
            None,
            400,
            detail="session_id 不能只有空白",
        )
        check(
            client,
            "检索超时",
            "POST",
            "/ask",
            {"session_id": "room-a", "question": "检索超时"},
            500,
            question="检索超时",
            failed_stage="retrieve",
            error_type="TimeoutError",
        )
        check(
            client,
            "失败不追加历史",
            "GET",
            "/sessions/room-a/history",
            None,
            200,
            kind="history",
            session="room-a",
        )
    with TestClient(app, raise_server_exceptions=False) as another_client:
        check(
            another_client,
            "换客户端仍保留历史",
            "GET",
            "/sessions/room-a/history",
            None,
            200,
            kind="history",
            session="room-a",
        )
    fresh = factory(fixture.retrieve, fixture.request, fixture.emit)
    with TestClient(fresh, raise_server_exceptions=False) as client:
        check(
            client,
            "新应用历史为空",
            "GET",
            "/sessions/room-a/history",
            None,
            200,
            kind="history",
            session="room-a",
            isolated=True,
            distinct=fresh is not app,
        )
    with TestClient(app, raise_server_exceptions=False) as client:
        check(
            client,
            "新建应用没有清空旧应用",
            "GET",
            "/sessions/room-a/history",
            None,
            200,
            kind="history",
            session="room-a",
        )
    _finish(run_dir, results)
