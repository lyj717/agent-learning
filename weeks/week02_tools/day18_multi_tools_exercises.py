"""Day 18：接上天气和 SQLite 订单，让模型从三个工具中选择。

默认离线；加 --live 问模型（会发真实请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day18_multi_tools_exercises.py
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day18_multi_tools_exercises.py --live

在线选择记录见 day18_工具选择记录.md。
本文件运行时会调用 seed_db()，重建 day18_orders.sqlite 里的六条假订单；
手改内容会在下次运行时被覆盖。
"""

import json
import sys

from day17_tool_calling_exercises import build_tools as day17_build_tools
from day18_seed_db import seed_db
from llm_client import chat_with_tools, make_client
from tools import calculator, get_weather, query_orders

LIVE = "--live" in sys.argv

# 键与 build_tools() 中的 function.name 一致。
TOOL_TABLE = {
    "calculator": calculator,
    "get_weather": get_weather,
    "query_orders": query_orders,
}


def build_tools() -> list[dict]:
    """返回计算器、模拟天气和已支付订单查询的工具说明。"""
    TOOLS = day17_build_tools()
    TOOLS.append(
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "得到一个城市的天气情况，数据是模拟快照。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "需要得到天气的城市名",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    )
    TOOLS.append(
        {
            "type": "function",
            "function": {
                "name": "query_orders",
                "description": "查固定报表的已支付订单情况,按城市返回已支付笔数和总金额。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "需要被查询的城市名",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    )
    return TOOLS


def execute_tool_call(name: str, arguments: str) -> str:
    """按名称分发工具调用，并把本地结果转成字符串。"""
    text = json.loads(arguments)
    function = TOOL_TABLE.get(name)
    if function is None:
        raise ValueError(f"没有这个工具!工具名为{name}")
    return str(function(**text))


def ask_with_tools(question: str, *, max_rounds: int = 3) -> str:
    """让模型选择工具，逐个执行并回填，返回最终回答。"""
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
            result = execute_tool_call(call.function.name, call.function.arguments)
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
    print("=== 第 1 题：完成 tools.py 里的 get_weather 与 query_orders ===")
    print("准备 SQLite 练习数据：重建 orders 表和六条假订单。")
    seed_db()
    for label, function, city in [
        ("模拟天气", get_weather, "杭州"),
        ("SQLite 订单", query_orders, "杭州"),
    ]:
        print(f"{label}：{function(city)}")
    print("预期：杭州 22°C、多云；杭州 paid 2 单、合计 200 元。")

    print("\n=== 第 2 题：三份说明 + 分发 ===")
    descriptions = build_tools()
    print("工具名：", [item["function"]["name"] for item in descriptions])
    for name, args in [
        ("calculator", '{"expression": "347 * 28"}'),
        ("get_weather", '{"city": "上海"}'),
        ("query_orders", '{"city": "北京"}'),
    ]:
        print(f"{name}({args}) -> {execute_tool_call(name, args)}")
    print("预期：9716；上海 25°C 晴；北京 paid 1 单、90 元。")

    print("\n=== 第 3 题：模型自动选工具 ===")
    if not LIVE:
        print("加 --live 可查看模型选择工具的真实轨迹。")
    else:
        # 这里保留学员最后一次用于对照的问法。
        questions = ["上海天气适合运输货物吗？"]
        for question in questions:
            print(f"\n问题：{question}")
            print(f"最终答复：{ask_with_tools(question)}")
