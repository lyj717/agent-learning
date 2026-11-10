"""Day54 前置 A2：调用 async 函数后拿到什么，Task 又是什么。

从 demonstrate_async 读起。本例只有本机人工等待，不访问模型或 HTTP。
它只回答一个问题：一个 async 函数从“被调用”到“跑完”，中间经过哪几个对象。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


async def read_notice(place: str, log: list[str]) -> dict[str, str]:
    """人工动作：进入函数体记一笔，等待一会儿，返回地点字典。"""
    log.append("函数体开始")
    await asyncio.sleep(0.01)
    log.append("函数体结束")
    return {"place": place}


async def demonstrate_async(run_dir: Path) -> None:
    """分三步看：协程对象、Task、await 后的结果。"""
    print("Week07 的 C 里，入口把你的限额器和几份工作一起交给事件循环。")
    print("要读懂那段，先分清代码在哪一步才真正开始执行。")
    print("学完应能说出：调用、创建 Task、await，三者各做了什么。")

    log: list[str] = []

    print("\n一、只调用：拿到的是协程对象，函数体还没开始")
    pending = read_notice("二楼", log)
    print(f"  类型={type(pending).__name__}；日志={log}")
    print("  这一步只是把“要做的事”打包好，没有执行。")

    print("\n二、create_task：把它交给事件循环排队")
    task = asyncio.create_task(pending)
    print(f"  类型={type(task).__name__}；日志={log}")
    print("  刚创建时还没轮到它跑；要等当前代码让出执行权。")

    print("\n三、让出一次，再 await 结果")
    # sleep(0)：让事件循环跑一轮已经排队的任务，然后回到这里。
    await asyncio.sleep(0)
    print(f"  让出一轮后日志={log}")
    print(
        "  这条日志是 task 在刚才那一轮里跑出来的；sleep(0) 自己什么都没做，只让了一下。"
    )
    print(
        "  await 不是“启动开关”：task 在 create_task 时就已经排队，这里只是给它一次运行机会。"
    )
    result = await task
    print(f"  await task 得到={result}；最终日志={log}")
    print("  await 的任务如果已完成，会立刻拿到结果，不再挂起。")

    print("\n注意：只调用不 await，函数体永远不执行；")
    print(
        "await 一个协程会执行它，await 一个 Task 只是等它完成——Task 可能早就开始跑了。"
    )
    print(
        "另外要对 create_task 的返回值保留引用：丢了引用，任务可能被回收，也 await 不到。"
    )
    print("本步之后才轮到“谁在什么时候被切换”，即 A1 演示的交替顺序。")

    assert log == ["函数体开始", "函数体结束"]
    assert result == {"place": "二楼"}
    (run_dir / "await_states.json").write_text(
        json.dumps({"log": log, "result": result}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def demonstrate(run_dir: Path) -> None:
    """从普通脚本启动一次异步主过程。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮状态与来源。"""
    run_logged(
        "await_states_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
