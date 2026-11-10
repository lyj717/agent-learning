"""Day54 前置 A1：两个任务在 await 处交替执行。

从 demonstrate_async 读起。本例只有本机人工等待，不访问模型或 HTTP。
它只回答一个问题：一个线程里，两个任务怎么轮着跑。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

PAUSE = 0.01


async def work(name: str, marks: list[str], pause: float) -> None:
    """一份工作：记一个标记，等一会儿，再记下一个。"""
    marks.append(f"{name}-1")
    # sleep(秒数)：这里是真的挂起，事件循环可以趁这段时间运行别的任务。
    await asyncio.sleep(pause)
    marks.append(f"{name}-2")
    await asyncio.sleep(pause)
    marks.append(f"{name}-3")


async def demonstrate_async(run_dir: Path) -> None:
    """让两个任务同时跑，打印实际交替顺序。"""
    print("Week07 的 C 卡在“多份工作共用一个限额器”。补课前先看清最基础的一件事：")
    print("一个线程里，两个任务是怎么轮着跑的。")
    print("学完应能预测：哪一步之后会换人，换人时另一个任务从哪里接着跑。")

    print("\n一、场景：两份工作都要“记一笔 → 等一会儿 → 再记一笔”。")
    print("它们不是线程，也不并行；共用同一个事件循环，在 await 处让出执行权。")

    print("\n二、实际跑一遍")
    marks: list[str] = []
    # gather：把两个协程同时交给事件循环，并等它们都结束。
    await asyncio.gather(work("甲", marks, PAUSE), work("乙", marks, PAUSE))
    print("  实际顺序：", " → ".join(marks))

    print("\n三、为什么会这样")
    print("  甲先跑，记下 甲-1，然后在 sleep 处挂起；")
    print("  事件循环看乙还在等运行，就切到乙：记下 乙-1，乙也挂起；")
    print("  两个都挂起后，等 0.01 秒到期，先醒的那个接着记 甲-2/乙-2，以此类推。")
    print("  所以顺序不是“甲全部做完再做乙”，而是按每次 await 交错。")

    print("\n注意：交错只发生在真正挂起的 await 上。没有 await 的代码一口气跑完，")
    print("不会因为“两个任务同时提交”就自动分成两半；下一步演示专门看这一点。")

    assert marks == ["甲-1", "乙-1", "甲-2", "乙-2", "甲-3", "乙-3"]
    (run_dir / "task_order.json").write_text(
        json.dumps({"order": marks}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮顺序与来源。"""
    run_logged(
        "task_order_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
