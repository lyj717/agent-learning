"""Day 33：为本地配送申请加人工确认，再恢复执行。

运行 --part a 只观察暂停；运行 --part b 对照批准、拒绝和同编号重复请求。
阅读顺序：DispatchState → request_review → resume_dispatch。
图的接线、模拟动作和命令行对照由 AI 给出，审核与恢复函数由学员完成。
这里只改 Python 列表模拟外部配送系统，不会真的发货或调用网络。
"""

import argparse
from typing import Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt

ACTION_LOG: list[str] = []


class DispatchState(TypedDict):
    """配送申请：申请编号、内容、审核结果与实际执行次数。"""

    request_id: str
    summary: str
    approved: bool
    action_count: int


def request_review(state: DispatchState) -> dict:
    """暂停配送申请，得到人工决定后更新 approved。"""
    print("进入review")
    decision = interrupt(
        {
            "question": "允许执行配送吗？",
            "request_id": state["request_id"],
            "summary": state["summary"],
        }
    )
    return {"approved": decision == "allow"}


def resume_dispatch(
    graph: CompiledStateGraph, request_id: str, decision: str
) -> DispatchState:
    """把人的 allow 或 deny 决定送回已暂停的同一会话。"""
    config = {"configurable": {"thread_id": request_id}}
    return graph.invoke(Command(resume=decision), config=config)


def choose_after_review(state: DispatchState) -> Literal["record", "stop"]:
    """AI 给定的条件选择：批准才去执行，否则结束。"""
    # Literal 只标明本函数会返回哪两个字符串；运行时返回值仍是普通str。
    return "record" if state["approved"] else "stop"


def record_dispatch(state: DispatchState) -> dict:
    """AI 给定的模拟动作：同一申请编号在本进程里只记录一次。"""
    if state["request_id"] not in ACTION_LOG:
        ACTION_LOG.append(state["request_id"])
        print(f"    模拟配送已执行：{state['request_id']}")
    else:
        print(f"    相同申请已记录，跳过重复动作：{state['request_id']}")
    return {"action_count": len(ACTION_LOG)}


def build_graph(checkpointer: SqliteSaver) -> CompiledStateGraph:
    """AI 给定的路线：审核 → 批准则执行，拒绝则结束。"""
    builder = StateGraph(DispatchState)
    builder.add_node("review", request_review)
    builder.add_node("record", record_dispatch)
    builder.add_edge(START, "review")
    builder.add_conditional_edges(
        "review", choose_after_review, {"record": "record", "stop": END}
    )
    builder.add_edge("record", END)
    return builder.compile(checkpointer=checkpointer)


def run_case(request_id: str, decision: str | None) -> None:
    """AI 给定的对照：先暂停，B 再恢复；每组都从空内存数据库开始。"""
    # clear() 清空上一个案例的模拟动作；每组都要单独从 0 次开始。
    ACTION_LOG.clear()
    config = {"configurable": {"thread_id": request_id}}
    initial: DispatchState = {
        "request_id": request_id,
        "summary": "云杉耳机维修件发往客户",
        "approved": False,
        "action_count": 0,
    }
    with SqliteSaver.from_conn_string(":memory:") as saver:
        graph = build_graph(saver)
        print(f"  本组 thread_id={request_id}")
        first = graph.invoke(initial, config)
        pending = graph.get_state(config)
        print(f"  暂停问题={first['__interrupt__'][0].value}")
        print(f"  暂停后 next={pending.next}；期望 ('review',)")
        print(f"  暂停后动作数={len(ACTION_LOG)}；期望 0")
        if decision is None:
            return

        final = resume_dispatch(graph, request_id, decision)
        expected = 1 if decision == "allow" else 0
        print(
            f"  人的回答={decision}；最终 approved={final['approved']}；"
            f"期望 {decision == 'allow'}"
        )
        print(f"  最终 action_count={final['action_count']}；期望 {expected}")
        print(f"  外部动作数={len(ACTION_LOG)}；期望 {expected}")
        print(f"  完成后 next={graph.get_state(config).next}；期望 ()")

        if decision == "allow":
            # 额外模拟同一业务编号的重复请求，检查给定动作函数的去重效果。
            record_dispatch(final)
            print(f"  同编号重复请求后外部动作数={len(ACTION_LOG)}；期望 1")


def main() -> None:
    """按 --part 选择只观察暂停，或继续核对批准与拒绝。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b"), default="a")
    args = parser.parse_args()

    if args.part == "a":
        print("=== A：只暂停，不给决定 ===")
        run_case("dispatch-a", None)
        return

    print("=== B1：人批准 ===")
    run_case("dispatch-allow", "allow")
    print("\n=== B2：人拒绝 ===")
    run_case("dispatch-deny", "deny")


if __name__ == "__main__":
    main()


# === 现象与原因：学员运行并自己填写；今天没有另一份记录 md ===
# 1. A 首次暂停时，交给人的问题包含哪些字段？snapshot.next 是什么？
#    此时模拟配送执行了几次，哪一段代码还没运行？
# 我的回答：包括question,request_id和summary，snapshot.next是('review',)
#   此时模拟配送还没有执行
#   decision = interrupt({"question": "允许执行配送吗？",request_id": state["request_id"],"summary": state["summary"]})后的代码都没有执行
# 2. B 的 allow 和 deny 各得到什么 approved、action_count 和外部动作数？
#    为什么 deny 不会进入 record 节点？
# 我的回答：
#   allow:approved = True action_count = 1, 外部动作数 = 1
#   deny:approved = False action_count = 0, 外部动作数 = 0
#   因为deny会导致approved为false，从而在choose_after_review中返回了stop
# 3. 对照你在 request_review 里打印的「进入 review」：每组从暂停到恢复，
#    这行共打印几次？它和实际配送次数为什么不一样？
# 我的回答：
#   每组都打印了两次，因为interrupt在得到值后会从头开始运行review节点，所以暂停和恢复都会运行一次print("进入review")
#   配送在record节点里执行，第一次暂停并没有执行这个节点，所以配送次数和进入review的次数不同
# 4. B1 最后模拟同编号重复请求后，外部动作数有没有增加？
#    这里的 ACTION_LOG 只在本进程有效；真实发货或转账要靠什么编号防重？
# 我的回答：
#   没有增加，靠一次具体业务操作的唯一编号防重
