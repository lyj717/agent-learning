"""Day 31：让消息字段追加新观察，并用同一消息 ID 修订它。

先运行 day31_messages_demo.py。默认运行 A；加 --part b 检查图中的两次消息更新。
问题、查询点单和本地结果均为固定教学数据，没有真实模型或网络请求。
这里使用消息对象：读 .type、.id、.content，不再用 Day 30 字典消息的键。
"""

import argparse
from copy import deepcopy
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph


class ReceiptState(TypedDict):
    """本地查询的状态；main 给齐初始字段。"""

    # messages 已配置合并规则：新消息追加，同消息 ID 的修订替换旧消息。
    messages: Annotated[list[AnyMessage], add_messages]
    lookup_results: dict[str, str]
    observation_message_id: str


def record_tool_result(state: ReceiptState) -> dict:
    """根据最新 assistant 点单，返回一条本地查询的 tool 观察。"""
    return {
        "messages": [
            ToolMessage(
                content=state["lookup_results"][
                    state["messages"][-1].tool_calls[0]["name"]
                ],
                id=state["observation_message_id"],
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        ]
    }


def build_receipt_graph() -> CompiledStateGraph:
    """编译先记录工具观察、再按消息 ID 复核观察的图。"""
    builder = StateGraph(ReceiptState)
    builder.add_node("record", record_tool_result)
    builder.add_node("confirm", confirm_receipt)
    builder.add_edge(START, "record")
    builder.add_edge("record", "confirm")
    builder.add_edge("confirm", END)
    return builder.compile()


def confirm_receipt(state: ReceiptState) -> dict:
    """AI 提供的节点：用相同消息 ID 交回一条复核后的观察。"""
    latest = state["messages"][-1]
    print(
        f"  confirm 读到 {len(state['messages'])} 条消息；"
        f"末条 id={latest.id}，内容={latest.content}"
    )
    # ToolMessage 的 id 是消息自身 ID；tool_call_id 对应模型点单，不决定合并位置。
    corrected = ToolMessage(
        content=f"{latest.content}（已复核）",
        id=latest.id,
        tool_call_id=latest.tool_call_id,
    )
    print(f"  confirm 只交回同 id={corrected.id} 的修订消息")
    return {"messages": [corrected]}


def make_case(
    question: str, call_id: str, lookup_name: str, message_id: str, result_text: str
) -> ReceiptState:
    """AI 用固定数据准备同一形状的初始状态。"""
    # HumanMessage(content=..., id=...)：创建用户消息对象，不调用模型。
    user_message = HumanMessage(content=question, id=f"user-{call_id}")
    # AIMessage(tool_calls=...)：保存一条已有的 assistant 点单；id 是这条消息自身 ID。
    assistant_message = AIMessage(
        content="",
        id=f"assistant-message-{call_id}",
        tool_calls=[{"id": call_id, "name": lookup_name, "args": {}}],
    )
    return {
        "messages": [user_message, assistant_message],
        "lookup_results": {lookup_name: result_text},
        "observation_message_id": message_id,
    }


def main() -> None:
    """A 对照单条更新与合并键；B 对照图里的追加和同 ID 修订。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b"), default="a")
    part = parser.parse_args().part

    if part == "a":
        updates = []
        for label, message_id in [
            ("原始观察", "observation-original"),
            ("另一条观察", "observation-audit"),
        ]:
            state = make_case(
                "青禾笔记本还有多少？",
                "call-31-stock",
                "lookup_stock",
                message_id,
                "青禾笔记本还剩 8 本",
            )
            before = deepcopy(state)
            update = record_tool_result(state)
            new_messages = update["messages"]
            print(f"\n{label}：本轮返回条数 {len(new_messages)}；期望 1")
            for message in new_messages:
                print(f"  类型 {message.type}；期望 tool")
                print(f"  消息 ID {message.id}；期望 {message_id}")
                print(f"  调用 ID {message.tool_call_id}；期望 call-31-stock")
                print(f"  内容 {message.content}；期望 青禾笔记本还剩 8 本")
            print(f"  原输入未修改 {state == before}；期望 True")
            updates.extend(new_messages)

        # add_messages(旧消息, 新消息)：按消息自身 ID 合并；这里两条只是合并键对照。
        merged = add_messages(updates[:1], updates[1:])
        print("\n同一个调用 ID、不同消息 ID 的对照（非真实工具重复执行）：")
        print(f"  合并后消息数 {len(merged)}；期望 2")
        print(f"  消息 ID {[message.id for message in merged]}")
        return

    graph = build_receipt_graph()
    cases = [
        ("库存", "call-31-campus", "lookup_campus", "receipt-campus", "校内现货 5 本"),
        (
            "运费",
            "call-31-shipping",
            "lookup_shipping",
            "receipt-shipping",
            "运费 6 元",
        ),
    ]
    for label, call_id, lookup_name, message_id, result_text in cases:
        initial = make_case(
            f"青禾笔记本的{label}如何？", call_id, lookup_name, message_id, result_text
        )
        before = deepcopy(initial)
        print(f"\n=== {label}：初始消息 ID {[m.id for m in initial['messages']]} ===")
        result = graph.invoke(initial)
        messages = result["messages"]
        assistant_messages = [m for m in messages if m.type == "ai"]
        tool_messages = [m for m in messages if m.type == "tool"]
        actual_assistant_id = assistant_messages[-1].id if assistant_messages else None
        actual_request_ids = [
            call["id"] for message in assistant_messages for call in message.tool_calls
        ]
        actual_tool_id = tool_messages[-1].id if tool_messages else None
        actual_call_id = tool_messages[-1].tool_call_id if tool_messages else None
        actual_content = tool_messages[-1].content if tool_messages else None
        print(f"最终消息数 {len(messages)}；期望 3")
        print(
            f"最终类型顺序 {[m.type for m in messages]}；期望 ['human', 'ai', 'tool']"
        )
        print(
            f"assistant 消息自身 ID {actual_assistant_id}；期望 assistant-message-{call_id}"
        )
        print(
            f"assistant 点单 ID {actual_request_ids}；期望 [{call_id!r}]；"
            f"tool 观察的调用 ID {actual_call_id}"
        )
        print(f"tool 消息自身 ID {actual_tool_id}；期望 {message_id}")
        print(f"tool 最终内容 {actual_content}；期望 {result_text}（已复核）")
        print(f"原输入未修改 {initial == before}；期望 True")


if __name__ == "__main__":
    main()

# === 现象与原因：学员原答及 AI 订正 ===
# 1. A 的两条 tool 消息有相同 tool_call_id，为何合并后仍是两条？
#    这与模型点单和工具观察的配对规则有什么不同？
# 我的回答：
#   两条 tool 消息自身的 id 分别是 observation-original 和 observation-audit，所以合并后为两条
#   模型点单和工具观察要求tool_call_id相同配对返回消息，A则比较两条消息自身的.id
# 2. B 的 record 只返回一条 tool 消息，为什么最终仍保留 human 与 ai 消息？
#    对照 Day 30 手工返回旧列表加新消息的写法。
# 我的回答：
#   record只返回一条tool消息，不修改human与ai消息，仍保存在messages列表里,如果没有配置 add_messages，这次返回的一条 tool 消息就会替换整个旧列表，human 和 ai 消息会消失。
#   Day30是每次手动维护state["messages"] + [reply]
# 3. B 的 confirm 之后 tool 消息为何仍只有一条，内容却变了？
#    指出修订前后相同的是哪个 ID，并引用一次实际输出。
# 我的回答：
#   confirm 交回一条新的 ToolMessage；它与原 tool 消息的 message.id 相同，add_messages 因而在原位置替换内容
#   相同的是message.id
#   confirm 读到 3 条，末条 id=receipt-campus、内容=校内现货 5 本；最终仍是 3 条，
# 4. 如果把 ReceiptState.messages 恢复成普通 list[AnyMessage]，
#    根据演示中的默认覆盖输出，预测 B 的最终消息数及缺失的消息类型。
# 我的回答：
#   最终消息数为1，缺失了human和ai的消息

# === AI 订正（2026-10-16；上方为学员讲解后的订正稿） ===
# 1. A 确实只返回一条 tool 消息，但 main 随后调用 add_messages 合并两次更新。
#    两条 tool 消息自身的 id 分别是 observation-original 和 observation-audit，
#    所以合并后为两条；相同的 tool_call_id=call-31-stock 不决定合并位置。
#    配对依据是 assistant 点单里的 tool_calls[0]["id"] 与
#    ToolMessage.tool_call_id 相同，不要求 assistant 消息自身 id 与 tool 消息 id 相同。
# 2. record 只交回本轮的一条 tool 消息；图看到 messages 字段配置了 add_messages，
#    把已有的 human、ai 消息作为旧列表，与这条更新合并后保存，因此最终三条都在。
#    Day 30 则由节点手工返回 state["messages"] + [新消息] 来保留旧消息。
# 3. confirm 交回一条新的 ToolMessage；它与原 tool 消息的 message.id 相同，
#    add_messages 因而在原位置替换内容。库存组实跑：confirm 读到 3 条，
#    末条 id=receipt-campus、内容=校内现货 5 本；最终仍是 3 条，
#    tool 内容变为“校内现货 5 本（已复核）”。相同的 tool_call_id 用于点单配对，
#    不决定这次替换；本题里也没有名为 tool_calls_id 的消息属性。
# 4. 原答正确。若去掉合并规则，record 的新列表会覆盖 human、ai；
#    confirm 再用一条修订消息覆盖它，最终只剩一条 tool 消息。
