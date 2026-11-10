"""Day54 C 的运行背景：构造学员的窗口限额器，并发提交并测量开始时刻。

完整作题接口在 WindowLimiter.acquire 旁；学员不需要读这里才能开工。
不含 acquire 的参考实现，不请求模型、HTTP 或外部限流服务。
"""

import asyncio
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

LimiterFactory = Callable[[int, float], Any]


def max_in_window(times: list[float], window: float) -> int:
    """统计任意长度 window 的区间里，最多有多少个开始时刻。"""
    best = 0
    for start in times:
        count = sum(1 for moment in times if start <= moment < start + window)
        best = max(best, count)
    return best


async def check_case(
    limiter_cls: LimiterFactory,
    name: str,
    limit: int,
    window: float,
    first_jobs: list[str],
    rest_jobs: list[str] | None = None,
    pause: float = 0.0,
) -> dict[str, object]:
    """测一组：同一限额器上的开始时刻、任意窗口内最多几次、是否全部执行。"""
    limiter = limiter_cls(limit, window)
    loop = asyncio.get_running_loop()
    begin = loop.time()
    starts: list[float] = []
    timed_out = False
    resume = begin

    async def one(job: str) -> None:
        """一份工作：等许可，记下开始时刻。"""
        await limiter.acquire()
        starts.append(loop.time() - begin)

    async def run_batch(jobs: list[str]) -> None:
        """并发跑一批，整体最多等 2 秒，防止漏归还时挂死。"""
        await asyncio.wait_for(asyncio.gather(*(one(job) for job in jobs)), timeout=2.0)

    try:
        await run_batch(first_jobs)
        if rest_jobs:
            await asyncio.sleep(pause)
            resume = loop.time()
            await run_batch(rest_jobs)
    except TimeoutError:
        timed_out = True

    elapsed = max(starts) if starts else 0.0
    peak = max_in_window(starts, window)
    expected_windows = math.ceil((len(first_jobs) + len(rest_jobs or [])) / limit)
    expected_min = window * (expected_windows - 1)
    all_started = len(starts) == len(first_jobs) + len(rest_jobs or [])
    waited_enough = elapsed >= expected_min - 0.02
    not_too_slow = elapsed <= expected_min + 0.40
    within_limit = peak <= limit
    resumed_promptly = True
    if rest_jobs:
        later = [moment for moment in starts if moment >= resume - begin - 0.001]
        resumed_promptly = bool(later) and (later[0] - (resume - begin)) <= 0.12
    passed = all(
        [
            not timed_out,
            all_started,
            within_limit,
            waited_enough,
            not_too_slow,
            resumed_promptly,
        ]
    )
    row = {
        "case": name,
        "passed": passed,
        "limit": limit,
        "window": window,
        "job_ids": first_jobs + (rest_jobs or []),
        "start_times": [round(moment, 4) for moment in starts],
        "max_in_any_window": peak,
        "all_started": all_started,
        "elapsed": round(elapsed, 4),
        "expected_min_elapsed": round(expected_min, 4),
        "timed_out": timed_out,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"  开始时刻（秒）={row['start_times']}")
    print(
        f"  任意 {window} 秒内最多开始 {peak} 次；期望 ≤ {limit}；"
        f"全部执行={all_started}；总耗时={elapsed:.3f}s"
    )
    print(f"  期望至少等待到 {expected_min:.3f}s；防挂起超时={timed_out}")
    return row


async def check_cases(limiter_cls: LimiterFactory, run_dir: Path) -> None:
    """汇总三组；失败也保存逐组 JSON，然后明确报未通过。"""
    cases = [
        (
            "two_per_window",
            2,
            0.2,
            ["馆藏", "开放", "借还", "预约", "续借"],
            None,
            0.0,
        ),
        ("one_per_window", 1, 0.15, ["书架", "门口", "服务台"], None, 0.0),
        ("idle_reset", 3, 0.15, ["a", "b", "c"], ["d", "e", "f"], 0.2),
    ]
    rows = []
    for name, limit, window, first_jobs, rest_jobs, pause in cases:
        row = await check_case(
            limiter_cls, name, limit, window, first_jobs, rest_jobs, pause
        )
        rows.append(row)
        (run_dir / f"{name}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "rate_limit_checks.json").write_text(
        json.dumps(
            {"passed": passed_count, "total": 3, "cases": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n本次 {passed_count}/3，模型与 HTTP 调用均为 0；实际结果已保存。")
    assert passed_count == 3, "窗口限额还有未通过项，请对照上面的实际与期望"
