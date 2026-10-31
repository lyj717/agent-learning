"""AI 维护的 Day 43 人工对照，仅提供输入和期望，不实现学员的指标函数。

片段名、排名与相关标签都是教学数据；本文件不读取 Week 5 真实基线。
"""

from collections.abc import Callable
from copy import deepcopy
from math import isclose

SIGNUP = "visit.md#L1-L2"
RETURN = "visit.md#L3-L4"
HOURS = "visit.md#L5-L6"
ADDRESS = "visit.md#L7-L8"
UNRELATED = "meals.md#L1-L2"
OTHER = "travel.md#L1-L2"


def _same(actual: object, expected: dict) -> bool:
    """核对字段、整数类型、None 与浮点误差，拒绝额外或缺失字段。"""
    if not isinstance(actual, dict) or actual.keys() != expected.keys():
        return False
    for key, value in expected.items():
        current = actual[key]
        if isinstance(value, float):
            # isclose(a, b, ...)：按相对与绝对误差比较浮点数，避免运算尾差误报。
            if type(current) not in {int, float} or not isclose(
                current, value, rel_tol=1e-9, abs_tol=1e-12
            ):
                return False
        elif type(current) is not type(value) or current != value:
            return False
    return True


def _run_cases(
    learner_fn: Callable[..., dict], cases: list[tuple[str, tuple, dict | type]]
) -> None:
    """运行对照及输入不变检查；失败全部列出，最后让进程明确失败。"""
    print("来源：AI 人工教学样本；没有真实模型、向量或数据库请求。")
    failures = 0
    for number, (name, arguments, expected) in enumerate(cases, start=1):
        # deepcopy(对象)：独立复制嵌套容器，用于核对调用前后输入未变。
        before = deepcopy(arguments)
        print(f"\n对照 {number}｜{name}")
        print(f"输入={arguments}")
        try:
            actual = learner_fn(*arguments)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，结束时统一报错。
            consistent = expected is ValueError and isinstance(error, ValueError)
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = isinstance(expected, dict) and _same(actual, expected)
            print(f"实际={actual}")
        expected_display = "ValueError" if expected is ValueError else expected
        print(f"期望={expected_display}；结果一致={consistent}")
        unchanged = arguments == before
        print(f"输入未改动={unchanged}；期望=True；一致={unchanged}")
        failures += int(not consistent) + int(not unchanged)
    print(f"\n汇总：{len(cases)} 组结果 + {len(cases)} 组输入检查；不一致={failures}")
    if failures:
        raise AssertionError(f"共 {failures} 项不一致，详见上方全部对照")


def run_a(score_fn: Callable[..., dict]) -> None:
    """展示九组正常/空边界及七组非法参数，不提供单题计算实现。"""
    ranked = [SIGNUP, UNRELATED, OTHER, RETURN]
    cases = [
        (
            "只取前三条：两个相关片段同源，只找回其中一个",
            (ranked.copy(), {SIGNUP, RETURN}, 3),
            {
                "retrieved_count": 3,
                "relevant_count": 2,
                "matched_count": 1,
                "hit": 1,
                "recall": 0.5,
                "precision": 1 / 3,
            },
        ),
        (
            "取前四条：同一排名，两个相关片段均进入",
            (ranked.copy(), {SIGNUP, RETURN}, 4),
            {
                "retrieved_count": 4,
                "relevant_count": 2,
                "matched_count": 2,
                "hit": 1,
                "recall": 1.0,
                "precision": 0.5,
            },
        ),
        (
            "相关片段在 k 之外",
            ([UNRELATED, OTHER, SIGNUP], {SIGNUP}, 2),
            {
                "retrieved_count": 2,
                "relevant_count": 1,
                "matched_count": 0,
                "hit": 0,
                "recall": 0.0,
                "precision": 0.0,
            },
        ),
        (
            "返回不足 k 条，Precision 仍除以 k",
            ([SIGNUP], {SIGNUP}, 3),
            {
                "retrieved_count": 1,
                "relevant_count": 1,
                "matched_count": 1,
                "hit": 1,
                "recall": 1.0,
                "precision": 1 / 3,
            },
        ),
        (
            "有答案但返回空候选",
            ([], {SIGNUP}, 3),
            {
                "retrieved_count": 0,
                "relevant_count": 1,
                "matched_count": 0,
                "hit": 0,
                "recall": 0.0,
                "precision": 0.0,
            },
        ),
        (
            "已确认无答案，仍返回候选",
            ([UNRELATED, OTHER], set(), 3),
            {
                "retrieved_count": 2,
                "relevant_count": 0,
                "matched_count": 0,
                "hit": None,
                "recall": None,
                "precision": None,
            },
        ),
        (
            "已确认无答案，返回也为空",
            ([], set(), 3),
            {
                "retrieved_count": 0,
                "relevant_count": 0,
                "matched_count": 0,
                "hit": None,
                "recall": None,
                "precision": None,
            },
        ),
        (
            "三个相关项只找回一个",
            ([RETURN, UNRELATED], {SIGNUP, RETURN, HOURS}, 2),
            {
                "retrieved_count": 2,
                "relevant_count": 3,
                "matched_count": 1,
                "hit": 1,
                "recall": 1 / 3,
                "precision": 0.5,
            },
        ),
        (
            "省略 k 使用默认值 3",
            ([SIGNUP, RETURN], {SIGNUP, RETURN}),
            {
                "retrieved_count": 2,
                "relevant_count": 2,
                "matched_count": 2,
                "hit": 1,
                "recall": 1.0,
                "precision": 2 / 3,
            },
        ),
        ("k=0", ([], {SIGNUP}, 0), ValueError),
        ("k 为负数", ([], {SIGNUP}, -1), ValueError),
        ("k 为 bool", ([], {SIGNUP}, True), ValueError),
        ("k 为小数", ([], {SIGNUP}, 1.5), ValueError),
        (
            "重复编号，即使重复发生在 k 之外",
            ([SIGNUP, RETURN, RETURN], {SIGNUP}, 1),
            ValueError,
        ),
        ("无答案也要检查重复编号", ([UNRELATED, UNRELATED], set(), 3), ValueError),
        ("无答案也要检查 k", ([], set(), 0), ValueError),
    ]
    _run_cases(score_fn, cases)


