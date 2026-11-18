"""Day61：五类失败模式的确定性检查与故障版验证。"""

# 脚本直接运行时要把仓库根加进 sys.path，之后的导入必然不在文件顶部。

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day61.day61_fixtures import (
    FormatError,
    ToolError,
    answer_with_citations,
    authorize_tool,
    dispatch_tool,
    parse_answer,
    run_agent_loop,
)

DAY61 = REPO_ROOT / "weeks/week08_evaluation_reliability/demos/day61"


def check_loop_limit() -> None:
    """检查循环步数不超过上限。"""
    assert run_agent_loop(max_steps=5)["steps"] <= 5


def check_tool_allowlist() -> None:
    """检查未知工具被分发层拒绝。"""
    with pytest.raises(ToolError):
        dispatch_tool("delete_file", {"path": "notes/a.md"})


def check_citation_grounding() -> None:
    """检查回答引用的编号都在证据内。"""
    answer = answer_with_citations("示例问题")
    assert answer["status"] == "answered"
    cited_ids = answer["cited_ids"]
    assert cited_ids
    for cited_id in cited_ids:
        assert cited_id in answer["evidence_ids"]


def check_format_schema() -> None:
    """检查回答格式的键、类型与允许值。"""
    assert set(
        parse_answer(raw='{"status": "answered", "answer": "x", "cited_ids": ["c1"]}')
    ) == {"status", "answer", "cited_ids"}
    with pytest.raises(FormatError):
        parse_answer('{"foo": 1}')
    with pytest.raises(FormatError):
        parse_answer("not json")


def check_tool_authorization() -> None:
    """检查工具名与路径的权限边界。"""
    assert authorize_tool("read_file", "notes/a.md") is True
    with pytest.raises(PermissionError):
        authorize_tool("delete_file", "notes/a.md")
    with pytest.raises(PermissionError):
        authorize_tool("read_file", "../secret")


def main() -> None:
    """运行检查器：正常版应全过，故障版应全部被抓住。"""
    from weeks.week08_evaluation_reliability.demos.day61.day61_checks import (
        run_checks,
    )

    checks = [
        ("循环上限", check_loop_limit),
        ("工具白名单", check_tool_allowlist),
        ("引用落地", check_citation_grounding),
        ("格式校验", check_format_schema),
        ("工具授权", check_tool_authorization),
    ]
    run_logged(
        "check",
        lambda _run_dir: run_checks(checks),
        config={"model_calls": 0},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY61 / "outputs",
        origin_env="DAY61_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
