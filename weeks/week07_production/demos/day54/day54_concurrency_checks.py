"""Day54 B 的 AI 运行背景：提供共享名额、异步动作和三组汇总检查。

完整作题接口在 call_with_limit 旁；学员不需要读这里才能开工。
不含 call_with_limit 的参考实现，不请求模型、HTTP 或外部限流服务。
"""

import asyncio
import inspect
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

Action = Callable[[str], Awaitable[dict[str, str]]]
LimitedCall = Callable[[asyncio.Semaphore, str, Action], Awaitable[dict[str, str]]]


async def check_case(
    function: LimitedCall,
    name: str,
    limit: int,
    jobs: list[str],
    failure_job: str | None,
) -> dict[str, object]:
    """为本组创建共享限制器和原对象，核对行为；不把循环变量捕获到下一组。"""
    semaphore = asyncio.Semaphore(limit)
    calls = dict.fromkeys(jobs, 0)
    expected = {job: {"job_id": job, "answer": f"人工结果:{job}"} for job in jobs}
    original_error = TimeoutError("人工工具超时")
    active = 0
    peak = 0
    started: list[str] = []
    finished: list[str] = []

    async def action(job_id: str) -> dict[str, str]:
        """已实现的离线动作：只接收工作编号，记录实际执行区间，返回原字典或原异常。"""
        nonlocal active, peak
        calls[job_id] += 1
        active += 1
        peak = max(peak, active)
        started.append(job_id)
        try:
            await asyncio.sleep(0.015)
            if job_id == failure_job:
                raise original_error
            return expected[job_id]
        finally:
            active -= 1
            finished.append(job_id)

    timed_out = False
    values: list[object] = []
    try:
        # return_exceptions=True：验收器收齐每一份结果或异常；学员函数仍原样抛出。
        # wait_for：只为防止漏归还导致检查挂起，不是新增的业务超时需求。
        values = await asyncio.wait_for(
            asyncio.gather(
                *(function(semaphore, job, action) for job in jobs),
                return_exceptions=True,
            ),
            timeout=1.5,
        )
    except TimeoutError:
        timed_out = True

    originals_match = len(values) == len(jobs)
    error_types = []
    for job, value in zip(jobs, values):
        target = original_error if job == failure_job else expected[job]
        originals_match = originals_match and value is target
        if isinstance(value, BaseException):
            error_types.append(type(value).__name__)
        # 漏 await 时关闭未执行对象以免产生警告；不替学员执行漏掉的动作。
        if inspect.iscoroutine(value):
            value.close()

    recovered = 0
    try:
        for _ in range(limit):
            await asyncio.wait_for(semaphore.acquire(), timeout=0.15)
            recovered += 1
    except TimeoutError:
        pass
    finally:
        for _ in range(recovered):
            semaphore.release()
    slots_restored = recovered == limit
    expected_errors = ["TimeoutError"] if failure_job else []
    passed = all(
        [
            not timed_out,
            peak == limit,
            all(c == 1 for c in calls.values()),
            originals_match,
            active == 0,
            slots_restored,
            error_types == expected_errors,
        ]
    )
    row = {
        "case": name,
        "passed": passed,
        "limit": limit,
        "job_ids": jobs,
        "action_calls": calls,
        "peak_active": peak,
        "active_at_end": active,
        "started_order": started,
        "finished_order": finished,
        "originals_match": originals_match,
        "error_types": error_types,
        "slots_restored": slots_restored,
        "timed_out": timed_out,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"实际：动作次数={calls}；最大同时执行数={peak}；结束后执行数={active}")
    print(f"期望：每份一次；最大同时执行数={limit}；结束后执行数=0")
    print(
        f"实际：原结果/异常保持={originals_match}；名额恢复={slots_restored}；防挂起超时={timed_out}"
    )
    print(
        f"实际异常类型={error_types}；期望={expected_errors}；实际完成顺序={finished}"
    )
    return row


async def check_cases(function: LimitedCall, run_dir: Path) -> None:
    """汇总三组；失败也保存逐组 JSON，然后明确报未通过。"""
    cases = [
        ("normal_one", 1, ["馆藏", "开放", "借还", "预约"], None),
        ("normal_two", 2, ["馆藏", "开放", "借还", "预约"], None),
        ("error_then_next", 1, ["失败资料", "后续资料", "最后资料"], "失败资料"),
    ]
    rows = []
    for name, limit, jobs, failure_job in cases:
        row = await check_case(function, name, limit, jobs, failure_job)
        rows.append(row)
        (run_dir / f"{name}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "concurrency_checks.json").write_text(
        json.dumps(
            {"passed": passed_count, "total": 3, "cases": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n本次 {passed_count}/3，模型与 HTTP 调用均为 0；实际结果已保存。")
    assert passed_count == 3, "并发上限还有未通过项，请对照上面的实际与期望"
