"""Day54 前置 A2b：亲手认识 Task 对象本身。

从 demonstrate_async 读起。本例只有本机人工等待，不访问模型或 HTTP。
它只回答一个问题：Task 是什么，为什么协程要变成 Task 才会跑。
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
    """人工动作：等 0.02 秒后返回地点字典。"""
    log.append(f"{place}:开始")
    await asyncio.sleep(0.02)
    log.append(f"{place}:结束")
    return {"place": place}


async def fail_once() -> None:
    """人工失败动作：等一会儿后抛异常。"""
    await asyncio.sleep(0.01)
    raise ValueError("人工失败，不请求服务商")


async def demonstrate_async(run_dir: Path) -> None:
    """看 Task 的类型、状态、结果和异常分别长什么样。"""
    print("Week07 的 C 之前，入口用 gather 把几份工作交给事件循环。")
    print("你一直只写“被调用的函数”，没亲手创建过 Task；本节补这一块。")
    print("学完应能说出：协程和 Task 差在哪，谁在调度，结果和异常存在哪。")

    log: list[str] = []

    print("\n一、协程不是任务：它只是“要做的事”的说明书")
    pending = read_notice("二楼", log)
    print(f"  type={type(pending).__name__}；日志={log}")
    print("  调用 async 函数只打包说明书，不会执行；要跑，得交给事件循环。")

    print("\n二、create_task：把说明书变成“排队中的任务”")
    task = asyncio.create_task(pending)
    print(f"  type={type(task).__name__}；done()={task.done()}；日志={log}")
    print("  Task 是事件循环的调度单位，它记住这份工作挂在哪、跑完没有。")

    print("\n三、让出一轮：Task 才有机会开始跑")
    await asyncio.sleep(0)
    print(f"  让出一轮后 done()={task.done()}；日志={log}")
    print("  它已经开始，但还在自己的 sleep 里，所以没结束。")

    print("\n四、await task：等它结束并取结果")
    result = await task
    print(f"  done()={task.done()}；result()={task.result()}；日志={log}")
    print("  await 一个没结束的 Task 会挂起；结束后再 await 会立刻拿到结果。")

    print("\n五、异常也存在 Task 里")
    bad = asyncio.create_task(fail_once())
    await asyncio.sleep(0.02)
    print(f"  done()={bad.done()}；exception()={type(bad.exception()).__name__}")
    try:
        await bad
    except ValueError as error:
        print(f"  await 一个失败的 Task 会重新抛出：{error}")

    print("\n注意：create_task 后要保留引用；丢了引用可能被回收，任务就悄悄没了。")
    print("gather 只是替你“批量 create_task 再一起等”，不是另一种对象。")

    assert result == {"place": "二楼"}
    assert task.done() and bad.done()
    (run_dir / "task_object.json").write_text(
        json.dumps(
            {"log": log, "task_type": type(task).__name__, "bad_error": "ValueError"},
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
    """保存本轮状态与来源。"""
    run_logged(
        "task_object_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
