"""Day 34 知识点：把消息对象转换成接口使用的字典。

独立运行本文件即可；会议室与查询结果都是人工教学数据。
只学习 convert_to_openai_messages，不请求接口，不执行工具，不导入其他演示。
"""

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
    convert_to_openai_messages,
)


def main() -> None:
    """对照单条与列表输入、消息 ID 选项和工具参数的字典格式。"""
    print("=== 1. 这是什么 ===")
    print("convert_to_openai_messages 把消息对象转换成兼容 Chat Completions 的字典。")
    print("导入：from langchain_core.messages import convert_to_openai_messages")
    print("签名：convert_to_openai_messages(messages, *, text_format='string',")
    print("      include_id=False, pass_through_unknown_blocks=True)")
    print("messages 必填；星号后是可选参数，传它们时必须写参数名。")
    print("单条消息输入返回 dict；消息列表输入返回 list[dict]。")

    print("\n=== 2. 为什么需要它 ===")
    print("本地可以用 HumanMessage、AIMessage、ToolMessage 读写消息。")
    print("兼容 Chat Completions 的请求需要 role、content、tool_calls 等字典字段。")
    print("这个函数转换表示；调用它本身不会向任何服务商发送请求。")

    print("\n=== 3. 具体场景与输入 ===")
    print("用户想查会议室；assistant 发出查询点单；tool 回填可用时段。")
    print("这三条是人工写好的教学消息，没有真的查询或预订会议室。")
    # HumanMessage(content=..., id=...)：创建一条带自身消息 ID 的用户消息。
    user = HumanMessage(
        content="请查海棠会议室 14:00 起一小时是否可用。", id="user-room"
    )
    # AIMessage(tool_calls=...)：保存 assistant 点单；args 在对象中是参数字典。
    assistant = AIMessage(
        content="",
        id="assistant-room",
        tool_calls=[
            {
                "id": "call-room-01",
                "name": "lookup_room",
                "args": {"room": "海棠", "start": "14:00", "hours": 1},
            }
        ],
    )
    # ToolMessage(tool_call_id=...)：创建工具观察，用调用 ID 与 assistant 点单配对。
    observation = ToolMessage(
        content="海棠会议室 14:00～15:00 可用。",
        id="tool-room",
        tool_call_id="call-room-01",
    )
    messages: list[BaseMessage] = [user, assistant, observation]
    print(f"对象角色：{[message.type for message in messages]}")
    print(f"消息自身 ID：{[message.id for message in messages]}")
    args = assistant.tool_calls[0]["args"]
    print(f"转换前 args 类型={type(args).__name__}")
    print(f"  room={args['room']}，start={args['start']}，hours={args['hours']}")

    print("\n=== 4. 核心调用：单条与列表 ===")
    print("调用：single = convert_to_openai_messages(user)")
    # convert_to_openai_messages(单条消息)：返回一个字典，不会自动套列表。
    single = convert_to_openai_messages(user)
    assert isinstance(single, dict)
    print(f"传入 user：返回类型={type(single).__name__}")
    print(f"  role={single['role']}，content={single['content']}")

    print("调用：converted = convert_to_openai_messages(messages)")
    # convert_to_openai_messages(消息列表)：逐条转换，返回字典列表。
    converted = convert_to_openai_messages(messages)
    assert isinstance(converted, list)
    print(f"传入 messages：返回类型={type(converted).__name__}，长度={len(converted)}")
    for index, message in enumerate(converted, start=1):
        print(
            f"第 {index} 条：role={message['role']}，"
            f"含消息自身 id={'id' in message}，content={message['content']!r}"
        )
    print("角色对应：human → user；ai → assistant；tool → tool。")

    call = converted[1]["tool_calls"][0]
    function = call["function"]
    print(f"点单格式：type={call['type']}，function.name={function['name']}")
    print(f"function.arguments 类型={type(function['arguments']).__name__}")
    print(f"  参数 JSON：{function['arguments']}")
    print(f"assistant 点单的调用 ID={call['id']}")
    print(f"tool 观察的 tool_call_id={converted[2]['tool_call_id']}")
    print("默认省略的是消息自身 id；点单 id 和 tool_call_id 仍然保留。")

    print("\n=== 5. 可选参数逐个看 ===")
    print("include_id=False 是默认值；True 会把已有消息自身 ID 也放进字典。")
    with_ids = convert_to_openai_messages(messages, include_id=True)
    assert isinstance(with_ids, list)
    for index, message in enumerate(with_ids, start=1):
        print(f"  include_id=True，第 {index} 条的 id={message['id']}")
    print("保留消息 ID 便于本地核对；发请求前仍要核对服务商是否接受这个额外字段。")

    print("text_format='string' 是默认值：纯文本保持字符串。")
    print("若正文是多个纯文字块，会用换行合成字符串；这不表示所有正文都强转字符串。")
    print("text_format='block'：把本例的一段文字包装成一个 text 块。")
    as_blocks = convert_to_openai_messages(user, text_format="block")
    assert isinstance(as_blocks, dict)
    block = as_blocks["content"][0]
    print(f"  content 类型={type(as_blocks['content']).__name__}，块数=1")
    print(f"  第一块 type={block['type']}，text={block['text']}")
    print("text_format 只接受 'string' 或 'block'；其他值会抛 ValueError。")

    print("pass_through_unknown_blocks=True：遇到库不认识的正文块时允许原样保留。")
    print("设为 False 则拒绝不认识的正文块并报错；本例纯文字不涉及这个开关。")
    print("原样保留不代表服务商支持该块；本课不展开其他正文格式。")

    print("\n=== 6. 注意什么 ===")
    print("消息自身 id、assistant 点单的 id、tool 观察的 tool_call_id 是不同字段。")
    print("对象点单的 args 是字典；接口点单的 function.arguments 是 JSON 文本。")
    print("函数返回的是字典或字典列表，不是整份消息的 JSON 文本，也不是模型答复。")
    print("此处的原生字典指兼容 Chat Completions 的消息格式，不能据此套用所有接口。")


if __name__ == "__main__":
    main()
