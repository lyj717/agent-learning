"""Day 4 剩下几个知识点的走查脚本。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

    1. 继承与 super().__init__()：让一个类基于另一个类来写
    2. __len__：让 len(自己的对象) 有意义
    3. Enum：把「只能从这几个值里挑」写进类型里
    4. @property：把算出来的值当属性用
    5. 模块与导入、if __name__ == "__main__" 到底在防什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_more_demo.py

另外单独跑一下这个，对比「直接运行」和「被导入」的区别：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_helpers.py
"""

from enum import Enum, StrEnum

import day04_helpers
from pydantic import BaseModel, ValidationError


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    """按顺序打印几行说明，让「先讲清楚再给代码」在源码里也看得见。"""
    for line in lines:
        print(line)


# ============================================================
section("1. 继承：让一个类基于另一个类来写")
# ============================================================

say(
    "这是什么：class 名字后面括号里写上另一个类，新类就自动拥有它的属性和方法。",
    "为什么需要：两个类常常有一大半代码是重复的，复制粘贴的话，改一处忘另一处。",
    "场景：普通消息 Message 和工具返回的消息 ToolMessage——后者只比前者多一个工具名。",
)
print()


class Message:
    """父类：一条普通消息。"""

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


class ToolMessage(Message):
    """子类：工具返回的消息，比普通消息多一个工具名。"""

    def __init__(self, content: str, tool_name: str) -> None:
        super().__init__(role="tool", content=content)  # 公共部分交给父类
        self.tool_name = tool_name  # 只写自己多出来的

    def __str__(self) -> str:
        return f"[{self.tool_name}] {super().__str__()}"  # 复用父类的显示逻辑


plain = Message(role="user", content="帮我查下天气")
tool = ToolMessage(content="杭州今天 22 度", tool_name="get_weather")

say(
    f"  普通消息打印出来：{plain}",
    f"  工具消息打印出来：{tool}",
)
print()

say(
    "继承在这里替我们省了什么：",
    "  ToolMessage 没有重写 role / content 的赋值，交给 super().__init__() 去做",
    "  它也没重写「role: content」的拼接格式，而是在 super().__str__() 的结果前面加东西",
    "",
    "三行语法各自的作用：",
    "  class ToolMessage(Message)   → 括号里写父类，表示「继承它」",
    "  super().__init__(...)        → 调用父类的初始化方法",
    "  super().__str__()            → 调用父类的 __str__，在结果上加东西",
    "",
    "另外，子类实例也是父类的实例："
    f"isinstance(tool, Message) = {isinstance(tool, Message)}",
    "",
    "要注意什么：继承表达的是「是一种」的关系（工具消息是一种消息）。",
    "只是「我需要用上对方」的时候不要继承，那是组合——day04_class_demo.py 第 5 节讲过。",
)


# ============================================================
section("2. __len__：让 len(自己的对象) 有意义")
# ============================================================

say(
    "这是什么：一个名字带双下划线的方法。写了它，len(你的对象) 就能用。",
    "为什么需要：len() 和 print() 一样，不认识你的类，它只会去找对象上的 __len__。",
    "           内置的 str、list、dict 都实现了它，所以它们能 len()；"
    "你的类默认没有，所以会报错。",
    "场景：一段对话历史，你想知道它已经攒了几条消息。",
)
print()


class Conversation:
    """一段对话历史。"""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def __len__(self) -> int:
        return len(self.messages)


empty = Conversation()
conv = Conversation()
conv.add(plain)
conv.add(tool)

say(
    f"  空的时候 len(conv) = {len(empty)}",
    f"  加了两条之后       = {len(conv)}",
    "",
    "  len(conv) 干的其实就是 conv.__len__()，两者结果一样。",
    "  真正在数长度的是里面那句 return len(self.messages)，"
    "外面的 len() 只是套了层语法糖。",
    "",
    "要注意什么：一旦有了 __len__，bool(对象) 也跟着变了——",
    f"  空会话 bool = {bool(empty)}，有消息的会话 bool = {bool(conv)}",
    "  因为 Python 判断真假时找不到 __bool__ 就退回去看 __len__，返回 0 就当假。",
    "  所以 if conversation: 说的是「有没有消息」，不是「对象存不存在」；",
    "  要判断 None 得写 if conversation is not None。",
)


# ============================================================
section("3. Enum：把「只能从这几个值里挑」写进类型里")
# ============================================================

say(
    "这是什么：把一组固定的选项定义成一个类型。像菜单上只有三道菜，"
    "除了这三样你点不了别的。",
    "为什么需要：像 role 这种字段本来只有 user / assistant / system 三种取值。",
    '           如果它的类型只是普通字符串，那么写成 "who"、"User"、'
    '"user "（多一个空格）都不会报错，',
    "           程序会一路带着这个错值跑到很远的地方才出问题。",
    "场景：一条消息的角色、一个任务的状态、一个工具的执行结果，都是固定几个选项。",
)
print()


class RoleFromEnum(str, Enum):
    """老写法（任何 Python 版本都能用）：混入 str，顺便还是个字符串。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Role(StrEnum):
    """新写法（Python 3.11+）：专门为「字符串枚举」准备的，推荐。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


