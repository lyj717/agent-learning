"""Day 17 练习：接上第一个工具（计算器），跑通一次完整的工具调用。

跑法（默认离线：只跑不花钱的自测）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py

真跑（真的问模型两个问题，最多 4 次请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py --live

**今天的交付物是一张流程图**（不是这个 .py）：weeks/week02_tools/day17_工具调用流程图.md
——把这次调用的每一步画出来，标清谁在执行。

今天要做的三件事（难度是递进的）：
    第 1 题  build_tools()          —— 写「给模型看的工具说明」（JSON Schema）
    第 2 题  execute_tool_call()    —— 执行模型点的那一单，把结果变成字符串
    第 3 题  ask_with_tools()       —— 把前两件串成完整闭环，直到模型给答复

本目录里今天会用到的文件（AI 搭的，你只管用）：

    llm_client.py       发请求的那一层，两个函数：
                          · make_client()      建客户端（密钥/超时/关掉 SDK 重试）
                          · chat_with_tools(messages, tools, *, client=None,
                                            model=None, max_tokens=2048)
                                发一次请求（带上工具说明），返回模型的**整个 message 对象**，
                                这样你才能看 message.tool_calls 判断它有没有「点单」。
                                注意它**不**开 JSON 模式——工具调用和 JSON 模式不能叠
                                （演示第 6 节「坑七」有实测证据）。
                          · （昨天那个 chat_json 今天用不上：它写死了 JSON 模式。）
                        怎么拿到：本文件顶部已经写好 `from llm_client import ...`。
                        PyCharm 若标红说找不到 llm_client，右键 week02_tools →
                        Mark Directory as → Sources Root（运行不受影响）。

    tools.py            「工具箱」：里面是真能执行的函数。今天只有
                        calculator(expression) -> float（支持 + - * / 和括号，
                        用 ast 安全求值，不用 eval）。Day 18 会往里加查天气和查数据库。
                        注意：**函数本身不是工具**——模型看不到你的代码，
                        它只看得到第 1 题要写的那份说明。

    day17_tool_calling_demo.py   讲解脚本（AI 搭，你跑它 + --live 看真实回合）
    day17_工具调用流程图.md        你的交付物（待填）
"""

import json
import sys

# 下面这几个名字是写题时才用到的（现在写着会被 ruff 当成「导入了没用」）：
#   第 2 题 execute_tool_call 里要用 calculator
#   第 3 题 ask_with_tools 里要用 chat_with_tools 和 make_client
# 写到哪一题，就把对应那行的 `#` 去掉：
# from tools import calculator
# from llm_client import chat_with_tools, make_client
# （顺带提醒：**别对这个文件跑 `ruff check --fix`**——它会把「还没用到」的 import
#   当垃圾删掉，你写到那儿就找不到名字了，Day 16 踩过一次。）

LIVE = "--live" in sys.argv


def build_tools() -> list[dict]:
    """第 1 题：写「给模型看的工具说明」，也就是 tools 参数要传的那个列表。

    要做的：
      · 返回一个 list，里面**一个** dict，形状是官方那套：
            {"type": "function",
             "function": {"name": ..., "description": ..., "parameters": {...}}}
      · name 就叫 "calculator"（要和 tools.py 里的函数名对上，你执行时靠它找函数）
      · description 用一句话说清「它是干什么的、什么时候该用它」
      · parameters 是一份 JSON Schema，形状：
            {"type": "object",
             "properties": {"expression": {"type": "string", "description": "..."}},
             "required": ["expression"]}
        注意 property 名 "expression" 要和 calculator 的参数名一致。

    期望结果：主程序会把你这份说明打印出来（键名齐、description 是人话就行）；
      判断对不对的硬标准——第 3 题真跑时，模型能照着它正确点单。
    提示：演示脚本第 4 节打印过一份**能用的**说明，照那个形状写；
      但别复制粘贴，Day 18 你要自己写第二、第三个工具的说明（那时没人给样板）。
    """
    raise NotImplementedError("第 1 题还没写")


