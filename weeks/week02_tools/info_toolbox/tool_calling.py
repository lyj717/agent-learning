"""三工具说明、分发与错误回填：从 Day 17–19 已完成的代码迁入。"""

import json

from llm import chat_with_tools, make_client
from tools import calculator, get_weather, query_orders

TOOL_TABLE = {
    "calculator": calculator,
    "get_weather": get_weather,
    "query_orders": query_orders,
}


def build_tools() -> list[dict]:
    """返回计算器、模拟天气和已支付订单查询的工具说明。"""
    return [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "计算一个数学算式，支持 + - * / 和括号。需要做算术时用它。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": '要计算的算式，例如 "347 * 28" 或 "(12+34)/2"',
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
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
        },
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
        },
    ]


def execute_tool_call(name: str, arguments: str) -> str:
    """按名称分发工具调用，并把本地结果转成字符串。"""
    text = json.loads(arguments)
    function = TOOL_TABLE.get(name)
    if function is None:
        raise ValueError(f"没有这个工具!工具名为{name}")
    return str(function(**text))


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
