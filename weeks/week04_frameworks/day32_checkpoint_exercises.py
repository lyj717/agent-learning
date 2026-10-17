"""Day 32：用 SQLite 检查点让本地工单图在进程重启后接续状态。

回复是固定教学文字，不调用真实模型或外部工单系统。
"""

import argparse
from pathlib import Path
from typing import Annotated, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph


class TicketState(TypedDict):
    """工单状态：旧消息按 ID 合并，处理次数由节点更新。"""

    # Day 31 学过：add_messages 使新消息追加，同消息 ID 更新旧项。
    messages: Annotated[list[AnyMessage], add_messages]
    reply_count: int


def ticket_reply(state: TicketState) -> dict:
    """AI 给定的本地节点：回复最新问题，并累加一次处理次数。"""
    latest = state["messages"][-1]
    print(
        f"  ticket 节点进入时：已有 {len(state['messages'])} 条消息，"
        f"reply_count={state['reply_count']}；最新内容={latest.content}"
    )
    # AIMessage(content=...) 只创建一条 assistant 消息，不会请求真实模型。
    # 节点仅返回本轮消息；messages 的旧项由图按 add_messages 保留。
    reply = AIMessage(content=f"已记录：{latest.content}")
    return {"messages": [reply], "reply_count": state["reply_count"] + 1}


def build_ticket_graph(checkpointer: SqliteSaver) -> CompiledStateGraph:
    """创建工单图，并安装传入的 SQLite 检查点保存器。"""
    builder = StateGraph(TicketState)
    builder.add_node("ticket", ticket_reply)
    builder.add_edge(START, "ticket")
    builder.add_edge("ticket", END)
    return builder.compile(checkpointer=checkpointer)


def submit_ticket_update(
    graph: CompiledStateGraph, ticket_id: str, detail: str
) -> TicketState:
    """给指定工单新增一条用户消息，并返回运行后的工单状态。"""
    config = {"configurable": {"thread_id": ticket_id}}
    snapshot = graph.get_state(config)
    message: dict
    if not snapshot.values:
        message = {"messages": HumanMessage(content=detail), "reply_count": 0}
    else:
        message = {"messages": HumanMessage(content=detail)}
    return graph.invoke(input=message, config=config)


