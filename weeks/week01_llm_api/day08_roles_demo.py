"""Day 8 材料一：system / user / assistant 三种角色。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**，只讲解并演示「一串消息是怎么拼出来的」：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_roles_demo.py

加上 --live，真的发三次请求做对照（需要网络，会消耗一点点额度）：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_roles_demo.py --live

看完这个演示，再去做 day08_exercises.py 里的题。
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 这个文件在 weeks/week01_llm_api/ 里，往上两层才是仓库根目录
ROOT = Path(__file__).resolve().parents[2]
LIVE = "--live" in sys.argv


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


def build_messages(
    question: str,
    *,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """把「人设 + 历史 + 新问题」按顺序拼成一个 messages 列表。

    这是纯逻辑：不发请求、不打印。Week 01 的聊天机器人每问一次，
    干的就是这件事——把到目前为止的对话重新拼一遍发出去。
    """
    messages: list[dict[str, str]] = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    if history is not None:
        messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


# ============================================================
section("1. 一条消息长什么样：role + content")
# ============================================================

say(
    "这是什么：你和模型的整段对话，是一串「消息」拼起来的列表。",
    "           每条消息两个关键字段——谁说的（role）、说了什么（content）。",
    "",
    "  [",
    '    {"role": "system",    "content": "你是一个只说一句话的技术助教。"},',
    '    {"role": "user",      "content": "什么是流式输出？"},',
    '    {"role": "assistant", "content": "边生成边发送，让你更快看到第一批字。"},',
    '    {"role": "user",      "content": "那它省时间吗？"},',
    "  ]",
    "",
    "  role 一共三种（还有第四种 tool，等 Week 02 讲工具调用时登场）：",
    "    system     开场设定：你是谁、守什么规矩。一般只写一条，放最前面",
    "    user       用户说的话",
    "    assistant  模型之前说过的话",
)


# ============================================================
section("2. 为什么非要分角色")
# ============================================================

say(
    "为什么需要它：模型看到的只是一串文本，它分不清哪句是自己说的、哪句是你说的。",
    "  role 就是贴在每句话上的「说话人标签」，模型靠它判断上下文。",
    "",
    "  一个类比——排一场戏：",
    "    system     剧本设定：「你演一个只用一句话回答的助教」",
    "    user       观众提问",
    "    assistant  演员上一句台词（要接着演，就得把之前的台词递给他）",
    "",
    "  system 的特殊之处：协议上给了它更高的优先级。所以人设、口吻、",
    "  硬性规则都写在 system 里，比塞进 user 更稳，也更不容易被后面的",
    "  问题带偏。你以后调 Agent，一半时间都在改 system。",
)


# ============================================================
section("3. 一个具体场景：只用一句话回答的技术助教")
# ============================================================

say(
    "场景：同一个问题「什么是 RAG？」，两种问法结果差很多。",
    "",
    "  不加 system：模型默认会写成一大段，还带小标题和项目符号。",
    "  加 system「你只用一句话回答，不超过 30 字」：输出立刻收敛。",
    "",
    "  这不是玄学：你把「该怎么答」从用户的临时要求，升级成了对话的固定规则。",
    "  这也是为什么 Week 01 的聊天机器人要留一个 --system 开关——",
    "  「人设」应该是配置，而不是每次都重复敲一遍。",
)


# ============================================================
section("4. 代码：把 messages 拼出来（纯逻辑，离线就能跑）")
# ============================================================

say(
    "  拼装规则就一句话：system 在最前，历史按时间排，新问题放最后。",
    "",
)

example = build_messages(
    "那它省时间吗？",
    system_prompt="你是一个只用一句话回答的技术助教。",
    history=[
        {"role": "user", "content": "什么是流式输出？"},
        {
            "role": "assistant",
            "content": "边生成边发送，让你更快看到第一批字。",
        },
    ],
)

say("  拼出来的 messages：")
for message in example:
    say(f"    {message}")
say(
    "",
    "  注意最后两条：user 是「新问题」，assistant 是「上一轮的回答」。",
    "  所谓多轮对话，不是模型记得住，而是你每次都把这段历史重新发一遍。",
    "  这是 Day 10 的地基，也是「上下文越用越贵」的根源。",
)


# ============================================================
section("5. --live：真的发三次请求，看看 system 和历史的威力")
# ============================================================

QUESTION = "什么是 RAG？"
SYSTEM = "你只用一句话回答，不超过 30 个字。"

say(
    "  离线演示就到这。想亲眼看差别，加 --live 重新运行。",
    "  它发的那次请求，最小就长这样（大约 20 行）：",
    "",
    "    client = OpenAI(api_key=os.environ['LLM_API_KEY'],",
    "                    base_url=os.environ.get('LLM_BASE_URL'))",
    "    response = client.chat.completions.create(",
    "        model=os.environ.get('LLM_MODEL'),",
    "        messages=[{'role': 'user', 'content': '什么是 RAG？'}],",
    "    )",
    "    print(response.choices[0].message.content)",
    "",
    "  三组对照：",
    "    A 无 system          —— 看它默认有多啰嗦",
    "    B 加 system          —— 看人设是怎么把输出勒住的",
    "    C system + 历史追问  —— 看「带上 assistant 那句」之后它会不会接着答",
)

if LIVE:
    # OpenAI(...)：建一个和模型通信的客户端。参数是密钥和服务商地址，
    # 换服务商只改这两个值，代码不用动
    from openai import OpenAI, OpenAIError

    load_dotenv(ROOT / ".env")
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    def ask(messages: list[dict[str, str]]) -> str:
        # chat.completions.create(...)：发一次请求，等模型把话说完再返回
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content

    try:
        print()
        say("  A 无 system：")
        say(f"    {ask(build_messages(QUESTION))}")
        print()
        say("  B 加 system：")
        say(f"    {ask(build_messages(QUESTION, system_prompt=SYSTEM))}")
        print()
        say("  C system + 历史追问「那它和微调有什么区别？」：")
        history = [
            {"role": "user", "content": QUESTION},
            {
                "role": "assistant",
                "content": "RAG 是回答前先检索外部资料，再据此生成答案。",
            },
        ]
        follow_up = build_messages(
            "那它和微调有什么区别？", system_prompt=SYSTEM, history=history
        )
        say(f"    {ask(follow_up)}")
    except OpenAIError as error:
        # 只捕 SDK 自己抛的异常类型，别用 except Exception 一把抓
        say(
            f"    调用失败：{type(error).__name__}",
            f"    {error}",
            "",
            "    常见的对照：401 密钥不对、404 模型名或地址写错、",
            "    429 限流、连接超时是网络问题。",
        )
else:
    print()
    say(
        "  想真的发一次，就加 --live 重新运行：",
        "    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_roles_demo.py --live",
        "",
        "  这一节没有联网，所以上面只打印了要对比的内容。",
    )


# ============================================================
section("6. 要注意什么")
# ============================================================

say(
    "  · system 放最前面，一条最稳。放多条、放中间，各家实现不一样，别依赖。",
    "  · assistant 的内容是「你替模型写的历史台词」。格式要和它真实回答一致，",
    "    否则模型会顺着你给的口吻继续（有时是好事，有时是坑）。",
    "  · 历史越长，每次请求带的内容越多，越慢也越贵——Day 9 算给你看。",
    "  · 别把密钥、密码这类东西写进 system：它和别的内容一样会被发出去。",
    "  · 连续两条 user、或者空的 assistant，各家行为不一致，别用来试探边界。",
    "",
    "  一句话小结：角色不是装饰，是你控制「模型该怎么答」最主要的三个旋钮。",
)


# ============================================================
section("7. 接下来动手（这些是你的事，不是我的）")
# ============================================================

say(
    "  1. 做练习，先别翻答案：",
    "     .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_exercises.py",
    "",
    "  2. 跑 temperature 实验，自己观察：",
    "     .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day08_temperature_demo.py",
    "",
    "  3. 把实验数据和你的判断填进交付物：",
    "     weeks/week01_llm_api/day08_参数对比记录.md",
    "",
    "  填完拿给我看，我帮你对答案、挑毛病。",
)
