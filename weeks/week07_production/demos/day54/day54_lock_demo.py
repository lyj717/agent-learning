"""Day54 C 的前置：单独认识 asyncio.Lock，以及共享计数为什么需要它。

从 demonstrate_async 读起。本例只用人工等待，不访问模型或 HTTP；
不实现窗口限额器，只回答“锁是什么、为什么共享计数会丢”。
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


async def bump_unsafe(counter: dict[str, int]) -> None:
    """不加锁：把共享计数读出来、让出去一会儿、再写回去。"""
    value = counter["n"]
    # sleep(秒数)：故意让出执行权，模拟真实里“读完之后又去等了网络”。
    await asyncio.sleep(0.01)
    counter["n"] = value + 1


async def bump_guarded(counter: dict[str, int], lock: asyncio.Lock) -> None:
    """加锁：读、改、写完整地放在一个 async with 里。"""
    async with lock:
        value = counter["n"]
        await asyncio.sleep(0.01)
        counter["n"] = value + 1


async def hold(lock: asyncio.Lock, name: str, pause: float, log: list[str]) -> None:
    """占住锁一段时间，记下进入和离开的顺序。"""
    async with lock:
        log.append(f"{name} 进入")
        await asyncio.sleep(pause)
        log.append(f"{name} 离开")


async def measure_peak(gate: Any, workers: int = 3, hold: float = 0.02) -> int:
    """让 workers 份工作同时抢同一个闸门，返回同时在里面的最大份数。"""
    inside = 0
    peak = 0

    async def one() -> None:
        """一份工作：进闸门待一会儿，再离开。"""
        nonlocal inside, peak
        async with gate:
            inside += 1
            peak = max(peak, inside)
            await asyncio.sleep(hold)
            inside -= 1

    await asyncio.gather(*(one() for _ in range(workers)))
    return peak


async def demonstrate_async(run_dir: Path) -> None:
    """展示锁保护共享计数、锁让第二个任务等待，以及它不是布尔开关。"""
    print("Week07 的 C 要给请求加“每个时间窗口最多开始几次”的限制。")
    print("动手之前先补一个前置：多份工作同时改同一份计数时，为什么需要锁。")
    print("学完能读懂 async with self.lock:，并说清它和“等一会儿”的区别。")

    print("\n一、是什么：asyncio.Lock 是一把异步锁。")
    print(
        "同一个锁的 async with 块，同一时刻只允许一个任务在里面；别的任务排队等它退出。"
    )

    print("\n二、为什么需要：共享计数的“读 → 改 → 写”中间会被别的任务插进来。")
    counter = {"n": 0}
    await asyncio.gather(bump_unsafe(counter), bump_unsafe(counter))
    print(f"  不加锁，两次 +1 之后 counter = {counter['n']}（期望 2）")
    print("  两个任务都读到了 0，各加一，再各写回 1；后写的那个把先写的覆盖了。")

    counter = {"n": 0}
    lock = asyncio.Lock()
    await asyncio.gather(bump_guarded(counter, lock), bump_guarded(counter, lock))
    print(f"  加锁，两次 +1 之后 counter = {counter['n']}（期望 2）")
    print("  第二个任务在 async with 处等第一个退出，进来时读到的是 1。")

    print("\n三、锁让后来者等待：两个任务抢同一把锁")
    log: list[str] = []
    lock = asyncio.Lock()
    await asyncio.gather(
        hold(lock, "甲", 0.05, log),
        hold(lock, "乙", 0.0, log),
    )
    print("  实际顺序：", " → ".join(log))
    print("  乙不是没执行，而是等甲离开后才进入。")

    print("\n四、注意：Lock 对象不是“锁没被占”的布尔值")
    probe = asyncio.Lock()
    print(f"  bool(Lock()) = {bool(probe)}；locked() = {probe.locked()}")
    async with probe:
        print(f"  进入 async with 后 locked() = {probe.locked()}")
    print(f"  离开块后 locked() = {probe.locked()}")
    print("  所以不要写 if not lock:；要进临界区就直接 async with lock:，让它自己等。")

    print("\n五、和 B 的信号量是什么关系")
    print("  Lock 就是“名额固定为 1 的信号量”：同一时刻只允许一份在里面。")
    lock_peak = await measure_peak(asyncio.Lock())
    sem_one_peak = await measure_peak(asyncio.Semaphore(1))
    sem_two_peak = await measure_peak(asyncio.Semaphore(2))
    print(f"  Lock          → 同时最多 {lock_peak} 份（期望 1）")
    print(f"  Semaphore(1)  → 同时最多 {sem_one_peak} 份（期望 1）")
    print(f"  Semaphore(2)  → 同时最多 {sem_two_peak} 份（期望 2）")
    sem = asyncio.Semaphore(2)
    print(f"  Semaphore(2) 刚创建时 locked() = {sem.locked()}（还有名额）")
    async with sem:
        print(f"  只占 1 个名额时 locked() = {sem.locked()}（仍可再进一份）")
    print("  区别不在“能不能同时进”，而在用途和 block 里放了什么：")
    print("  B 的信号量包住整段工作（里面可以 await 很久）；")
    print("  C 的锁只包住“看 count、占名额”这几行，等待要放到锁外。")

    print("\n六、和 C 的关系")
    print("  限额器里，“看窗口还有没有名额”和“占一个名额”必须成对做完；")
    print("  如果中间被别的任务插进来，两份额外的任务会同时看到“还有一个名额”。")
    print("  但“等窗口过去”这段要放在锁外面：占着锁睡觉，别人连判断都进不来。")

    assert counter["n"] == 2
    assert log == ["甲 进入", "甲 离开", "乙 进入", "乙 离开"]
    assert (lock_peak, sem_one_peak, sem_two_peak) == (1, 1, 2)
    (run_dir / "lock_demo.json").write_text(
        json.dumps(
            {
                "guarded_counter": counter["n"],
                "order": log,
                "peaks": {
                    "lock": lock_peak,
                    "semaphore_1": sem_one_peak,
                    "semaphore_2": sem_two_peak,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮讲解、实际顺序与来源。"""
    run_logged(
        "lock_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
