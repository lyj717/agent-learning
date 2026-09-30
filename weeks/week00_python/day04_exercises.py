"""Day 4 练习：类、self、特殊方法，以及 Pydantic 的校验与转换。

写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_exercises.py

本日考点（想不起来去查 docs/python-7天补齐清单.md 的 Day 4，
或者翻今天的两个演示脚本 day04_class_demo.py、day04_pydantic_demo.py）：
  - 类与实例：class、__init__(self, ...)、self 指的是「正在调用方法的这个实例」
  - 类属性 vs 实例属性：前者所有实例共享，后者各有一份
  - 特殊方法：__str__ 给人看（print 用的就是它），
    __repr__ 给开发者看（调试器、列表里显示的是它）
  - Pydantic：BaseModel + 类型注解，字段写完，__init__、__repr__、校验全有了
    · 校验失败会抛 pydantic.ValidationError，不会悄悄放过
    · .model_dump() 转成字典，.model_validate_json() 直接从 JSON 字符串解析
    · Field(default_factory=list) 处理可变默认值——Day 3 那个坑的自动挡
    · model_json_schema() 生成工具描述，Week 02 直接把这段交给模型
  - if __name__ == "__main__": 被 import 时不执行下面那段

做题规矩照旧：先自己想 20 分钟；每写完一题单独跑一次；
卡住就按 notes/卡住了怎么办.md 里的六招走，还不行再问我。
"""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

# ============================================================
# 第 1 题：手写一个 Message 类
# ============================================================


class Message:
    """一条对话消息：谁说的（role），说了什么（content）。
    期望结果：
        print(msg)   -> user: 你好，帮我查下天气
        f"{msg}"     -> 同上
        [msg]        -> [Message(role='user', content='你好，帮我查下天气')]
    """

    def __init__(self, role: str, content: str) -> None:
        """创建实例时执行一次，用来把数据存到这个实例身上。"""
        self.role = role
        self.content = content

    def __str__(self) -> str:
        """print(msg)、f"{msg}"、str(msg) 都会走到这里。"""
        return self.role + ": " + self.content

    def __repr__(self) -> str:
        """调试器、交互式环境、列表里显示的就是它。"""
        role = self.role
        content = self.content
        rep = f"Message({role=}, {content=})"
        return rep


# ============================================================
# 第 2 题：同样的数据，改用 Pydantic 写
# ============================================================


class PydanticMessage(BaseModel):
    """
    期望结果：
        PydanticMessage(role="user", content="你好") 能直接创建
        print 出来长这样：role='user' content='你好'
        .model_dump() 得到 {'role': 'user', 'content': '你好'}
    """

    role: str
    content: str


# ============================================================
# 第 3 题：用 Pydantic 描述一次工具调用
# ============================================================

# 假装这是模型返回的一段工具调用 JSON
RAW_TOOL_CALL = (
    '{"name": "search_docs", "arguments": {"query": "RAG 是什么", "top_k": 3}}'
)
RAW_TOOL_CALL_NO_ARGS = '{"name": "get_time"}'


class ToolCall(BaseModel):
    """Agent 要执行的一次工具调用：调哪个工具（name）+ 传什么参数（arguments）。
    期望结果：
        ToolCall(name="get_time")            -> arguments 自动是 {}
        ToolCall(name="x", arguments="不是字典") -> 抛 ValidationError
    """

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


def parse_tool_call(raw: str) -> ToolCall:
    """把模型返回的 JSON 字符串变成 ToolCall 对象。
    期望结果：
        parse_tool_call(RAW_TOOL_CALL).name            -> 'search_docs'
        parse_tool_call(RAW_TOOL_CALL).arguments["top_k"] -> 3
        parse_tool_call(RAW_TOOL_CALL_NO_ARGS).arguments  -> {}
        parse_tool_call('{"name": "x"')                -> 抛 ValidationError
    """
    return ToolCall.model_validate_json(raw)


# ============================================================
# 第 4 题：故意传错，看 Pydantic 怎么拦
# ============================================================


def demo_invalid_inputs() -> None:
    """把四种错误写法各跑一遍，看看报错长什么样。
    ValidationError，把报错打印出来：
        1. PydanticMessage(role=123, content="你好")
        2. PydanticMessage(content="没有 role")
        3. ToolCall(name="search_docs", arguments="不是字典")
        4. ToolCall.model_validate_json('{"name": "get_time"')
    期望结果：四种情况都抛 ValidationError，报错信息里能看出
    """
    cases = [
        ("数字传给字符串字段", lambda: PydanticMessage(role=123, content="你好")),
        ("必填字段缺失", lambda: PydanticMessage(content="没有 role")),
        ("模型参数不对", lambda: ToolCall(name="search_docs", arguments="不是字典")),
        (
            "JSON 本身就是坏的",
            lambda: ToolCall.model_validate_json('{"name": "get_time"'),
        ),
    ]
    for title, run in cases:
        print(f"--- {title} ---")
        try:
            run()  # ← 注意这里有括号，是在这里才执行的
        except ValidationError as e:
            print(e)


if __name__ == "__main__":
    print("=== 第 1 题：手写 Message 类 ===")
    msg = Message(role="user", content="你好，帮我查下天气")
    print(f"  print(msg)：{msg}")
    print(f"  单独看 repr：{msg!r}")
    print(f"  放进真正的列表里看到的是 repr：{[msg]}")

    print("\n=== 第 2 题：同样的数据，用 Pydantic 写 ===")
    pydantic_msg = PydanticMessage(role="user", content="你好，帮我查下天气")
    print(f"  print 出来：{pydantic_msg}")
    print(f"  它有哪些字段：{PydanticMessage.model_fields}")
    print(f"  .model_dump()：{pydantic_msg.model_dump()}")

    print("\n=== 第 3 题：从 JSON 解析工具调用 ===")
    call = parse_tool_call(RAW_TOOL_CALL)
    print(f"  工具名：{call.name}")
    print(f"  参数：{call.arguments}")
    print(f"  参数里的 top_k：{call.arguments['top_k']}")
    print(f"  不带参数的调用：{parse_tool_call(RAW_TOOL_CALL_NO_ARGS)}")
    print(f"  Week 02 要交给模型的工具描述：{ToolCall.model_json_schema()}")

    print("\n=== 第 4 题：故意传错，看 Pydantic 怎么拦 ===")
    demo_invalid_inputs()

# ============================================================
# 现象与原因（第 4 题跑完之后，把你的观察和解释写在这里）
# ============================================================
#
# 下面四种写法各自抛了什么错？报错信息里最关键的那句是什么？
#   validation error
#   PydanticMessage(role=123, content="你好")   ->
#   Input should be a valid string [type=string_type, input_value=123, input_type=int]
#   PydanticMessage(content="没有 role")        ->
#   Field required [type=missing, input_value={'content': '没有 role'}, input_type=dict]
#   ToolCall(name="x", arguments="不是字典")    ->
#   Input should be a valid dictionary [type=dict_type, input_value='不是字典', input_type=str]
#   ToolCall.model_validate_json('{"name": "x"')->
#   Invalid JSON: EOF while parsing an object
#   at line 1 column 19 [type=json_invalid, input_value='{"name": "get_time"', input_type=str]
#   为什么说「校验」值钱？如果不用 Pydantic，这些错会在什么地方才暴露？
#   校验将这些错误在一开始就拦在外面并告知如何修改，如果不校验，会直到这些内容被真正使用时才暴露，很难溯源
