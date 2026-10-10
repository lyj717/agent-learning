"""Day 19：本地工具失败后回填错误，并限制模型请求轮数。

直接运行只调用本地工具；加 --live 会请求真实模型。
学员的运行观察保存在文件末尾。
"""

import sys

from day18_multi_tools_exercises import build_tools, execute_tool_call
from day18_seed_db import seed_db
from llm_client import chat_with_tools, make_client

LIVE = "--live" in sys.argv


def tool_result_or_error(name: str, arguments: str) -> str:
    """执行本地工具；成功返回结果，失败返回可回填的错误文字。"""
    try:
        return execute_tool_call(name, arguments)
    except Exception as error:  # noqa: BLE001  本地工具的不同异常都要回填给模型。
        return f"工具执行失败：{type(error).__name__}: {error!s}"


def ask_with_recovery(question: str, *, max_rounds: int = 3) -> str:
    """请求模型、执行并回填工具结果，在轮数上限内返回最终答复。"""
    istoolcall = False
    client = make_client()
    messages = [{"role": "user", "content": question}]
    rounds = 0
    for round_no in range(1, max_rounds + 1):
        rounds = round_no
        message = chat_with_tools(messages, build_tools(), client=client)
        if not message.tool_calls:
            if istoolcall is False:
                print("本次未调用工具")
            return message.content or ""
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            istoolcall = True
            result = tool_result_or_error(call.function.name, call.function.arguments)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
            print(f"     [第 {round_no} 轮] 它点了 {call.function.name}")
            print(f"        id        = {call.id}")
            print(f"        arguments = {call.function.arguments}")
            print(f"        → 本地执行 = {result}")
    if rounds == max_rounds:
        return "达到最大轮数！"
    return "模型调用失败，请重试！"


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
        print("离线模式不请求模型；加 --live 可观察真实工具调用。")
    else:
        question = (
            "请用 calculator 计算 12 ** 2，先把 expression 写成 12 ** 2。"
            "若工具报错，请根据错误改成等价的四则运算，不要自己心算。"
        )
        print(f"问题：{question}")
        print(f"最终答复：{ask_with_recovery(question)}")


# 现象与原因（完成练习并运行后，由学员填写；不要照抄演示中的人为轨迹）
#
# 1. 第 1 题里，坏算式得到的错误文字是什么？好算式为什么返回 144？
#    我的观察：工具执行失败：<class 'ValueError'>: 算式里出现了我不认识的东西：BinOp(left=Constant(value=12), op=Pow(), right=Constant(value=2))
#    我的解释：好算式为12 * 12符合工具函数，因此能正确调用
#
# 2. 跑 day19_error_recovery_probe.py：一直点错且 max_rounds=2 时，
#    模型请求了几次？为什么「请求轮数」与「工具调用次数」不能混为一谈？
#    我的观察：模型请求了两次
#    我的解释：模型一次请求可以不止调用一个工具，也可以不调用工具，两者次数不一定相同
#
# 3. 跑 --live：第一轮实际选了哪个工具、给了什么参数？工具有没有报错？
#    如果报错，回填后模型下一轮怎么做、最终答复是什么？如果没报错，
#    如实写「未观察到错误」和你尝试过的问法，不要补造自纠过程。
#    第一轮：选了calculator，
#    id = call_00_nWeJSJNsAjqfOrDAAC0g4885
#    arguments = {"expression": "12 ** 2"}
#   报错了，工具执行失败：<class 'ValueError'>: 算式里出现了我不认识的东西：BinOp(left=Constant(value=12), op=Pow(), right=Constant(value=2))
#    第二轮：选了calculator
#   id = call_00_aXi9Uu9fwZLWMctrTSzr4746
#    arguments = {"expression": "12 * 12"}
#   最终答复：计算完成：**12 × 12 = 144**。
#   （首次调用时 `12 ** 2` 报错，因为该工具不支持幂运算符 `**`；按你的要求改成了等价的乘法 `12 * 12`，没有心算。）
# 4. 若用户问「南京的模拟天气」，本地工具报不支持南京后，
#    为什么不能擅自改成查询上海？你会怎样向用户说明？
#    我的回答：擅自改成查询上海属于乱调用工具，应该向用户说明自己不支持这座城市的天气查询
