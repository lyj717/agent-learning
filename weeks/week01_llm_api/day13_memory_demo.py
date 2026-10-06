"""Day 13 材料一：简易长期记忆——「记忆」到底存在哪。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网**：用假数据和假回答把「存事实 → 重启 → 喂回去」演一遍。
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day13_memory_demo.py

加上 --live，真的对比一次「带记忆」和「不带记忆」（需要网络）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day13_memory_demo.py --live
"""

import json
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

# 往上两层是仓库根目录（这个文件在 weeks/week01_llm_api/ 里）
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv

# 演示用的临时文件：放系统临时目录里，跑完就删。
# （别写进仓库里的 .pytest_tmp —— 那是 pytest 自己建的目录，
#   权限归它，你写会 [WinError 5] / PermissionError）
DEMO_FACTS = Path(tempfile.gettempdir()) / "day13_facts_demo.json"


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 先说清楚：模型没有记忆，一点都没有")
# ============================================================

say(
    "  每次请求，模型看到的只有你这一次发过去的 messages——前面聊过什么，",
    "  它一个字都不知道（Day 10 讲过：历史是你自己攒的，每次整段发过去）。",
    "",
    "  所以「长期记忆」这件事，翻译成人话就是：",
    "",
    "    **把要记住的东西存在外面，每次请求再想办法喂给它。**",
    "",
    "  存的媒介不同，就分出了三档：",
    "",
    "    ① 上下文窗口（messages 里带着）   —— 短期记忆，一关就没了，还越带越贵",
    "    ② 本地文件（JSON / SQLite）      —— 简易长期记忆，今天做这个",
    "    ③ 向量库 + 检索                  —— 真正的长期记忆，Week 05 的 RAG",
    "",
    "  三档的区别只在「存哪」和「怎么找回来」，共同点是一样的：**每次都要重新喂**。",
)


# ============================================================
section("2. 场景：今天告诉它的名字，明天它还该记得")
# ============================================================

say(
    "  昨天那个机器人：你告诉它「我叫刘小明」，聊完关掉程序——",
    "  今天再打开，它不认识了，因为它没有任何东西可以「记」。",
    "",
    "  更麻烦的是：就算你不关程序，只要打了 /clear，历史清空，名字也没了",
    "  （/clear 清的正是它唯一记得事的地方）。",
    "",
    "  所以要做两件事：",
    "    · 用户说「记住这个」时，把这条事实**写到磁盘上**；",
    "    · 每次启动（以及每次请求），把磁盘上的事实**拼进 system 提示词**。",
    "",
    "  为什么拼进 system 而不是拼进历史？因为 system 是「设定」，不会参与裁剪",
    "  （Day 12 的 trim 只动历史），/clear 也清不掉它——它每次都重新喂。",
)


# ============================================================
section("3. 存什么、怎么存：一个小 JSON 就够")
# ============================================================

say(
    "  最省事的格式就是一个字符串列表，存成 JSON：",
    "",
    '    ["我叫刘小明", "我在学 Agent 开发", "我住在杭州"]',
    "",
    "  为什么是「一条条事实」而不是「把聊天记录存下来」：",
    "    · 聊天记录会越来越长，最后还是会撞上上下文窗口和钱包（Day 9 算过）；",
    "    · 事实是压缩过的信息——一段对话最后能沉淀出两三句话，那才值得长期带着。",
    "",
    "  这也正是 Week 05 RAG 的雏形：**把外面的知识找回来、拼进提示词**。",
    "  区别只是今天用「读一个 JSON」，那时候用「向量检索」。",
)


# ============================================================
section("4. 离线演一遍：存 → 重启 → 读回来 → 拼进 system")
# ============================================================

say("  ① 用户说「记住我叫刘小明」，我们把它存进文件：")

DEMO_FACTS.parent.mkdir(parents=True, exist_ok=True)
facts = []
if DEMO_FACTS.exists():
    DEMO_FACTS.unlink()

