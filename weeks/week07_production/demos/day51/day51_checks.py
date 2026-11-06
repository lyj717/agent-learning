"""AI 维护的 Day51A 对照入口；不请求网络、检索库或模型。"""

import copy
import json
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError


def _finish(run_dir: Path, results: list[dict]) -> None:
    """保存全部对照后统一报错，避免只报告第一处问题。"""
    (run_dir / "checks.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    passed = sum(row["passed"] for row in results)
    print(f"对照汇总：{passed}/{len(results)} 组通过")
    if passed != len(results):
        raise AssertionError("请对照本轮实际与期望，未全部通过")


def run_a(model: type[BaseModel], run_dir: Path) -> None:
    """检查请求模型的严格类型、必填/默认值、范围和额外字段。"""
    if not model.model_fields:
        raise NotImplementedError("第 A 题的请求模型还没写")
    cases = [
        ("正常两字段", {"question": "借阅地点", "top_k": 4}, True),
        ("默认 top_k", {"question": "借阅地点"}, True),
        ("空格字符串在模型层合法", {"question": "  "}, True),
        ("空字符串", {"question": ""}, False),
        ("question 类型错", {"question": 7}, False),
        ("缺 question", {}, False),
        ("top_k 下界", {"question": "借阅地点", "top_k": 0}, False),
        ("top_k 上界", {"question": "借阅地点", "top_k": 5}, False),
        ("top_k 字符串", {"question": "借阅地点", "top_k": "2"}, False),
        ("top_k 布尔值", {"question": "借阅地点", "top_k": True}, False),
        ("多余字段", {"question": "借阅地点", "debug": True}, False),
    ]
    results = []
    for label, payload, accepted in cases:
        original = copy.deepcopy(payload)
        value = None
        rejected = False
        try:
            # model_validate(字典)：返回模型实例；不合格时抛 ValidationError。
            value = model.model_validate(payload)
        except ValidationError:
            rejected = True
        if accepted:
            expected = {
                "question": payload["question"],
                "top_k": payload.get("top_k", 2),
            }
            actual = value.model_dump() if value is not None else None
            correct = not rejected and actual == expected
        else:
            expected = "ValidationError"
            actual = "ValidationError" if rejected else value.model_dump()
            correct = rejected
        passed = bool(correct and payload == original)
        print(f"\n{label}；输入={payload}")
        print(
            "实际：", actual, "；期望：", expected, "；输入保持：", payload == original
        )
        print("通过：", passed)
        results.append(
            {"case": label, "input": payload, "actual": actual, "passed": passed}
        )
    _finish(run_dir, results)


def run_b(factory: Callable[[], FastAPI], run_dir: Path) -> None:
    """用本地请求经过学员应用，核对状态码、正文与方法/路径边界。"""
    app = factory()
    if not isinstance(app, FastAPI):
        raise TypeError("create_app 必须返回 FastAPI 应用对象")
    cases = [
        ("健康检查", "GET", "/health", None, 200, {"status": "ok", "mode": "offline"}),
        (
            "正常清理空白",
            "POST",
            "/inspect",
            {"question": " 开放时间 ", "top_k": 3},
            200,
            {"question": "开放时间", "top_k": 3, "character_count": 4},
        ),
        (
            "省略 top_k",
            "POST",
            "/inspect",
            {"question": "借阅地点"},
            200,
            {"question": "借阅地点", "top_k": 2, "character_count": 4},
        ),
        ("空字符串", "POST", "/inspect", {"question": ""}, 422, None),
        (
            "只有空格",
            "POST",
            "/inspect",
            {"question": "  "},
            400,
            {"detail": "question 不能只有空白"},
        ),
        ("top_k 过小", "POST", "/inspect", {"question": "地点", "top_k": 0}, 422, None),
        ("top_k 过大", "POST", "/inspect", {"question": "地点", "top_k": 5}, 422, None),
        (
            "top_k 类型错",
            "POST",
            "/inspect",
            {"question": "地点", "top_k": "2"},
            422,
            None,
        ),
        ("缺 question", "POST", "/inspect", {}, 422, None),
        (
            "额外字段",
            "POST",
            "/inspect",
            {"question": "地点", "debug": True},
            422,
            None,
        ),
        ("错误方法", "GET", "/inspect", None, 405, None),
        ("未知路径", "GET", "/unknown", None, 404, None),
    ]
    results = []
    # 普通代码错误显示为 500，让后面的案例仍能检查；不把失败改成成功。
    with TestClient(app, raise_server_exceptions=False) as client:
        for label, method, path, payload, status, expected_body in cases:
            # request(method, path, json=数据)：在应用内执行指定方法，不建立网络连接。
            response = client.request(method, path, json=payload)
            try:
                body = response.json()
            except ValueError:
                body = {"unparsed_text": response.text}
            body_ok = (
                body == expected_body
                if expected_body is not None
                else (isinstance(body, dict) and "detail" in body)
            )
            passed = response.status_code == status and body_ok
            row = {
                "case": label,
                "method": method,
                "path": path,
                "input": payload,
                "status": response.status_code,
                "body": body,
                "passed": passed,
            }
            with (run_dir / "requests.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"\n{label}：{method} {path}；发送 JSON={payload}")
            print("实际/期望状态码：", response.status_code, "/", status)
            if status == 422:
                print("正文有 detail：", isinstance(body, dict) and "detail" in body)
            else:
                print("实际正文：", body, "；期望正文：", expected_body or "含 detail")
            print("通过：", passed)
            results.append(row)
    _finish(run_dir, results)
