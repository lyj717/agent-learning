"""Day55 A2 的检查器：工具白名单、参数范围与拒绝原因。

不含参考实现，不执行真实工具、不访问文件或网络。
"""

import json
from pathlib import Path
from typing import Any

READ_PREFIX = "/data/public/"
SEARCH_MAX = 200

POLICY = {
    "read_file": {"prefix": READ_PREFIX},
    "search": {"max_len": SEARCH_MAX},
}


def run_case(
    fn: Any,
    name: str,
    tool: str,
    args: dict[str, str],
    expected_allowed: bool,
    expected_reason: str,
) -> dict[str, object]:
    """跑一组：允许与否、拒绝原因，以及拒绝时是否泄露路径。"""
    allowed: bool | None = None
    reason: str | None = None
    error: str | None = None
    try:
        allowed, reason = fn(tool, args, POLICY)
    except Exception as caught:  # noqa: BLE001 - 检查器记录全部失败。
        error = f"{type(caught).__name__}: {caught}"
    passed = all(
        [
            allowed == expected_allowed,
            reason == expected_reason,
            error is None,
            reason is not None and READ_PREFIX not in reason,
        ]
    )
    row = {
        "case": name,
        "passed": passed,
        "tool": tool,
        "args": args,
        "allowed": allowed,
        "reason": reason,
        "error": error,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"  {tool}({args}) → allowed={allowed}，reason={reason}")
    print(f"  期望 allowed={expected_allowed}，reason={expected_reason}；异常={error}")
    return row


def check_cases(fn: Any, run_dir: Path) -> None:
    """汇总八组；失败也保存 JSON，然后明确报未通过。"""
    cases = [
        ("read_public", "read_file", {"path": "/data/public/rule.md"}, True, "允许"),
        (
            "read_traversal",
            "read_file",
            {"path": "/data/public/../private.md"},
            False,
            "路径越界",
        ),
        (
            "read_outside",
            "read_file",
            {"path": "/data/private/secret.md"},
            False,
            "路径越界",
        ),
        ("read_missing", "read_file", {}, False, "缺少参数"),
        ("search_ok", "search", {"query": "二楼"}, True, "允许"),
        ("search_empty", "search", {"query": ""}, False, "缺少参数"),
        ("search_long", "search", {"query": "x" * 300}, False, "查询过长"),
        ("injected_delete", "delete_file", {"path": "/data"}, False, "工具不在白名单"),
    ]
    rows = []
    for name, tool, args, allowed, reason in cases:
        row = run_case(fn, name, tool, args, allowed, reason)
        rows.append(row)
        (run_dir / f"{name}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "tool_auth_checks.json").write_text(
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
    assert passed_count == len(rows), "工具授权还有未通过项，请对照上面的实际与期望"
