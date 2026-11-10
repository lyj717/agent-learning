"""Day54 C：时间窗口内的开始次数限制。

窗口限额演示在 demos/day54；测量与三组对照由 AI 提供，观察与亲跑数据在记录的 C 节。
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day54.day54_rate_limit_checks import check_cases


class WindowLimiter:
    """固定窗口的开始次数限制器：每个 window 秒内最多放行 limit 次。"""

    def __init__(self, limit: int, window: float) -> None:
        """创建限额器；limit 与 window 由入口按位置传入，均为正数。"""
        self.limit = limit
        self.window = window
        self.lock = asyncio.Lock()
        # window_start 为 None 表示还没开过窗口；count 是当前窗口已放行几次。
        self.window_start: float | None = None
        self.count = 0

    async def acquire(self) -> None:
        """等到本窗口有名额时占一次开始许可，返回 None；名额用完就等下一窗口。"""
        while True:
            async with self.lock:
                start = asyncio.get_running_loop().time()
                if (
                    self.window_start is None
                    or start - self.window_start >= self.window
                ):
                    self.count = 0
                    self.window_start = start
                if self.count < self.limit:
                    self.count += 1
                    return
                gap = self.window - (start - self.window_start)
            await asyncio.sleep(gap)


def run_exercise(run_dir: Path) -> None:
    """把学员的限额器交给三组背景检查，保存实际结果；无需修改。"""
    asyncio.run(check_cases(WindowLimiter, run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和检查 JSON。"""
    run_logged(
        "rate_limit_exercise",
        run_exercise,
        {"model_calls": 0, "http_requests": 0, "case_count": 3},
        Path(__file__),
        ROOT / "weeks/week07_production/demos/day54/outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
