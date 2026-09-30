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
卡住就按 notes/卡住了怎么办.md 里的五招走，还不行再问我。
"""

from pydantic import BaseModel

# 后面几题还会用到下面这些，等真用到了再往上加——
# 提前加会被 ruff 当成「导入了但没用」（F401）拦下来：
#   from typing import Any
#   from pydantic import Field, ValidationError


# ============================================================
# 第 1 题：手写一个 Message 类
# ============================================================


class Message:
    """一条对话消息：谁说的（role），说了什么（content）。

    要做的：把三个方法补完整。

        __init__(self, role, content)
            把两个参数存到实例属性上：self.role、self.content

        __str__(self) -> str
            返回 "user: 你好" 这样的形式，给人看。
            注意是 return 一个字符串，不是 print（day04_class_demo.py 第 1 节
            讲的就是「有返回值的函数要接住」）。

        __repr__(self) -> str
            给开发者看的形式，惯例是写成「重建这个对象的样子」：
            Message(role='user', content='你好')
            提示：f-string 里用 !r 能让字符串带上引号，
            day01_fstring_demo.py 里有这个用法。

    期望结果：
        print(msg)   -> user: 你好，帮我查下天气
        f"{msg}"     -> 同上
        [msg]        -> [Message(role='user', content='你好，帮我查下天气')]
    """

    def __init__(self, role: str, content: str) -> None:
        """创建实例时执行一次，用来把数据存到这个实例身上。"""
        raise NotImplementedError("第 1 题还没写：__init__")

    def __str__(self) -> str:
        """print(msg)、f"{msg}"、str(msg) 都会走到这里。"""
        raise NotImplementedError("第 1 题还没写：__str__")

    def __repr__(self) -> str:
        """调试器、交互式环境、列表里显示的就是它。"""
        raise NotImplementedError("第 1 题还没写：__repr__")


# ============================================================
# 第 2 题：同样的数据，改用 Pydantic 写
# ============================================================


class PydanticMessage(BaseModel):
    """和上面的 Message 表达同样的东西，但你一个字的方法都不用写。

    要做的：在这个类里写两行字段：
        role: str
        content: str

    不要写 __init__，也不要写 __str__ / __repr__——Pydantic 全都替你生成。

    期望结果：
        PydanticMessage(role="user", content="你好") 能直接创建
        print 出来长这样：role='user' content='你好'
        .model_dump() 得到 {'role': 'user', 'content': '你好'}

    要留意的地方：Pydantic 默认会「忽略你没定义的字段」，所以如果你
    少写了一个字段，这里不会报错，只会得到一个空模型。主程序里特意
    打了 model_fields，就是让你一眼看穿这件事。
    """


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

    要做的：写两行字段
        name: str
        arguments: dict[str, Any]

    arguments 要允许不传（不传时是空字典），所以这一行得写成：
        arguments: dict[str, Any] = Field(default_factory=dict)

    为什么要用 Field(default_factory=dict) 而不是直接写 = {}？
    想想第 4 题（Day 3 那道）——同一个坑，Pydantic 给了标准解法。
    记得把 Field 和 Any 加到文件顶部的导入里。

    期望结果：
        ToolCall(name="get_time")            -> arguments 自动是 {}
        ToolCall(name="x", arguments="不是字典") -> 抛 ValidationError
    """


def parse_tool_call(raw: str) -> ToolCall:
    """把模型返回的 JSON 字符串变成 ToolCall 对象。

    要做的：一行就够——用 Pydantic 自带的方法，不要自己 json.loads 再拼。

    提示：查一下 ToolCall 上名字带 validate 的方法，看哪个能直接吃字符串。

    期望结果：
        parse_tool_call(RAW_TOOL_CALL).name            -> 'search_docs'
        parse_tool_call(RAW_TOOL_CALL).arguments["top_k"] -> 3
        parse_tool_call(RAW_TOOL_CALL_NO_ARGS).arguments  -> {}
        parse_tool_call('{"name": "x"')                -> 抛 ValidationError
    """
    raise NotImplementedError("第 3 题还没写")


# ============================================================
# 第 4 题：故意传错，看 Pydantic 怎么拦
# ============================================================


def demo_invalid_inputs() -> None:
    """把四种错误写法各跑一遍，看看报错长什么样。

    要做的：写一个循环，把下面四种情况逐个跑一次，用 try/except 接住
    ValidationError，把报错打印出来：

        1. PydanticMessage(role=123, content="你好")
              数字当成字符串传进去了
        2. PydanticMessage(content="没有 role")
              必填字段没给
        3. ToolCall(name="search_docs", arguments="不是字典")
              参数该是字典，给了字符串
        4. ToolCall.model_validate_json('{"name": "get_time"')
              JSON 本身就是坏的，少一个大括号

    提示：这几个都是「要抛异常」的写法，不是正常流程，所以必须包在
    try/except 里，否则第一行就中断了。

    期望结果：四种情况都抛 ValidationError，报错信息里能看出
    「哪个字段、期望什么类型、实际收到了什么」。
    """
    raise NotImplementedError("第 4 题还没写")


if __name__ == "__main__":
    print("=== 第 1 题：手写 Message 类 ===")
    msg = Message(role="user", content="你好，帮我查下天气")
    print(f"  print(msg)：{msg}")
    print(f"  单独看 repr：{msg!r}")
    print(f"  放进列表里看到的是 repr：[{msg}]")

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
#
#   PydanticMessage(role=123, content="你好")   ->
#
#   PydanticMessage(content="没有 role")        ->
#
#   ToolCall(name="x", arguments="不是字典")    ->
#
#   ToolCall.model_validate_json('{"name": "x"')->
#
# 为什么说「校验」值钱？如果不用 Pydantic，这些错会在什么地方才暴露？
#
# （写完可以把这几行删掉，或者留着当笔记）
