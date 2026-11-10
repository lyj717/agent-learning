"""Day55 A1 的检查器：错误映射、公开字段与敏感信息不泄露。

不含参考实现，不请求模型、HTTP 或真实密钥。
"""

import json
from pathlib import Path
from typing import Any

SECRET = "sk-live-SECRET-9f3a"
PATH = "/srv/private/prompt.md"


def run_case(fn: Any, name: str, exc: BaseException, status: int, detail: str) -> dict:
    """跑一组：状态码、正文、字段集合与泄露检查。"""
    request_id = "req-check-001"
    body: dict[str, str] | None = None
    error: str | None = None
    try:
        status_code, body = fn(exc, request_id)
    except Exception as caught:  # noqa: BLE001 - 检查器记录全部失败。
        status_code = None
        error = f"{type(caught).__name__}: {caught}"
    text = json.dumps(body, ensure_ascii=False) if body is not None else ""
    expected_body = {"detail": detail, "request_id": request_id}
    passed = all(
        [
            status_code == status,
            body == expected_body,
            SECRET not in text,
            PATH not in text,
            str(exc) not in text,
            error is None,
        ]
    )
    row = {
        "case": name,
        "passed": passed,
        "status": status_code,
        "expected_status": status,
        "body": body,
        "error": error,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"  状态码={status_code}（期望 {status}）；正文={body}")
    print(f"  期望正文={expected_body}；异常={error}")
    return row


def check_cases(fn: Any, run_dir: Path) -> None:
    """汇总五组；失败也保存 JSON，然后明确报未通过。"""
    cases = [
        (
            "timeout",
            TimeoutError(f"连接 {SECRET} 超时，读取 {PATH} 失败"),
            504,
            "上游超时",
        ),
        ("connection", ConnectionError(f"连不上 {PATH}"), 502, "上游连接失败"),
        ("bad_value", ValueError(f"参数里出现 {SECRET}"), 400, "请求不合法"),
        ("unknown", KeyError(f"内部键 {PATH} 不存在"), 500, "内部错误"),
        ("runtime", RuntimeError("内部故障，含 sk-live- 前缀"), 500, "内部错误"),
    ]
    rows = []
    for name, exc, status, detail in cases:
        row = run_case(fn, name, exc, status, detail)
        rows.append(row)
        (run_dir / f"{name}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "error_checks.json").write_text(
        json.dumps(
            {"passed": passed_count, "total": len(rows), "cases": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"\n本次 {passed_count}/{len(rows)}，模型与 HTTP 调用均为 0；实际结果已保存。"
    )
    assert passed_count == len(rows), "错误响应还有未通过项，请对照上面的实际与期望"
