"""Day 34 知识点：把接口字典转换成 LangChain 消息对象。

独立运行本文件即可；诊室、时段与工具结果都是人工教学数据。
只学习 convert_to_messages，不调用模型，不执行工具，不建立业务图。
"""

import json

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
    convert_to_messages,
)


def main() -> None:
    """逐字段对照字典消息与消息对象，并核对单条输入的包装方式。"""
    print("=== 1. 这是什么 ===")
    print("convert_to_messages 把一批消息转换成 LangChain 的消息对象列表。")
    print("导入：from langchain_core.messages import convert_to_messages")
    print("本课写法：convert_to_messages(messages) -> list[BaseMessage]")
    print("messages 是唯一的必填参数；本例传 list[dict]，没有其他可选参数。")
    print("BaseMessage 是消息对象的共同基类名称，不是让你自己创建的消息角色。")
    print("函数也支持其他消息表示；今天只看接口字典，不展开其他输入。")

    print("\n=== 2. 为什么需要它 ===")
    print("兼容 Chat Completions 的接口用字典保存 role、content 和 tool_calls。")
    print("已经学过的消息对象则用 .type、.content、.tool_calls 等属性读取。")
    print("转换函数负责统一表示；转换之后才能按对象的属性读取这些字段。")

    print("\n=== 3. 具体场景与输入 ===")
    print("用户问诊室可约时段；assistant 点单查询；tool 给回一条时段观察。")
    print("下面三条消息都是事先写好的教学材料，查询没有真的执行。")
    # json.dumps(对象, ensure_ascii=False)：把参数字典写成保留中文的 JSON 文本。
    arguments = json.dumps(
        {"clinic": "皮肤科", "day": "明天", "period": "下午"}, ensure_ascii=False
    )
    native_messages: list[dict] = [
        {
            "role": "user",
            "id": "user-message-clinic",
            "content": "请查明天下午皮肤科的可约时段。",
        },
        {
            "role": "assistant",
            "id": "assistant-message-clinic",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-clinic-01",
                    "type": "function",
                    "function": {
                        "name": "lookup_clinic_slots",
                        "arguments": arguments,
                    },
                }
            ],
        },
        {
            "role": "tool",
            "id": "tool-message-clinic",
            "tool_call_id": "call-clinic-01",
            "content": "明天下午可约：14:00、15:30。",
        },
    ]
    print(f"转换前角色：{[message['role'] for message in native_messages]}")
    print(
        f"转换前 assistant.content={native_messages[1]['content']!r}，"
        f"类型={type(native_messages[1]['content']).__name__}"
    )
    print(f"转换前 function.arguments 类型：{type(arguments).__name__}")
    print(f"转换前参数 JSON：{arguments}")

    print("\n=== 4. 核心调用与逐字段结果 ===")
    print("调用：converted = convert_to_messages(native_messages)")
    # convert_to_messages(一批消息)：转换每条消息，始终返回消息对象列表。
    converted: list[BaseMessage] = convert_to_messages(native_messages)
    print(f"返回容器类型：{type(converted).__name__}；消息数：{len(converted)}")
    for index, message in enumerate(converted, start=1):
        print(
            f"第 {index} 条：类名={type(message).__name__}，"
            f".type={message.type}，.id={message.id}"
        )
        print(f"  .content={message.content!r}")
    print("角色对应：user → human；assistant → ai；tool → tool。")

    assistant = converted[1]
    observation = converted[2]
    # 本例的第二、三条分别应转换成 AIMessage、ToolMessage，再读取各自特有的属性。
    assert isinstance(assistant, AIMessage)
    assert isinstance(observation, ToolMessage)
    print(f"本例的 None 正文转为 AIMessage.content={assistant.content!r}，类型=str。")
    print("空字符串表示这条点单没有正文；它不是模型给出的最终答复。")
    call = assistant.tool_calls[0]
    print(f"assistant.tool_calls[0]['name']={call['name']}")
    print(f"assistant.tool_calls[0]['args'] 类型={type(call['args']).__name__}")
    print(
        f"  clinic={call['args']['clinic']}，day={call['args']['day']}，"
        f"period={call['args']['period']}"
    )
    print(f"点单的调用 ID：{call['id']}")
    print(f"tool 观察配对的 tool_call_id：{observation.tool_call_id}")
    print(f"调用 ID 配对相同：{call['id'] == observation.tool_call_id}")
    print("消息自身的 .id 也保留；它给消息编号，tool_call_id 给工具调用配对。")

    print("\n=== 5. 只有一条时怎样传 ===")
    single = convert_to_messages([native_messages[0]])
    print("调用：convert_to_messages([native_messages[0]])")
    print(f"返回仍是 {type(single).__name__}，长度={len(single)}；不是一条裸对象。")
    print(f"取第一条后才得到 {type(single[0]).__name__}，内容={single[0].content}")

    print("\n=== 6. 注意什么 ===")
    print("单条字典也用 [字典] 包装；不要把单个字典当成这一批消息直接传入。")
    print("原生点单的 function.arguments 是 JSON 文本；对象点单的 args 是字典。")
    print("已有消息 ID 和调用 ID 各自保留，转换不会把它们变成同一种编号。")
    print("这里只转换消息表示，不请求模型，也不执行点单里的查询。")
    print("转换成功不能证明查询结果真实，也不能代替你的业务参数检查。")


if __name__ == "__main__":
    main()
