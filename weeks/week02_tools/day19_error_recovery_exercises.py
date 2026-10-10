"""Day 19 练习：本地工具失败后，把错误回填给模型，让它在轮数上限内自纠。

先跑离线演示，再做本文件：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day19_error_recovery_demo.py
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day19_error_recovery_exercises.py
完成两题后再加 --live（会发真实请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day19_error_recovery_exercises.py --live

Day 18 已有三个工具和完整闭环。今天只增加「本地异常变成 tool 结果」及
「达到最大请求轮数就停」。观察与结论请写进仓库根目录的 FAILURES.md，
本文件末尾不用再写一份。模型是否真的改参数，以你运行时的轨迹为准。
"""

import sys

from day18_seed_db import seed_db

# 写第 1 题时取消下一行：execute_tool_call(工具名, JSON 参数字符串)
# 来自 Day 18；成功返回字符串，失败时抛异常。
# from day18_multi_tools_exercises import execute_tool_call

# 写第 2 题时取消下面两行：build_tools() 返回三份工具说明；
# make_client() 建客户端，chat_with_tools(messages, tools, client=...) 发一次模型请求。
# from day18_multi_tools_exercises import build_tools
# from llm_client import chat_with_tools, make_client

LIVE = "--live" in sys.argv


def tool_result_or_error(name: str, arguments: str) -> str:
    """第 1 题：本地工具成功就返回结果，失败就返回可回填的错误文字。

    要做的：调用 Day 18 的 execute_tool_call(name, arguments)。只用 try/except
    包住这次本地执行；成功时原样返回，异常时返回
    `工具执行失败：异常类名: 异常内容`。不要在这里调用模型，也不要吞掉异常后返回空串。
    期望结果：calculator 收到 `12 ** 2` 时得到以「工具执行失败：」开头的文字；
    收到 `12 * 12` 时得到字符串 `144`。未知工具、坏 JSON 也应变成错误文字。
    提示：`type(error).__name__` 是异常类名；`str(error)` 是具体原因。
    为了覆盖本仓库三个本地工具可能抛出的错误，可以在**本函数内部**捕获
    `Exception`；别把发模型请求的 `chat_with_tools` 也包进这个 try。
    顶部已留好 execute_tool_call 的注释 import，写本题时取消注释。
    """
    raise NotImplementedError("第 1 题：还没把本地工具异常变成回填文字")


def ask_with_recovery(question: str, *, max_rounds: int = 3) -> str:
    """第 2 题：在限定模型请求轮数内执行工具、回填结果或错误，并返回答复。

    要做的：沿用 Day 18 的 ask_with_tools() 循环；这次每个 tool_call 用
    tool_result_or_error(name, arguments) 取得结果，按原 call.id 回填。
    每轮打印轮次、工具名、原始参数、调用 ID、本地结果或错误。若模型没有继续点
    工具，就返回它的 content；循环用尽则明确返回「达到最大轮数」。
    期望结果：第一轮工具报错后，第二轮仍能请求模型；模型给出新工具调用就继续
    执行，给出最终答复就结束；一直点错时，最多请求 max_rounds 次。
    提示：max_rounds 数的是**模型请求**，不是 tool_calls 个数。一轮有两个
    tool_calls 时，要先保存整条 assistant 消息，再给两个 call 分别回填
    `{"role": "tool", "tool_call_id": call.id, "content": result}`。
    assistant 消息用 `message.model_dump(exclude_none=True)` 原样加入 messages。
    make_client、chat_with_tools 和 build_tools 的注释 import 已在顶部，写本题时
    取消注释。不要捕获 chat_with_tools 的网络/API 错误来冒充本地工具错误。
    """
    raise NotImplementedError("第 2 题：还没接上错误回填和轮数上限")


if __name__ == "__main__":
    # seed_db()：重建六条固定假订单；这让三工具闭环中的订单查询也随时可用。
    seed_db()
    print("=== 第 1 题：工具报错变成回填文字 ===")
    for label, name, arguments in [
        ("坏算式", "calculator", '{"expression": "12 ** 2"}'),
        ("改好的算式", "calculator", '{"expression": "12 * 12"}'),
        ("未知工具", "find_invoice", '{"invoice_id": "FP001"}'),
        ("坏 JSON", "calculator", '{"expression":'),
    ]:
        print(f"{label}：{tool_result_or_error(name, arguments)}")
    print("预期：坏算式、未知工具和坏 JSON 返回错误文字；改好的算式返回 144。")

    print("\n=== 第 2 题：错误回填与最大轮数 ===")
    if not LIVE:
        print("第 2 题写完后加 --live；如首轮没报错，就如实记录并调整问法再试。")
    else:
        question = (
            "请用 calculator 计算 12 ** 2，先把 expression 写成 12 ** 2。"
            "若工具报错，请根据错误改成等价的四则运算，不要自己心算。"
        )
        print(f"问题：{question}")
        print(f"最终答复：{ask_with_recovery(question)}")
