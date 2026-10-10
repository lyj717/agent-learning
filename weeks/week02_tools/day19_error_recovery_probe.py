"""Day 19 离线自测：用假模型验证错误回填、调用 ID 和轮数上限。

先完成 day19_error_recovery_exercises.py 的两题，再运行本文件。
它不会发网络请求；检查的是消息如何回填，不会替你做真实模型实验。
"""

import sys
from pathlib import Path
from types import SimpleNamespace

# 本脚本与练习文件同目录；从仓库根目录运行时，先把该目录加入导入路径。
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import day19_error_recovery_exercises as practice


class FakeMessage:
    """只提供练习闭环会读取的 content、tool_calls 和 model_dump。"""

    def __init__(self, *, calls=None, content=None):
        self.tool_calls = calls
        self.content = content

    def model_dump(self, *, exclude_none=True):
        result = {"role": "assistant"}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in self.tool_calls
            ]
        return result


def call(call_id: str, expression: str):
    """造一条计算器点单；参数保留为模型实际会给的 JSON 字符串。"""
    # SimpleNamespace(字段=值)：造一个能用 .id、.function.name 读取字段的小对象。
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name="calculator", arguments=f'{{"expression": "{expression}"}}'
        ),
    )


class FakeChat:
    """每次被调用就返回下一条预设消息，并保存当时发出的消息列表。"""

    def __init__(self, replies):
        self.replies = replies
        self.sent = []

    def __call__(self, messages, tools, *, client=None):
        self.sent.append(list(messages))
        index = len(self.sent) - 1
        return self.replies[min(index, len(self.replies) - 1)]


def check(condition: bool, description: str) -> None:
    print(f"  {'✓' if condition else '✗'} {description}")
    if not condition:
        raise AssertionError(description)


print("检查 1：本地失败变成工具结果，成功仍返回原值")
bad = practice.tool_result_or_error("calculator", '{"expression": "12 ** 2"}')
good = practice.tool_result_or_error("calculator", '{"expression": "12 * 12"}')
print(f"  错误：{bad}")
print(f"  成功：{good}")
check(bad.startswith("工具执行失败："), "坏算式回填了错误文字")
check(good == "144", "好算式保留正常结果")

# 覆盖的只有练习模块里的两个名字；不会建客户端，也不会向网络发请求。
check(
    hasattr(practice, "make_client") and hasattr(practice, "chat_with_tools"),
    "第 2 题需要先取消顶部两行 import 的注释",
)
practice.make_client = lambda: object()

print("\n检查 2：失败 → 改参数 → 最终答复")
fake = FakeChat(
    [
        FakeMessage(calls=[call("call_bad", "12 ** 2")]),
        FakeMessage(calls=[call("call_good", "12 * 12")]),
        FakeMessage(content="12 的平方是 144。"),
    ]
)
practice.chat_with_tools = fake
answer = practice.ask_with_recovery("12 的平方是多少？", max_rounds=3)
print(f"  最终答复：{answer}")
check(len(fake.sent) == 3, "共请求模型 3 次")
second_messages = fake.sent[1]
third_messages = fake.sent[2]
check(
    second_messages[-1]["role"] == "tool"
    and second_messages[-1]["tool_call_id"] == "call_bad"
    and second_messages[-1]["content"].startswith("工具执行失败："),
    "第二次请求带回了第一条点单的错误与 ID",
)
check(
    third_messages[-1]["role"] == "tool"
    and third_messages[-1]["tool_call_id"] == "call_good"
    and third_messages[-1]["content"] == "144",
    "第三次请求带回了修正后的结果与 ID",
)
check(answer == "12 的平方是 144。", "返回最终答复")

print("\n检查 3：一直点错时，不能发出第 3 次请求")
always_bad = FakeChat([FakeMessage(calls=[call("call_stuck", "12 ** 2")])])
practice.chat_with_tools = always_bad
stopped = practice.ask_with_recovery("反复点错的示意", max_rounds=2)
print(f"  停止文字：{stopped}")
check(len(always_bad.sent) == 2, "max_rounds=2 时只请求模型 2 次")
check("最大轮数" in stopped, "明确告知达到上限")

print("\n检查 4：同轮两条点单，每个 ID 都有自己的结果")
two_calls = FakeChat(
    [
        FakeMessage(calls=[call("call_a", "12 ** 2"), call("call_b", "12 * 12")]),
        FakeMessage(content="已看到两条工具结果。"),
    ]
)
practice.chat_with_tools = two_calls
practice.ask_with_recovery("同轮两条点单的示意", max_rounds=2)
returned = [item for item in two_calls.sent[1] if item["role"] == "tool"]
check(
    len(returned) == 2
    and {item["tool_call_id"] for item in returned} == {"call_a", "call_b"},
    "两条工具结果分别对上各自的调用 ID",
)

print("\n四组检查通过后，再运行练习的 --live，观察真实模型会不会自纠。")
