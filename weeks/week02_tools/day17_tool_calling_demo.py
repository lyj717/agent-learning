"""Day 17 材料：工具调用（tool calling）——模型不自己算，它「点单」，你上菜。

每一节都按同一个顺序来：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

默认**不联网、不消耗额度**：把真实抓下来的两轮返回原样摆给你看。
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_demo.py

加 --live 自己真跑一轮完整的工具调用（2 次请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_demo.py --live
"""

import json
import os
import sys

from llm_client import make_client
from tools import calculator

LIVE = "--live" in sys.argv

# 今天是「算数学」这个场景。注意：真正的计算不在模型那边发生，在**你这台机器上**发生。
USER_QUESTION = "帮我算一下 347 × 28 等于多少？"


def section(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 先说清楚：工具调用不是「模型去执行函数」")
# ============================================================

say(
    "  名字有点骗人：**模型不会执行你的函数**，它也没有能力执行。",
    "  它做的是「点单」——用结构化输出告诉你：",
    "",
    '      我要调 calculator 这个工具，参数是 expression="347 * 28"',
    "",
    "  真正干活的是**你的代码**：你把工具结果算出来，再递回去，它才开口回答。",
    "",
    "  所以一次完整的工具调用是**两个来回**：",
    "",
    "      ① 你  ：把「有哪些工具、参数长什么样」连同问题一起发过去",
    '      ② 模型：不回答，回一句「请调用 calculator(expression="347 * 28")」',
    "      ③ 你  ：本地执行 → 9716",
    "      ④ 你  ：把 9716 作为「工具结果」回填进对话",
    "      ⑤ 模型：拿到结果，说人话：「347 × 28 = 9716」",
    "",
    "  谁在什么时候执行了什么——这张分工图就是你今天要交的流程图（要自己画）。",
)


# ============================================================
section("2. 为什么需要它：模型自己算不靠谱")
# ============================================================

say(
    "  两个理由：",
    "",
    "  · **算数不可靠**：模型是「猜下一个词」，多位数乘法、精确到分的小数它经常错。",
    "    但 Python 的 `347 * 28` 永远不会错。把计算交出去，错的那部分就消失了。",
    "  · **拿不到实时数据**：今天几度、数据库里有多少订单——它训练完就固定了，",
    "    只能靠你去查，再把结果给它。",
    "",
    "  它擅长的两件事（这也是为什么这条路走得通）：",
    "    ① 听懂「帮我算一下 347 × 28」是要做乘法；",
    '    ② 把参数抽成 {"expression": "347 * 28"}——这不就是昨天刚练的活。',
)


# ============================================================
section("3. 场景：工具箱里先放一个计算器")
# ============================================================

say(
    "  今天只接一个工具（Day 18 再加查天气、查数据库）。工具在**两个地方**各有一份东西：",
    "",
    "    ① 能执行的函数：weeks/week02_tools/tools.py 里的 calculator(expression)",
    "       —— 它就是普通 Python 函数，不知道怎么跟模型打交道",
    "    ② 给模型看的说明（JSON Schema）：名字、干什么用的、参数叫什么、必填吗",
    "       —— 这份说明今天由你写（练习第 1 题）",
    "",
    "  模型看不到你的代码，它只看得到「说明」。所以说明写得清不清楚，",
    "  直接决定它会不会用、用得对不对（Day 18 会专门折腾这条）。",
)


# ============================================================
section("4. 代码：五步，两步是模型的活")
# ============================================================

say(
    "  第 1 步 · 你：写工具的说明（模型看到的就这一份）",
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算一个数学算式，支持 + - * / 和括号。需要做算术时用它。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": '要计算的算式，例如 "347 * 28" 或 "(12+34)/2"',
                    }
                },
                "required": ["expression"],
            },
        },
    }
]
print(json.dumps(TOOLS, ensure_ascii=False, indent=2))

say(
    "",
    "  第 2 步 · 模型：返回的不是回答，而是「点单」",
    "",
    "    finish_reason = 'tool_calls'          ← 看见这个就知道它要调工具",
    "    content = ''                          ← 正文可能是空的，这不算失败",
    "    message.tool_calls = [",
    "        {",
    "          'id': 'call_00_Mi6SM4VQocT47Ej7RnHd6914',   ← 回填时要用它配对",
    "          'type': 'function',",
    "          'function': {",
    "              'name': 'calculator',",
    "              'arguments': '{\"expression\": \"347 * 28\"}',  ← 注意是**字符串**",
    "          },",
    "        }",
    "    ]",
    "",
    "  第 3 步 · 你：执行本地函数",
    "",
    "    arguments 是 JSON **文本**，先 json.loads 变成 dict：{'expression': '347 * 28'}",
    "    再算：calculator('347 * 28') → 9716",
    "",
    "  第 4 步 · 你：把结果回填。要加两条消息：",
    "",
    "    # assistant 那条：把模型刚才的返回原样放回去（含 tool_calls，一个字都别改）",
    "    messages.append(choice.message.model_dump(exclude_none=True))",
    "    # tool 那条：告诉它「你点的那道菜做好了」",
    "    messages.append({",
    "        'role': 'tool',",
    "        'tool_call_id': call.id,      ← 必须对上上面那个 id",
    "        'content': '9716',            ← 工具结果，**必须是字符串**",
    "    })",
    "",
    "  回填完的消息角色长这样：['user', 'assistant', 'tool']",
    "",
    "  第 5 步 · 模型：这回才给你人话",
    "",
    "    finish_reason = 'stop'",
    "    content = '347 × 28 = **9716**\\n\\n计算过程拆解：\\n- = 6940 + 2776\\n- = 9716'",
)


