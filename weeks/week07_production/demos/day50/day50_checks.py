"""AI 维护的 Day50 人工对照：只验证日志行为，不访问真实资料与模型。"""

# 各轮回调都在本轮同步执行完才进入下一轮，没有延后执行或跨轮保存。
# ruff: noqa: B023

import copy
import json
import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.documents import Document

FAKE_SECRET = "AI_FAKE_SECRET_ONLY_FOR_CHECK"


def _emit(run_dir: Path, events: list[dict], event: dict) -> None:
    """逐次保存并打印实际事件，保留副本以查字段和调用顺序。"""
    events.append(copy.deepcopy(event))
    line = json.dumps(event, ensure_ascii=False, allow_nan=False)
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")
    print("事件：", line)


def _valid_events(events: list[dict], expected: list[tuple[str, str]]) -> bool:
    """检查精确字段、状态顺序、耗时类型和敏感内容，拒绝多余载荷。"""
    if len(events) != len(expected):
        return False
    for event, (stage, state) in zip(events, expected, strict=True):
        fields = {"request_id", "stage", "state"}
        if state != "start":
            fields.add("elapsed_ms")
        if state == "error":
            fields.add("error_type")
        if set(event) != fields or event["stage"] != stage or event["state"] != state:
            return False
        if not isinstance(event["request_id"], str) or not event["request_id"]:
            return False
        if state != "start":
            value = event["elapsed_ms"]
            if not isinstance(value, float) or not math.isfinite(value) or value < 0:
                return False
        if state == "error" and not isinstance(event["error_type"], str):
            return False
    return FAKE_SECRET not in json.dumps(events, ensure_ascii=False)