def execute_tool_call(name: str, arguments: str) -> str:
    """第 2 题：执行模型点的那一单，返回「要回填给模型的字符串」。

    参数就是模型返回的那两样：
      name —— 工具名，例如 "calculator"
      arguments —— **一段 JSON 文本**，例如 '{"expression": "347 * 28"}'

    要做的：
      · 先把 arguments 用 json.loads 变成 dict（它可能不是合法 JSON，别吞异常）
      · 按 name 找到对应的函数执行：目前只有 calculator 一个
      · 把结果返回成**字符串**（模型那边收的就是字符串，见演示第 6 节坑三）
      · 遇到不认识的工具名，抛 ValueError，消息里写清是哪个名字

    期望结果（主程序会离线跑这几条）：
      execute_tool_call("calculator", '{"expression": "347 * 28"}')   -> "9716"
      execute_tool_call("calculator", '{"expression": "(12+34)/2"}')  -> "23.0"
      execute_tool_call("get_weather", "{}")                          -> ValueError
    提示：算出来是 float，要 str() 一下；返回值是字符串 "9716" 而不是数字 9716。
    """
    raise NotImplementedError("第 2 题还没写")


def ask_with_tools(question: str, *, max_rounds: int = 3) -> str:
    """第 3 题：完整闭环——问一句，需要工具就执行并回填，直到模型给出答复。

    这一题是把前面两件事串成一个循环。用大白话说：

        发请求（带上工具说明）
            ↓
        看 message.tool_calls
            ↓
        是空的 → 它就是最终回答，把 message.content 返回，结束
            ↓ 不空（它点单了）
        把 assistant 那条原样放回对话
        逐个执行它点的工具，每条结果用 role="tool" 回填
            ↓
        回到第一步，再发一次（这时的输入里已经有工具结果了）

    落到代码上：
      1. client = make_client()
      2. messages = [{"role": "user", "content": question}]
      3. 循环 max_rounds 次：
           message = chat_with_tools(messages, build_tools(), client=client)
           if not message.tool_calls:            # 没点单，这就是答案
               return message.content or ""
           messages.append(message.model_dump(exclude_none=True))   # 原样放回
           for call in message.tool_calls:
               result = execute_tool_call(call.function.name, call.function.arguments)
               messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
      4. 圈数用完还没答案 → 返回一句说明（别抛异常，也别死循环）

    期望结果（--live 两条）：
      · "帮我算一下 347 × 28 等于多少？" → 回答里出现 9716；
        你能看到它先点单（finish_reason=tool_calls 或 tool_calls 非空），再给答复
      · "你好，你是谁？" → 压根不需要工具，一轮就回答
    提示：`message.model_dump(exclude_none=True)` 是把对象转成 dict（Day 16 学的
      `model_dump`，OpenAI 的返回也是 Pydantic 模型）；少了 assistant 那条，
      或者 tool_call_id 对不上，第二轮会 400。
    """
    raise NotImplementedError("第 3 题还没写")


if __name__ == "__main__":
    print("=== 第 1 题：你写的工具说明 ===")
    tools = build_tools()
    print(json.dumps(tools, ensure_ascii=False, indent=2))
    print(f"  一共 {len(tools)} 个工具（今天预期 1 个）")

    print("\n=== 第 2 题：执行模型点的那一单（离线，不联网）===")
    cases = [
        ("calculator", '{"expression": "347 * 28"}'),
        ("calculator", '{"expression": "(12+34)/2"}'),
        ("get_weather", "{}"),
    ]
    for name, arguments in cases:
        try:
            print(f"  {name}({arguments}) -> {execute_tool_call(name, arguments)!r}")
        except NotImplementedError as error:
            print(f"  {name}({arguments}) -> 还没写：{error}")
        except ValueError as error:
            print(f"  {name}({arguments}) -> ValueError: {error}")
    print('  预期：前两条给出 "9716" / "23.0"，第三条抛 ValueError（没有这个工具）')

    print("\n=== 第 3 题：完整闭环（要联网、会花钱，默认不跑）===")
    if not LIVE:
        print("  想跑就加 --live：")
        print(
            "  .venv\\Scripts\\python.exe "
            "weeks\\week02_tools\\day17_tool_calling_exercises.py --live"
        )
        print("  跑完之后，把过程画进 day17_工具调用流程图.md（今天的交付物）")
    else:
        for question in ["帮我算一下 347 × 28 等于多少？", "你好，你是谁？"]:
            print(f"\n  ── 我问：{question}")
            print(f"     它答：{ask_with_tools(question)}")
