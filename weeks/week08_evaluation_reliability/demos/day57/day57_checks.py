"""AI 维护的 Day57 人工对照：规则判分与基线比较的输入、期望。

只提供输入与期望，不实现学员的 judge_answer / compare_baseline。
题目文本与两版回答读自本目录 JSON；本轮期望写在本文件，
不从基线文件反推。数据为教学样本，不发起任何请求。
"""

import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

DAY57 = Path(__file__).resolve().parent

EXPECTED_V2 = {
    "q01": [],
    "q02": [],
    "q03": ["missing_points", "forbidden_text"],
    "q04": [],
    "q05": [],
    "q06": [],
    "q07": [],
    "q08": ["no_citation"],
}

ALL_IDS = ["q01", "q02", "q03", "q04", "q05", "q06", "q07", "q08"]


def _load(name: str) -> object:
    """读取本目录的 JSON 文件，统一用 UTF-8。"""
    return json.loads((DAY57 / name).read_text(encoding="utf-8"))


def _same_result(actual: object, expected: dict) -> bool:
    """核对返回字典的键、id、布尔值与失败项列表。"""
    if not isinstance(actual, dict) or set(actual) != {"id", "passed", "failed"}:
        return False
    return (
        actual["id"] == expected["id"]
        and type(actual["passed"]) is bool
        and actual["passed"] is expected["passed"]
        and actual["failed"] == expected["failed"]
    )


def _run_judge_cases(
    judge_fn: Callable[..., dict],
    cases: list[tuple[str, dict, dict, list[str]]],
) -> None:
    """逐组调用 judge_answer，打印实际与期望，最后统一报错。"""
    print("来源：AI 人工教学样本；没有模型、向量或网络请求。")
    result_failures = 0
    input_failures = 0
    for number, (name, case, answer, expected_failed) in enumerate(cases, start=1):
        before = deepcopy((case, answer))
        expected = {
            "id": case["id"],
            "passed": not expected_failed,
            "failed": expected_failed,
        }
        print(f"\n对照 {number}｜{name}")
        print(f"题目={case['id']}；回答={answer['answer']}")
        print(f"要点={case['must_include']}；禁词={case['must_not_include']}")
        print(f"引用={answer['cited_ids']}；检索结果={case['retrieved_ids']}")
        try:
            actual = judge_fn(case, answer)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
            consistent = False
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = _same_result(actual, expected)
            print(f"实际={actual}")
        print(f"期望={expected}；结果一致={consistent}")
        unchanged = (case, answer) == before
        print(f"输入未改动={unchanged}；期望=True；一致={unchanged}")
        result_failures += int(not consistent)
        input_failures += int(not unchanged)
    total = len(cases)
    print(
        f"\n汇总：结果一致 {total - result_failures}/{total}；"
        f"输入未改动 {total - input_failures}/{total}"
    )
    if result_failures or input_failures:
        raise AssertionError("存在不一致，详见上方全部对照")


def run_a(judge_fn: Callable[..., dict]) -> None:
    """运行八道真实题（v2 回答）与六组边界检查。"""
    cases = _load("day57_cases.json")
    answers = _load("day57_answers_v2.json")
    by_id = {case["id"]: case for case in cases}
    base = by_id["q01"]
    q01_text = answers["q01"]["answer"]
    q03 = by_id["q03"]

    rows = [
        (
            f"{case['id']}（v2 回答）",
            case,
            answers[case["id"]],
            EXPECTED_V2[case["id"]],
        )
        for case in cases
    ]
    rows += [
        (
            "status 不是 answered，只留 not_answered",
            base,
            {"status": "insufficient", "answer": "资料不足", "cited_ids": []},
            ["not_answered"],
        ),
        (
            "回答只有空白，只留 empty_answer",
            base,
            {
                "status": "answered",
                "answer": "   ",
                "cited_ids": [base["retrieved_ids"][0]],
            },
            ["empty_answer"],
        ),
        (
            "引用编号不在本次检索结果里",
            base,
            {
                "status": "answered",
                "answer": q01_text,
                "cited_ids": ["notes/python-notes.md#L99-L100"],
            },
            ["citation_not_retrieved"],
        ),
        (
            "缺要点并踩禁词，两个失败项都报",
            q03,
            {
                "status": "answered",
                "answer": "def f(x=[]) 就行。",
                "cited_ids": [q03["retrieved_ids"][0]],
            },
            ["missing_points", "forbidden_text"],
        ),
        (
            "完全不给引用",
            base,
            {"status": "answered", "answer": q01_text, "cited_ids": []},
            ["no_citation"],
        ),
        (
            "重复引用同一编号不算失败",
            base,
            {
                "status": "answered",
                "answer": q01_text,
                "cited_ids": [base["retrieved_ids"][0], base["retrieved_ids"][0]],
            },
            [],
        ),
    ]
    _run_judge_cases(judge_fn, rows)


