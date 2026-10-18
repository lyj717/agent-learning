"""Day 31：消息字段怎样追加新消息、按消息 ID 修订旧消息。

阅读顺序：main → PlainState / MergedState → post_draft → revise_draft → build_demo_graph。
直接运行即可；客服回复是固定教学文字，没有模型请求或真实订单查询。
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph


def main() -> None:
    """用同样的两个节点，对照默认覆盖与按消息 ID 合并。"""
    print("=== 1. 这是什么 ===")
    print("Day 29～30 的普通列表字段收到新值时，旧列表会被整个替换。")
    print(
        "给 messages 配 add_messages 后，新 ID 会追加；已有 ID 会在原位置被新消息替换。"
    )
    print("合并发生在图写入状态时；节点仍只交回本轮的更新字典。")

    print("\n=== 2. 为什么需要它 ===")
    print("Day 30 为保留历史，每个节点都手写 state['messages'] + [新消息]。")
    print("以后节点多了，容易忘记拼旧项，也不方便按消息 ID 修订已有内容。")

    print("\n=== 3. 场景 ===")
    print("用户询问青禾笔记本到货时间；两个教学节点先写草稿，再更正同一条回复。")
    print("两次回复使用同一个消息 ID：reply-1；文字是固定示意，不是真实库存信息。")
    print("对照只改状态定义，节点返回值和 START → draft → revise → END 路线不变。")

    print("\n=== 4. 先不建图，直接调用 add_messages ===")
    # left 是状态里已有的消息；right 是本次要写入的消息。返回合并后的列表。
    existing = [HumanMessage(content="青禾笔记本何时到货？", id="question-1")]
    draft_update = [AIMessage(content="草稿：明日到货", id="reply-1")]
    print("第 1 次：right 的 reply-1 在 left 中不存在，所以追加。")
    print(f"  left 的 ID：{[message.id for message in existing]}")
    print(f"  right 的 ID：{[message.id for message in draft_update]}")
    after_draft = add_messages(existing, draft_update)
    print(f"  返回 {len(after_draft)} 条：")
    for message in after_draft:
        print(f"    {message.id}：{message.content}")
    print(f"  原来的 existing 仍有 {len(existing)} 条；合并结果要接住返回值。")

    revised_update = [AIMessage(content="更正：预计后日到货", id="reply-1")]
    print("第 2 次：right 的 reply-1 已在 left 中，所以替换原位置那条消息。")
    print(f"  left 的 ID：{[message.id for message in after_draft]}")
    print(f"  right 的 ID：{[message.id for message in revised_update]}")
    after_revision = add_messages(after_draft, revised_update)
    print(f"  返回 {len(after_revision)} 条：")
    for message in after_revision:
        print(f"    {message.id}：{message.content}")

    print("\n=== 5. 放回图里：谁调用 add_messages ===")
    print(
        "PlainState / MergedState 是状态类型说明；真正传给 invoke 的初始状态仍是字典。"
    )
    print("先建图：StateGraph 接收状态类型，add_node 注册节点，add_edge 连接路线。")
    print("compile 只把图变成可执行对象；invoke(initial) 才从 START 开始运行。")
    print(
        "节点返回 {'messages': [本轮消息]} 后，图把已有列表当 left、更新列表当 right。"
    )
    print("MergedState 为 messages 配了 add_messages，图调用它并保存返回的列表。")
    for label, state_schema in [
        ("普通列表：默认替换", PlainState),
        ("配置 add_messages：按 ID 合并", MergedState),
    ]:
        print(f"\n{label}")
        # HumanMessage 是消息类；content 是正文，id 是这条消息自身的标识。
        # 构造对象只准备输入数据，不会请求模型。这里显式给 id，便于对照合并。
        initial = {
            "messages": [HumanMessage(content="青禾笔记本何时到货？", id="question-1")]
        }
        # 传入的是 PlainState / MergedState 这个状态类型，不是 initial 状态数据。
        graph = build_demo_graph(state_schema)
        print("  图已编译；现在调用 invoke，节点才开始执行")
        # invoke(initial)：initial 是进入图的状态字典；沿边执行节点到 END。
        # 返回值是最终状态字典，其中 messages 已按状态类型指定的规则合并。
        result = graph.invoke(initial)
        print(f"最终消息数：{len(result['messages'])}")
        for message in result["messages"]:
            print(
                f"  类型={message.type}；消息 ID={message.id}；内容={message.content}"
            )
        print(f"调用者初始消息数仍为：{len(initial['messages'])}")

    print("\n=== 6. 注意什么 ===")
    print(
        "Annotated[字段类型, 合并函数] 写在状态类型里，指定这个字段以后怎样接收更新。"
    )
    print("add_messages(旧消息列表, 本轮返回列表) 产出合并列表；图会自动调用它。")
    print("写 Annotated[..., add_messages] 时传函数本身，不在定义处写 add_messages()。")
    print("AIMessage 只是 assistant 消息对象；创建它不会请求真实模型。")
    print("本例显式设置消息 ID 便于对照；没传 ID 时，合并过程中可生成 ID。")
    print("消息对象用 .type、.id、.content 读取；这里 .type 分别是 human 和 ai。")
    print("Day 30 的简化字典消息用键读取，不能对这里的消息对象写 ['role']。")
    print(
        "工具点单的 call ID 与 tool 观察的 tool_call_id 用于配对；消息合并看 message.id。"
    )
    print("今天不处理删除消息、检查点或真实模型调用。")


class PlainState(TypedDict):
    """没有合并规则；节点返回的新列表直接替换旧列表。"""

    # TypedDict 描述字典应有哪些键、值是什么类型；运行时仍使用普通字典。
    # AnyMessage 是消息类型的合集；list[AnyMessage] 只说明字段装什么，不指定合并方式。
    messages: list[AnyMessage]


class MergedState(TypedDict):
    """消息字段配置合并规则；其他字段仍用默认替换。"""

    # Annotated[原本的字段类型, 附加信息] 是 Python 的类型注解写法，不是消息或函数调用。
    # 这里把合并函数附在 messages 类型上；StateGraph 读到它，日后写入时调用该函数。
    # 节点返回后，可近似理解为：新 messages = add_messages(旧 messages, 更新字典["messages"])。
    # add_messages(旧消息列表, 节点返回的新消息列表) -> 合并后的消息列表：
    # 新消息 ID 追加，已有消息 ID 在原位置替换。此处传函数本身，不加括号。
    messages: Annotated[list[AnyMessage], add_messages]


def post_draft(state: PlainState | MergedState) -> dict:
    """只交回一条新草稿消息，不手工拼接旧消息。"""
    # state 是图传入的当前状态；节点返回的字典只列出本轮要更新的字段。
    print(f"  draft 节点进入时有 {len(state['messages'])} 条消息")
    # AIMessage 是消息类；content 是正文，id 是这条 assistant 消息自身的标识。
    # 创建它只得到消息对象，不会调用模型。图稍后按消息 id 合并节点返回的列表。
    draft = AIMessage(content="草稿：明日到货", id="reply-1")
    print(f"  draft 节点只返回 id={draft.id} 的一条消息")
    return {"messages": [draft]}


def revise_draft(state: PlainState | MergedState) -> dict:
    """用与草稿相同的消息 ID 交回修订版。"""
    print(f"  revise 节点进入时看到的消息 ID：{[m.id for m in state['messages']]}")
    revised = AIMessage(content="更正：预计后日到货", id="reply-1")
    print(f"  revise 节点只返回 id={revised.id} 的修订消息")
    return {"messages": [revised]}


def build_demo_graph(state_schema: type) -> CompiledStateGraph:
    """同一组节点与边，使用传入的状态定义编译图。"""
    # StateGraph(state_schema)：本例传入的参数是状态类型，如 PlainState / MergedState。
    # 返回图的构建器；它据此知道有哪些字段、各字段有没有合并规则，此时不运行节点。
    builder = StateGraph(state_schema)
    # add_node(节点名, 节点函数)：第一个参数是边会引用的名字；第二个参数是函数本身。
    # 这里传 post_draft 而非 post_draft()，因为建图时只登记，不能提前调用。
    # 图运行时才调用这个函数，传入当前状态；函数交回要更新的字段字典。
    builder.add_node("draft", post_draft)
    builder.add_node("revise", revise_draft)
    # add_edge(起点, 终点)：两个参数是节点名或 START / END，表示固定下一站。
    # START 是框架入口，END 是终点；"draft"、"revise" 是上面注册的节点名。
    builder.add_edge(START, "draft")
    builder.add_edge("draft", "revise")
    builder.add_edge("revise", END)
    # compile()：检查图的连接并生成 CompiledStateGraph，可用 invoke 执行。
    # compile 没有必填参数，也不会处理 initial 或调用节点。
    return builder.compile()


if __name__ == "__main__":
    main()
