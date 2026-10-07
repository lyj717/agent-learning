"""Day 16 加餐：怎么判断「11 位数字」——`re.fullmatch` 是什么，以及它的坑。

演示脚本里那句 `re.fullmatch(r"\\d{11}", value)` 是这一节的主角。
完全离线，跑法：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_regex_demo.py
"""

import re


def section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# ============================================================
section("1. 先说清楚：re 是标准库，fullmatch 在问「整串对不对得上」")
# ============================================================

print(
    """  re 是 Python 自带的正则表达式模块（不用装，import re 就有）。

  re.fullmatch(模式, 字符串) 回答的是一个问题：
     「整个字符串，是不是**正好**符合这个模式？」
     符合 -> 返回一个 Match 对象（在 if 里是真值）
     不符合 -> 返回 None（在 if 里是假值）

  所以它几乎总是这么用：
     if re.fullmatch(模式, 值) is None:
         报错

  为什么需要它：你要的规则是「11 位数字」——这是**格式**，不是类型。
  `str` 只能告诉你「它是个字符串」，管不了「这个字符串长什么样」。"""
)


# ============================================================
section("2. 把 r'\\d{11}' 拆开读")
# ============================================================

print(
    r"""  模式：\d{11}

    r"..."  原始字符串（raw string）：里面的反斜杠**不当转义符**，
            原样交给正则引擎。写正则一律加这个 r，不然 \d 会被 Python
            先当成普通转义处理，很容易踩坑。

    \d      「一个数字字符」（d = digit）

    {11}    量词：前面那个东西**重复 11 次**

  连起来就是「11 个数字字符，从第一个到最后一个」。"""
)


# ============================================================
section("3. 实测：什么样的字符串能过")
# ============================================================

CASES = [
    ("13800138000", "标准 11 位"),
    ("138-0013-8000", "带横线"),
    ("1380013800", "只有 10 位"),
    ("138001380001", "有 12 位"),
    ("", "空串"),
    ("1380013800a", "最后一位是字母"),
    (" 13800138000", "前面多个空格"),
]

for value, label in CASES:
    result = re.fullmatch(r"\d{11}", value)
    verdict = "通过" if result else "拦下"
    print(f"  {label:<14} {value!r:<20} -> {verdict}")
    print(f"                 返回值：{result!r}")


# ============================================================
section("4. 三个兄弟：search / match / fullmatch")
# ============================================================

TEXT = "我的电话是13800138000哦"

print(f"  拿这串来试：{TEXT!r}\n")
print(f"  re.search(r'\\d{{11}}', ...)   -> {re.search(r'\d{11}', TEXT)}")
print(f"  re.match(r'\\d{{11}}', ...)    -> {re.match(r'\d{11}', TEXT)}")
print(f"  re.fullmatch(r'\\d{{11}}', ...) -> {re.fullmatch(r'\d{11}', TEXT)}")

print(
    """\n  · search：整串里**任意位置**找得到就算命中（上面这串能找到，因为中间有 11 位数字）
  · match：只要求**开头**对得上（这串开头是「我」，所以没命中）
  · fullmatch：**整串**必须正好是这 11 位，多一个字符都不行

  校验用户输入时你要的几乎总是 fullmatch——search 会把
  「我的电话是13800138000哦」这种整句当成合法电话号码放过去。"""
)


# ============================================================
section("5. 坑：\\d 说的「数字」比你想的多")
# ============================================================

WEIRD = [
    ("１３８００１３８０００", "全角数字（中文输入法下打出来的）"),
    ("١٣٨٠٠١٣٨٠٠٠", "阿拉伯-印度数字"),
]

for value, label in WEIRD:
    result = re.fullmatch(r"\d{11}", value)
    print(f"  {label}")
    print(f"    {value!r}")
    print(
        f"    re.fullmatch(r'\\d{{11}}', ...) -> {'通过（！）' if result else '拦下'}"
    )
    # isdigit()：字符串里每个字符都是数字时返回 True，否则 False。
    # 注意「数字」是按 Unicode 算的——全角数字也算，所以它和 \d 一样会被绕过
    print(f"    .isdigit() 怎么说：{value.isdigit()}")
    print(f"    字符编码里它算数字吗：{value[0].isdigit()}\n")

