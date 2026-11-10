"""Day54 D 的检查器与异常类型：重试次数、错误边界和等待间隔。

两道异常类型由 AI 提供，学员只写 call_with_retry。
检查器不含参考实现，不请求模型、HTTP 或外部服务。
"""

import asyncio
import itertools
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

Action = Callable[[str], Awaitable[dict[str, str]]]
RetryFn = Callable[..., Awaitable[dict[str, str]]]


class RateLimitedError(Exception):
    """下游返回限流：属于可重试错误。"""


class BadRequestError(Exception):
    """请求参数错误：属于不可重试错误。"""


def _intervals(times: list[float]) -> list[float]:
    """相邻两次调用的间隔。"""
    return [round(later - earlier, 3) for earlier, later in itertools.pairwise(times)]


async def run_case(
    retry_fn: RetryFn,
    name: str,
    script: list[Any],
    attempts: int,
    base_delay: float,
    expected_calls: int,
    expected_error: BaseException | None,
    expected_intervals: list[float],
    job_id: str = "馆藏",
) -> dict[str, object]:
    """按剧本跑一组：记录调用次数、返回/异常、每次调用时刻和间隔。"""
    loop = asyncio.get_running_loop()
    begin = loop.time()
    calls: list[str] = []
    times: list[float] = []

    async def action(job: str) -> dict[str, str]:
        """按剧本第 N 次抛出异常或返回字典。"""
        index = len(calls)
        calls.append(job)
        times.append(loop.time() - begin)
        step = script[index]
        if isinstance(step, BaseException):
            raise step
        return step

    result: dict[str, str] | None = None
    error: BaseException | None = None
    try:
        result = await asyncio.wait_for(
            retry_fn(action, job_id, attempts=attempts, base_delay=base_delay),
            timeout=2.0,
        )
    except BaseException as exc:  # noqa: BLE001 - 检查器记录全部失败。
        error = exc

    intervals = _intervals(times)
    error_ok = (error is None and expected_error is None) or (
        error is not None and expected_error is not None and error is expected_error
    )
    timing_ok = True
    for actual, expected in zip(intervals, expected_intervals):
        timing_ok = timing_ok and (expected * 0.8 <= actual <= expected + 0.03)
    passed = all(
        [
            len(calls) == expected_calls,
            error_ok,
            timing_ok,
            len(intervals) == len(expected_intervals),
            (result is not None) == (expected_error is None),
        ]
    )
    row = {
        "case": name,
        "passed": passed,
        "attempts": attempts,
        "base_delay": base_delay,
        "calls": len(calls),
        "call_times": [round(moment, 3) for moment in times],
        "intervals": intervals,
        "result": result,
        "error_type": None if error is None else type(error).__name__,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"  调用次数={len(calls)}（期望 {expected_calls}）；时刻={row['call_times']}")
    print(
        f"  间隔={intervals}（期望 {expected_intervals}）；"
        f"异常={row['error_type']}；返回={result}"
    )
    return row


async def check_cases(retry_fn: RetryFn, run_dir: Path) -> None:
    """汇总七种情形；失败也保存 JSON，然后明确报未通过。"""
    ok = {"job_id": "馆藏", "answer": "人工结果:馆藏"}
    timeout_first = TimeoutError("第一次超时")
    limited = [RateLimitedError(f"第 {n} 次限流") for n in (1, 2, 3)]
    bad = BadRequestError("参数错误")
    value = ValueError("不能重试的普通错误")
    one_timeout = TimeoutError("只允许一次")

    cases = [
        ("ok_now", [ok], 3, 0.05, 1, None, []),
        ("timeout_then_ok", [timeout_first, ok], 3, 0.05, 2, None, [0.05]),
        ("exhausted", limited[:], 3, 0.05, 3, limited[2], [0.05, 0.10]),
        ("bad_request", [bad], 3, 0.05, 1, bad, []),
        ("value_error", [value], 3, 0.05, 1, value, []),
        ("attempts_one", [one_timeout], 1, 0.05, 1, one_timeout, []),
    ]
    rows = []
    for name, script, attempts, base, calls, error, intervals in cases:
        row = await run_case(
            retry_fn, name, script, attempts, base, calls, error, intervals
        )
        rows.append(row)
        (run_dir / f"{name}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "retry_checks.json").write_text(
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
    assert passed_count == len(rows), "重试边界还有未通过项，请对照上面的实际与期望"
