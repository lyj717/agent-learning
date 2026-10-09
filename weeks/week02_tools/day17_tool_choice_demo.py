"""Day 17 加餐：模型是怎么知道该调用哪个工具的？

答案一句话：**没有魔法**。你写的工具说明（名字 + 描述 + 参数）会被塞进请求里，
模型就是靠**读这些文字**来决定点哪一单的。这个脚本用三段实验证明它：

默认离线（只讲清楚机制 + 摆出实测数据）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_choice_demo.py

加 --live 真跑四轮（会花钱，几分钱），亲眼看到「改描述 → 选择就变」：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_choice_demo.py --live
"""

import os
import sys

from llm_client import make_client

LIVE = "--live" in sys.argv

# 实验用的问题：它明显该用「查天气」，一个字都跟算数没关系
QUESTION = "杭州今天多少度？"


def section(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


def weather_tool(description: str) -> dict:
    """造一个「查天气」的工具说明，描述由参数给——实验就是改它。"""
    return {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，例如 杭州"}
                },
                "required": ["city"],
            },
        },
    }


CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "计算一个数学算式，支持 + - * / 和括号。需要做算术时用它。",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "算式"}},
            "required": ["expression"],
        },
    },
}


# ============================================================
section("1. 机制：你的说明书被「塞进」了请求里")
# ============================================================

print(
    """  模型没有你的代码，也看不到 tools.py。请求发出去的时候，长这样：

       messages: [
           {role: user, content: "杭州今天多少度？"}
       ]
       tools: [
           {name: "get_weather", description: "查询某地今天的天气", parameters: {...}},
           {name: "calculator",   description: "计算一个数学算式",     parameters: {...}}
       ]

  `tools` 这一大块会**变成提示词的一部分**送给模型。它能看到的全部信息就是：
      ① 有个工具叫 get_weather
      ② description 写着「查询某地今天的天气」
      ③ 它要一个 city 参数，是必填

  于是它做的事跟你读这段说明时做的事一样：**理解文字，然后判断哪个工具合适**。
  换句话说：**你说它是什么，它就是什么**。说明写得含糊，它就只能猜。"""
)


# ============================================================
section("2. 证据一：工具说明确实占着输入 token（实测）")
# ============================================================

print(
    """  同一个问题（"杭州今天多少度？"），带不带 tools：

      不带工具：prompt_tokens ≈ 10 出头
      带两个工具：prompt_tokens = 339 里的大头就是这两份说明

  多出来的那两百多个 token，就是你写的那份 JSON Schema——它是**逐字发给模型**的。
  所以：工具说明不是注释，是提示词；写长了花钱，写歪了选错。"""
)


# ============================================================
section("3. 证据二（可跑）：只改 description，选择就变")
# ============================================================

print(
    f"""  实验设计：同一个问题「{QUESTION}」，工具箱里都放着 get_weather 和 calculator，
  唯一的变量是 **get_weather 的 description**：

      第 1 轮：description = "查询某地今天的天气，给出温度和天气状况"   ← 正常
      第 2 轮：description = "处理地理相关的请求"                      ← 含糊
      第 3 轮：description = "计算数学表达式并返回数值"                ← 故意误导（跟计算器撞车）

  加 --live 会真跑这三轮（外加一组「名字中性化」的对照），看它每轮点哪个工具。

  实测结果（2026-10-09，跑完才发现要改我的讲法）：**三轮它都点了 get_weather，一次没被带偏**。
  原因不难想：工具**名字**里明明白白写着 weather，参数又只要一个 city——
  名字和参数名的信息量已经大到盖过了那句被改坏的 description。

  所以要真正看清「描述说了算」，得先把名字里的提示抹掉：
  再把两个工具叫成 tool_a / tool_b，描述才是唯一的线索。--live 里那两轮就是干这个的。"""
)


