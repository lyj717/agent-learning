"""Day56 B 的检查器：返回、异常、重试次数、span 结构与并发峰值。

不含参考实现，不请求模型、HTTP 或外部服务。
"""

import asyncio
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from weeks.week07_production.demos.day53.day53_trace_runtime import local_tracing
from weeks.week07_production.exercises.day54_rate_limit_exercises import WindowLimiter


def read_summary(case_dir: Path) -> dict[str, Any]:
    """读本轮 trace_summary.json。"""
    return json.loads((case_dir / "trace_summary.json").read_text(encoding="utf-8"))


def span_check(summary: dict[str, Any], answers: int, roots: int) -> tuple[bool, str]:
    """检查 span 数量、trace 数、根数与父子关系。"""
    rows = summary["rows"]
    requests = [row for row in rows if row["name"] == "request"]
    answer_rows = [row for row in rows if row["name"] == "answer"]
    ok = all(
        [
            len(requests) == roots,
            len(answer_rows) == answers,
            summary["trace_count"] == roots,
            summary["root_count"] == roots,
        ]
    )
    for root in requests:
        if root["parent_span_id"] is not None:
            ok = False
        children = [
            row for row in answer_rows if row["parent_span_id"] == root["span_id"]
        ]
        if not children:
            ok = False
        if any(row["trace_id"] != root["trace_id"] for row in children):
            ok = False
    return ok, (
        f"spans={summary['span_count']} roots={summary['root_count']} "
        f"traces={summary['trace_count']}"
    )


async def run_single(
    fn: Callable[..., Any],
    name: str,
    case_dir: Path,
    action: Callable[[], dict[str, object]],
    attempts: int,
) -> dict[str, object]:
    """跑一组单请求：记录返回/异常与 span 结构。"""
    limiter = WindowLimiter(2, 0.5)
    semaphore = asyncio.Semaphore(2)
    result = None
    error: BaseException | None = None
    with local_tracing(case_dir) as tracer:
        try:
            result = await fn(
                limiter,
                semaphore,
                tracer,
                f"req-{name}",
                action,
                attempts=attempts,
                base_delay=0.02,
            )
        except BaseException as caught:  # noqa: BLE001 - 检查器记录全部失败。
            error = caught
    return {"result": result, "error": error, "summary": read_summary(case_dir)}


async def run_fixed(
    fn: Callable[..., Any],
    run_dir: Path,
    name: str,
    script: list[Any],
    attempts: int,
    expected_calls: int,
    expected_answers: int,
) -> dict[str, object]:
    """按固定剧本跑一组单请求。"""
    case_dir = run_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)
    calls: list[Any] = []

    def action() -> dict[str, object]:
        """按剧本第 N 步抛异常或返回字典。"""
        step = script[len(calls)]
        calls.append(step)
        if isinstance(step, BaseException):
            raise step
        return step

    output = await run_single(fn, name, case_dir, action, attempts)
    error = output["error"]
    summary = output["summary"]
    span_ok, span_text = span_check(summary, expected_answers, 1)
    expected_error = script[-1] if isinstance(script[-1], BaseException) else None
    error_ok = error is expected_error if expected_error is not None else error is None
    passed = all([len(calls) == expected_calls, error_ok, span_ok])
    row = {
        "case": name,
        "passed": passed,
        "calls": len(calls),
        "expected_calls": expected_calls,
        "error": None if error is None else type(error).__name__,
        "span": span_text,
    }
    print(f"\n{name}：{'通过' if passed else '未通过'}")
    print(f"  调用次数={len(calls)}（期望 {expected_calls}）；异常={row['error']}")
    print(f"  span 检查={span_ok}（{span_text}；answer 期望 {expected_answers}）")
    return row


async def run_concurrency(fn: Callable[..., Any], run_dir: Path) -> dict[str, object]:
    """3 份同时提交，检查并发峰值不超过 2，且三个请求都有完整 span。"""
    case_dir = run_dir / "concurrency"
    case_dir.mkdir(parents=True, exist_ok=True)
    limiter = WindowLimiter(2, 0.5)
    semaphore = asyncio.Semaphore(2)
    peak = 0
    active = 0
    lock = threading.Lock()

    def action() -> dict[str, object]:
        """同步动作：模拟一次 0.1 秒的下游调用。"""
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.1)
        with lock:
            active -= 1
        return {"answer": "二楼", "cited_ids": ["public.md#L1-L1"]}

    errors: list[BaseException] = []
    with local_tracing(case_dir) as tracer:

        async def one(index: int) -> None:
            """一份请求。"""
            try:
                await fn(
                    limiter,
                    semaphore,
                    tracer,
                    f"req-c{index}",
                    action,
                    attempts=3,
                    base_delay=0.02,
                )
            except BaseException as caught:  # noqa: BLE001
                errors.append(caught)

        await asyncio.gather(*(one(index) for index in range(3)))

    summary = read_summary(case_dir)
    span_ok, span_text = span_check(summary, 3, 3)
    passed = all([peak <= 2, peak >= 1, not errors, span_ok])
    row = {
        "case": "concurrency",
        "passed": passed,
        "peak": peak,
        "errors": [type(error).__name__ for error in errors],
        "span": span_text,
    }
    print("\nconcurrency：", "通过" if passed else "未通过")
    print(f"  同时最多 {peak} 份在跑（期望 ≤ 2）；异常={row['errors']}；{span_text}")
    return row


async def check_cases(fn: Callable[..., Any], run_dir: Path) -> None:
    """汇总五组；失败也保存 JSON，然后明确报未通过。"""
    timeout_a = TimeoutError("第一次超时")
    timeout_b = TimeoutError("第二次超时")
    timeout_c = TimeoutError("第三次超时")
    fatal = ValueError("不能重试")
    rows = [
        await run_fixed(fn, run_dir, "success", [{"answer": "二楼"}], 3, 1, 1),
        await run_fixed(
            fn, run_dir, "retry_then_ok", [timeout_a, {"answer": "二楼"}], 3, 2, 2
        ),
        await run_fixed(
            fn, run_dir, "exhausted", [timeout_a, timeout_b, timeout_c], 3, 3, 3
        ),
        await run_fixed(fn, run_dir, "fatal", [fatal], 3, 1, 1),
        await run_concurrency(fn, run_dir),
    ]
    passed_count = sum(row["passed"] for row in rows)
    (run_dir / "integration_checks.json").write_text(
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
    assert passed_count == len(rows), "整合链路还有未通过项，请对照上面的实际与期望"
