"""Day 4 综合题：把今天学的拼起来，给聊天历史做一个 Conversation 类。

Week 01 你要写的流式 CLI 聊天机器人，内部就得有这么个东西：
一边往里追加消息，一边能整体打印出来，还要能转成 API 要的格式。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_conversation_exercise.py

做完这题，Day 4 的清单就齐了。卡住先按 notes/卡住了怎么办.md 的五招走。
"""

from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    """消息角色。只能从这三个里挑。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """一条消息。只有两个字段，校验交给 Pydantic。"""

    role: Role
    content: str


class Conversation:
    """一段对话历史。
    1. 准备一个空列表装消息，存到 self.messages
    2. 往历史里追加一条，不返回值
    3. 返回消息条数，让 len(conv) 能用
    4. 把整段历史拼成多行文本，每行 "role: content"
    5. 转成 OpenAI API 要的形状：
        [{"role": "user", "content": "..."}, ...]
    """

    def __init__(self) -> None:
        self.messages = []

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def __len__(self) -> int:
        return len(self.messages)

    def __str__(self) -> str:
        line = []
        for message in self.messages:
            line.append(f"{message.role}: {message.content}")
        return "\n".join(line)

    def to_api_messages(self) -> list[dict[str, str]]:
        txt = []
        for message in self.messages:
            txt.append(message.model_dump(mode="json"))
        return txt


class SystemMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__(role=Role.SYSTEM, content=content)


if __name__ == "__main__":
    conv = Conversation()
    conv.add(Message(role=Role.SYSTEM, content="你是一个简洁的助手"))
    conv.add(Message(role="user", content="杭州今天天气怎么样"))
    conv.add(Message(role=Role.ASSISTANT, content="22 度，多云"))

    print("=== 整段历史（__str__） ===")
    print(conv)

    print("\n=== 条数（__len__） ===")
    print(f"len(conv) = {len(conv)}")

    print("\n=== 转成 API 要的格式（to_api_messages） ===")
    for item in conv.to_api_messages():
        print(f"  {item}")
    print("  注意 role 已经是普通字符串 'user'，不是枚举对象——")
    print("  因为这段要交给 json.dumps 发出去。")


# ============================================================
# 现象与原因
# ============================================================
#
# 1. Message(role="who", content="你好") 抛的错，关键那句是什么？
#    validation error
#    Input should be 'user', 'assistant' or 'system' [type=enum, input_value='who', input_type=str]
# 2. 如果 Message 的 role 类型写成普通的 str，而不是 Role 枚举，
#    上面那种拼错会在什么时候才被发现？
#     到实际调用时才会发现，而且很难发现问题在哪
# 3. 这题用的是 StrEnum。如果换成 class Role(str, Enum)，
#    __str__ 里 f"{m.role}" 会打印出什么？要怎么改才对？
#    打印出Role.USER(类名.成员名），需要加上.value
# 4. 为什么 to_api_messages 不能直接用默认的 model_dump()？
#    （想想 role 会变成什么，以及这段数据接下来要去哪）
#     因为json格式不支持Role这种自己定义的格式，只能先转化成str格式
# 加分：
#   写一个 SystemMessage(Message)，创建时只给 content，
#   role 自动是 Role.SYSTEM。
