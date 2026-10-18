"""Day 33 可选复习：节点 return 的字典怎样成为图状态更新。

同一个函数，先普通调用，再注册为节点运行；只比较是谁把更新写进状态。
不使用 interrupt、保存器或人工恢复。阅读顺序：main → approve_node → inspect_node。
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ApprovalState(TypedDict):
    """图管理的两项数据。"""

    request_id: str
    approved: bool


def main() -> None:
    """对照普通返回值和由图执行的状态更新。"""
    print("=== 1. 这是什么 ===")
    print("StateGraph 约定：节点返回的字典，是对图状态的更新。")
    print(
        "字典的键指定更新哪个字段；这里 approved 没有自定义合并规则，所以新值替换旧值。"
    )

    print("\n=== 2. 为什么需要它 ===")
    print("节点只负责给出自己改变的字段，图负责把更新应用好，再交给下一步。")

    print("\n=== 3. 场景 ===")
    print("一份申请原来 approved=False；审核函数给出 {'approved': True}。")
    print("申请编号 request_id 没有被更新，应继续保留。")
    initial: ApprovalState = {"request_id": "application-18", "approved": False}

    print("\n=== 4.1 先当普通 Python 函数调用 ===")
    update = approve_node(initial)
    print(f"调用者得到的返回字典：{update}")
    print(f"原来的 initial：{initial}，approved 仍是 False。")

    print("\n=== 4.2 再让 StateGraph 运行同一个函数 ===")
    # Day 29 已学的支持环境：声明状态字段、注册节点、连接顺序，再编译。
    builder = StateGraph(ApprovalState)
    builder.add_node("approve", approve_node)
    builder.add_node("inspect", inspect_node)
    builder.add_edge(START, "approve")
    builder.add_edge("approve", "inspect")
    builder.add_edge("inspect", END)
    graph = builder.compile()
    # invoke 把输入交给图；图会接收每个节点的返回字典并应用状态更新。
    final = graph.invoke(initial)
    print(f"图最后交回的状态：{final}")

    print("\n=== 5. 注意什么 ===")
    print("return 只交回字典；注册为节点并由图运行后，图才按字段名应用这个更新。")
    print("返回 {'approved': True} 只替换 approved；没返回的 request_id 继续保留。")
    print("TypedDict 的类型注解说明有哪些字段；执行状态更新的是 LangGraph。")


def approve_node(state: ApprovalState) -> dict:
    """只交回 approved 的新值，没有直接修改收到的字典。"""
    print(f"    审核函数收到 approved={state['approved']}")
    return {"approved": True}


def inspect_node(state: ApprovalState) -> dict:
    """观察图已更新的状态，不再修改任何字段。"""
    print(f"    下一节点读到 approved={state['approved']}")
    print(f"    下一节点仍读到 request_id={state['request_id']}")
    return {}


if __name__ == "__main__":
    main()
