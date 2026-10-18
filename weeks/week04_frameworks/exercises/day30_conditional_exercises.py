"""Day 30：把手写 Agent 的选路判断接成条件边。

直接运行对照选路结果；加 --part b 对照图的完整执行路线。
本文件的“模型回复”和本地查询都使用固定教学数据，不请求真实模型或网络。
点单字典只保留本课要用的字段，不是服务商原生响应的完整形状。
"""

import argparse
from copy import deepcopy
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


class AgentRouteState(TypedDict):
    """main 给齐初始字段；AI 提供的节点负责更新消息、查询进度与轨迹。"""

    question: str
    checks: list[str]  # 需要做的本地查询名；教学数据只使用 lookup_price、lookup_stock
    next_check: int
    messages: list[dict]
    finish_reason: str | None
    answer: str | None
    trace: list[str]


def route_after_model(state: AgentRouteState) -> str:
    """根据模型本轮点单与结束原因，选择工具节点或终点。"""
    if state["finish_reason"] == "tool_calls" and state["messages"][-1]["tool_calls"]:
        next_node = "tool"
    elif state["finish_reason"] == "stop" and not state["messages"][-1]["tool_calls"]:
        next_node = END
    else:
        raise ValueError("结束原因与最新点单列表矛盾！")
    return next_node


def build_agent_route_graph() -> CompiledStateGraph:
    """连接模型的条件边，以及工具返回模型的固定边。"""
    builder = StateGraph(AgentRouteState)
    builder.add_node("model", fixed_model_node)
    builder.add_node("tool", run_local_tool)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", route_after_model)
    builder.add_edge("tool", "model")
    return builder.compile()


TOOL_RESULTS = {
    "lookup_price": "云杉卡纸每包 9 元",
    "lookup_stock": "云杉卡纸还剩 12 包",
}


def fixed_model_node(state: AgentRouteState) -> dict:
    """AI 提供的固定假模型节点：生成一条点单或最终答复。"""
    if state["next_check"] < len(state["checks"]):
        check_name = state["checks"][state["next_check"]]
        call = {"id": f"lookup_{state['next_check'] + 1}", "name": check_name}
        reply = {"role": "assistant", "content": "", "tool_calls": [call]}
        print(f"  model 节点发出 assistant 点单：{call}")
        return {
            "messages": state["messages"] + [reply],
            "finish_reason": "tool_calls",
            "trace": state["trace"] + ["模型点单"],
        }

    observations = [
        message["content"] for message in state["messages"] if message["role"] == "tool"
    ]
    answer = "；".join(observations) if observations else "无需查询本地资料"
    reply = {"role": "assistant", "content": answer, "tool_calls": []}
    print(f"  model 节点给出最终答复：{answer}")
    return {
        "messages": state["messages"] + [reply],
        "finish_reason": "stop",
        "answer": answer,
        "trace": state["trace"] + ["模型答复"],
    }


def run_local_tool(state: AgentRouteState) -> dict:
    """AI 提供的本地工具节点：执行点单，回填带相同 ID 的观察。"""
    call = state["messages"][-1]["tool_calls"][0]
    # TOOL_RESULTS[工具名]：查固定教学表；不是网络查询或模型推断。
    observation = TOOL_RESULTS[call["name"]]
    tool_message = {
        "role": "tool",
        "tool_call_id": call["id"],
        "content": observation,
    }
    print(f"  tool 节点执行本地查询：{call['name']}；观察 ID={call['id']}")
    return {
        "messages": state["messages"] + [tool_message],
        "next_check": state["next_check"] + 1,
        "trace": state["trace"] + ["工具观察"],
    }


