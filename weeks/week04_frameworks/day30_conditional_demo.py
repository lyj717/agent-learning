"""Day 30：节点写完状态后，条件边怎样决定下一站。

阅读顺序：main → DeliveryState → fixed_model_reply → choose_next → check_rule → build_demo_graph。
直接运行即可；请求和规则都是固定教学数据，不调用模型或联网服务。
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


def main() -> None:
    """先讲条件边，再运行普通与加急两条路线。"""
    print("=== 1. 这是什么 ===")
    print("Day 29 的固定边总去同一站；条件边会在节点完成后读状态，选择下一站。")
    print("节点返回要写入状态的字典；选路函数只返回节点名或 END，不负责改状态。")

    print("\n=== 2. 为什么需要它 ===")
    print("Day 27 的 if 根据模型本轮结果决定：点工具就执行工具，答完就结束。")
    print("图里也要保留这个判断，不能把模型节点同时固定连向工具和结束。")

    print("\n=== 3. 场景 ===")
    print("固定假模型对两条配送请求给出不同决定：普通请求结束，加急请求核对示例规则。")
    print("决定来自下面的教学表，不是真实模型或服务商原生字段。")
    print("路线：START → model；普通 → END，加急 → check_rule → END。")

    print("\n=== 4. 代码与实际输出 ===")
    print("build_demo_graph 注册节点、固定入口和条件边，再 compile；此时尚未处理请求。")
    graph = build_demo_graph()
    for request, expected_trace in [
        ("普通配送云杉卡纸", ["收到请求", "示意模型返回"]),
        ("加急配送云杉卡纸", ["收到请求", "示意模型返回", "核对规则"]),
    ]:
        initial: DeliveryState = {
            "request": request,
            "decision": "未返回",
            "answer": "",
            "trace": ["收到请求"],
        }
        print(f"\n请求：{request}；初始 decision={initial['decision']}")
        # invoke(初始状态)：沿图执行到 END，返回合并后的最终状态。
        result = graph.invoke(initial)
        print(f"最终答复：{result['answer']}")
        print(f"实际轨迹：{result['trace']}；期望：{expected_trace}")

    print("\n=== 5. 注意什么 ===")
    print("choose_next 读的是 model 写入的决定，不是初始的『未返回』。")
    print("返回 check_rule 才执行该节点；返回 END 就停止，不再运行核对节点。")
    print("END 是导入的终点标记，打印时是 __end__；不要手写字符串 'END'。")
    print("选路时遇到未知决定应报错，不能把它当成已经答完。")
    print("本例核对节点只接向 END。练习会把工具节点固定接回模型节点，让模型看到观察。")
    print("真实模型点单与工具观察是两条不同消息；本例没有实现这两类消息。")


class DeliveryState(TypedDict):
    """图共享的字段；今天所有初始字段都由 main 给出。"""

    request: str
    decision: str
    answer: str
    trace: list[str]


def fixed_model_reply(state: DeliveryState) -> dict:
    """从固定教学表取示意模型决定，交回字段更新。"""
    replies = {
        "普通配送云杉卡纸": ("done", "普通配送可按常规流程处理"),
        "加急配送云杉卡纸": ("check_rule", "等待核对加急规则"),
    }
    decision, answer = replies[state["request"]]
    print(f"  model 节点写入 decision={decision}")
    return {
        "decision": decision,
        "answer": answer,
        "trace": state["trace"] + ["示意模型返回"],
    }


def choose_next(state: DeliveryState) -> str:
    """根据更新后的状态返回下一节点名，或返回 END。"""
    if state["decision"] == "check_rule":
        destination = "check_rule"
    elif state["decision"] == "done":
        destination = END
    else:
        raise ValueError(f"未知的模型决定：{state['decision']}")
    print(f"  条件边读到 decision={state['decision']}，选择 {destination}")
    return destination


def check_rule(state: DeliveryState) -> dict:
    """用固定教学规则补全答复，不代表真实配送政策。"""
    print("  check_rule 节点被执行")
    return {
        "answer": "示例规则：加急请求须先核对截单时间",
        "trace": state["trace"] + ["核对规则"],
    }


def build_demo_graph() -> CompiledStateGraph:
    """连接固定入口、条件分支和核对后的终点。"""
    # StateGraph(状态类型)：创建图的构建器；DeliveryState 是类型，不是运行数据。
    builder = StateGraph(DeliveryState)
    # add_node(节点名, 函数)：注册处理状态的函数本身，不在这里调用函数。
    builder.add_node("model", fixed_model_reply)
    builder.add_node("check_rule", check_rule)
    # add_edge(起点, 终点)：固定连接；每次从 START 先到 model。
    builder.add_edge(START, "model")
    # add_conditional_edges(出发节点, 选路函数)：model 完成后才调用 choose_next。
    # choose_next 返回的节点名会成为下一站，返回 END 则停止。
    builder.add_conditional_edges("model", choose_next)
    builder.add_edge("check_rule", END)
    # compile()：检查连接并生成可以 invoke 的图；此时还没有执行节点。
    return builder.compile()


if __name__ == "__main__":
    main()