# ============================================================
section("5. 实测数据（2026-10-09 真跑）")
# ============================================================

say(
    "  把两轮的账单和关键字段摆一起，你能看到几件事：",
    "",
    "    第一轮：prompt_tokens=339  completion_tokens=59   finish_reason=tool_calls",
    "    第二轮：prompt_tokens=405  completion_tokens=49   finish_reason=stop",
    "              （prompt 里 256 个 token 命中了缓存，Day 9 学的那个）",
    "",
    "  · **339 个输入 token 里，很大一部分是那份工具说明**——工具不是免费的，",
    "    每轮都要重新发一遍，所以工具别写得又长又啰嗦、也别一次塞几十个。",
    "  · 第二轮输入变成 405：多出来的是「模型的要求 + 工具结果」这两条消息。",
    "  · `content` 第一轮是空的（这次跑是 `''`，另一次是「我来帮你计算。」）——",
    "    **看到空 content 别慌**，先看 finish_reason：它是 tool_calls，说明模型在点单。",
)


# ============================================================
section("6. 要注意什么：六个坑")
# ============================================================

say(
    "  坑一：arguments 是**字符串**，不是 dict。",
    '    长这样：\'{"expression": "347 * 28"}\'。忘了 json.loads 就会拿着字符串去取键，',
    "    报 TypeError；而且它可能是不合法的 JSON，别忘了 try（Day 15 的老朋友）。",
    "",
    "  坑二：assistant 那条消息必须**原样**放回去，尤其是 tool_calls 里的 id。",
    "    少了它 / 改了一个字，第二轮会 400；tool 消息里的 tool_call_id 也要对得上。",
    "    顺手记住：OpenAI 返回的 message 是对象不是 dict，用 model_dump() 转（Day 16 学的）。",
    "",
    "  坑三：tool 消息的 content 必须是字符串。",
    "    算出 9716 要用 str(9716) 或者 json.dumps——直接塞数字进去，有的服务端会报错。",
    "",
    "  坑四：一次可能点**多个**工具。",
    "    tool_calls 是个列表，模型可以一口气要你调三个（比如同时查天气和算账）。",
    "    每个都要执行、都要用各自的 tool_call_id 回填。",
    "",
    "  坑五：模型只点单，执行权在你手里。",
    "    它说「调用 delete_user(1)」你也不能照做——危险工具要人确认、要白名单。",
    "    这是 Agent 安全的第一道门，面试常问。",
    "",
    "  坑六：它可能点不存在的工具、或把参数写错。",
    "    `function.name` 不在你的工具箱里、`arguments` 少字段/类型不对——都在所难免。",
    "    昨天写的 Pydantic 校验正好用来拦参数（Day 19 会把错误回填给它自纠）。",
    "",
    "  坑七：别把「JSON 模式」和「工具调用」叠在一起。",
    '    `response_format={"type": "json_object"}` 管的是「让正文变成 JSON」，',
    "    工具调用管的是「让模型在 tool_calls 里点单」——两个都在管输出形状。",
    "    实测（2026-10-09）两个一起发：不报错，但 finish_reason='stop'、tool_calls=None，",
    "    正文变成一段夹着内部标记、根本没法解析的残渣。",
    "    所以今天用 llm_client 里新加的 `chat_with_tools()`（它**不**开 JSON 模式）。",
)


# ============================================================
section("7. 接下来动手（这些是你的事）")
# ============================================================

say(
    "  1. 写练习：weeks/week02_tools/day17_tool_calling_exercises.py",
    "     三题：写工具说明 → 执行模型点的那一单 → 把整个闭环串起来",
    "",
    "  2. 跑：",
    "     .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py",
    "     .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py --live",
    "",
    "  3. **画流程图**（今天的交付物，别省）：weeks/week02_tools/day17_工具调用流程图.md",
    "     标清每一步「谁在执行」，把你真跑的 id、参数、结果贴到对应位置。",
)


if LIVE:
    section("--live：真跑一轮（第一次请求 + 回填 + 第二次请求）")

    client = make_client()
    messages = [{"role": "user", "content": USER_QUESTION}]

    print(f"  用户说：{USER_QUESTION}\n")
    first = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "deepseek-flash"),
        messages=messages,
        tools=TOOLS,
        max_tokens=2048,
    )
    choice = first.choices[0]
    print("① 第一次请求（带 tools）：")
    print(f"    finish_reason = {choice.finish_reason}")
    print(f"    content = {choice.message.content!r}")
    print(
        f"    usage：输入 {first.usage.prompt_tokens} / 输出 {first.usage.completion_tokens}"
    )

    for call in choice.message.tool_calls or []:
        print(f"    工具名 = {call.function.name}")
        print(
            f"    arguments = {call.function.arguments!r}（类型 {type(call.function.arguments).__name__}）"
        )

        args = json.loads(call.function.arguments)
        result = calculator(args["expression"])
        print(f"    json.loads 之后 = {args}")
        print(f"    本地执行 → {result}")

        messages.append(choice.message.model_dump(exclude_none=True))
        messages.append(
            {"role": "tool", "tool_call_id": call.id, "content": str(result)}
        )

    print(f"\n② 回填之后的消息角色：{[m['role'] for m in messages]}\n")
    second = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "deepseek-flash"),
        messages=messages,
        tools=TOOLS,
        max_tokens=2048,
    )
    print("③ 第二次请求（带上工具结果）：")
    print(f"    finish_reason = {second.choices[0].finish_reason}")
    print(
        f"    usage：输入 {second.usage.prompt_tokens} / 输出 {second.usage.completion_tokens}"
    )
    print(f"\n    模型最后的回答：\n{second.choices[0].message.content}")
