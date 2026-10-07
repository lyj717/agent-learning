"""Day 16 材料：Pydantic 校验与失败重试——把「模型说它是 JSON」变成「程序敢用」。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**：脏数据是写死的，报错是真跑出来的。
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_demo.py

加 --live 真跑一轮「校验失败 → 把错误回填 → 模型改对」（需要网络，2 次调用）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_demo.py --live
"""

import json
import re
import sys
from pathlib import Path

from llm_client import chat_json, make_client
from pydantic import BaseModel, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 今天还是抽昨天那四个字段，但这次给每个字段配上「什么算合格」。
TEXT = "我叫刘小明，电话 13800138000，在杭州做后端，2021 年入职。"


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 先说清楚：昨天只答了半个问题")
# ============================================================

say(
    "昨天那个 parse_or_none 只回答一个问题：**这段文本能不能变成 dict**。",
    "  「能」就返回 dict，「不能」就 None。就这一条判断。",
    "",
    "今天要回答的是第二个问题：**dict 里的值，合不合我的规矩**。",
    "  规矩包括：缺失的字段是 None 还是空串？电话是不是 11 位数字？",
    "  该是字符串的地方有没有塞进来一个数字？",
    "",
    "Pydantic 的用法你 Week 00 Day 4 学过——BaseModel + 类型注解，",
    "校验就自动有了。今天的新东西只有两件：",
    "  ① 把「规矩」写得比类型更细（空串归一、格式校验）；",
    "  ② 校验失败之后**不扔掉错误**，而是把错误回填给模型再问一次。",
)


# ============================================================
section("2. 为什么需要它：昨天真跑出来的两个现场")
# ============================================================

say(
    "  现场一（抖动）：第 9 条气象台文本，同一条、同一份提示词，跑 4 次——",
    '    3 次给 `{"name": null}`，1 次给 `{"name": ""}`。',
    "    昨天的判定是 `is not None`，两种写法都算「解析成功」，",
    "    于是成功率照样 100%，但其中一次的值其实是废的。",
    "",
    '  现场二（形状对、内容错）：第 8 条孙悟空那句，模型给了 `"job": "大王"`。',
    "    它是字符串、格式完全合法，昨天的判定一点问题都挑不出来。",
    "",
    "  结论：只判「有没有拿到 dict」太粗。要有第二道关，而且这道关得能说出",
    "  **具体哪里不对**——因为那句「哪里不对」正好可以喂回给模型，让它自己改。",
)


# ============================================================
section("3. 代码 A：把规矩写成一个类")
# ============================================================


