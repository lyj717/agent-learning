"""Day 10 材料一：多轮对话——「记忆」到底在谁手里。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**：把每一轮「到底发出去什么」原样打印给你看。
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day10_messages_demo.py

加上 --live，真的聊两轮，验证「不带历史就接不上话」（需要网络）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day10_messages_demo.py --live
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 往上两层是仓库根目录（这个文件在 weeks/week01_llm_api/ 里）
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

SYSTEM = "你是一个只说一句话的天气助手。"


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：中文 0.6/字、英文 0.3/字符（官方换算比例）。
    只是估算——准数永远看响应里的 usage，Day 9 学过。
    """
    chinese = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    others = len(text) - chinese
    return round(chinese * 0.6 + others * 0.3)


def count_tokens(messages: list[dict[str, str]]) -> int:
    """把一整串 messages 的 token 估出来。"""
    return sum(estimate_tokens(m["content"]) for m in messages)


# ============================================================
section("1. 先说清楚：模型本身没有记忆")
# ============================================================

say(
    "这是什么：调用模型的那个接口是**无状态**的——你把 messages 发过去，",
    "           它回答完就把这次请求忘了。第二次调用它不记得第一次说过什么。",
    "",
    "为什么容易误会：你在网页里聊天，它好像记得你上一句说了什么。",
    "  那不是模型记住了，是**网页把历史替你攒着**，每次都重新发一遍。",
    "",
    "  所以「多轮对话」这件事，说穿了就是两句话：",
    "    ① 你在本地维护一个 messages 列表；",
    "    ② 每次请求，把整个列表原样发过去。",
    "  模型没有变聪明，是你每次都把前情提要又念了一遍。",
)


# ============================================================
section("2. 场景：连续追问 5 轮，每一轮到底发了什么")
# ============================================================

say(
    "  下面不联网。用一个列表当「历史」，模拟 5 轮问答，",
    "  把每一轮**真正发出去的东西**和估算的 token 打出来。",
    "",
)

history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM}]
sizes: list[int] = []
script = [
    ("杭州今天多少度？", "22 度，多云。"),
    ("那明天呢？", "明天 25 度，晴。"),
    ("要带伞吗？", "不用，明天不下雨。"),
    ("后天呢？", "后天 20 度，有阵雨，建议带伞。"),
    ("这一周哪天最热？", "明天最热，25 度。"),
]

for round_no, (question, answer) in enumerate(script, start=1):
    payload = history + [{"role": "user", "content": question}]
    sizes.append(len(payload))
    say(
        f"  ── 第 {round_no} 轮 ──",
        f"  发出去 {len(payload)} 条消息，估算 {count_tokens(payload)} 个 token",
    )
    for message in payload:
        say(f"     {message['role']:<9} {message['content']}")
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    say("")

say(
    f"  看出来了吗：第 1 轮只发了 {sizes[0]} 条消息，"
    f"第 {len(script)} 轮发了 {sizes[-1]} 条——",
    "  但每一轮**新增**的内容，其实只有一问一答。",
    "  多出来的全是把前面几轮又发了一遍。这就是 Day 9 算过的「输入滚雪球」。",
    "",
    f"  5 轮下来，历史里一共攒了 {len(history)} 条消息。",
    "  这就是 /clear 要清掉的东西。",
)


# ============================================================
section("3. /clear 清的是什么")
# ============================================================

say(
    "  /clear 不是「让模型忘掉」——模型本来就不记得。",
    "  它清的是**你手里的那个列表**，也就是下一轮不再把旧内容发过去。",
    "",
)

cleared = [m for m in history if m["role"] == "system"]
say(
    f"  clear 之前：{len(history)} 条消息",
    f"  clear 之后：{len(cleared)} 条 —— 只剩 system 人设",
    "",
    "  注意这里的设计选择：**system 要留着**。人设是配置，不是对话内容；",
    "  把 system 也清掉，机器人下一句就会变回默认人格。",
    "",
    "  顺带一提：清空历史还能省钱——下一轮的输入 token 直接从最大掉回最小。",
)


# ============================================================
section("4. 三个坑，全在「忘了往历史里放东西」")
# ============================================================

say(
    "  坑一：只把用户的话加进去，忘了把模型的回答加进去。",
    "    下一轮你问「那明天呢」——历史里有你上一句、没有它上一句，",
    "    模型只能猜，「那」指的是什么。这就是串味。",
    "",
    "  坑二：一次都不加，每轮都当新对话。",
    "    表现是「失忆」：你刚说过的名字，它下一句就忘。",
    "",
    "  坑三：加进去了但顺序错了。",
    "    必须严格按时间：user、assistant、user、assistant……",
    "    顺序一乱，模型会把你和它说的话搞混。",
    "",
    "  写代码时的口诀：**问一句、答一句，两个都要往列表里放**，顺序不能反。",
)


# ============================================================
section("5. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 你的任务：把上面这套「攒历史」的逻辑，写成一个类：",
    "     weeks/week01_llm_api/chat_cli/conversation.py",
    "     （骨架和「要做的」都写好了，照着填）",
    "",
    "  2. 然后写命令行那一层：",
    "     weeks/week01_llm_api/chat_cli/chat_cli.py",
    "     读一行 → 是命令就处理 /clear、/cost、/exit → 不是命令就发给模型",
    "",
    "  3. 自测：",
    "     cd weeks\\week01_llm_api\\chat_cli",
    "     ..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -v",
    "     测试是我写好的，红了就说明还没写对。",
)


if LIVE:
    from openai import OpenAI, OpenAIError

    section("--live：真聊两轮，看看「带历史」和「不带历史」的区别")
    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    def ask(messages: list[dict[str, str]]) -> str:
        # chat.completions.create(...)：发一次请求，等它说完再返回
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=512,
        )
        return (response.choices[0].message.content or "").strip()

    try:
        first = "记住：我叫刘小明。只回复两个字：好的"
        round_one = [{"role": "user", "content": first}]
        say("  第 1 轮（问）：", f"    {first}")
        say("  第 1 轮（答）：", f"    {ask(round_one)}")

        with_history = round_one + [
            {"role": "assistant", "content": "好的"},
            {"role": "user", "content": "我叫什么？"},
        ]
        without_history = [{"role": "user", "content": "我叫什么？"}]
        print()
        say(
            "  第 2 轮，带着历史问「我叫什么？」：",
            f"    {ask(with_history)}",
            "",
            "  第 2 轮，不带历史问同一句：",
            f"    {ask(without_history)}",
            "",
            "  带历史那个能答出「刘小明」，不带历史的答不出——差别就只在那个列表。",
        )
    except OpenAIError as error:
        # 只捕 SDK 自己的异常类型
        say(f"  调用失败：{type(error).__name__}: {error}")