def main() -> None:
    """A 检查图装好保存器；B 用两个独立进程检查工单接续与隔离。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b"), default="a")
    parser.add_argument("--phase", choices=("first", "followup"), default="first")
    parser.add_argument("--ticket-id")
    args = parser.parse_args()

    if args.part == "b" and args.phase == "followup" and not args.ticket_id:
        parser.error("followup 需要第一次运行时打印的 --ticket-id")

    ticket_id = args.ticket_id or f"ticket-{uuid4().hex[:8]}"
    # 文件路径以本脚本为基准；两次从不同终端运行也会连到同一份 SQLite 文件。
    db_path = Path(__file__).with_name("day32_checkpoint_exercises.sqlite").resolve()
    config = {"configurable": {"thread_id": ticket_id}}
    print(f"SQLite 文件：{db_path}")
    print(f"工单会话 thread_id：{ticket_id}")

    # SqliteSaver.from_conn_string(文件路径) 打开本地检查点保存器；with 结束时关闭连接。
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = build_ticket_graph(saver)

        if args.part == "a":
            # A 使用随机会话；只验证图是否会执行节点并保存一次状态。
            initial: TicketState = {
                "messages": [HumanMessage(content="云杉耳机左声道无声")],
                "reply_count": 0,
            }
            result = graph.invoke(initial, config)
            saved = graph.get_state(config)
            print(f"A 实际 reply_count={result['reply_count']}；期望 1")
            print(
                f"A 实际角色顺序={[m.type for m in result['messages']]}；期望 ['human', 'ai']"
            )
            print(f"A 检查点里的 reply_count={saved.values['reply_count']}；期望 1")
            return

        # 主程序只阻止拿错旧 ID；B 函数仍须自己判断新旧会话的输入形状。
        before = graph.get_state(config)
        old_values = before.values if before is not None else {}
        if args.phase == "first" and old_values:
            raise SystemExit("这个 ticket_id 已有状态；请为 first 换一个新 ID")
        if args.phase == "followup" and not old_values:
            raise SystemExit("没有这个旧工单；先运行 first，并核对 ticket_id")
        old_message_count = len(old_values.get("messages", []))
        expected_old_count = 0 if args.phase == "first" else 2
        print(
            f"B 本轮开始前检查点里的旧消息数={old_message_count}；"
            f"期望 {expected_old_count}"
        )

        detail = (
            "云杉耳机左声道无声"
            if args.phase == "first"
            else "补充：换过数据线后仍无声音"
        )
        result = submit_ticket_update(graph, ticket_id, detail)
        expected_count = 1 if args.phase == "first" else 2
        expected_roles = ["human", "ai"] * expected_count
        saved = graph.get_state(config)
        print(f"B 实际 reply_count={result['reply_count']}；期望 {expected_count}")
        print(
            f"B 实际角色顺序={[m.type for m in result['messages']]}；期望 {expected_roles}"
        )
        print(f"B 消息自身 ID={[m.id for m in result['messages']]}")
        print(
            f"B 磁盘检查点 reply_count={saved.values['reply_count']}；期望 {expected_count}"
        )

    if args.phase == "first":
        print("\n关闭本次 Python 进程，再运行：")
        print(
            ".venv\\Scripts\\python.exe -B "
            "weeks\\week04_frameworks\\day32_checkpoint_exercises.py "
            f"--part b --phase followup --ticket-id {ticket_id}"
        )


if __name__ == "__main__":
    main()


# === 现象与原因 ===
# 1. 只看同一工单的 B followup 输出：开始前有几条旧消息？ticket 节点进入时
#    看到几条消息、reply_count 是多少？再看你写的 message 字典：本轮传给
#    invoke 的 input 有哪些键，没重传的旧消息与旧次数从哪里来？
# 我的回答：
#   开始有2条旧消息，ticket进入时看到3条，reply_count是1
#   传给input的只有message键，没重传的旧消息与旧次数是invoke(..., config)按同一thread_id通过保存器恢复的
# 2. 用一个没用过的 --ticket-id 再运行 B first。分别记录「原工单 followup」
#    和「新工单 first」的最终角色顺序、reply_count。两次用同一 SQLite 文件，
#    为什么新工单没有接上原工单？
# 我的回答：
#   原工单 followup： ['human', 'ai', 'human', 'ai']，reply_count=2
#   新工单 first：['human', 'ai']， reply_count=1；
#   因为两次的thread_id不同，
# 3. 对照输出里的「工单会话 thread_id」与「B 消息自身 ID」：它们分别给什么编号？
#    如果只换 thread_id，文件与消息文字都不变，get_state 读到哪段会话？
# 我的回答：
#   工单会话 thread_id：ticket-08f0a632，是整个工单的编号
#   B 消息自身 ID=['2e16dc0d-febc-4a2f-a2ff-c7acd2412560', 'bf2e0dc5-a418-4c68-84d4-7750d6fe0ce0', 'b56e9055-c10e-4ca6-897e-14e23bcf4c9b', 'eacfc093-844e-4049-ba79-7aea0a5209ef']，是每条消息各自的编号
#   如果只换 thread_id，get_state会读到config 里当前 thread_id 对应的会话
# 4. 对照你写的 graph.get_state 与 graph.invoke：哪个只读取旧状态，哪个运行图？
#    在两次输出中，哪一行能证明 ticket 节点真的执行了？
# 我的回答：
#   graph.get_state只读取旧状态，graph.invoke运行图
#   ticket 节点进入时：已有 3 条消息，reply_count=1；最新内容=补充：换过数据线后仍无声音
