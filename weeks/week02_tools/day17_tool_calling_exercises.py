"""Day 17 练习：接上第一个工具（计算器），跑通一次完整的工具调用。

跑法（默认离线：只跑不花钱的自测）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py

真跑（真的问模型两个问题，最多 4 次请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_tool_calling_exercises.py --live

工具调用流程图保存在 weeks/week02_tools/day17_工具调用流程图.md。

本文件已实现的三部分：
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
                        它只看得到 build_tools() 返回的工具说明。

    day17_tool_calling_demo.py   讲解脚本（AI 搭，你跑它 + --live 看真实回合）
    day17_工具调用流程图.md        学员的流程图记录
"""

import json
import sys

from llm_client import chat_with_tools, make_client
from tools import calculator

LIVE = "--live" in sys.argv

TOOL_TABLE = {"calculator": calculator}


def build_tools() -> list[dict]:
    """拼出 tools 参数：给模型看的工具说明（一份 JSON Schema）。"""
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
    return TOOLS


def execute_tool_call(name: str, arguments: str) -> str:
    """执行模型点的那一单（名字 + 参数 JSON 文本），返回要回填给模型的字符串。"""
    # 这里**不**包 try/except：json.loads 遇到坏 JSON 会自己抛 JSONDecodeError，
    # 让它照原样往上抛就行（「别吞异常」的意思就是这个）。写 `except X: raise` 属于空操作，
    # ruff 的 TRY203 会把它挑出来。
    text = json.loads(arguments)
    function = TOOL_TABLE.get(name)
    if function is None:
        raise ValueError(f"没有这个工具!工具名为{name}")
    return str(function(**text))


def ask_with_tools(question: str, *, max_rounds: int = 3) -> str:
    """完整闭环：问一句，需要工具就执行并回填，直到模型给出答复。"""
    client = make_client()
    messages = [{"role": "user", "content": question}]
    for round_no in range(1, max_rounds + 1):
        message = chat_with_tools(messages, build_tools(), client=client)
        if not message.tool_calls:
            return message.content or ""
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            result = execute_tool_call(call.function.name, call.function.arguments)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
            # 把这一轮的轨迹打出来（填交付物那张表要用）。缩进对齐上面的「我问 / 它答」，
            # 每条信息自带标签——裸着 print 两个值，夹在输出里根本认不出哪个是哪个。
            print(f"     [第 {round_no} 轮] 它点了 {call.function.name}")
            print(f"        id        = {call.id}")
            print(f"        arguments = {call.function.arguments}")
            print(f"        → 本地执行 = {result}")
    return "模型调用失败，请重试！"


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
            # 答案可能是多行的；换行后也补上缩进，免得第二行顶到最左边、看着像另一段输出
            answer = ask_with_tools(question)
            print("     它答：" + answer.replace("\n", "\n           "))
