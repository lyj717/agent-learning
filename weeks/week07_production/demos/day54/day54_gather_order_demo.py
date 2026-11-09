"""Day54 A 回温：区分 gather 的传入顺序、实际完成顺序和返回列表顺序。

先读 demonstrate_async；人工等待只演示调度，不访问模型或 HTTP。
本例不引入 Semaphore，也不提供后续并发限制练习的参考实现。
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
    """只交换 gather 的两个传入位置，核对实际完成顺序与结果位置。"""
    print("Week07 将控制多个任务的同时执行数量；先恢复 gather 的结果对应关系。")
    print("本节只解决一个问题：快的任务先完成，返回列表会不会把它放在第一项？")
    print("\n一、是什么：gather 把多个可等待对象交给异步调度，并收集各自的返回值。")
    print("为什么需要：同时读取多份资料后，还要知道每一份结果对应哪一次输入。")
    print("场景：书架资料的人工等待较长，门口通知较短；交换它们的传入位置。")
    print("\n二、调用接口（由 import asyncio 提供）")
    print("await asyncio.gather(待执行对象1, 待执行对象2, ...)")
    print(
        "这里传入 read_piece(...) 得到的对象；本例全部正常结束，await 后得到结果列表。"
    )
    print(
        "列表第 1 项对应第 1 个传入对象，第 2 项对应第 2 个；不会按完成时间重新排序。"
    )
    print(
        "可选 return_exceptions 默认 False，本例不传；异常与取消另讲，这里不增加新目标。"
    )

    print("\n三、先传书架资料，再传门口通知")
    finished_a: list[str] = []
    # gather：并发调度传入对象；await 后返回按传入位置排列的结果列表。
    values_a = await asyncio.gather(
        read_piece("书架资料", 0.06, finished_a),
        read_piece("门口通知", 0.01, finished_a),
    )
    print("传入顺序：", ["书架资料", "门口通知"])
    print("本轮实际完成顺序：", finished_a)
    print("gather 返回列表：", values_a)

    print("\n四、只交换传入位置：先门口通知，再书架资料")
    finished_b: list[str] = []
    values_b = await asyncio.gather(
        read_piece("门口通知", 0.01, finished_b),
        read_piece("书架资料", 0.06, finished_b),
    )
    print("传入顺序：", ["门口通知", "书架资料"])
    print("本轮实际完成顺序：", finished_b)
    print("gather 返回列表：", values_b)
    assert values_a == ["书架资料", "门口通知"]
    assert values_b == ["门口通知", "书架资料"]
    (run_dir / "gather_order.json").write_text(
        json.dumps(
            [
                {
                    "input_order": ["书架资料", "门口通知"],
                    "finished": finished_a,
                    "result": values_a,
                },
                {
                    "input_order": ["门口通知", "书架资料"],
                    "finished": finished_b,
                    "result": values_b,
                },
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("\n五、注意：完成顺序记录在哪里 append；结果顺序看 gather 传入位置。")
    print("两种顺序可能相同，也可能不同；返回值是一个列表，不是两种随机排列的字符串。")
    print("asyncio.sleep 会在等待期间让出控制权；time.sleep 会阻塞当前线程。")
    print("只把函数写成 async def，不会自动把内部的阻塞调用变成异步等待。")
    print("人工等待的实际完成顺序另存 JSON，不要求匹配固定耗时；没有模型或服务请求。")


async def read_piece(name: str, delay: float, finished: list[str]) -> str:
    """运行背景：三个参数必填，等待 delay 秒后向 finished 追加 name，并返回该字符串。"""
    print("  开始：", name)
    # sleep(秒数)：可等待的人工延迟；await 时让其他就绪任务有机会继续执行。
    await asyncio.sleep(delay)
    finished.append(name)
    print("  完成：", name)
    return name


def demonstrate(run_dir: Path) -> None:
    """由日志入口传入已创建的本轮目录，启动一次异步主过程。"""
    # run(协程对象)：在普通脚本中启动事件循环，等本次主过程完成后关闭。
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本轮控制台、配置、源码摘要和实际顺序，不填写学员短检验。"""
    run_logged(
        "gather_order_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0, "purpose": "async_prerequisite_review"},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
