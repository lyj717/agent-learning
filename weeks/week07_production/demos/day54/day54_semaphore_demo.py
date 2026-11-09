"""Day54 B1：单独认识 Semaphore 的名额、等待与异常后归还。

从 demonstrate_async 读起。本例是本机人工等待，不访问模型或 HTTP，
不实现后续练习的异步动作包装器。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


async def demonstrate_async(run_dir: Path) -> None:
    """展示同一个限制器的占用、等待和归还，不要求重写运行入口。"""
    print("Week07 要让多个任务共用受控的资源；本节认识控制同时执行数量的 Semaphore。")
    print(
        "学完能看出哪段工作正在占名额、其他任务何时等待，后面的练习会用它包住一个动作。"
    )
    print("\n一、是什么：Semaphore（信号量）在这里是一份可共享的名额管理器。")
    print("为什么需要：把很多任务交给 gather，不会自动限制其中只有几个进入工作区。")
    print(
        "场景：资料处理器只有两个处理名额；先看名额是否用尽，再看只有一个名额时的等待。"
    )
    print("\n二、导入与接口：import asyncio")
    print("asyncio.Semaphore(value=1) 创建管理器；value 是初始名额整数，省略时为 1。")
    print("本课使用正整数；0 合法但一开始没有可获取名额，负数会抛 ValueError。")
    print("async with sem: 先等待并取得一个名额，才执行块内代码；退出时自动归还。")
    print(
        "正常退出、return 或抛异常都会经过归还；不同任务必须共用同一个 sem 才能合计限制。"
    )
    print(
        "手工接口是 await sem.acquire()（取得时返回 True）、sem.release()（归还，返回 None）。"
    )
    print(
        "本课用 async with；sem.locked() 无参数，返回当前是否无法立即取得名额的 bool。"
    )

    print("\n三、两个名额：locked 只说明现在还能不能立即取得名额")
    # Semaphore(2)：创建一个初始有两个名额的对象；不是启动两个任务。
    sem = asyncio.Semaphore(2)
    flags = {"initial_locked": sem.locked()}
    async with sem:
        flags["one_used_locked"] = sem.locked()
        print("占用一个名额后 locked：", sem.locked(), "；仍可进入另一个任务。")
        async with sem:
            flags["two_used_locked"] = sem.locked()
            print("两个名额都占用后 locked：", sem.locked())
    flags["all_released_locked"] = sem.locked()
    print("两个块都退出后 locked：", sem.locked())

    print("\n四、一个名额：两个小工作共用同一个对象")
    single_slot = asyncio.Semaphore(1)
    steps: list[str] = []

    async def occupy_first() -> None:
        """演示用小工作：取得共享名额后暂停片刻，再退出工作区。"""
        async with single_slot:
            steps.append("第一份进入")
            print("第一份进入；现在占着唯一名额。")
            # sleep(秒数)：人工异步等待，让其他就绪任务可以继续运行。
            await asyncio.sleep(0.02)
            steps.append("第一份即将退出")
            print("第一份即将退出，async with 会归还名额。")

    async def wait_second() -> None:
        """演示用小工作：有自己的执行机会，也仍需等共享名额才能进入。"""
        steps.append("第二份申请")
        print("第二份已经执行到申请处，正在等名额。")
        async with single_slot:
            steps.append("第二份进入")
            print("第二份现在才进入。")

    # gather：同时调度两份工作，并等待两者完成；名额管理仍由共享对象负责。
    await asyncio.gather(occupy_first(), wait_second())

    print("\n五、异常：工作失败也会先退出工作区、归还名额，再把异常传给外面")
    try:
        async with single_slot:
            raise RuntimeError("人工失败，不请求服务商")
    except RuntimeError:
        released_after_error = not single_slot.locked()
        print("外面收到异常；唯一名额已归还：", released_after_error)
    assert flags == {
        "initial_locked": False,
        "one_used_locked": False,
        "two_used_locked": True,
        "all_released_locked": False,
    }
    assert steps.index("第一份即将退出") < steps.index("第二份进入")
    assert released_after_error
    (run_dir / "semaphore_demo.json").write_text(
        json.dumps(
            {
                "flags": flags,
                "waiting_steps": steps,
                "released_after_error": released_after_error,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("\n注意：名额管理器不替你调用业务函数；它只管受控代码块能否进入及何时退出。")
    print("等待中的任务不占工作名额；已进入的任务即使正在 await，也仍占着名额。")
    print(
        "Semaphore(2) 表示最多同时两个受控块，不表示每秒只允许两次。速率限制后段再学。"
    )
    print("本例限同一事件循环内共用的对象，不将其当作线程或多进程间的总限额。")


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮讲解、实际状态与来源。"""
    run_logged(
        "semaphore_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