def _finish(run_dir: Path, results: list[dict]) -> None:
    """保存全部对照后才统一报错，便于一次查看全部剩余问题。"""
    (run_dir / "checks.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    count = sum(item["passed"] for item in results)
    print(f"对照汇总：{count}/{len(results)} 组通过")
    if count != len(results):
        raise AssertionError("对照未全部通过，请看以上各组实际与期望")


def run_a(function: Callable, run_dir: Path) -> None:
    """检查任意返回值、异常身份、中断边界及开始事件先于动作。"""
    results = []
    cases = [
        ("正常对象与毫秒计时", {"private": FAKE_SECRET}, None),
        ("None 是正常返回", None, None),
        ("False 是正常返回", False, None),
        ("普通异常原样抛出", None, TimeoutError(FAKE_SECRET)),
        ("中断不伪装普通错误", None, KeyboardInterrupt(FAKE_SECRET)),
    ]
    for index, (label, value, failure) in enumerate(cases, start=1):
        print(f"\nA{index} {label}")
        events: list[dict] = []
        action_count = 0
        start_before_action = False
        request_id = f"a-{index}"

        def emit(event: dict) -> None:
            """将本组事件写入公共证据文件。"""
            # run_dir、events 已在外层准备好；传给练习的 emit 只接收 event。
            _emit(run_dir, events, event)

        def action() -> Any:
            """检查动作开始前已有 start，模拟已知返回或失败。"""
            nonlocal action_count, start_before_action
            action_count += 1
            start_before_action = len(events) == 1 and events[0]["state"] == "start"
            if index == 1:
                time.sleep(0.01)
            if failure is not None:
                raise failure
            return value

        caught = None
        returned = object()
        try:
            returned = function(request_id, "probe", action, emit)
        except NotImplementedError:
            raise
        except BaseException as error:  # noqa: BLE001 - 专门检查中断是否原样传出。
            caught = error
        if failure is None:
            expected = [("probe", "start"), ("probe", "ok")]
            result_ok = caught is None and returned is value
        elif isinstance(failure, Exception):
            expected = [("probe", "start"), ("probe", "error")]
            result_ok = caught is failure
            result_ok = (
                result_ok
                and bool(events)
                and events[-1].get("error_type") == type(failure).__name__
            )
        else:
            expected = [("probe", "start")]
            result_ok = caught is failure
        valid = _valid_events(events, expected)
        ids_ok = all(event.get("request_id") == request_id for event in events)
        elapsed_ok = index != 1 or (
            len(events) == 2 and 5 <= events[-1].get("elapsed_ms", -1) < 60000
        )
        passed = bool(
            result_ok
            and valid
            and ids_ok
            and elapsed_ok
            and start_before_action
            and action_count == 1
        )
        print(
            f"实际：返回/异常身份={result_ok}，事件协议={valid}，ID={ids_ok}，"
            f"开始先于动作={start_before_action}，调用次数={action_count}，计时={elapsed_ok}"
        )
        print("期望：以上均 True，动作调用 1 次；通过=", passed)
        results.append({"case": f"a{index}", "label": label, "passed": passed})
    _finish(run_dir, results)


def run_b(function: Callable, run_dir: Path) -> None:
    """检查真实旧业务形状中的四阶段、短路、关联 ID 及输入保持。"""
    results = []
    seen_ids: set[str] = set()
    labels = [
        "正常证据回答",
        "空候选跳过生成",
        "检索失败",
        "生成失败",
        "JSON 不合法",
        "响应未正常结束",
        "准备消息失败",
        "引用编号越界",
    ]
    for index, label in enumerate(labels, start=1):
        print(f"\nB{index} {label}")
        events: list[dict] = []
        evidence = [
            Document(
                id="shelf.md#L1-L1",
                page_content="请到二楼取书。",
                metadata={"source": "shelf.md", "line_start": 1, "line_end": 1},
            )
        ]
        if index == 2:
            evidence = []
        if index == 7:
            evidence[0].metadata.pop("source")
        checked = {
            "status": "answered",
            "answer": "请到二楼取书。",
            "cited_ids": ["shelf.md#L1-L1"],
        }
        response = {
            "raw_text": json.dumps(checked, ensure_ascii=False),
            "finish_reason": "stop",
            "usage": None,
        }
        if index == 5:
            response["raw_text"] = "not-json " + FAKE_SECRET
        if index == 6:
            response["finish_reason"] = "length"
        if index == 8:
            response["raw_text"] = json.dumps({**checked, "cited_ids": ["unknown"]})
        before = copy.deepcopy((evidence, response))
        calls = {"retrieve": 0, "request": 0}
        callback_inputs_ok = True
        failure = TimeoutError(FAKE_SECRET)

        def emit(event: dict) -> None:
            """保存本题实际日志。"""
            _emit(run_dir, events, event)

        def retrieve(question: str) -> list[Document]:
            """返回人工候选或触发指定失败，不访问数据库。"""
            nonlocal callback_inputs_ok
            calls["retrieve"] += 1
            callback_inputs_ok = callback_inputs_ok and question == "去哪里取书？"
            if index == 3:
                raise failure
            return evidence

        def request(messages: list[dict[str, str]]) -> dict:
            """检查沿用旧消息形状，返回替身响应或触发指定失败。"""
            nonlocal callback_inputs_ok
            calls["request"] += 1
            try:
                payload = json.loads(messages[1]["content"])
                callback_inputs_ok = callback_inputs_ok and (
                    [message["role"] for message in messages] == ["system", "user"]
                    and payload["question"] == "去哪里取书？"
                    and payload["evidence"][0]["id"] == evidence[0].id
                    and payload["evidence"][0]["text"] == evidence[0].page_content
                )
            except (IndexError, KeyError, TypeError, ValueError):
                callback_inputs_ok = False
            if index == 4:
                raise failure
            return response

        result = None
        caught = None
        try:
            result = function("去哪里取书？", retrieve, request, emit)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部组，不吞中断。
            caught = error
        stages = ["retrieve", "prepare", "generate", "validate"]
        failed_stage = {
            3: "retrieve",
            4: "generate",
            5: "validate",
            6: "validate",
            7: "prepare",
            8: "validate",
        }.get(index)
        expected: list[tuple[str, str]] = []
        for stage in stages:
            expected.append((stage, "start"))
            expected.append((stage, "error" if stage == failed_stage else "ok"))
            if stage == failed_stage or index == 2:
                break
        valid = _valid_events(events, expected)
        ids = {event.get("request_id") for event in events}
        request_id = next(iter(ids)) if len(ids) == 1 else None
        try:
            uuid_ok = (
                isinstance(request_id, str)
                and UUID(request_id).hex == request_id
                and UUID(request_id).version == 4
                and request_id not in seen_ids
            )
        except (ValueError, AttributeError):
            uuid_ok = False
        if isinstance(request_id, str):
            seen_ids.add(request_id)
        if index in (1, 2):
            result_ok = caught is None and result == {
                "request_id": request_id,
                "checked": checked if index == 1 else None,
            }
        else:
            error_type = {
                3: TimeoutError,
                4: TimeoutError,
                5: ValueError,
                6: ValueError,
                7: KeyError,
                8: ValueError,
            }[index]
            result_ok = isinstance(caught, error_type)
            if index in (3, 4):
                result_ok = result_ok and caught is failure
            result_ok = (
                result_ok
                and bool(events)
                and events[-1].get("error_type") == error_type.__name__
            )
        counts_ok = calls == {"retrieve": 1, "request": 0 if index in (2, 3, 7) else 1}
        unchanged = (evidence, response) == before
        passed = bool(
            result_ok
            and valid
            and uuid_ok
            and counts_ok
            and unchanged
            and callback_inputs_ok
        )
        print(
            f"实际：结果/异常={result_ok}，阶段协议={valid}，新请求ID={uuid_ok}，"
            f"回调次数={calls}，回调输入={callback_inputs_ok}，输入保持={unchanged}"
        )
        print(f"期望：阶段={expected}；检查均 True；通过={passed}")
        results.append({"case": f"b{index}", "label": label, "passed": passed})
    _finish(run_dir, results)