print(
    """  Python 3 里 \\d 默认匹配的是 Unicode 意义上的数字，不止 0-9。
  所以「11 位数字」这条规矩，用 \\d 写会被全角数字绕过；
  用 .isdigit() 写呢？上面两行说明它**有一模一样的问题**。

  想真的只认 ASCII 的 0-9，两种写法：
     re.fullmatch(r"[0-9]{11}", value)              # 直接把字符集写死
     re.fullmatch(r"\\d{11}", value, re.ASCII)        # 或者加这个开关
  也可以先挡一道：value.isascii() and value.isdigit() and len(value) == 11

  这类「看起来是数字、其实不是 0-9」的输入，在真实项目里就是脏数据，
  校验那一关不挡住，它就会一路混进数据库。"""
)


# ============================================================
section("6. 回到你的练习：两种写法怎么选")
# ============================================================

print(
    """  练习里我给的最简写法：
      value.isdigit() and len(value) == 11
    好处：不用导 re，一眼看懂。
    代价：全角数字能绕过（跟 \\d 一样）。

  演示脚本里用的是：
      re.fullmatch(r"\\d{11}", value)
    好处：一个表达式说清「从头到尾」的规矩，以后要加规则（比如允许 +86 开头）
          改的是模式，不用改 if 的结构。

  两种都能跑，你的交付物照最简写法来就行；差别写进「现象与原因」里更值钱：
  **校验规则写得松，脏数据就进来了；写得紧，正常数据可能被误伤**——这是取舍。"""
)


# ============================================================
section("7. 那么：isdigit + len 和 fullmatch 到底一样吗")
# ============================================================


def by_isdigit(value: str) -> bool:
    """写法一：先问「是不是全是数字」，再问「长度是不是 11」。"""
    return value.isdigit() and len(value) == 11


def by_fullmatch(value: str) -> bool:
    """写法二：用一个模式同时说清「几个」和「什么字符」。"""
    return re.fullmatch(r"\d{11}", value) is not None


COMPARE = [
    ("13800138000", "ASCII 11 位"),
    ("138-0013-8000", "带横线"),
    ("1380013800", "只有 10 位"),
    ("１３８００１３８０００", "全角 11 位"),
    ("١٣٨٠٠١٣٨٠٠٠", "阿拉伯-印度 11 位"),
    ("१२३४५६७८९०१", "天城文 11 位"),
    ("²²²²²²²²²²²", "上标 2 连写 11 个"),
]

print(f"  {'样例':<18}{'isdigit+len':<14}{'fullmatch':<12}两边")
for value, label in COMPARE:
    first, second = by_isdigit(value), by_fullmatch(value)
    verdict = "一致" if first == second else "❌ 不一致"
    print(f"  {label:<18}{first!s:<14}{second!s:<12}{verdict}")

print(
    r"""
  绝大多数情况一致——都是「11 个十进制数字」就过，其余都拦。
  分歧出现在最后一行，上标 2。下面三行是现跑的证据："""
)

print(f"    '²'.isdigit()              -> {('²').isdigit()}")
print(f"    re.fullmatch(r'\\d', '²')   -> {re.fullmatch(r'\d', '²')}")
try:
    int("²")
except ValueError as error:
    print(f"    int('²')                   -> ValueError: {error}")

print(
    r"""
  所以严格说：isdigit 的「数字」是个更大的集合（十进制数字 + 上标/下标这类），
  \d 的「数字」只包含十进制数字。要判断「能不能当整数用」，isdigit 都不够格——
  真正靠谱的是 try: int(value)。

  另外两处小差别：
    · fullmatch 返回的是 Match 对象（真值），不是 True/False；写 if 里没差别，
      但要记进变量、再拿去做别的判断时，写法一更干净。
    · 传进来的如果不是字符串（比如模型给了数字 18600001111），
      写法一抛 AttributeError，写法二抛 TypeError——都不是你以为的「校验失败」，
      所以在这些写法之前，先让 Pydantic 把类型管住。
  后一条也现跑一遍（故意传个不是字符串的东西进去）："""
)

number = 18600001111
try:
    by_isdigit(number)  # type: ignore[arg-type]
except AttributeError as error:
    print(f"    isdigit 写法   -> AttributeError: {error}")
try:
    by_fullmatch(number)  # type: ignore[arg-type]
except TypeError as error:
    print(f"    fullmatch 写法 -> TypeError: {error}")

print(
    r"""
  结论：对「手机号必须是 11 位 ASCII 数字」这个需求，两种写法效果一样；
  但别把「isdigit 就是数字」当成普遍真理，它和正则的 \d 不是同一套标准。"""
)
