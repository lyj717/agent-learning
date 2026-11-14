"""AI 维护的 Day59 人工对照：百分位与测量汇总的输入、期望。

只提供输入与期望，不实现 percentile / summarize_measurements。
全部离线，不加载向量模型、不发模型请求。
"""

from collections.abc import Callable
from copy import deepcopy

ROW1 = {
    "retrieval_ms": 10.0,
    "ttft_ms": 100.0,
    "generation_ms": 200.0,
    "end_to_end_ms": 210.0,
    "prompt_tokens": 100,
    "completion_tokens": 10,
    "cost_cny": 0.001,
}
ROW2 = {
    "retrieval_ms": 20.0,
    "ttft_ms": 200.0,
    "generation_ms": 400.0,
    "end_to_end_ms": 420.0,
    "prompt_tokens": 200,
    "completion_tokens": 20,
    "cost_cny": 0.002,
}
ROW3 = {
    "retrieval_ms": 30.0,
    "ttft_ms": 300.0,
    "generation_ms": 600.0,
    "end_to_end_ms": 630.0,
    "prompt_tokens": 300,
    "completion_tokens": 30,
    "cost_cny": 0.003,
}


def run_a(percentile_fn: Callable[[list[float], float], float]) -> None:
    """检查最近秩百分位，共 10 组。"""
    cases: list[tuple[str, list[float], float, float | type]] = [
        ("4 个样本，P50", [10, 20, 30, 40], 50, 20.0),
        ("4 个样本，P95", [10, 20, 30, 40], 95, 40.0),
        ("单个样本", [5], 50, 5.0),
        ("乱序输入，P75", [40, 10, 30, 20], 75, 30.0),
        ("P100 取最大值", [1, 2, 3], 100, 3.0),
        ("P0 非法", [1, 2, 3], 0, ValueError),
        ("P101 非法", [1, 2, 3], 101, ValueError),
        ("空列表", [], 50, ValueError),
        ("列表含 bool", [1, True, 3], 50, ValueError),
        ("p 是 bool", [1, 2, 3], True, ValueError),
    ]
    print("来源：AI 人工检查样本；没有模型或网络请求。")
    failures = 0
    for number, (name, values, p, expected) in enumerate(cases, start=1):
        before = deepcopy((values, p))
        print(f"\n对照 {number}｜{name}")
        print(f"输入 values={values}；p={p}")
        try:
            actual = percentile_fn(values, p)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
            consistent = isinstance(expected, type) and isinstance(error, expected)
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = isinstance(expected, float) and actual == expected
            print(f"实际={actual}")
        print(f"期望={expected}；结果一致={consistent}")
        unchanged = (values, p) == before
        print(f"输入未改动={unchanged}")
        failures += int(not consistent) + int(not unchanged)
    total = len(cases)
    print(f"\n汇总：结果一致 {total - failures}/{total}")
    if failures:
        raise AssertionError("百分位结果与期望不一致，详见上方对照")


def _expected_summary() -> dict:
    """返回三行样本的期望汇总。"""
    return {
        "count": 3,
        "retrieval_p50": 20.0,
        "retrieval_p95": 30.0,
        "ttft_p50": 200.0,
        "ttft_p95": 300.0,
        "generation_p50": 400.0,
        "generation_p95": 600.0,
        "end_to_end_p50": 420.0,
        "end_to_end_p95": 630.0,
        "prompt_tokens": 600,
        "completion_tokens": 60,
        "total_tokens": 660,
        "total_cost": 0.006,
        "mean_cost": 0.002,
    }


def _same(actual: object, expected: dict) -> bool:
    """逐键比较，浮点允许 1e-9 误差，整数类型要一致。"""
    if not isinstance(actual, dict) or set(actual) != set(expected):
        return False
    for key, value in expected.items():
        current = actual[key]
        if isinstance(value, float):
            if not isinstance(current, (int, float)) or abs(current - value) > 1e-9:
                return False
        elif type(current) is not type(value) or current != value:
            return False
    return True


def run_b(summarize_fn: Callable[[list[dict]], dict]) -> None:
    """检查测量汇总，共 7 组。"""
    single = {**ROW2}
    cases: list[tuple[str, list[dict], dict | type]] = [
        ("三行样本", [ROW1.copy(), ROW2.copy(), ROW3.copy()], _expected_summary()),
        (
            "单行样本",
            [single],
            {
                "count": 1,
                "retrieval_p50": 20.0,
                "retrieval_p95": 20.0,
                "ttft_p50": 200.0,
                "ttft_p95": 200.0,
                "generation_p50": 400.0,
                "generation_p95": 400.0,
                "end_to_end_p50": 420.0,
                "end_to_end_p95": 420.0,
                "prompt_tokens": 200,
                "completion_tokens": 20,
                "total_tokens": 220,
                "total_cost": 0.002,
                "mean_cost": 0.002,
            },
        ),
        ("空列表", [], ValueError),
        ("缺少 cost_cny", [{"retrieval_ms": 1.0}], ValueError),
        (
            "字段不是数字",
            [{**ROW1, "ttft_ms": "100"}],
            ValueError,
        ),
        (
            "真实测量行带附加键",
            [
                {
                    **ROW1,
                    "id": "q01",
                    "question": "示例问题",
                    "raw_text": "示例回答",
                    "evidence_ids": ["notes#L1-L2"],
                }
            ],
            {
                "count": 1,
                "retrieval_p50": 10.0,
                "retrieval_p95": 10.0,
                "ttft_p50": 100.0,
                "ttft_p95": 100.0,
                "generation_p50": 200.0,
                "generation_p95": 200.0,
                "end_to_end_p50": 210.0,
                "end_to_end_p95": 210.0,
                "prompt_tokens": 100,
                "completion_tokens": 10,
                "total_tokens": 110,
                "total_cost": 0.001,
                "mean_cost": 0.001,
            },
        ),
        (
            "输入不是列表",
            {"retrieval_ms": 1.0},
            TypeError,
        ),
    ]
    print("来源：AI 人工检查样本；没有模型或网络请求。")
    failures = 0
    for number, (name, rows, expected) in enumerate(cases, start=1):
        before = deepcopy(rows)
        print(f"\n对照 {number}｜{name}")
        print(f"输入行数={len(rows) if isinstance(rows, list) else '非列表'}")
        try:
            actual = summarize_fn(rows)
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
        unchanged = rows == before
        print(f"输入未改动={unchanged}")
        failures += int(not consistent) + int(not unchanged)
    total = len(cases)
    print(f"\n汇总：结果一致 {total - failures}/{total}")
    if failures:
        raise AssertionError("汇总结果与期望不一致，详见上方对照")
