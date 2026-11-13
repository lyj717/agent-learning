"""Day56 B：把限流、并发、追踪和重试接成一条请求处理链。

检查器由 AI 提供，五组情形与期望写在 serve_question 的题面里；你只写这个函数。
"""

import asyncio
import sys
from collections.abc import Callable
from pathlib import Path

from opentelemetry.trace import Tracer

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day54.day54_retry_checks import RateLimitedError
from weeks.week07_production.demos.day56.day56_checks import check_cases
from weeks.week07_production.exercises.day53_span_exercises import trace_stage
from weeks.week07_production.exercises.day54_rate_limit_exercises import WindowLimiter


async def serve_question(
    limiter: WindowLimiter,
    semaphore: asyncio.Semaphore,
    tracer: Tracer,
    request_id: str,
    action: Callable[[], dict[str, object]],
    *,
    attempts: int = 3,
    base_delay: float = 0.05,
) -> dict[str, object]:
    """要做的：把一次请求包进并发名额、窗口限额、追踪和重试，返回动作结果。
    入口会这样调用你（示意）：
        limiter = WindowLimiter(2, 0.5)
        semaphore = asyncio.Semaphore(2)
        with local_tracing(run_dir) as tracer:
            result = await serve_question(
                limiter, semaphore, tracer, "req-001", lambda: answer_with_trace(...)
            )
    参数（均由入口传入，不用重新定义）：
    - limiter：共享的窗口限额器，await limiter.acquire() 取一个开始名额；
    - semaphore：共享的并发名额，async with semaphore 包住整份逻辑工作；
    - tracer：追踪工具，用来创建 span；
    - request_id：公开编号，写进 span 属性；
    - action：同步动作，成功返回字典，失败抛异常；
    - attempts / base_delay：最多尝试次数、第一次重试前等待秒数。
    规则：
    1. 先取并发名额，再在名为 "request" 的根 span 里按尝试循环；根 span 属性写 request_id。
    2. 每次尝试前 await limiter.acquire()；每次尝试用
       await asyncio.to_thread(trace_stage, tracer, request_id, "answer", action)
       包住动作。action 是同步函数，直接调用会阻塞事件循环，并发测试会因此失败。
    3. 可重试异常：TimeoutError、ConnectionError、RateLimitedError；
       第 n 次失败后等 base_delay * 2 ** (n - 1) 秒再试。
    4. 不可重试异常（如 ValueError）立刻原样抛出，不等待、不重试。
    5. 次数用完仍失败：抛出最后一次捕获到的那个异常对象。
    6. 成功时返回 action 给的同一个字典。
    五组情形（入口逐条打印实际与期望）：
    | 情形 | action 的行为 | attempts | 期望 |
    |---|---|---|---|
    | success | 直接返回字典 | 3 | 返回字典；1 个 request + 1 个 answer span |
    | retry_then_ok | 第 1 次 TimeoutError，第 2 次返回 | 3 | 返回字典；2 个 answer span，同一 trace |
    | exhausted | 三次都 TimeoutError | 3 | 抛 TimeoutError；3 个 answer span |
    | fatal | 抛 ValueError | 3 | 立刻抛 ValueError；只调用 1 次 |
    | concurrency | 3 份各等 0.1 秒的动作 | 3 | 同时最多 2 份在跑 |
    """
    async with semaphore:
        with tracer.start_as_current_span(
            "request",
            attributes={"request_id": request_id},
        ):
            await limiter.acquire()
            for count in range(1, attempts + 1):
                try:
                    return await asyncio.to_thread(trace_stage, tracer, request_id, "answer", action)
                except (TimeoutError, ConnectionError, RateLimitedError):
                    if count == attempts:
                        raise
                    await asyncio.sleep(base_delay * 2 ** (count - 1))


def run_exercise(run_dir: Path) -> None:
    """把学员的整合函数交给五组检查，保存实际结果；无需修改。"""
    asyncio.run(check_cases(serve_question, run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "integration_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 5},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day56/outputs",
        origin_env="DAY56_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
