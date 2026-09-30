"""用一个「模型返回的工具调用」讲清 Pydantic：为什么需要它、怎么用、它帮你做了什么。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_pydantic_demo.py

顺序上和 day04_class_demo.py 接着看：先有类，再来看 Pydantic 这个「开箱即用」的类。
"""

import json

from pydantic import BaseModel, Field, ValidationError


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


# ============================================================
section("1. 先看不用 Pydantic 的时候：校验得自己写")
# ============================================================

# 模型（或者前端、或者别的服务）给了我们一段数据，我们只知道它「大概」长这样
raw_tool_call = {
    "name": "search_docs",
    "arguments": {"query": "RAG 是什么", "top_k": 3},
}

print("原始数据：", raw_tool_call)
print()


def validate_by_hand(data: dict) -> dict:
    """手写校验：每个字段都要自己检查一遍。"""
    if not isinstance(data, dict):
        raise TypeError("整体必须是个字典")
    if "name" not in data:
        raise ValueError("缺少 name")
    if not isinstance(data["name"], str):
        raise TypeError(f"name 必须是字符串，现在是 {type(data['name']).__name__}")
    arguments = data.get("arguments", {})
    if not isinstance(arguments, dict):
        raise TypeError(f"arguments 必须是字典，现在是 {type(arguments).__name__}")
    if "top_k" in arguments and not isinstance(arguments["top_k"], int):
        raise TypeError("top_k 必须是整数")
    return data


print("手写校验通过：", validate_by_hand(raw_tool_call)["name"])
print("（顺带一提：类型不对抛 TypeError、字段缺失抛 ValueError，这是 Python 惯例）")
print()
print("问题在哪？")
print("  1. 每加一个字段，就要多加一段 if，还得自己想报错文案")
print("  2. 稍微复杂的规则（字符串长度、取值范围、嵌套结构）会写成一大坨")
print("  3. 换个数据结构，这套检查要整个重写一遍")
print("  4. 最要命的：只要有一处忘了检查，脏数据就一路带进后面的流程")


# ============================================================
section("2. 换成 Pydantic：字段写完，校验就有了")
# ============================================================


class ToolCall(BaseModel):
    """一次工具调用。类型注解就是校验规则。"""

    name: str
    arguments: dict = Field(default_factory=dict)


call = ToolCall(name="search_docs", arguments={"query": "RAG 是什么", "top_k": 3})
print("创建成功：", call)
print()
print("注意我们只写了两个字段，却直接得到了：")
print("  __init__    —— 按字段名收参数（多传的会被忽略，少传必填的会报错）")
print("  __repr__    —— 上面那行打印就是它")
print("  __eq__      —— 两个内容一样的对象可以 == 比较")
print("  类型校验    —— 不合规的数据进不来")


# ============================================================
section("3. 校验失败长什么样")
# ============================================================

print("试试把数字传给字符串字段：\n")
try:
    ToolCall(name=123)
except ValidationError as e:
    print(e)

print("\n这段话怎么读：")
print("  1 validation error for ToolCall   → 有 1 处不合格")
print("  name                              → 出问题的是 name 字段")
print("  Input should be a valid string    → 它期望字符串")
print("  [type=string_type, input_value=123, input_type=int]")
print("                                    → 实际收到的是 int 类型的 123")


# ============================================================
section("4. 它会帮你转换，也有明确的边界")
# ============================================================


class SearchArgs(BaseModel):
    query: str
    top_k: int = 5


print('top_k 传字符串 "3"：')
coerced = SearchArgs(query="RAG 是什么", top_k="3")
print(f"  结果：{coerced.top_k}，类型：{type(coerced.top_k).__name__}")
print("  说明：能无损转换的（字符串 3 → 整数 3），Pydantic 默认帮你转")
print()

print("反过来，数字 123 想当字符串用：")
try:
    SearchArgs(query=123)
except ValidationError:
    print("  被拒绝了——Pydantic v2 不再做这种有歧义的转换")
print()

print("这条边界在 Agent 开发里很重要：模型返回的 JSON 常常把数字写成字符串，")
print("能自动转换省掉很多麻烦；但它不会替你「猜」意思，猜错的地方一律报错。")


# ============================================================
section("5. 默认值：Field(default_factory=dict) 是 Day 3 那个坑的自动挡")
# ============================================================


class Note(BaseModel):
    text: str
    tags: list[str] = Field(default_factory=list)


a = Note(text="第一条")
b = Note(text="第二条")
a.tags.append("重点")

print("a:", a)
print("b:", b)
print()
print("a 的 tags 被改了，b 完全不受影响——因为 default_factory 每次")
print("创建实例时都重新调用一次函数（这里是 list），生成一个新的空列表。")
print("这正是 Day 3 里你要手写 if basket is None: basket = [] 的那件事。")


# ============================================================
section("6. 嵌套模型：真实工具调用的样子")
# ============================================================


class TypedToolCall(BaseModel):
    """这次把 arguments 也定义成模型，而不是随便一个 dict。"""

    name: str
    arguments: SearchArgs


print("嵌套的好处：参数内部的字段也被校验了\n")
print("正常创建一个：")
print(" ", TypedToolCall(name="search_docs", arguments=SearchArgs(query="RAG")))
print()

print("参数里传个不合法的值：")
try:
    TypedToolCall(name="search_docs", arguments={"query": "RAG", "top_k": "很多"})
except ValidationError as e:
    first_line = str(e).splitlines()[1]
    print(f"  被拦下：{first_line.strip()}")
print()
print("注意报错里带上了字段路径（arguments.top_k），一眼知道是嵌套里哪一层出的问题。")


# ============================================================
section("7. 三个最常用的动作：转字典、转 JSON、从 JSON 解析")
# ============================================================

raw = '{"name": "search_docs", "arguments": {"query": "RAG 是什么", "top_k": 3}}'

parsed = TypedToolCall.model_validate_json(raw)
print("从 JSON 字符串直接解析：")
print(" ", parsed)
print()

dumped = parsed.model_dump()
print("转成字典（.model_dump()）：")
print(" ", dumped)
print("  类型是", type(dumped).__name__, "，所以能直接丢给别的函数、写进日志")
print()

print("转成 JSON 字符串（.model_dump_json()）：")
print(" ", parsed.model_dump_json(ensure_ascii=False))


# ============================================================
section("8. 和 Agent 的关系：这就是「工具描述」的来源")
# ============================================================

print("SearchArgs 的 JSON Schema：")
print(json.dumps(SearchArgs.model_json_schema(), ensure_ascii=False, indent=2))
print()
print("Week 02 你会做的事：把这个 schema 连同函数说明一起交给模型，")
print("模型就知道「有个工具叫 search_docs，参数是 query（必填）和 top_k（默认 5）」。")
print("所以类型注解写得准不准，直接决定模型会不会正确调用你的函数。")


section("总结")
print("1. Pydantic 用「类型注解 + 字段声明」替你生成 __init__、__repr__ 和校验")
print("2. 不合法的数据在创建对象的那一刻就被拦下，不会流进后面的流程")
print("3. 能无损转换的会帮你转（'3' → 3），有歧义的会拒绝（123 → str）")
print("4. 可变的默认值用 Field(default_factory=...)，Day 3 的坑有了标准解法")
print("5. 模型可以嵌套，报错信息会带上字段路径")
print("6. model_dump / model_dump_json / model_validate_json 是日常三件套")
print("7. model_json_schema() 生成的就是交给模型的工具描述")
