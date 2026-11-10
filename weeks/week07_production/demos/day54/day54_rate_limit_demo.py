"""Day54 C1：单独认识时间窗口内的开始次数限制。

从 demonstrate_async 读起。本例用人工计时，不访问模型或 HTTP；
只展示计数规则和两个常见错误，不给练习要交的 WindowLimiter 实现。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

LIMIT = 2
WINDOW = 0.2


async def demonstrate_async(run_dir: Path) -> None:
    """展示窗口计数、两种错误等待方式与正确形状，不要求重写运行入口。"""
    print("Week07 要把 Agent 做成有调用记录、能扛住负载的服务。")
    print("B 已经能限制“同时几份工作”，本节学另一个维度：单位时间里最多开始几次。")
    print("学完应能说清两者的区别，并在练习里写一个窗口限额函数。")

    print("\n一、是什么：固定窗口限额，每个 window 秒内最多放行 limit 次开始。")
    print("它数的是“开始时刻”，不是“同时有几个在跑”；开始之后跑多久不影响下一窗口。")

    print("\n二、为什么需要：并发上限管不住请求密度。")
    print("2 份工作同时跑 1 秒，可能只发了 2 次请求；也可能这 1 秒里换了 50 批短任务。")
    print("下游按分钟/秒计费和限流时，看的是这 50 次，不是“同一时刻 2 个”。")

    print("\n三、场景：服务商允许每分钟 60 次请求。")
    print(
        "并发上限 2 保证不同时打 3 个，但不能保证 1 秒内不发出 20 个；窗口限额补这一块。"
    )

    print(f"\n四、计数规则：limit={LIMIT}，window={WINDOW} 秒，共 5 份工作")
    # 下面这组时刻是按规则算出来的示例，不是真实等待；窗口从第一次开始计时。
    timeline = [
        (0.000, 1, 1),
        (0.001, 1, 2),
        (0.200, 2, 3),
        (0.201, 2, 4),
        (0.400, 3, 5),
    ]
    for moment, window_no, job_no in timeline:
        print(f"  第 {job_no} 份：t={moment:.3f}s，落在第 {window_no} 个窗口")
    print(
        "第 3、4 份要等第 1 个窗口结束；第 5 份再等一个窗口。等待期间它们没有开始，也没有丢。"
    )

    print("\n五、错误示范 A：窗口满就跳过，不等待")
    gate = SkipGate(LIMIT, WINDOW)
    allowed = []
    skipped = []
    loop = asyncio.get_running_loop()
    for name in ["馆藏", "开放", "借还", "预约", "续借"]:
        if gate.allow(loop.time()):
            allowed.append(name)
        else:
            skipped.append(name)
    print(f"  5 份里放行 {len(allowed)} 份：{allowed}")
    print(f"  另外 {len(skipped)} 份被直接跳过：{skipped}，它们没有开始，也不会再执行")
    print("  allow() 只回答“现在能不能立刻开始”，回答“不能”不代表这份工作可以不要。")
    print("  这不是限速，是丢工作；验收里“每份都执行一次”会立刻失败。")

    print("\n六、错误示范 B：等完窗口不再重新判断，直接占位")
    trace: list[str] = []
    no_recheck = NoRecheckGate(LIMIT, WINDOW, trace)
    starts: list[float] = []

    async def one(job: str) -> None:
        """模拟一份工作：等到许可，记下开始时刻。"""
        await no_recheck.wait(job)
        starts.append(loop.time())

    begin = loop.time()
    await asyncio.gather(
        *(one(name) for name in ["馆藏", "开放", "借还", "预约", "续借"])
    )
    relative = sorted(round(moment - begin, 3) for moment in starts)
    peak = max_in_window(relative, WINDOW)
    print("  每一份自己的判断过程：")
    for line in trace:
        print(f"    {line}")
    print(f"  5 份都执行了，开始时刻：{relative}")
    print(f"  但任意 {WINDOW} 秒内最多开始 {peak} 次，超过 limit={LIMIT}")
    print(
        "  三份在第 1 个窗口结束时同时醒来；它们各自把共享计数重置成 1 再开始，"
        "所以同一瞬间挤进了 3 份。"
    )
    print("  醒来后本来应该回到循环，让共享的 count 决定谁还能进；不能自己重置窗口。")

    print("\n七、正确形状（练习里由你写）")
    print("  循环：锁内判断本窗口还有没有名额、有名额就占一次并返回；")
    print("        没名额就只算出“还要等多久”，出锁后 sleep，再回到循环重新判断。")
    print("  锁只保护计数的读改写，不包住 sleep；等待的工作不占名额，也不该被丢掉。")
    print("  _window_start 为 None 表示还没开窗；当前时间用循环的单调时钟。")

    print(
        "\n注意：固定窗口在相邻两窗交界处最多可放 2×limit 次（前窗末尾 + 后窗开头），"
    )
    print(
        "它不是“任意连续 window 秒内最多 limit 次”的滑动窗口；真实服务商还会返回 429，"
    )
    print("本节只学本机单进程内的窗口计数，不代表分布式限流。")

    assert len(allowed) == 2
    assert peak == 3
    (run_dir / "rate_limit_demo.json").write_text(
        json.dumps(
            {
                "timeline": timeline,
                "skip_allowed": allowed,
                "skip_skipped": skipped,
                "no_recheck_starts": relative,
                "no_recheck_trace": trace,
                "no_recheck_peak_in_window": peak,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def max_in_window(times: list[float], window: float) -> int:
    """统计任意长度 window 的区间里，最多有多少个开始时刻。"""
    best = 0
    for start in times:
        count = sum(1 for moment in times if start <= moment < start + window)
        best = max(best, count)
    return best


class SkipGate:
    """错误示范 A：窗口满时报告失败，让调用方自己处理。"""

    def __init__(self, limit: int, window: float) -> None:
        self.limit = limit
        self.window = window
        self.start: float | None = None
        self.count = 0

    def allow(self, now: float) -> bool:
        """立即判断能否开始：能就占一次并返回 True，否则返回 False。"""
        if self.start is None or now - self.start >= self.window:
            self.start = now
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class NoRecheckGate:
    """错误示范 B：等到窗口结束就占位，不回到循环重新判断。"""

    def __init__(self, limit: int, window: float, trace: list[str]) -> None:
        self.limit = limit
        self.window = window
        self.start: float | None = None
        self.count = 0
        self.trace = trace

    async def wait(self, job: str) -> None:
        """等到本窗口结束或直接占位，返回 None。"""
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self.start is None or now - self.start >= self.window:
            self.start = now
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            self.trace.append(f"{job}：有名额，直接占位，共享 count={self.count}")
            return
        pause = self.window - (now - self.start)
        self.trace.append(f"{job}：名额已满，先睡 {pause:.3f} 秒")
        await asyncio.sleep(pause)
        self.start = loop.time()
        self.count = 1
        self.trace.append(f"{job}：醒来不重判，把共享 count 重置为 1 并开始")


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮讲解、实际时刻与来源。"""
    run_logged(
        "rate_limit_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0, "limit": LIMIT, "window_s": WINDOW},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
