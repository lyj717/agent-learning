"""Day61 的 pytest 外壳：把学员的五个检查接入现有测试入口。

检查逻辑在 week08 的练习文件里；这里只负责让 `pytest tests` 能收集到。
正常版下应 5 passed；故障版由 Day61 检查器单独验证。
"""

from weeks.week08_evaluation_reliability.exercises.day61_failure_exercises import (
    check_citation_grounding,
    check_format_schema,
    check_loop_limit,
    check_tool_allowlist,
    check_tool_authorization,
)


def test_loop_limit() -> None:
    """循环不超过步数上限。"""
    check_loop_limit()


def test_tool_allowlist() -> None:
    """未知工具被拒绝。"""
    check_tool_allowlist()


def test_citation_grounding() -> None:
    """引用编号都在证据内。"""
    check_citation_grounding()


def test_format_schema() -> None:
    """回答格式符合键与类型要求。"""
    check_format_schema()


def test_tool_authorization() -> None:
    """越权工具与路径被拒绝。"""
    check_tool_authorization()