for fact in ["我叫刘小明", "我在学 Agent 开发"]:
    facts.append(fact)
    # json.dumps(对象, ensure_ascii=False)：把 Python 对象转成 JSON 字符串，
    # ensure_ascii=False 是让中文原样写出来，而不是变成 \u5218 这种转义
    DEMO_FACTS.write_text(
        json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    say(f"     + {fact}")

say(
    "",
    f"   文件内容（{DEMO_FACTS.name}）：",
    DEMO_FACTS.read_text(encoding="utf-8").strip(),
)

say("", "  ② 「重启程序」——刚才那个列表已经没了，只能从文件读回来：")
facts = json.loads(DEMO_FACTS.read_text(encoding="utf-8"))
say(f"    读回来：{facts}")

say("", "  ③ 拼进 system 提示词（这才是「记忆」真正起作用的地方）：")

BASE_SYSTEM = "你是一个只说一句话的助手。"
system_text = (
    BASE_SYSTEM
    + "\n你记得关于用户的这些事实：\n"
    + "\n".join(f"- {fact}" for fact in facts)
)
say("")
for line in system_text.splitlines():
    say(f"    {line}")

say(
    "",
    "  ④ 下一次请求发出去的 messages 就长这样（注意第一条已经被撑大了）：",
    "",
)
for message in [
    {"role": "system", "content": system_text},
    {"role": "user", "content": "我叫什么？"},
]:
    role, content = message["role"], message["content"].replace("\n", " / ")
    say(f"    {role:<9} {content}")

say(
    "",
    "  关键是最后这一步：**记忆不写在历史里，而是每次从文件读出来、拼进 system**。",
    "  所以 /clear 清掉历史之后，它照样记得你叫什么——因为名字压根不在历史里。",
)

DEMO_FACTS.unlink(missing_ok=True)


# ============================================================
section("5. 要注意什么")
# ============================================================

say(
    "  · **隐私**：事实存在本地文件里，就是明文。别让用户往里写密码、身份证号；",
    "    这个文件也要加进 .gitignore，绝不能跟着代码提交上去。",
    "  · **文件会坏**：手工编辑过、写到一半断电，JSON 就可能解析失败。",
    "    读的时候要兜住（读不动就当成「还没有记忆」，或者备份后重建），别让程序崩。",
    "  · **记忆不能无限塞**：每一条事实都会进每一次请求的 system，事实越多越贵、",
    "    越容易把上下文挤爆。真要长期用，得配合「只取相关的几条」——那就是检索。",
    "  · **别把记忆和上下文搞混**：/clear 清的是上下文（历史），清不掉文件里的记忆；",
    "    想让记忆也忘掉，得给它一个「忘掉某条」的操作，或者手工删文件。",
    "  · **写进去的是事实，不是指令**：如果事实里夹着「忽略上面所有要求」这种话，",
    "    它会跟着 system 一起生效——这是提示词注入的一个入口（Week 07 会讲防御）。",
)


# ============================================================
section("6. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 写 chat_cli/memory.py：load_facts / add_fact / compose_system 三个函数",
    "     （骨架和「要做的」都写好了）",
    "",
    "  2. conversation.py 加一个 set_system()：换人设用",
    "     （/remember 之后要让新事实马上生效，不能等重启）",
    "",
    "  3. chat_cli.py 里接三处（TODO(Day 13) 都标好了）：",
    "     · 启动时：读事实 → 拼 system → 建 Conversation",
    "     · 新命令 /remember <一句话>",
    "     · 提示语里把 /remember 加进去",
    "",
    "  4. 验收：tests/test_memory.py（我写好了），另外自己手测一次——",
    "     /remember 我叫刘小明 → /clear → 问「我叫什么」，它应该还答得出来。",
)


if LIVE:
    from openai import OpenAI, OpenAIError

    section("--live：真跑一次，看「带记忆」和「不带记忆」的差别")
    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )

    def ask(messages: list[dict[str, str]]) -> str:
        response = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=512,
        )
        return (response.choices[0].message.content or "").strip()

    with_memory = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": "我叫什么？"},
    ]
    without_memory = [
        {"role": "system", "content": BASE_SYSTEM},
        {"role": "user", "content": "我叫什么？"},
    ]
    try:
        say(
            "  问「我叫什么？」，system 里带上记忆：",
            f"    {ask(with_memory)}",
            "",
            "  同一个问题，system 里不带记忆（历史也是空的）：",
            f"    {ask(without_memory)}",
            "",
            "  差别只在 system 里那几行——不是模型记住了，是我们喂给它了。",
        )
    except OpenAIError as error:
        # 只捕 SDK 自己的异常类型
        say(f"  调用失败：{type(error).__name__}: {error}")