class PersonExtract(BaseModel):
    """从一段文本里抽出来的一个人。四个字段都允许缺失，缺失就记 None。"""

    # Field(description=...) 不只是注释：它会进 JSON Schema，
    # 而那份 schema 就是将来交给模型看的「字段说明」
    name: str | None = Field(
        default=None, description="姓名，字符串；原文没有就填 null"
    )
    phone: str | None = Field(
        default=None, description="11 位手机号；原文没有就填 null"
    )
    city: str | None = Field(
        default=None, description="城市，字符串；原文没有就填 null"
    )
    job: str | None = Field(default=None, description="岗位，字符串；原文没有就填 null")

    @field_validator("name", "phone", "city", "job", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        """把空串、纯空白、"未知" 这类占位符统一成 None。
        field_validator 是 Pydantic 的钩子：在「校验某个字段」时插一段自己的代码。
        mode="before" 表示**在类型校验之前**执行——这一步必须抢在前面，
        因为 "" 本身是合法字符串，等到类型校验那一关它已经被当成正常值收下了。
        """
        if isinstance(value, str):
            text = value.strip()
            if text in {"", "未知", "null", "N/A", "无"}:
                return None
            return text
        return value

    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        """电话要么是 None，要么是 11 位数字——其他一律报错。
        这里用 mode="after"（默认值）：等类型校验确定它是字符串之后再查格式。
        抛 ValueError 里的那句话，会原样出现在报错信息里，也会被我们回填给模型。
        """
        # re.fullmatch(模式, 字符串)：整个字符串是不是**正好**符合这个模式，
        # 符合返回 Match 对象、不符合返回 None；\d 是一个数字字符，{11} 是重复 11 次。
        # 「整个」三个字是关键，和 re.search / re.match 的区别见 day16_regex_demo.py
        if value is not None and not re.fullmatch(r"\d{11}", value):
            raise ValueError(f"手机号必须是 11 位数字，收到 {value!r}")
        return value


print("这份类的结构（也是将来交给模型的字段说明）：")
print(json.dumps(PersonExtract.model_json_schema(), ensure_ascii=False, indent=2))

say(
    "",
    "  顺带一个坑：类的 docstring 会变成 schema 里的 description（上面第一行就是），",
    "  也就是说它会**跟着 schema 一起被交给模型**。所以别把草稿、TODO、",
    "  或者「这题还没写完」写进 docstring——模型会看到的。",
)


# ============================================================
section("4. 代码 B：四种脏数据，看它们分别卡在哪")
# ============================================================

DIRTY_CASES = [
    ("空串当缺失", '{"name": "", "phone": null, "city": "北京", "job": null}'),
    (
        "电话带了横线",
        '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}',
    ),
    (
        "电话是数字",
        '{"name": "张伟", "phone": 18600001111, "city": "北京", "job": "数据分析师"}',
    ),
    ("JSON 本身坏了", '{"name": "李娜", "phone": "13711112222"'),
]

for label, raw in DIRTY_CASES:
    print(f"\n── {label} ──")
    print(f"  原始文本：{raw}")
    try:
        person = PersonExtract.model_validate_json(raw)
        print(f"  校验通过：{person.model_dump()}")
    except ValidationError as error:
        # error.errors() 是这题的原料：一个 list，每个元素是 dict，
        # 形如 {'type': 'value_error', 'loc': ('phone',), 'msg': 'Value error, ...',
        #       'input': '138-0013-8000', 'url': 'https://errors.pydantic.dev/...'}
        print(f"  原始报错结构：{error.errors()}")
        print("  校验失败：")
        for item in error.errors():
            where = ".".join(str(part) for part in item["loc"]) or "整体"
            print(f"    位置 {where}｜{item['msg']}｜收到的值 {item['input']!r}")

say(
    "",
    "  逐条看：",
    '   · 「空串当缺失」——通过，而且 name 从 "" 变成了 None。这就是 blank_to_none 干的活；',
    "     没有它，你就会拿到一个空字符串当姓名，昨天那个坑原样还在。",
    "   · 「电话带了横线」——卡在 phone_must_be_11_digits，报的是我们自己写的那句话。",
    "   · 「电话是数字」——卡在类型：Pydantic v2 不把数字当字符串用（Week 00 见过这条边界）。",
    "   · 「JSON 本身坏了」——也是 ValidationError，但 type 是 json_invalid；",
    '     想区分「语法坏」和「值不对」，就看 error.errors()[0]["type"]。',
)


# ============================================================
section("5. 代码 C：把错误回填给模型，重试一次")
# ============================================================


def errors_to_hint(error: ValidationError) -> str:
    """把 Pydantic 的报错整理成一句**给模型看**的话。

    为什么不直接把 str(error) 丢过去：那是给程序员看的排版（带方括号、
    带 input_type），模型能读懂但容易跑偏。挑出「哪个字段、什么问题、
    收到什么值」三件事，写成中文短句，模型改起来最省事。
    """
    lines = []
    for item in error.errors():
        where = ".".join(str(part) for part in item["loc"]) or "整体"
        lines.append(f"- 字段 {where}：{item['msg']}（收到的值：{item['input']!r}）")
    return "\n".join(lines)


print("校验失败时，回填给模型的那段话长这样：")
bad = '{"name": "王芳", "phone": "138-0013-8000", "city": "上海", "job": "销售"}'
try:
    PersonExtract.model_validate_json(bad)
except ValidationError as error:
    print(errors_to_hint(error))

print(
    "\n  这行里最容易被卡住的是把 loc 拼成字段路径那一句。逐段拆开看：\n"
    "\n"
    '      ".".join(str(part) for part in item["loc"]) or "整体"\n'
    "\n"
    '    for part in item["loc"]   part 只是个临时变量名，自己起的——每次循环\n'
    "                              从 loc 里取出一个元素交给它，叫 p、piece 都行\n"
    "    str(part)                 把它转成字符串（为什么必须转，见下面实测）\n"
    '    ".".join(...)             用点把它们串起来，得到 arguments.top_k 这种路径\n'
    '    or "整体"                  loc 是空元组时 join 出来是空字符串（假值），兜成「整体」'
)

print("\n  实测四种 loc：")
for loc in [("phone",), ("arguments", "top_k"), ("items", 0, "name"), ()]:
    pieces = ".".join(str(part) for part in loc)
    print(f"    {loc!r:<28} -> {pieces!r:<22} -> {pieces or '整体'!r}")

print("\n  要是偷懒不写 str(part) 会怎样（拿带下标的 loc 试）：")
try:
    ".".join(part for part in ("items", 0, "name"))
except TypeError as error:
    print(f"    TypeError: {error}")
print(
    "  因为 loc 里的元素不全是字符串——嵌套结构里会带下标（整数）。\n"
    "  join 只收字符串，所以每个元素都得先 str() 一下。"
)

print(
    "\n  上面只有一条错。可是 error.errors() 是个**列表**——一次出现好几条错时，"
    "\n  拼成一段文字的必要性就看得出来了："
)

# 这条数据一次踩两个坑：phone 不是 11 位数字，city 给的是数字不是字符串。
multi_bad = '{"name": "王芳", "phone": "138-0013-8000", "city": 123, "job": null}'
try:
    PersonExtract.model_validate_json(multi_bad)
except ValidationError as error:
    print(f"\n    原始列表里有 {len(error.errors())} 条错：")
    for item in error.errors():
        where = ".".join(str(part) for part in item["loc"]) or "整体"
        print(f"      type={item['type']}｜loc={item['loc']}｜{where}｜{item['msg']}")
    print("\n    拼成一段话之后（这才是要发给模型的东西）：")
    print(errors_to_hint(error))
    print("\n    对比一下 str(error) 长什么样（Pydantic 的原始排版，给程序员看的）：")
    print("     " + str(error).replace("\n", "\n     "))

say(
    "",
    "  完整的重试回合（这才是今天真正的新东西）：",
    "",
    "    ① 发请求，拿到原始文本",
    "    ② 校验：过了 → 结束",
    "    ③ 没过 → 把原始文本按 assistant 的口气塞回对话，再追加一条 user：",
    "       「你刚才的输出没通过校验，问题是……，请只输出修正后的 JSON」",
    "    ④ 用**同一串对话**再发一次（不是新开一轮对话）",
    "    ⑤ 再校验一次；还不过就放弃，返回 None（今天只重试 1 次）",
    "",
    "  为什么要把原始文本也塞回去：模型是无状态的，你不告诉它「刚才说了什么」，",
    "  它不知道要改哪一份输出。",
)


# ============================================================
section("6. 要注意什么：五个坑")
# ============================================================

say(
    "  坑一：校验通过 ≠ 抽得对。",
    '    `{"job": "大王"}` 在 PersonExtract 眼里完全合法（字符串嘛）。',
    "    Pydantic 管的是形状、类型、格式；「这个值忠不忠实于原文」它管不了。",
    "    要管忠实度得换判据（对照原文、写评测集），那是 Week 08 的事。",
    "    今天别把「校验通过」当成「抽对了」——这句话面试时很值钱。",
    "",
    "  坑二：别把错误吞掉。",
    "    写 `except ValidationError: return None` 就等于退回昨天，",
    "    而且把手里唯一能拿来纠错的材料（那句话哪里不对）扔了。",
    "",
    "  坑三：重试必须有上限。",
    "    今天重试 1 次。不设上限的话，模型要是每次都栽在同一个字段上，",
    "    你就得到一台自动烧钱的机器（Day 19 会专门做「最多 N 次」）。",
    "",
    "  坑四：重试不是「再问一遍」。",
    "    不带错误信息重发，等于把同样的问题再掷一次骰子，纯浪费。",
    "    要带上「哪里不对」，模型才有新信息可用。",
    "",
    "  坑五：finish_reason 是 length 时别重试解析。",
    "    那不是 JSON 写错，是额度不够、内容被截断（Day 15 的坑二）。",
    "    这时该加 max_tokens 重新请求，而不是拿着半截文本去校验。",
)


# ============================================================
section("7. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 写练习：weeks/week02_tools/day16_pydantic_exercises.py",
    "     三题：把规矩写成模型 → 把报错变成给模型看的话 → 带重试地抽一次",
    "",
    "  2. 故意喂脏数据，看程序会不会崩：",
    "     .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py",
    "     .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_pydantic_exercises.py --live",
    "",
    "  3. 填交付物：weeks/week02_tools/day16_脏数据处理记录.md",
)


if LIVE:
    section("--live：真跑一轮「校验失败 → 回填 → 改对」")

    client = make_client()
    messages = [
        {
            "role": "system",
            "content": "你是信息抽取助手，只输出 JSON。字段：name、phone、city、job，"
            "缺失的字段填 null，phone 是 11 位手机号。",
        },
        {"role": "user", "content": f"从下面这段话里抽取字段：\n{TEXT}"},
    ]

    text, finish_reason = chat_json(messages, client=client)
    print("① 第一次请求：")
    print(f"    finish_reason = {finish_reason}")
    print(f"    原始文本 = {text!r}")

    # 为了演示**必定会**走到失败分支，这里把第一次的返回人为改坏：
    # 把 phone 换成带横线的写法（138-0013-8000）。
    # 注意别换成「未知」——那是 blank_to_none 会吃掉的值，
    # 换上去校验反而通过了，这条坑我自己先踩了一次。
    # 真实的脏数据是模型自己给的，但那条路不一定每次都踩中，
    # 教学演示要的是确定性。
    if '"phone"' in text:
        # re.sub(模式, 替换成什么, 原字符串)：把命中的部分**全部替换**，返回新字符串。
        # 这里只是演示用的道具——把真实的号码换成一段带横线的假号码，
        # 好让下面必定走到「校验失败」那一支。
        dirty = re.sub(r'"phone"\s*:\s*"[^"]*"', '"phone": "138-0013-8000"', text)
    else:
        dirty = text
    print(f"    人为改坏后的文本 = {dirty!r}")

    try:
        PersonExtract.model_validate_json(dirty)
        print("    （居然通过了？把这条现象记下来）")
    except ValidationError as error:
        hint = errors_to_hint(error)
        print("② 校验失败，准备回填：")
        print(f"    {hint}")

        retry_messages = [
            *messages,
            {"role": "assistant", "content": dirty},
            {
                "role": "user",
                "content": f"你刚才的输出没通过校验：\n{hint}\n"
                "请只输出修正后的 JSON，缺失的字段填 null。",
            },
        ]
        text2, finish_reason2 = chat_json(retry_messages, client=client)
        print("③ 带着错误再问一次：")
        print(f"    finish_reason = {finish_reason2}")
        print(f"    原始文本 = {text2!r}")
        try:
            fixed = PersonExtract.model_validate_json(text2)
            print("④ 这次校验通过：")
            print(f"    {fixed.model_dump()}")
        except ValidationError as error2:
            print("④ 还是没过——那就认输返回 None（今天只重试一次）：")
            print(f"    {errors_to_hint(error2)}")
