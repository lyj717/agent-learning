"""异常：程序遇到做不到的事怎么办。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day05_exception_demo.py
"""

import json
from pathlib import Path


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 异常是什么：做不到的事，就抛出来")
# ============================================================

say(
    "这是什么：程序执行过程中遇到做不到的事（文件不在、类型不对、键不存在），",
    "           会「抛出」一个异常对象，然后停止往下走。",
    "为什么需要：不处理的话整个程序当场中断；处理了就能决定「接下来怎么办」。",
    "场景：模型返回一段坏 JSON、配置文件里少了密钥、用户输入了 abc 而不是数字。",
)
print()


def parse_top_k(text: str) -> int:
    """把用户输入的字符串变成整数。"""
    return int(text)


say(f'  正常情况：parse_top_k("3") = {parse_top_k("3")}')
print()
say('  那 parse_top_k("三个") 会怎样？')
try:
    parse_top_k("三个")
except ValueError as error:
    say(
        f"    抛出了 ValueError：{error}",
        "    我们接住了它，程序继续往下跑——这就是 try/except 的作用。",
    )
print()
say(
    "如果没接住呢？整个脚本会直接中断，把调用栈打印出来，后面的代码一行都不执行。",
    "你 Day 4 第一次跑练习文件时看到的那片红字，就是这个。",
)


# ============================================================
section("2. 要捕具体的异常，不要一把抓")
# ============================================================

say(
    "这是什么：except 后面写什么类型，就只接住什么类型。",
    "为什么需要：写 except Exception 会把「你自己代码里的 bug」也一起接住，",
    "           于是错误被伪装成「数据问题」，你查半天查不出来。",
)
print()


def count_words(text: str) -> int:
    """数一数有几个词。注意下面有个故意的拼写错误。"""
    words = text.split()
    return len(words) + word_count  # noqa: F821  ← 这一行会抛 NameError


say("先看不推荐的写法（一把抓）：")
try:
    count_words("a b c")
except Exception as error:  # noqa: BLE001
    say(
        f"  被接住了：{type(error).__name__}: {error}",
        "  问题是：这明明是代码写错了，却被当成「运行时的意外」吞掉了。",
        "  如果这里接着写「没关系，按 0 处理」，这个 bug 会一直藏在程序里。",
    )
print()

say("再看推荐的做法（只捕预期内的类型）：")
try:
    count_words("a b c")
except ValueError as error:
    say(f"  当成数据错误处理：{error}")
except NameError as error:
    say(
        f"  这个才被单独接住：{type(error).__name__}: {error}",
        "  真实程序里它不会被接住，而是直接中断并指向出错的那一行——这正是你想要的。",
        "  一条实用经验：except 后面写得出具体类型，就写具体类型；",
        "  只有真的要「兜住一切」时（比如最外层的入口）才用 Exception，而且要记日志。",
    )


# ============================================================
section("3. else 和 finally：三段式")
# ============================================================

say(
    "这是什么：try 除了 except，还可以配 else 和 finally。",
    "为什么需要：它们把「出错时」和「不管怎样都要做」的代码分开放，意图更清楚。",
    "场景：读配置文件——成功就用它，失败就用默认值，最后不管怎样都记一条日志。",
)
print()


def read_first_line(path: Path) -> str:
    """读文件的第一行，读不到就抛 FileNotFoundError。"""
    with path.open(encoding="utf-8") as handle:
        return handle.readline().strip()


missing = Path("这个文件不存在.json")
try:
    line = read_first_line(missing)
except FileNotFoundError:
    say("  except：文件不在，用默认值顶上")
    line = "（没有配置，使用默认值）"
else:
    say("  else：上面没出错才会执行到这里")
finally:
    say("  finally：不管成功失败都会执行——收尾、关资源、记日志放这里")

say(f"  最终拿到的值：{line!r}")


# ============================================================
section("4. raise：自己主动抛错")
# ============================================================

say(
    "这是什么：你可以在发现数据不合理时，主动 raise 一个异常。",
    "为什么需要：早报错比晚报错好。让错误停在「刚发现问题」的地方，",
    "           而不是带着错值跑半小时后在一个不相干的地方炸掉。",
    "场景：工具参数校验——top_k 传了 0 或负数，直接拒绝，别硬着头皮往下算。",
)
print()


