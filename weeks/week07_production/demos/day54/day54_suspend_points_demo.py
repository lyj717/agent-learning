"""Day54 前置 A3：什么代码会让出执行权，什么不会。

从 demonstrate_async 读起。本例只有本机人工等待，不访问模型或 HTTP。
它只回答一个问题：哪些 await 会换人，哪些不会。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


async def fast(name: str, log: list[str]) -> None:
    """一口气跑完，中间没有 await。"""
    log.append(f"{name}:一步到底")


async def slow(name: str, log: list[str]) -> None:
    """中间有一次 sleep(0)，会给事件循环让出一次机会。"""
    log.append(f"{name}:先记一笔")
    await asyncio.sleep(0)
    log.append(f"{name}:让出后再记一笔")


async def demonstrate_async(run_dir: Path) -> None:
    """对比“没有 await”和“await sleep(0)”两种任务的实际顺序。"""
    print("Week07 的 C 里，很多错误都来自“以为这里会切换，其实不会”。")
    print("本节只回答：什么代码会让出执行权，什么不会。")
    print("学完应能判断：一段代码中间会不会被别的任务插进来。")

    print("\n一、一个没有 await 的任务 + 一个会挂起的任务")
    log: list[str] = []
    await asyncio.gather(fast("甲", log), slow("乙", log))
    print("  实际顺序：", " → ".join(log))
    print("  甲中间没有 await，所以它一口气跑完，乙才轮到；")
    print("  乙在 sleep(0) 处让出一次，才出现“先记一笔 / 再记一笔”分开的两段。")

    print("\n二、两个都会让出的任务")
    log = []
    await asyncio.gather(slow("甲", log), slow("乙", log))
    print("  实际顺序：", " → ".join(log))
    print("  两边都在同一个 sleep(0) 处让出，于是交替推进。")

    print("\n三、结论")
    print("  任务之间只有在这几种时候才换人：await 一个真的会挂起的操作")
    print("  （sleep、等待锁或名额、等网络/文件），或者显式 await sleep(0)。")
    print("  一段普通的赋值、判断、加法中间没有 await，别的任务插不进来。")
    print("  这就是 C 里“看 count、占名额”可以写成几行同步代码的原因。")

    print("\n注意：await 一个已经完成的协程（里面没有挂起）不会换人；")
    print("await 一个还没完成的任务才会挂起。A2 演示里的 await task 就属于后者。")

    assert log == [
        "甲:先记一笔",
        "乙:先记一笔",
        "甲:让出后再记一笔",
        "乙:让出后再记一笔",
    ]
    (run_dir / "suspend_points.json").write_text(
        json.dumps({"two_slow_order": log}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮顺序与来源。"""
    run_logged(
        "suspend_points_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