say(
    "定义好之后，取值就写 Role.USER 这种形式，不再手打字符串。两种写法打印起来不一样：",
    f'  老写法 f"{{RoleFromEnum.USER}}" → {f"{RoleFromEnum.USER}"!r}',
    f'  新写法 f"{{Role.USER}}"        → {f"{Role.USER}"!r}',
    "",
    "这是两种写法唯一需要留心的地方：",
    '  老写法打印出来是 RoleFromEnum.USER，想要 "user" 必须显式写 .value',
    "  新写法用 StrEnum，打印出来就是值本身",
    f'  两个都「顺便」是字符串，所以能和 "user" 直接比较：'
    f'Role.USER == "user" → {Role.USER == "user"}',
    "",
    "枚举真正值钱的地方在这：拼错了当场报错，而且报错直接列出合法值有哪几个。",
)
print()


class StrictMessage(BaseModel):
    role: Role
    content: str


try:
    StrictMessage(role="who", content="你好")
except ValidationError as error:
    for line in str(error).splitlines()[:3]:
        print(" ", line)

say(
    "",
    '对比一下：如果 role 的类型写成普通字符串，"who" 会被照单全收，谁也不会拦，',
    "一路带到 Week 01 真的去调 API 时才被服务端拒绝——那时候更难查。",
    "附带好处：所有合法值集中在一处，读代码的人一看就知道有哪些可选。",
)


# ============================================================
section("4. @property：把算出来的值当属性用")
# ============================================================

say(
    "这是什么：在方法上面加一行 @property，这个方法就能像字段一样访问，不用加括号。",
    "为什么需要：有些值不是存下来的，而是由已有数据算出来的（总价、条数、平均值）。",
    "           对用的人来说，「总价」就该是个属性，不该是个动作。",
    "场景：购物车存的是单价列表，总额是算出来的。",
)
print()


class Basket:
    """购物车：只存单价列表，总额算出来。"""

    def __init__(self, prices: list[float]) -> None:
        self.prices = prices

    @property
    def total(self) -> float:
        return sum(self.prices)

    @property
    def count(self) -> int:
        return len(self.prices)


basket = Basket([399.0, 129.0, 129.0])
say(
    f"  不用加括号：basket.total = {basket.total}，basket.count = {basket.count}",
    "",
    "  和写成普通方法的区别：",
    "    basket.total()   → 调用者一看就知道「这是算出来的」",
    "    basket.total     → 用起来像读一个字段，读起来更顺",
    "",
    "要注意什么：",
    "  1. 默认只能读不能改，basket.total = 1 会报 AttributeError",
    "  2. 每次访问都会重新执行一遍函数，所以别在里面放网络请求、读大文件这类慢操作",
)

try:
    basket.total = 1  # 这一行就是要让它报错
except AttributeError as error:
    print("  试一下赋值：", error)


# ============================================================
section("5. 模块与导入、__main__ 到底在防什么")
# ============================================================

say(
    "这是什么：把代码分到不同文件里，用 import 互相使用。一个 .py 文件就是一个模块。",
    "为什么需要：全堆在一个文件里会越来越难找；而且文件有两种用途，"
    "混在一起会互相干扰——",
    "           一种是「给人直接运行的脚本」，一种是「被别的文件引用的库」。",
    "场景：day04_helpers.py 是库（放函数和常量），本文件是脚本（import 它来用）。",
)
print()

say(
    "本文件开头那句 import day04_helpers 执行的时候，屏幕上什么都没多出来。",
    "这就是 __main__ 保护在起作用：",
    f"  day04_helpers.__name__ = {day04_helpers.__name__!r}  ← 被导入时，值是模块名",
    f"  本文件被直接运行时 __name__ = {__name__!r}",
    "",
    f"拿它里面的东西来用：{day04_helpers.format_tool(day04_helpers.SEARCH_TOOL)}",
    "",
    "两种导入写法，区别只在「用的时候怎么称呼它」：",
    "  import day04_helpers                  → 用的时候写 day04_helpers.format_tool(...)",
    "  from day04_helpers import format_tool → 用的时候直接写 format_tool(...)",
    "  第一种一眼看出东西是哪来的，第二种少打字；真实代码里两种都有。",
    "",
    "现在自己跑一下这一条命令，对比一下：",
    "  .venv\\Scripts\\python.exe weeks\\week00_python\\day04_helpers.py",
    "同一个文件，直接运行时 __name__ 是 '__main__'，保护里面的代码才会执行。",
    "",
    "为什么需要这个保护：如果库文件一被 import 就顺手执行一堆东西，",
    "别人只是引一下你的模块，你的自测代码、示例脚本、"
    "甚至启动服务就会莫名其妙地跑起来。",
    "所以惯例是：库文件里只放定义，真正要执行的东西统统塞进 __main__ 保护里。",
)


section("总结")
say(
    "1. 继承说明「是一种」的关系；super() 用来复用父类的实现",
    "2. 写了 __len__，len(obj) 和 bool(obj) 就都跟着变了",
    "3. Enum 把「只能从这几个值里挑」变成类型约束，拼错当场报错",
    "4. StrEnum 打印出来就是值；class X(str, Enum) 得写 .value",
    "5. @property 让方法用起来像属性，代价是每次访问都重算、且默认不能赋值",
    "6. if __name__ == '__main__' 保护的是「被 import 时不要有副作用」",
)
