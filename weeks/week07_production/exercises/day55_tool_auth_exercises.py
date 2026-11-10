"""Day55 A2：执行工具前的授权检查，挡住越权参数与注入诱导的调用。

入口提供工具名、参数和策略，检查器逐组打印实际与期望；你只写 authorize。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day55.day55_tool_auth_checks import check_cases


def authorize(
    tool_name: str, args: dict[str, str], policy: dict[str, dict[str, object]]
) -> tuple[bool, str]:
    """执行工具前的授权检查：返回 (是否允许, 固定短原因)。"""
    prefix = policy["read_file"]["prefix"]
    max_len = policy["search"]["max_len"]
    if not isinstance(prefix, str):
        return False, "工具不在白名单"
    if not isinstance(max_len, int):
        return False, "工具不在白名单"
    if tool_name not in policy:
        return False, "工具不在白名单"
    if tool_name == "read_file":
        if (
            "path" not in set(args)
            or not isinstance(args["path"], str)
            or not args["path"].strip()
        ):
            return False, "缺少参数"
        if not args["path"].startswith(prefix) or ".." in args["path"]:
            return False, "路径越界"
        return True, "允许"
    if tool_name == "search":
        if (
            "query" not in args
            or not isinstance(args["query"], str)
            or not args["query"].strip()
        ):
            return False, "缺少参数"
        if len(args["query"]) > max_len:
            return False, "查询过长"
        return True, "允许"
    return False, "工具不在白名单"


def run_exercise(run_dir: Path) -> None:
    """把学员的授权函数交给八组检查，保存实际结果；无需修改。"""
    check_cases(authorize, run_dir)


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "tool_auth_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 8},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day55/outputs",
        origin_env="DAY55_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
