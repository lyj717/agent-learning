"""Day 18 练习：接上天气和 SQLite 订单，让模型从三个工具中选择。

先跑讲解：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day18_multi_tools_demo.py
再做本文件，默认离线；写完后加 --live 问模型（会发真实请求）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day18_multi_tools_exercises.py
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day18_multi_tools_exercises.py --live

今天的记录写在 day18_工具选择记录.md，本文件末尾不用再写一份「现象与原因」。
"""

import sys

# 写第 2 题 build_tools 时，把这行取消注释。
# from day17_tool_calling_exercises import build_tools as day17_build_tools
from day18_seed_db import seed_db

# 写第 2 题 execute_tool_call 时，把这行取消注释。
# import json
# 写第 3 题 ask_with_tools 时，把这行取消注释。
# from llm_client import chat_with_tools, make_client
from tools import calculator, get_weather, query_orders

LIVE = "--live" in sys.argv

# 第 2 题：把新工具也登记到这里。键必须与 build_tools() 的 function.name 一致。
TOOL_TABLE = {"calculator": calculator}


def build_tools() -> list[dict]:
    """给模型三份工具说明。

    要做的：先用 day17_build_tools() 拿到已完成的计算器说明；再写天气、订单
    两份 JSON Schema，append 到同一个列表。天气参数 city；订单参数 city。
    函数名必须分别是 get_weather、query_orders，参数名必须与 tools.py 一致。
    描述写清各自的数据来源、使用场景、返回内容；订单只统计已支付订单。

    期望结果：返回列表恰好三份；名字与 TOOL_TABLE 三个键逐一对应。

    提示：照 Day 17 的 build_tools 结构写。city 是必填 string；不要把
    订单工具描述成「可以查询任意数据库内容」，它实际上只能查固定报表。
    day17_build_tools 的导入已在文件顶部注释，写这题时取消注释。
    """
    raise NotImplementedError("第 2 题：三份工具说明还没写")


def execute_tool_call(name: str, arguments: str) -> str:
    """按模型给的工具名执行一次本地函数，并把结果转成字符串。

    要做的：用 json.loads(arguments) 解析参数；从 TOOL_TABLE 查函数；
    名字不存在就抛带工具名的 ValueError；把 dict 用 ** 展开传给函数。
    别在这里吞掉函数报错，Day 19 才练「错误回填」。

    期望结果：天气返回含城市/摄氏温度/状况的字符串，订单返回含城市/
    已支付笔数/总金额的字符串；不存在的工具会抛 ValueError。

    提示：Day 17 的 execute_tool_call 逻辑可以直接迁移；json 的导入
    已在文件顶部注释，写这题时取消注释。别忘了把新函数加进 TOOL_TABLE。
    """
    raise NotImplementedError("第 2 题：多工具分发还没写")


def ask_with_tools(question: str, *, max_rounds: int = 3) -> str:
    """让模型自动选工具，执行并回填，直到给出最终回答。

    要做的：沿用 Day 17 的完整闭环，把工具说明换成 build_tools()；
    每一轮打印「轮次 / 实际工具名 / 原始 arguments / 本地结果」；
    若本轮未点工具，打印「未调用工具」再返回 message.content。
    一轮可能有多个 tool_calls，要逐个执行、逐个按 call.id 回填。

    期望结果：--live 的每道问题都有第一轮选择轨迹和最终答复，
    足够填写记录表。达到 max_rounds 时明确返回「达到最大轮数」。

    提示：make_client、chat_with_tools 的导入已在顶部注释，写时取消注释；
    assistant 消息要用
    message.model_dump(exclude_none=True) 原样加入 messages，tool 消息
    的 tool_call_id 要用对应 call.id。max_rounds 默认 3，表示最多 3 次请求。
    """
    raise NotImplementedError("第 3 题：多工具闭环还没写")


if __name__ == "__main__":
    print("=== 第 1 题：完成 tools.py 里的 get_weather 与 query_orders ===")
    seed_db()
    for label, function, city in [
        ("模拟天气", get_weather, "杭州"),
        ("SQLite 订单", query_orders, "杭州"),
    ]:
        try:
            print(f"{label}：{function(city)}")
        except NotImplementedError as error:
            print(f"{label}：{error}")
    print("预期：杭州 22°C、多云；杭州 paid 2 单、合计 200 元。")

    print("\n=== 第 2 题：三份说明 + 分发 ===")
    try:
        descriptions = build_tools()
        print("工具名：", [item["function"]["name"] for item in descriptions])
        for name, args in [
            ("calculator", '{"expression": "347 * 28"}'),
            ("get_weather", '{"city": "上海"}'),
            ("query_orders", '{"city": "北京"}'),
        ]:
            print(f"{name}({args}) -> {execute_tool_call(name, args)}")
        print("预期：9716；上海 25°C 晴；北京 paid 1 单、90 元。")
    except NotImplementedError as error:
        print(error)

    print("\n=== 第 3 题：模型自动选工具 ===")
    if not LIVE:
        print("写完前两题和闭环后，加 --live 运行；第一轮选哪个要自己先预测。")
    else:
        # 若要找选错案例，可改问法或工具说明，重跑同一道题；真实结果写进 md。
        questions = [
            "模拟数据里杭州天气怎么样？",
            "347 × 28 等于多少？",
            "杭州有几笔已支付订单，合计多少钱？",
            "你好，你是谁？",
            "杭州今天消费了多少？",
            "上海有多少单？",
        ]
        for question in questions:
            print(f"\n问题：{question}")
            try:
                print(f"最终答复：{ask_with_tools(question)}")
            except NotImplementedError as error:
                print(error)
                break
