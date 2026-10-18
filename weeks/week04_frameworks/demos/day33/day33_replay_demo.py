"""Day 33 知识点：恢复时，包含 interrupt 的节点从哪里重新执行。

这份只用 before/after 两种记录定位执行顺序，没有公告、审批状态或动作去重。
阅读顺序：main，重点看 probe_node 中 interrupt 前后的两条 append。
"""

from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ProbeState(TypedDict):
    """只标记节点是否已完整执行完。"""

    done: bool


def main() -> None:
    """用两条位置记录证明节点恢复时从开头重跑。"""
    print("=== 1. 这是什么 ===")
    print("节点重跑：恢复中断时，框架会重新进入含 interrupt 的那个节点。")
    print("它先执行节点开头，再让 interrupt 取回已经提供的回答。")

    print("\n=== 2. 为什么需要知道 ===")
    print("写在 interrupt 前的代码会再执行一次，理解这一点才能放对有影响的操作。")

    print("\n=== 3. 场景 ===")
    print("before 代表经过 interrupt 前一行；after 代表经过后一行。")
    print("这两条记录只定位执行位置，不模拟任何实际业务动作。")

    print("\n=== 4. 代码与真实输出 ===")
    events: list[str] = []

    def probe_node(_state: ProbeState) -> dict:
        """在暂停调用前后各留下一个位置标记。"""
        # 这里使用 main 中创建的同一份 events 列表，两次进节点的记录会保留在一起。
        events.append("before")
        interrupt("现在可以继续吗？")
        events.append("after")
        return {"done": True}

    # 已学过的运行环境：单节点图、内存 SQLite 保存器和固定会话。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        builder = StateGraph(ProbeState)
        builder.add_node("probe", probe_node)
        builder.add_edge(START, "probe")
        builder.add_edge("probe", END)
        graph = builder.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": "replay-position-example"}}

        graph.invoke({"done": False}, config)
        print(f"4.1 首次暂停后 events={events}")
        print("    只经过 before，尚未到 after。")

        # 此处复用已学过的恢复调用，观察位置记录，不增加业务处理。
        final = graph.invoke(Command(resume=True), config)
        print(f"4.2 恢复后 events={events}")
        print(
            f"    before 共 {events.count('before')} 次，"
            f"after 共 {events.count('after')} 次，done={final['done']}。"
        )

    print("\n=== 5. 注意什么 ===")
    print("before 重复，说明节点从开头重跑；after 此时只经过一次。")
    print("若 before 那一行换成发货或扣款，就会在获准继续前先产生影响。")
    print("本知识点只解释重跑位置；如何识别重复动作由副作用与幂等演示单独说明。")


if __name__ == "__main__":
    main()
