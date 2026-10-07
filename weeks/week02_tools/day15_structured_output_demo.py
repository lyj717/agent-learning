"""Day 15 材料：结构化输出——让模型交字段，而不是交作文。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**：把要发出去的请求、以及真跑出来的返回原样摆给你看
（里面的数据是 2026-10-07 用 .env 里那个模型真实抓下来的）。
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day15_structured_output_demo.py

加 --live 自己真跑 3 次，亲眼看差别（需要网络，一次几分钱）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day15_structured_output_demo.py --live
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 今天拿来抽的那段「杂乱文本」。真人写的简历、聊天记录就长这样：
# 有用的信息混在废话里，顺序还不固定。
TEXT = "我叫刘小明，电话 13800138000，在杭州做后端，2021 年入职。"

# 你想从文本里拿到的东西。四个字段，名字和类型都定死——
# 这就是「结构化」三个字的来源：先定形状，再往里填。
SCHEMA_HINT = (
    "name（姓名，字符串）、phone（手机号，字符串）、"
    "city（城市，字符串）、job（岗位，字符串）"
)

# 真跑抓到的那段「带围栏」的返回。模型为了让输出好看，给它裹了一层说明，
# 结果程序反而读不了。
RAW_WITH_FENCE = """下面是一个描述用户基本信息的 JSON 示例，用花括号表示对象：

```json
{
  "id": 1001,
  "name": "Alice",
  "isAdmin": false
}
```

