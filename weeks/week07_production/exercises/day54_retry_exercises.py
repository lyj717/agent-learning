"""Day54 D：重试的次数与异常边界。

可重试错误按指数退避再试，其余异常与次数用完都原样抛出；六种情形与期望写在检查器里。
"""

import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day54.day54_retry_checks import (
    RateLimitedError,
    check_cases,
)


async def call_with_retry(
    action: Callable[[str], Awaitable[dict[str, str]]],
    job_id: str,
    *,
    attempts: int = 3,
    base_delay: float = 0.05,
) -> dict[str, str]:
    """最多尝试 attempts 次：成功返回字典，可重试错误按退避再试，其余原样抛出。"""
    for count in range(1, attempts + 1):
        try:
            return await action(job_id)
        except (TimeoutError, ConnectionError, RateLimitedError):
            if count == attempts:
                raise
            await asyncio.sleep(base_delay * 2 ** (count - 1))


def run_exercise(run_dir: Path) -> None:
    """把学员的重试包装器交给六种情形检查，保存实际结果；无需修改。"""
    asyncio.run(check_cases(call_with_retry, run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "retry_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 6},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day54/outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