if LIVE:
    section("--live：真跑四轮（第一轮不带工具，看它没有工具时会怎样）")

    client = make_client()
    model = os.environ.get("LLM_MODEL", "deepseek-flash")

    def ask(tools: list[dict] | None):
        fields = {
            "model": model,
            "messages": [{"role": "user", "content": QUESTION}],
            "max_tokens": 2048,
        }
        if tools:
            fields["tools"] = tools
        response = client.chat.completions.create(**fields)
        choice = response.choices[0]
        return choice, response.usage

    print("  ① 不带任何工具（它只能靠自己「记」的天气）")
    choice, usage = ask(None)
    print(f"     prompt_tokens = {usage.prompt_tokens}")
    print(f"     finish_reason = {choice.finish_reason}")
    print(f"     它的回答：{(choice.message.content or '')[:120]}")

    rounds = [
        ("② 正常描述", "查询某地今天的天气，给出温度和天气状况"),
        ("③ 含糊描述", "处理地理相关的请求"),
        ("④ 误导描述（和计算器撞车）", "计算数学表达式并返回数值"),
    ]
    for label, description in rounds:
        tools = [weather_tool(description), CALCULATOR_TOOL]
        choice, usage = ask(tools)
        calls = choice.message.tool_calls or []
        print(f"\n  {label}：description = {description!r}")
        print(
            f"     prompt_tokens = {usage.prompt_tokens}，finish_reason = {choice.finish_reason}"
        )
        if not calls:
            print(f"     它没点单，直接回了：{(choice.message.content or '')[:100]}")
        for call in calls:
            print(f"     点了：{call.function.name}  参数：{call.function.arguments}")

    print("\n  ── 下面两轮把名字中性化：tool_a / tool_b，描述成了唯一的线索 ──")

    def neutral(name: str, description: str, arg_name: str) -> dict:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {arg_name: {"type": "string", "description": "参数"}},
                    "required": [arg_name],
                },
            },
        }

    neutral_rounds = [
        (
            "⑤ 中性名字 + 正常描述",
            [
                neutral("tool_a", "查询某地今天的天气，给出温度和天气状况", "arg1"),
                neutral("tool_b", "计算一个数学算式，支持四则运算", "arg1"),
            ],
        ),
        (
            "⑥ 中性名字 + 把 tool_a 的描述改成算数学（纯误导）",
            [
                neutral("tool_a", "计算数学表达式并返回数值", "arg1"),
                neutral("tool_b", "计算一个数学算式，支持四则运算", "arg1"),
            ],
        ),
    ]
    for label, tools in neutral_rounds:
        choice, usage = ask(tools)
        calls = choice.message.tool_calls or []
        print(f"\n  {label}")
        for item in tools:
            print(f"     {item['function']['name']}：{item['function']['description']}")
        print(f"     finish_reason = {choice.finish_reason}")
        if not calls:
            print(f"     它没点单，直接回了：{(choice.message.content or '')[:100]}")
        for call in calls:
            print(f"     → 点了：{call.function.name}  参数：{call.function.arguments}")

    print(
        "\n  对照着看：②③④ 里名字有信息（get_weather + city），怎么改描述都不动；"
        "\n  ⑤⑥ 里名字成了 tool_a / tool_b，选择就跟着**描述**走了。"
        "\n  所以它不是只看描述——工具名、参数名、description 三个一起看，谁信息量大谁说了算。"
    )
else:
    print("\n  （加 --live 才能看到这三轮的对比）")


# ============================================================
section("4. 由此能推出来的几条（Day 18 要学的就是这些）")
# ============================================================

print(
    """  · **没有「工具选择算法」**：它拿到的就是 名字 + description + 参数名/说明。
    这几样里哪个信息量大，哪个就当主线索——名字起得好，描述写歪了也能救回来。
  · **工具名和参数名是最便宜的提示**（实测 ②③④）：名字里带着 weather、参数叫 city，
    哪怕描述被改成「计算数学表达式」，它还是选对了。所以别用 func1 / tool_a / arg1。
  · **描述决定了它「认为你有什么能力」**（实测 ⑥）：把查天气那个工具的描述改成算数学，
    它直接回答「我目前可用的两个工具都只做数学计算，没法查天气」——
    连「我没有这个工具」这个判断，都是从你写的描述里读出来的。
  · **它也可能坚持不调用工具**（⑥ 就是）：宁可说「我做不到」，也不硬点一单。
    这时候要么改描述，要么用 `tool_choice` 强制（Day 18 讲）。
  · **参数名和 required 也参与判断**：⑤ 里参数叫 arg1，它照样传对了；
    但描述里没说清该传什么时，它可能编一个值出来。
  · **同样的输入不保证同样的选择**：Day 8 那条「temperature=0 也复现不了」在这里同样成立，
    所以别靠一次运行下结论。"""
)


# ============================================================
section("5. 你能插手的旋钮：tool_choice（实测四种取值）")
# ============================================================

print(
    """  前面六轮都是「它自己决定」。如果你想插手，API 给了 `tool_choice` 这个参数：

      auto（默认，有工具时）  它自己决定：可以不点、点一个、点多个
      none                   这一轮禁止点工具，只能给文字回答
      required               必须点，不许只回文字
      {"type": "function", "function": {"name": "calculator"}}   强制只用这一个

  文档还写了一条本地限制：**思考模式下不支持 required 和「指定具体工具」**。
  2026-10-09 实测（deepseek-flash，默认开思考模式）：

      tool_choice="required"           → 400 BadRequestError：
                                          Thinking mode does not support this tool_choice
      tool_choice={"type":"function",  → 同样的 400
                   "function":{"name":"calculator"}}
      tool_choice="none" / "auto"      → 正常，不点工具（那轮问的是「你好呀」）

  绕法：先把思考模式关掉，再传 required。实测（同一句问候语）：

      thinking={"type": "disabled"} + tool_choice="required"
        → finish_reason='tool_calls'，它点了 calculator，
          参数是它自己编的 {"expression": "1"}

  最后那行很值得看：**「必须用工具」这种硬要求，会逼它编一个假参数出来交差**。
  所以 required 只在「确定这一轮就该调工具」时才用，别当默认。"""
)
