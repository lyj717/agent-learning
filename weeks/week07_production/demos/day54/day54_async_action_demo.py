"""Day54 B2：单独认识异步动作的函数、待执行对象和 await 后的结果。

从 demonstrate_async 读起；使用自己的人工通知案例，不依赖先跑其他演示。
这里没有信号量或完整的并发包装器，组合留给练习。
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
    """把异步动作的来源、调用与最终结果分别打印出来。"""
    print("Week07 将给不同动作统一加并发限制；先分清传来的异步函数该怎样执行。")
    print("本节只教调用角色与 await，不实现并发限制；练习再把它与名额管理接起来。")
    print("\n一、是什么：异步 action 仍是调用方写好的函数，调用后得到可等待对象。")
    print(
        "为什么需要：Day50 的普通 action() 可直接拿结果；本节还需 await 才拿到业务结果。"
    )
    print("场景：一个人工通知读取器，传入地点，异步等待后返回通知字典。")
    print("\n二、动作接口：read_notice(place: str) -> await 后得到 dict[str, str]")
    print(
        '必填地点字符串，例如 await read_notice("二楼") 得到 {place: 二楼, notice: 按时闭馆}。'
    )
    print("无模型或 HTTP 请求；这个演示函数已写好，正常返回。本节不另演示异常。")

    print("\n三、函数、待执行对象、业务结果")
    action = read_notice
    print("① action = read_notice：拿到函数，这一步没有执行函数体。")
    pending = action("二楼")
    print(
        "② pending = action(二楼)：拿到", type(pending).__name__, "，还没有业务字典。"
    )
    print("③ 下面执行 await pending，才会看到动作内部打印。")
    result = await pending
    print("④ await 完成，拿到业务结果：", result)
    assert result == {"place": "二楼", "notice": "按时闭馆"}
    (run_dir / "async_action_demo.json").write_text(
        json.dumps(
            {"pending_type": type(pending).__name__, "result": result},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("\n四、对应到练习的参数")
    print(
        "这里写 action = read_notice 只是把函数来源摆出来；练习入口会直接把已写好的函数传给你。"
    )
    print(
        "练习里不要重新给 action 赋值。按题面传 job_id，写 await action(job_id) 执行动作一次。"
    )
    print("不带括号的 action 是函数，action(job_id) 是可等待对象，await 后才是结果。")
    print(
        "异步等待抛出的异常仍可向调用方传递；具体输入、结果字段与失败案例见练习题面。"
    )


async def read_notice(place: str) -> dict[str, str]:
    """人工动作：place 字符串必填，等待后返回 place 与固定 notice 两个字符串字段。"""
    print("  动作内部：现在开始读取", place)
    # sleep(秒数)：人工异步等待，本例不发网络请求。
    await asyncio.sleep(0.01)
    return {"place": place, "notice": "按时闭馆"}


def demonstrate(run_dir: Path) -> None:
    """用 run 启动一次异步主过程，返回 None。"""
    asyncio.run(demonstrate_async(run_dir))


def main() -> None:
    """保存本次实际返回、配置与控制台。"""
    run_logged(
        "async_action_demo",
        demonstrate,
        {"model_calls": 0, "http_requests": 0},
        Path(__file__),
        Path(__file__).resolve().parent / "outputs",
        origin_env="DAY54_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