def check_top_k(value: int) -> int:
    """校验 top_k，不合格就抛 ValueError。"""
    if value <= 0:
        # 报错信息里要写清「期望什么、实际收到什么」
        raise ValueError(f"top_k 必须是正整数，收到的是 {value!r}")
    return value


say(f"  合格：check_top_k(5) = {check_top_k(5)}")
print()

say("  不合格时，报错信息写得好不好，差别很大：")
for bad_message in [None, "参数错误", "top_k 必须是正整数，收到的是 -1"]:
    if bad_message is None:
        say("    差：raise ValueError()   → 什么信息都没有")
    else:
        say(f'    写法：raise ValueError("{bad_message}")')
print()

try:
    check_top_k(-1)
except ValueError as error:
    say(f"  实际抛出来：ValueError: {error}")
say(
    "",
    "  对比一下 Day 4 里 Pydantic 的报错，风格是一样的：",
    "  Input should be a valid string [input_value=123, input_type=int]",
    "  期望什么 + 实际收到什么，两样都写，看到的人才知道怎么改。",
)


# ============================================================
section("5. 自定义异常：给自己的错误起个名字")
# ============================================================

say(
    "这是什么：自己定义一个异常类，通常就是继承 Exception，什么都不用写。",
    "为什么需要：调用方想「只接住配置问题」时，靠内置异常类型区分不出来，",
    "           一个名字清楚的异常比一堆字符串好得多。",
    "场景：缺少 API Key——这种错该让整个程序停下来，而不是当成普通数据错误。",
)
print()


class MissingConfigError(Exception):
    """缺少必需的配置项时抛这个。"""


def require_config(name: str, value: str | None) -> str:
    if not value:
        raise MissingConfigError(
            f"缺少配置 {name}：请复制 .env.example 为 .env，填入后重试"
        )
    return value


say(f"  传了值就用：{require_config('LLM_MODEL', 'gpt-4o-mini')}")
print()

try:
    require_config("LLM_API_KEY", None)
except MissingConfigError as error:
    say(
        f"  没传值就抛自定义异常：{type(error).__name__}",
        f"  里面的话可以直接念给人听：{error}",
        "",
        "  注意最后那句话的作用：它不只说「缺了什么」，还告诉人「怎么补上」。",
        "  报错信息是写给「半小时后焦头烂额的自己」看的。",
    )


# ============================================================
section("6. 异常之间也有继承关系")
# ============================================================

say(
    "  你可能见过好几个异常名字，它们其实排成一棵树。",
    f"  json.JSONDecodeError 是 ValueError 的子类吗："
    f"{issubclass(json.JSONDecodeError, ValueError)}",
    "",
    "  所以 except ValueError 除了接住 int('abc')，也会顺手接住 JSON 解析失败。",
    "  常用的一小把：",
    "    FileNotFoundError  路径不存在（open 读不到文件）",
    "    KeyError           字典里没这个键，或环境变量没设置",
    "    ValueError         值不合法（int('abc')、JSON 格式错）",
    "    TypeError          类型不对（字符串加数字）",
    "    AttributeError     对象没有这个属性（拼错了？类型不对？）",
)


# ============================================================
section("7. 要注意什么")
# ============================================================

say(
    "  1. 能用 if 判断的，别用异常：先 if path.exists() 比 try 读不到再 except 清楚。",
    "  2. 别写 except: pass——那是把问题扫到地毯下面，出问题时你连线索都没有。",
    "  3. 早抛：一进函数就检查参数，别算到一半才炸，那时候已经晚了。",
    "  4. except 里要保留原信息：可以 raise 重新抛出，或者 logger.exception 记下来，",
    "     别只在屏幕上打印一句「出错了」然后把异常吃掉。",
)


section("总结")
say(
    "1. try/except 接住预期的错误；except 后面写具体类型，别一把抓",
    "2. else 管「没出错时」，finally 管「无论如何都要做」",
    "3. raise 主动早报错，信息里写清期望什么、收到什么",
    "4. 自定义异常 = 继承 Exception，用名字表达「这是哪一类问题」",
    "5. 异常有继承关系，捕父类会顺带捕住子类",
)
