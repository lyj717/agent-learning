"""AI 维护的 Day60 对照检查：compare_conditions 的输入与期望。

只提供输入与期望，不实现学员函数，也不调用模型。
"""

from collections.abc import Callable
from copy import deepcopy

BASE = [
    {
        "id": "q01",
        "ttft_ms": 100.0,
        "end_to_end_ms": 200.0,
        "cost_cny": 0.001,
    },
    {
        "id": "q01",
        "ttft_ms": 120.0,
        "end_to_end_ms": 220.0,
        "cost_cny": 0.003,
    },
    {
        "id": "q02",
        "ttft_ms": 200.0,
        "end_to_end_ms": 400.0,
        "cost_cny": 0.002,
    },
    {
        "id": "q02",
        "ttft_ms": 220.0,
        "end_to_end_ms": 420.0,
        "cost_cny": 0.004,
    },
]
OPT = [
    {
        "id": "q01",
        "ttft_ms": 50.0,
        "end_to_end_ms": 120.0,
        "cost_cny": 0.0005,
    },
    {
        "id": "q01",
        "ttft_ms": 70.0,
        "end_to_end_ms": 140.0,
        "cost_cny": 0.0015,
    },
    {
        "id": "q02",
        "ttft_ms": 100.0,
        "end_to_end_ms": 240.0,
        "cost_cny": 0.001,
    },
    {
        "id": "q02",
        "ttft_ms": 120.0,
        "end_to_end_ms": 260.0,
        "cost_cny": 0.003,
    },
]

EXPECTED = {
    "questions": [
        {
            "id": "q01",
            "baseline_ttft": 110.0,
            "optimized_ttft": 60.0,
            "ttft_delta": -50.0,
            "baseline_end_to_end": 210.0,
            "optimized_end_to_end": 130.0,
            "end_to_end_delta": -80.0,
            "baseline_cost": 0.002,
            "optimized_cost": 0.001,
            "cost_delta": -0.001,
        },
        {
            "id": "q02",
            "baseline_ttft": 210.0,
            "optimized_ttft": 110.0,
            "ttft_delta": -100.0,
            "baseline_end_to_end": 410.0,
            "optimized_end_to_end": 250.0,
            "end_to_end_delta": -160.0,
            "baseline_cost": 0.003,
            "optimized_cost": 0.002,
            "cost_delta": -0.001,
        },
    ],
    "baseline_mean_end_to_end": 310.0,
    "optimized_mean_end_to_end": 190.0,
    "end_to_end_delta_mean": -120.0,
    "baseline_total_cost": 0.005,
    "optimized_total_cost": 0.003,
    "cost_delta_total": -0.002,
}


def _close(left: object, right: float) -> bool:
    """浮点按 1e-9 比较，类型允许 int/float。"""
    return isinstance(left, (int, float)) and abs(left - right) <= 1e-9


def _same(actual: object, expected: dict) -> bool:
    """逐字段比较，浮点允许误差。"""
    if not isinstance(actual, dict) or set(actual) != set(expected):
        return False
    questions = actual["questions"]
    if not isinstance(questions, list) or len(questions) != len(expected["questions"]):
        return False
    for current, wanted in zip(questions, expected["questions"]):
        if not isinstance(current, dict) or set(current) != set(wanted):
            return False
        if current["id"] != wanted["id"]:
            return False
        for key, value in wanted.items():
            if key == "id":
                continue
            if not _close(current[key], value):
                return False
    for key, value in expected.items():
        if key == "questions":
            continue
        if not _close(actual[key], value):
            return False
    return True


def run_a(compare_fn: Callable[[list[dict], list[dict]], dict]) -> None:
    """检查两套条件的逐题中位数与整体差值，共 6 组。"""
    cases: list[tuple[str, list[dict], list[dict], dict | type]] = [
        ("两题各两轮", BASE, OPT, EXPECTED),
        (
            "单题单轮，差值为 0",
            [{"id": "q01", "ttft_ms": 10.0, "end_to_end_ms": 20.0, "cost_cny": 0.001}],
            [{"id": "q01", "ttft_ms": 10.0, "end_to_end_ms": 20.0, "cost_cny": 0.001}],
            {
                "questions": [
                    {
                        "id": "q01",
                        "baseline_ttft": 10.0,
                        "optimized_ttft": 10.0,
                        "ttft_delta": 0.0,
                        "baseline_end_to_end": 20.0,
                        "optimized_end_to_end": 20.0,
                        "end_to_end_delta": 0.0,
                        "baseline_cost": 0.001,
                        "optimized_cost": 0.001,
                        "cost_delta": 0.0,
                    }
                ],
                "baseline_mean_end_to_end": 20.0,
                "optimized_mean_end_to_end": 20.0,
                "end_to_end_delta_mean": 0.0,
                "baseline_total_cost": 0.001,
                "optimized_total_cost": 0.001,
                "cost_delta_total": 0.0,
            },
        ),
        ("baseline 为空", [], OPT, ValueError),
        ("题号集合不同", BASE, [OPT[0]], ValueError),
        (
            "缺 cost_cny",
            [{"id": "q01", "ttft_ms": 1.0, "end_to_end_ms": 2.0}],
            [{"id": "q01", "ttft_ms": 1.0, "end_to_end_ms": 2.0, "cost_cny": 0.001}],
            ValueError,
        ),
        ("输入不是列表", {"id": "q01"}, OPT, TypeError),
    ]

    print("来源：AI 人工检查样本；没有模型或网络请求。")
    failures = 0
    for number, (name, baseline, optimized, expected) in enumerate(cases, start=1):
        before = deepcopy((baseline, optimized))
        print(f"\n对照 {number}｜{name}")
        try:
            actual = compare_fn(baseline, optimized)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
            consistent = isinstance(expected, type) and isinstance(error, expected)
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = isinstance(expected, dict) and _same(actual, expected)
            print(f"实际={actual}")
        expected_text = expected.__name__ if isinstance(expected, type) else expected
        print(f"期望={expected_text}；结果一致={consistent}")
        unchanged = (baseline, optimized) == before
        print(f"输入未改动={unchanged}")
        failures += int(not consistent) + int(not unchanged)
    total = len(cases)
    print(f"\n汇总：结果一致 {total - failures}/{total}")
    if failures:
        raise AssertionError("对照结果与期望不一致，详见上方汇总")