def _same_compare(actual: object, expected: dict) -> bool:
    """核对四类结果的键集合与每个题号列表。"""
    return isinstance(actual, dict) and actual == expected


def _run_compare_cases(
    compare_fn: Callable[..., dict],
    cases: list[tuple[str, dict, dict, dict | type]],
) -> None:
    """逐组调用 compare_baseline，打印实际与期望，最后统一报错。"""
    print("来源：AI 人工教学样本；没有模型、向量或网络请求。")
    result_failures = 0
    input_failures = 0
    for number, (name, baseline, current, expected) in enumerate(cases, start=1):
        before = deepcopy((baseline, current))
        print(f"\n比较 {number}｜{name}")
        print(f"baseline={baseline}")
        print(f"current={current}")
        try:
            actual = compare_fn(baseline, current)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
            consistent = isinstance(expected, type) and isinstance(error, expected)
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = isinstance(expected, dict) and _same_compare(actual, expected)
            print(f"实际={actual}")
        expected_text = expected.__name__ if isinstance(expected, type) else expected
        print(f"期望={expected_text}；结果一致={consistent}")
        unchanged = (baseline, current) == before
        print(f"输入未改动={unchanged}；期望=True；一致={unchanged}")
        result_failures += int(not consistent)
        input_failures += int(not unchanged)
    total = len(cases)
    print(
        f"\n汇总：结果一致 {total - result_failures}/{total}；"
        f"输入未改动 {total - input_failures}/{total}"
    )
    if result_failures or input_failures:
        raise AssertionError("存在不一致，详见上方全部对照")


def run_b(compare_fn: Callable[..., dict]) -> None:
    """运行九组基线比较，含乱序输入、题号不一致与类型错误。"""
    all_pass = {case_id: {"passed": True} for case_id in ALL_IDS}
    one_fails = {case_id: {"passed": case_id != "q02"} for case_id in ALL_IDS}
    q03_fails = {case_id: {"passed": case_id != "q03"} for case_id in ALL_IDS}
    q08_fails = {case_id: {"passed": case_id != "q08"} for case_id in ALL_IDS}
    empty_result = {
        "regressed": [],
        "fixed": [],
        "still_failing": [],
        "unchanged_pass": [],
    }

    cases = [
        (
            "两版完全相同",
            all_pass,
            deepcopy(all_pass),
            {**deepcopy(empty_result), "unchanged_pass": ALL_IDS},
        ),
        (
            "只修好 q02",
            one_fails,
            all_pass,
            {
                **deepcopy(empty_result),
                "fixed": ["q02"],
                "unchanged_pass": [i for i in ALL_IDS if i != "q02"],
            },
        ),
        (
            "只改坏 q03",
            all_pass,
            q03_fails,
            {
                **deepcopy(empty_result),
                "regressed": ["q03"],
                "unchanged_pass": [i for i in ALL_IDS if i != "q03"],
            },
        ),
        (
            "一修好一改坏：总数不变",
            one_fails,
            q03_fails,
            {
                "regressed": ["q03"],
                "fixed": ["q02"],
                "still_failing": [],
                "unchanged_pass": [i for i in ALL_IDS if i not in {"q02", "q03"}],
            },
        ),
        (
            "两次都失败，不算回归",
            q08_fails,
            q08_fails,
            {
                **deepcopy(empty_result),
                "still_failing": ["q08"],
                "unchanged_pass": [i for i in ALL_IDS if i != "q08"],
            },
        ),
        (
            "输入顺序打乱，输出仍按题号升序",
            {
                "q03": {"passed": True},
                "q01": {"passed": True},
                "q02": {"passed": False},
                "q04": {"passed": False},
            },
            {
                "q04": {"passed": False},
                "q02": {"passed": False},
                "q01": {"passed": True},
                "q03": {"passed": True},
            },
            {
                "regressed": [],
                "fixed": [],
                "still_failing": ["q02", "q04"],
                "unchanged_pass": ["q01", "q03"],
            },
        ),
        (
            "题号集合不同要拒绝",
            {"q01": {"passed": True}, "q02": {"passed": True}},
            {"q01": {"passed": True}},
            ValueError,
        ),
        (
            "passed 不是布尔值要拒绝",
            {"q01": {"passed": "yes"}},
            {"q01": {"passed": True}},
            TypeError,
        ),
        ("两边都是空字典", {}, {}, empty_result),
    ]
    _run_compare_cases(compare_fn, cases)