def main() -> None:
    """A 单独核对选路；B 对照零次、一次、两次工具执行。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b"), default="a")
    part = parser.parse_args().part
    if part == "a":
        old_call = {"id": "old_1", "name": "lookup_price"}
        current_call = {"id": "lookup_1", "name": "lookup_stock"}
        route_cases = [
            (
                "本轮点单",
                "tool_calls",
                [{"role": "assistant", "content": "", "tool_calls": [current_call]}],
                "tool",
            ),
            (
                "直接答复",
                "stop",
                [{"role": "assistant", "content": "已答复", "tool_calls": []}],
                END,
            ),
            (
                "先前点单、这轮已经答复",
                "stop",
                [
                    {"role": "assistant", "content": "", "tool_calls": [old_call]},
                    {"role": "tool", "tool_call_id": "old_1", "content": "已查询"},
                    {"role": "assistant", "content": "已答复", "tool_calls": []},
                ],
                END,
            ),
            (
                "结束原因说点单，最新消息却没有点单",
                "tool_calls",
                [{"role": "assistant", "content": "", "tool_calls": []}],
                "ValueError",
            ),
        ]
        for label, finish_reason, messages, expected in route_cases:
            state: AgentRouteState = {
                "question": "云杉卡纸库存如何？",
                "checks": [],
                "next_check": 0,
                "messages": messages,
                "finish_reason": finish_reason,
                "answer": None,
                "trace": [],
            }
            before = deepcopy(state)
            try:
                actual = route_after_model(state)
            except ValueError:
                actual = "ValueError"
            older_calls = sum(
                len(message["tool_calls"])
                for message in messages[:-1]
                if message["role"] == "assistant"
            )
            print(f"{label}：实际下一站 {actual}；期望 {expected}")
            print(
                f"  结束原因 {finish_reason}；历史点单数 {older_calls}；"
                f"最新消息点单数 {len(messages[-1]['tool_calls'])}；原输入未修改 {state == before}"
            )
        return

    graph = build_agent_route_graph()
    cases = [
        (
            "直接回答",
            [],
            "无需查询本地资料",
            ["收到问题", "模型答复"],
            ["user", "assistant"],
        ),
        (
            "查一次库存",
            ["lookup_stock"],
            "云杉卡纸还剩 12 包",
            ["收到问题", "模型点单", "工具观察", "模型答复"],
            ["user", "assistant", "tool", "assistant"],
        ),
        (
            "先查价格再查库存",
            ["lookup_price", "lookup_stock"],
            "云杉卡纸每包 9 元；云杉卡纸还剩 12 包",
            ["收到问题", "模型点单", "工具观察", "模型点单", "工具观察", "模型答复"],
            ["user", "assistant", "tool", "assistant", "tool", "assistant"],
        ),
    ]
    for label, checks, expected_answer, expected_trace, expected_roles in cases:
        initial: AgentRouteState = {
            "question": "云杉卡纸有哪些资料？",
            "checks": checks,
            "next_check": 0,
            "messages": [{"role": "user", "content": "云杉卡纸有哪些资料？"}],
            "finish_reason": None,
            "answer": None,
            "trace": ["收到问题"],
        }
        before = deepcopy(initial)
        print(f"\n=== {label}；计划本地查询 {checks} ===")
        result = graph.invoke(initial)
        roles = [message["role"] for message in result["messages"]]
        call_ids = [
            call["id"]
            for message in result["messages"]
            if message["role"] == "assistant"
            for call in message["tool_calls"]
        ]
        observation_ids = [
            message["tool_call_id"]
            for message in result["messages"]
            if message["role"] == "tool"
        ]
        print(f"实际角色顺序：{roles}；期望：{expected_roles}")
        print(f"assistant 点单 ID：{call_ids}；tool 观察 ID：{observation_ids}")
        print(f"实际轨迹：{result['trace']}；期望：{expected_trace}")
        print(f"实际答复：{result['answer']}；期望：{expected_answer}")
        print(f"已执行查询数：{result['next_check']}；期望：{len(checks)}")
        print(f"原输入未修改：{initial == before}；期望：True")


if __name__ == "__main__":
    main()

# === 现象与原因：自己运行后填写；今天没有另一份交付物 md ===
# 1. A 的第三组历史中有点单，为什么下一站仍是 END？请指出本轮实际看的字段。
# 我的回答：
#   第三组的"tool_calls"已经为[]了，并且finsh_reason为stop，说明下一次不需要调用工具，下一站便为END
#    实际看最新消息的“tool_calls"以及finish_reason这两个字段
# 2. B 的零次、一次、两次查询，各有几次 model 节点和 tool 节点？
#    哪一组输出证明工具观察后回到了模型，而不是工具执行后直接结束？
# 我的回答：
#   零次：1个model节点和0个tool节点
#   一次：2个model节点和1个tool节点
#   两次：3个model节点和2个tool节点
#   轨迹为['收到问题', '模型点单', '工具观察', '模型答复']，而不是工具观察之后就结束了
# 3. 指出一次 assistant 点单 ID 和对应 tool 观察 ID；它们各是哪种消息？
#    为什么不能说 tool 节点“发出了模型点单”？
# 我的回答：
#   assistant 点单 ID：['lookup_1']；tool 观察 ID：['lookup_1']
#   点单id是assistant的消息，tool观察是tool的消息
#   因为模型点单不是由tool节点发出的，是model节点发出的
# 4. 本课为何让节点返回完整的新 messages、trace 列表？对照 Day 29 的
#    day29_state_demo.py 输出：若只返回新的一条，默认字段更新会把旧项怎样处理？
# 我的回答：
#   为了保证消息和轨迹的完整性如果只返回新的一条，若只返回新的一条，每条新的消息会覆盖原有的消息
