"""Day54 B：给异步动作加共享并发上限的通用包装器。

两份 API 演示在 demos/day54；动作、共享名额和汇总运行环境均由 AI 提供。
观察与亲跑数据见 demos/day54/day54_记录.md。
"""

import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day54.day54_concurrency_checks import check_cases


async def call_with_limit(
    semaphore: asyncio.Semaphore,
    job_id: str,
    action: Callable[[str], Awaitable[dict[str, str]]],
) -> dict[str, str]:
    """在共享名额内执行一次异步动作，返回原结果；异常原样传出并归还名额。"""
    async with semaphore:
        return await action(job_id)


def run_exercise(run_dir: Path) -> None:
    """把学员函数交给三组背景检查，保存实际结果；无需修改。"""
    asyncio.run(check_cases(call_with_limit, run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "concurrency_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 3},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day54/outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
