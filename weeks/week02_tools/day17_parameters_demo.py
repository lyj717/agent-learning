"""Day 17 加餐：工具说明里的 `parameters` 到底写什么。

一句话：**它就是一份 JSON Schema**——用 JSON 描述「这个函数要收什么样的入参」。
模型看不到你的代码，它只知道这份描述，所以参数名、类型、必填与否、取值范围，
全得在这里说清楚。

默认离线（逐键讲解）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_parameters_demo.py

加 --live 跑三轮实测（约 3 次请求），看「写得细」和「写得糊」分别会拿到什么参数：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day17_parameters_demo.py --live
"""

import json
import os
import sys

from llm_client import make_client

LIVE = "--live" in sys.argv
QUESTION = "杭州明天多少度？我想看华氏度。"


def section(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


# ============================================================
section("1. 这是什么：一份「入参说明书」")
# ============================================================

print(
    """  parameters 里写的是 JSON Schema。工具的入参**永远是一个对象**，
  所以最外层固定是 `"type": "object"`，里面三样东西最常用：

      properties   每个参数一条：参数名 → 它的类型和说明
      required     哪些参数是必填（写在这里面的名字，模型必须给）
      description  这条参数的说明（单位？格式？取值范围？）

  除了这三样，还能用：enum（限定取值）、items（数组元素类型）、
  default（默认值）、minimum / maximum（数值范围）、嵌套 object 等等——
  完整的清单在官方「JSON Schema 参考」里（接口文档 parameters 那节有链接）。"""
)


# ============================================================
section("2. 一份「写得细」的示例，逐键看")
# ============================================================

GOOD_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询某个城市某一天的天气，返回温度和天气状况。",
        "parameters": {
            "type": "object",  # 外层固定：工具入参是个对象
            "properties": {
                "city": {  # ← 参数名。模型会照这个名字回填
                    "type": "string",
                    "description": "城市名，中文，例如 杭州、上海",  # 写给模型看的
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],  # 只允许这两个值
                    "description": "温度单位：celsius=摄氏度，fahrenheit=华氏度",
                    "default": "celsius",
                },
                "date": {
                    "type": "string",
                    "description": "日期，格式 YYYY-MM-DD；不传表示今天",
                },
            },
            "required": ["city"],  # 只有 city 必填，unit 和 date 可选
        },
    },
}

print(json.dumps(GOOD_TOOL, ensure_ascii=False, indent=2))
print(
    """
  逐条读一下它传达了什么：
    · city 必填、是字符串、写中文——模型才会填「杭州」而不是「Hangzhou」
    · unit 的 enum 把取值钉死，它就只能填 celsius 或 fahrenheit，
      不会自创 "C"、"华氏"、"fahrenheit度" 这种脏值（Day 16 校验会感谢你）
    · date 没进 required，所以可以不传；description 里又交代了格式和默认含义
    · 「不传表示今天」这句话只能写在 description 里——Schema 本身表达不了这层意思"""
)


# ============================================================
section("3. 一份「写得糊」的对照")
# ============================================================

VAGUE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查天气",
        "parameters": {
            "type": "object",
            # properties 是空的：模型完全不知道要传什么
        },
    },
}

print(json.dumps(VAGUE_TOOL, ensure_ascii=False, indent=2))
print(
    """
  这份能跑，但模型没有线索可依。实测（2026-10-09）它**照样点了单**，
  参数给的是个空对象 `{}`——注意这个结果：它不会去编参数名，但你的函数
  一执行就会因为缺参数报 KeyError。所以 Schema 写糊的代价不是「不调用」，
  而是「调了却没法用」；要么在 Schema 里写清，要么在代码里校验（Day 16 那套）。"""
)


if LIVE:
    section("--live：三轮实测（同一句话，只换工具说明）")

    client = make_client()
    model = os.environ.get("LLM_MODEL", "deepseek-flash")

    def ask(tool: dict, *, strict: bool = False):
        function = dict(tool["function"])
        if strict:
            function["strict"] = True
        fields = {
            "model": model,
            "messages": [{"role": "user", "content": QUESTION}],
            "tools": [{"type": "function", "function": function}],
            "max_tokens": 2048,
        }
        response = client.chat.completions.create(**fields)
        choice = response.choices[0]
        return choice, response.usage

    for label, tool in [
        ("① 写得细的（city 必填 + unit 枚举 + date 可选）", GOOD_TOOL),
        ("② 写得糊的（properties 空）", VAGUE_TOOL),
    ]:
        print(f"\n  {label}")
        choice, usage = ask(tool)
        calls = choice.message.tool_calls or []
        print(f"     finish_reason = {choice.finish_reason}")
        if not calls:
            print(f"     没点单，直接回：{(choice.message.content or '')[:80]}")
        for call in calls:
            print(f"     → {call.function.name}  arguments = {call.function.arguments}")

    print("\n  ③ 写得细的 + strict=True（Beta：保证输出符合 schema）")
    try:
        choice, usage = ask(GOOD_TOOL, strict=True)
        calls = choice.message.tool_calls or []
        print(f"     finish_reason = {choice.finish_reason}")
        for call in calls:
            print(f"     → {call.function.name}  arguments = {call.function.arguments}")
    except Exception as error:  # noqa: BLE001
        print(f"     报错：{type(error).__name__}: {str(error)[:200]}")

    print(
        "\n  对比 ① 和 ②：同一句话、同一个模型，唯一的差别就是你写的那份 Schema。"
        "\n  ① 的 unit 被映射成了枚举值 fahrenheit（问题里说的是「华氏度」）；"
        "\n  ② 参数是空的——它照点单，但你的函数没法用这份参数。"
        "\n  （它填出来的参数长得像不像样，就是这份 Schema 的分数。）"
    )


# ============================================================
section("4. 写 parameters 的六条经验")
# ============================================================

print(
    """  · 外层永远是 `"type": "object"`：工具入参是对象，哪怕只有一个参数。
  · 参数名用「你会用的名字」：city、expression、days 比 arg1、param2 有用得多。
  · 每个参数都配 description：单位、格式、示例、缺省含义，全写在这儿。
  · 取值可枚举就用 enum：它比描述里的「请填摄氏度或华氏度」硬得多。
  · required 只放真的必须的：多写会逼模型编值（Day 17 实测过 required 的威力），
    少写会让它在信息不足时干脆不传。
  · 复杂结构就嵌套：数组用 `"type": "array", "items": {...}`，
    对象里再写 object；数据库查询工具（Day 18）就是这么搭的。

  写完自检一句话：**「换我拿到这份说明，能不能填对参数？」**填不出，就是没写清。"""
)