一句话解释：JSON 是一种轻量级的文本数据格式……"""


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 先说清楚：模型默认给你的是「散文」，程序要的是「字段」")
# ============================================================

say(
    "这是什么：你问模型一句话，它默认回你一段**人读着舒服的话**。",
    "  结构化输出就是反过来——要求它按一张**固定的表格**回答：",
    "  字段名有哪些、每个字段是什么类型，事先说死。",
    "",
    "两个容易混的概念，今天先分清：",
    "  · JSON 模式（response_format）——只保证「这段话是合法 JSON」，",
    "    字段叫 name 还是 xingming、少没少字段，它不管；",
    "  · schema 约束（Day 16 的 Pydantic、工具定义里的 strict）——",
    "    「字段必须叫这些、类型必须对」，强得多。",
    "",
    "为什么需要它：模型只有回字段，程序才能接着干活。",
    "  你要把 1000 份简历里的电话导进表格，靠正则和肉眼都不现实；",
    "  模型能读懂「在杭州做后端」是城市+岗位，但它顺手加的一句寒暄，",
    "  就足以让你的 json.loads 当场报错。",
)


# ============================================================
section("2. 看看不控制的后果：一段真实抓下来的返回")
# ============================================================

say(
    "  下面是这个模型**真实返回**的一段文字（提示词只说要 JSON，没开 JSON 模式）。",
    "  注意开头那句话和中间那对围栏：",
    "",
)

print(RAW_WITH_FENCE)

try:
    json.loads(RAW_WITH_FENCE)
except json.JSONDecodeError as error:
    say(
        "",
        "  拿去 json.loads 会怎样（真跑的结果）：",
        f"    JSONDecodeError: {error.msg}（line {error.lineno} column {error.colno}，"
        f"char {error.pos}）",
        "",
        "  报错位置是**第 1 个字符**——第 1 个字符是「下」，不是花括号。",
        "  内容其实是对的，只是外面裹了一层「给你的说明」。程序不认这层包装。",
    )


# ============================================================
section("3. 场景：Agent 里到处都是这个动作")
# ============================================================

say(
    "  1. 用户说「帮我查下杭州明天的天气」——你要抽的不是天气，是",
    '     {"city": "杭州", "when": "明天"} 这个工具参数（Day 17 起的正戏）。',
    '  2. 一千条工单要分类——你要的是 {"category": "退款", "urgent": true}。',
    '  3. RAG 里要标引用来源——你要的是 {"answer": "...", "cited_ids": [3, 7]}。',
    "",
    "  共同点：**下一个环节是代码，不是人**。",
    "  给代码的答案，就必须能被代码直接读。",
)


# ============================================================
section("4. 代码：两处改动")
# ============================================================

payload = {
    "model": "deepseek-flash",
    "messages": [
        {
            "role": "system",
            "content": f"你是信息抽取助手，只输出 JSON。字段：{SCHEMA_HINT}",
        },
        {
            "role": "user",
            "content": f"从下面这段话里抽取字段，输出 JSON：\n{TEXT}",
        },
    ],
    # 这一行是今天的开关：告诉服务商「我只要 JSON 对象」。
    "response_format": {"type": "json_object"},
    "max_tokens": 2048,
}

say(
    "  要发出去的请求长这样：",
    "",
    json.dumps(payload, ensure_ascii=False, indent=2),
    "",
    "  三件事要同时做到，缺一个都不成：",
    "    ① system 里写清**字段名和类型**（模型才知道你要哪几个坑）；",
    "    ② user 里给原文；",
    "    ③ response_format 打开 JSON 模式。",
    "",
    "  请求发出去之后，拿到的是**一小段文本**，不是 dict。",
    "  从文本到 dict 要过两道关：json.loads（语法对不对），",
    "  再检查字段（该有的有没有）。第二道关 Day 16 用 Pydantic 做正。",
)


# ============================================================
section("5. 实测：开 JSON 模式 + 提示词里有 json 这个词")
# ============================================================

REAL_ANSWER = '{"name":"刘小明","phone":"13800138000","city":"杭州","job":"后端"}'

say(
    "  2026-10-07 真跑的结果（原样抄下来）：",
    "",
    "    finish_reason = stop",
    f"    content = {REAL_ANSWER!r}",
    "    usage: prompt_tokens=102, completion_tokens=262（其中 reasoning_tokens=240）",
    "",
    f"  json.loads 一次就过，拿到普通 dict：{json.loads(REAL_ANSWER)}",
    "",
    "  两个数字值得多看一眼：",
    "    · completion_tokens 里的 240 是**思考**。这个模型默认带思考，",
    "      思考的 token 和正文一起算进输出账单（Day 9 算过这笔账）；",
    "    · 同一个请求我跑过两次，一次 331、一次 262——思考长短每次都不同，",
    "      所以「模型一定给我一模一样的输出」这个假设站不住（FAILURES.md 里",
    "      那条 temperature=0 也复现不了的记录，说的是同一件事）。",
)


# ============================================================
section("6. 要注意什么：三个坑，全部真实踩过")
# ============================================================

say(
    "  坑一：开了 JSON 模式，提示词里却**没有出现 json 这个词**。",
    "    不是模型不听话，是服务商直接拒收。真跑的报错原文：",
    "",
    "      BadRequestError: Error code: 400 - Prompt must contain the word 'json'",
    "      in some form to use 'response_format' of type 'json_object'.",
    "",
    "    换句话说，JSON 模式是**要来的**，不是**打开的**：你得先开口要，",
    "    它才给你。system 或 user 任意一处写上「输出 JSON」都算数。",
    "",
    "  坑二：max_tokens 给小了，额度会被思考吃光。",
    "    同一段文本、同一个提示词，只改 max_tokens（真跑）：",
    "",
    "      max_tokens=150 → finish_reason=length，content=''  ← 一个字都没有",
    "      max_tokens=200 → finish_reason=length，content=''  ← 还是空的",
    "      max_tokens=240 → finish_reason=stop，JSON 完整，长度 59",
    "",
    "    空的后果是 json.loads('') 报 JSONDecodeError: Expecting value（char 0）。",
    "    看到 char 0，先想「是不是根本没内容」，别急着怀疑 JSON 写错了。",
    "    **看到 finish_reason=length 就别解析了，加额度重来。**",
    "",
    "  坑三：不开 JSON 模式，靠提示词「求」它输出 JSON。",
    "    实测确实拿到过干净的 JSON（真跑过一次），但那是运气——",
    "    第 2 节那段带围栏的返回，就是同一个模型「自由发挥」时的作品。",
    "    别把「今天运气好」当成「接口保证」。",
    "",
    "  最后一条不算坑，是方法：**别跑一次就宣布成功。**",
    "    今天的交付物是「连续跑 10 条真实文本，统计解析成功率」——",
    "    「成功率」这三个字，就意味着分母大于 1。",
)


# ============================================================
section("7. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 写练习：weeks/week02_tools/day15_structured_output_exercises.py",
    "     三题：拼提示词 → 安全解析 → 串起来真抽一遍",
    "",
    "  2. 跑 10 条样本，统计成功率：",
    "     .venv\\Scripts\\python.exe "
    "weeks\\week02_tools\\day15_structured_output_exercises.py --live",
    "",
    "  3. 填交付物：weeks/week02_tools/day15_抽取成功率记录.md",
    "     里面是待填表格 + 引导问题，数据和结论都留给你。",
)


if LIVE:
    import os

    from dotenv import load_dotenv
    from openai import APIError, OpenAI

    section("--live：三次真实调用，亲眼确认")
    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
        # 关掉 SDK 的自带重试，Day 12 学过的坑：不然一次调用会悄悄变成好几次
        max_retries=0,
    )
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    def ask(question: str, *, json_mode: bool, max_tokens: int = 2048):
        """发一次请求，返回（finish_reason, content, usage）。"""
        fields = {
            "model": model,
            "messages": question,
            "max_tokens": max_tokens,
        }
        if json_mode:
            fields["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**fields)
        return (
            response.choices[0].finish_reason,
            response.choices[0].message.content,
            response.usage,
        )

    def show(label: str, finish_reason: str, content: str, usage) -> None:
        say(
            f"  ── {label} ──",
            f"    finish_reason = {finish_reason}",
            f"    content = {content!r}",
            f"    usage: 输入 {usage.prompt_tokens} / 输出 {usage.completion_tokens}",
        )
        try:
            parsed = json.loads(content or "")
            say(f"    json.loads 成功：{parsed}")
        except json.JSONDecodeError as error:
            say(f"    json.loads 失败：{error.msg}（char {error.pos}）")
        print()

    with_json_word = [
        {
            "role": "system",
            "content": f"你是信息抽取助手，只输出 JSON。字段：{SCHEMA_HINT}",
        },
        {"role": "user", "content": f"从下面这段话里抽取字段，输出 JSON：\n{TEXT}"},
    ]
    without_json_word = [
        {"role": "system", "content": "你是信息抽取助手。"},
        {"role": "user", "content": f"这段话里说了什么？\n{TEXT}"},
    ]

    try:
        finish, content, usage = ask(with_json_word, json_mode=True)
        show("① JSON 模式 + 提示词里有 json", finish, content, usage)

        finish, content, usage = ask(with_json_word, json_mode=True, max_tokens=150)
        show("② JSON 模式 + max_tokens=150（额度不够）", finish, content, usage)

        try:
            ask(without_json_word, json_mode=True)
            say("  ③ 提示词里没有 json 字样 —— 居然通过了？把这条报给 AGENTS 里的人。")
        except APIError as error:
            say(
                "  ── ③ JSON 模式 + 提示词里没有 json 字样 ──",
                f"    {type(error).__name__}: {error}",
                "",
                "  三次跑完，回头看第 4~6 节，三条都对上了。",
            )
    except APIError as error:
        say(f"  调用失败（检查网络和 .env）：{type(error).__name__}: {error}")