def run_b(evaluate_fn: Callable[..., dict]) -> None:
    """展示跨题平均与无答案分组，覆盖空集、非法参数及 A 的错误传播。"""
    first = {"ranked_ids": [SIGNUP], "relevant_ids": {SIGNUP, RETURN, HOURS, ADDRESS}}
    second = {"ranked_ids": [UNRELATED], "relevant_ids": {RETURN}}
    no_answer = {"ranked_ids": [UNRELATED], "relevant_ids": set()}
    cases = [
        (
            "两道有答案题加一道无答案题：平均只除以 2",
            ([deepcopy(first), deepcopy(second), deepcopy(no_answer)], 3),
            {
                "total": 3,
                "answerable_count": 2,
                "no_answer_count": 1,
                "mean_hit": 0.5,
                "mean_recall": 0.125,
                "mean_precision": 1 / 6,
                "no_answer_with_candidates": 1,
            },
        ),
        (
            "两个有答案题：逐题平均，不能用命中总数 / 相关总数",
            ([deepcopy(first), deepcopy(second)], 3),
            {
                "total": 2,
                "answerable_count": 2,
                "no_answer_count": 0,
                "mean_hit": 0.5,
                "mean_recall": 0.125,
                "mean_precision": 1 / 6,
                "no_answer_with_candidates": 0,
            },
        ),
        (
            "只有无答案题：一题有候选、一题没有",
            ([deepcopy(no_answer), {"ranked_ids": [], "relevant_ids": set()}], 3),
            {
                "total": 2,
                "answerable_count": 0,
                "no_answer_count": 2,
                "mean_hit": None,
                "mean_recall": None,
                "mean_precision": None,
                "no_answer_with_candidates": 1,
            },
        ),
        (
            "空样本",
            ([], 3),
            {
                "total": 0,
                "answerable_count": 0,
                "no_answer_count": 0,
                "mean_hit": None,
                "mean_recall": None,
                "mean_precision": None,
                "no_answer_with_candidates": 0,
            },
        ),
        (
            "单题并省略 k 使用默认值 3",
            ([{"ranked_ids": [SIGNUP, RETURN], "relevant_ids": {SIGNUP, RETURN}}],),
            {
                "total": 1,
                "answerable_count": 1,
                "no_answer_count": 0,
                "mean_hit": 1.0,
                "mean_recall": 1.0,
                "mean_precision": 2 / 3,
                "no_answer_with_candidates": 0,
            },
        ),
        ("空样本也拒绝 k=0", ([], 0), ValueError),
        ("空样本也拒绝 bool", ([], False), ValueError),
        ("空样本也拒绝负数", ([], -2), ValueError),
        ("空样本也拒绝小数", ([], 2.5), ValueError),
        (
            "第二题重复编号时传播 A 的异常",
            (
                [
                    deepcopy(first),
                    {"ranked_ids": [RETURN, RETURN], "relevant_ids": {RETURN}},
                ],
                3,
            ),
            ValueError,
        ),
        (
            "k=1：相关片段排第二，不能计入前一条",
            ([{"ranked_ids": [UNRELATED, SIGNUP], "relevant_ids": {SIGNUP}}], 1),
            {
                "total": 1,
                "answerable_count": 1,
                "no_answer_count": 0,
                "mean_hit": 0.0,
                "mean_recall": 0.0,
                "mean_precision": 0.0,
                "no_answer_with_candidates": 0,
            },
        ),
        (
            "k=4：两个相关片段排第三和第四，均应计入",
            (
                [
                    {
                        "ranked_ids": [UNRELATED, OTHER, SIGNUP, RETURN],
                        "relevant_ids": {SIGNUP, RETURN},
                    }
                ],
                4,
            ),
            {
                "total": 1,
                "answerable_count": 1,
                "no_answer_count": 0,
                "mean_hit": 1.0,
                "mean_recall": 1.0,
                "mean_precision": 0.5,
                "no_answer_with_candidates": 0,
            },
        ),
    ]
    _run_cases(evaluate_fn, cases)
