"""Day 34：用 LangGraph 实现带工具、预算与停止判断的单任务 Agent。"""

import argparse
import sys
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Literal, TypedDict

# 支持从仓库根目录或 exercises 目录直接运行，跨目录模块使用明确的包路径。
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    ToolMessage,
    convert_to_messages,
    convert_to_openai_messages,
)
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from weeks.week04_frameworks.demos.day34 import day34_support as support


class AgentState(TypedDict):
    """单任务 Agent 的消息、轨迹、用量与运行限制。"""

    # messages 沿用 Day 31；节点只返回本轮新消息，旧项由图合并。
    messages: Annotated[list[AnyMessage], add_messages]
    # 下面两个普通列表没有 reducer，返回更新时须自行保留旧项。
    trace: list[dict]  # 四种事件的字段见 support.TRACE_GUIDE，或直接运行支持文件查看。
    usages: list[dict | None]
    steps: int  # 已尝试的模型请求次数，不是节点执行次数。
    answer: str | None
    stop_reason: str | None
    scenario: str  # 指定 support.request_model 使用哪一组教学情境。
    limits: dict  # 键与默认值见 support.DEFAULT_LIMITS。
    started_at: float  # 本任务开始时的单调时钟读数，今天只在同一进程使用。


def model_node(
    state: AgentState, *, chat_fn: Callable[..., dict] = support.request_model
) -> dict:
    """执行一次模型请求；chat_fn 默认离线，Day35 可传入同接口的真实请求函数。"""
    step = state["steps"]
    trace = state["trace"].copy()
    now = time.monotonic()
    time_dict = support.plan_next_call(
        started_at=state["started_at"],
        now=now,
        task_limit=state["limits"]["task_limit_seconds"],
        call_limit=state["limits"]["call_limit_seconds"],
    )
    if time_dict["stop_reason"] == "task_timeout":
        trace.append({"step": step, "event": "stop", "reason": "task_timeout"})
        return {
            "messages": [],
            "trace": trace,
            "usages": state["usages"],
            "steps": step,
            "answer": None,
            "stop_reason": "task_timeout",
        }
    try:
        message_dict = chat_fn(
            messages=convert_to_openai_messages(state["messages"]),
            scenario=state["scenario"],
            timeout_seconds=time_dict["next_timeout"],
        )
    except TimeoutError:
        trace.append(
            {"step": step + 1, "event": "request", "finish_reason": None, "usage": None}
        )
        trace.append({"step": step + 1, "event": "stop", "reason": "call_timeout"})
        return {
            "messages": [],
            "trace": trace,
            "usages": state["usages"],
            "steps": step + 1,
            "answer": None,
            "stop_reason": "call_timeout",
        }
    message = message_dict["message"]
    usage = message_dict["usage"]
    finish_reason = message_dict["finish_reason"]
    trace.append(
        {
            "step": step + 1,
            "event": "request",
            "finish_reason": finish_reason,
            "usage": usage,
        }
    )
    if finish_reason == "stop":
        trace.append(
            {
                "step": step + 1,
                "event": "final",
                "answer": message["content"],
            }
        )
        return {
            "messages": convert_to_messages([message]),
            "trace": trace,
            "usages": state["usages"] + [usage],
            "steps": step + 1,
            "answer": message["content"],
            "stop_reason": "final_answer",
        }
    return {
        "messages": convert_to_messages([message]),
        "trace": trace,
        "usages": state["usages"] + [usage],
        "steps": step + 1,
        "answer": None,
        "stop_reason": None,
    }


def tools_node(state: AgentState) -> dict:
    """执行本轮全部工具点单，返回观察消息与工具轨迹。"""
    trace = state["trace"].copy()
    step = state["steps"]
    messages = []
    calls = convert_to_openai_messages(state["messages"][-1])["tool_calls"]
    for call in calls:
        name = call["function"]["name"]
        arguments = call["function"]["arguments"]
        tool_message = support.execute_call(
            call=call, allow_code=state["limits"]["allow_code"]
        )
        trace.append(
            {
                "step": step,
                "event": "tool",
                "tool": name,
                "arguments": arguments,
                "tool_call_id": tool_message["tool_call_id"],
                "observation": tool_message["content"],
            }
        )
        messages.append(tool_message)
    return {"messages": convert_to_messages(messages), "trace": trace}


def check_limits(state: AgentState) -> dict:
    """按无进展重复、预算和请求次数判断是否停止。"""
    limits = state["limits"]
    trace = state["trace"].copy()
    step = state["steps"]
    tool_trace = []
    for t in trace:
        if t["event"] == "tool":
            tool_trace.append(t)
    if (
        support.repeat_stop_reason(
            trace=tool_trace, repeat_limit=limits["repeat_limit"]
        )
        == "repeated_call"
    ):
        trace.append({"step": step, "event": "stop", "reason": "repeated_call"})
        return {"trace": trace, "stop_reason": "repeated_call"}
    summary = support.summarize_usage(
        usages=state["usages"], price=support.TEACHING_PRICE
    )
    stop_reason = support.stop_before_next_request(
        summary=summary,
        total_token_limit=limits["token_limit"],
        cost_limit_yuan=limits["cost_limit_yuan"],
    )
    if stop_reason is not None:
        trace.append({"step": step, "event": "stop", "reason": stop_reason})
        return {
            "stop_reason": stop_reason,
            "trace": trace,
        }
    if step >= limits["max_steps"]:
        trace.append({"step": step, "event": "stop", "reason": "max_steps"})
        return {
            "stop_reason": "max_steps",
            "trace": trace,
        }
    return {
        "stop_reason": None,
        "trace": trace,
    }


def route_after_model(state: AgentState) -> Literal["tools", "end"]:
    """根据模型节点的停止状态选择工具或结束。"""
    return "tools" if state["stop_reason"] is None else "end"


def route_after_limits(state: AgentState) -> Literal["model", "end"]:
    """根据停止判断选择继续请求模型或结束。"""
    return "model" if state["stop_reason"] is None else "end"


def build_agent_graph() -> CompiledStateGraph:
    """连接模型、工具与停止判断节点，编译单任务图。"""
    builder = StateGraph(AgentState)
    builder.add_node("model", model_node)
    builder.add_node("tools", tools_node)
    builder.add_node("check", check_limits)
    builder.add_edge(START, "model")
    builder.add_conditional_edges(
        "model", route_after_model, {"tools": "tools", "end": END}
    )
    builder.add_edge("tools", "check")
    builder.add_conditional_edges(
        "check", route_after_limits, {"model": "model", "end": END}
    )
    return builder.compile()


def run_graph_agent(question: str, *, scenario: str = "normal", **overrides) -> dict:
    """运行单任务图，返回答复、原生消息、轨迹与用量汇总。"""
    initial = make_initial(question=question, scenario=scenario, overrides=overrides)
    graph = build_agent_graph()
    results = graph.invoke(initial)
    return {
        "answer": results["answer"],
        "stop_reason": results["stop_reason"],
        "steps": results["steps"],
        "messages": convert_to_openai_messages(results["messages"]),
        "trace": results["trace"],
        "usage": support.summarize_usage(
            usages=results["usages"], price=support.TEACHING_PRICE
        ),
    }


# 以下为运行检查与对照输出。
def make_initial(
    question: str, *, scenario: str = "normal", overrides: dict | None = None
) -> AgentState:
    """为每个独立任务准备完整的初始状态。"""
    limits = {**support.DEFAULT_LIMITS, **(overrides or {})}
    if type(limits["max_steps"]) is not int or limits["max_steps"] < 1:
        raise ValueError("max_steps 必须是正整数")
    return {
        "messages": [HumanMessage(content=question)],
        "trace": [],
        "usages": [],
        "steps": 0,
        "answer": None,
        "stop_reason": None,
        "scenario": scenario,
        "limits": limits,
        # monotonic() 读取不会受校时影响的秒数；两次读数之差用于计算经过时间。
        "started_at": time.monotonic(),
    }


def apply_for_inspection(state: AgentState, update: dict) -> AgentState:
    """合并节点的部分更新，供单节点检查使用。"""
    # add_messages 会给没有消息 ID 的对象补 ID；检查环境不能因此改动被测原输入。
    old = deepcopy(state)
    new = deepcopy(update)
    result = {**old, **new}
    if "messages" in new:
        result["messages"] = add_messages(old["messages"], new["messages"])
    return result


def print_state(state: AgentState) -> None:
    """打印状态、消息身份与完整轨迹。"""
    print(f"  steps={state['steps']}；stop_reason={state['stop_reason']}")
    print(f"  answer={state['answer']}")
    summary = support.summarize_usage(state["usages"], price=support.TEACHING_PRICE)
    print(f"  已收到响应的用量记录汇总={summary}")
    for index, message in enumerate(state["messages"], start=1):
        print(f"  消息{index}：type={message.type}；内容={message.content!r}")
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                print(
                    f"    assistant 点单 id={call['id']}；{call['name']}({call['args']})"
                )
        elif isinstance(message, ToolMessage):
            print(f"    tool 对应点单 id={message.tool_call_id}")
    for event in state["trace"]:
        print(f"  轨迹：{event}")


def inspect_model() -> None:
    """打印模型节点的三组检查结果。"""
    cases = [
        ("正常点单", "normal", {}, "1, None；新增一条 ai；尚无 tool"),
        ("任务一开始已到期", "normal", {"task_limit_seconds": 0.0}, "0, task_timeout"),
        ("单次请求超时", "slow_model", {"call_limit_seconds": 0.05}, "1, call_timeout"),
    ]
    for label, scenario, overrides, expected in cases:
        state = make_initial(support.QUESTION, scenario=scenario, overrides=overrides)
        before = deepcopy(state)
        print(f"\n=== A {label}；期望 steps, stop_reason：{expected} ===")
        update = model_node(state)
        print(f"  返回字段={sorted(update)}")
        print(
            "  期望字段=['answer', 'messages', 'steps', 'stop_reason', 'trace', 'usages']"
        )
        print_state(apply_for_inspection(state, update))
        print(f"  原输入未修改={state == before}；期望 True")


def inspect_tools() -> None:
    """打印工具节点的五组检查结果。"""
    cases = [
        (
            "单条检索",
            [("search_notes", {"keyword": "蓝湾便签", "limit": 2})],
            False,
            "catalog.txt:2 与 stock.txt:2 两条命中，作为一条 tool 的 JSON 正文",
        ),
        (
            "同轮两条计算",
            [
                ("calculator", {"expression": "22 * 3"}),
                ("calculator", {"expression": "27 / 3"}),
            ],
            False,
            "两条 tool 正文分别是数值 66、9 的 JSON 文本",
        ),
        (
            "坏参数",
            [("calculator", {"expression": ["22", "3"]})],
            False,
            "工具执行失败的错误文字，仍保留本条调用 ID",
        ),
        (
            "未获代码权限",
            [("run_code", {"code": "22 * 3"})],
            False,
            "PermissionError 错误文字，代码未执行",
        ),
        (
            "已获代码权限",
            [("run_code", {"code": "22 * 3"})],
            True,
            "JSON 对象中 ok=true、value=66",
        ),
    ]
    for case_number, (label, specs, allow_code, expected_content) in enumerate(
        cases, start=1
    ):
        state = make_initial(
            "这是工具节点的固定输入", overrides={"allow_code": allow_code}
        )
        calls = [
            {"id": f"fixture-{case_number}-{index}", "name": name, "args": args}
            for index, (name, args) in enumerate(specs, start=1)
        ]
        state["messages"].append(AIMessage(content="", tool_calls=calls))
        state["steps"] = 1
        state["usages"] = [{"prompt_tokens": 19, "completion_tokens": 7}]
        state["trace"] = [
            {
                "step": 1,
                "event": "request",
                "finish_reason": "tool_calls",
                "usage": state["usages"][0],
            }
        ]
        before = deepcopy(state)
        print(
            f"\n=== B {label}；期望 {len(calls)} 条新 tool，steps 仍为 1，answer=None ==="
        )
        print(f"  本组正文期望：{expected_content}")
        update = tools_node(state)
        print_state(apply_for_inspection(state, update))
        print(f"  原输入未修改={state == before}；期望 True")


def inspect_limits() -> None:
    """打印停止判断的结果与预期对照。"""
    first = {
        "step": 1,
        "event": "tool",
        "tool": "search_notes",
        "arguments": '{"keyword":"缺货商品","limit":2}',
        "tool_call_id": "fixture-old",
        "observation": "[]",
    }
    repeated = {
        **first,
        "step": 2,
        "arguments": '{"limit":2,"keyword":"缺货商品"}',
        "tool_call_id": "fixture-new",
    }
    changed = {**repeated, "observation": '[{"text":"新增库存 3 件"}]'}
    cases = [
        (
            "参数键顺序和调用ID变了，观察没变",
            [first, repeated],
            [],
            {},
            "repeated_call",
        ),
        ("相同查询得到新观察", [first, changed], [], {}, None),
        (
            "重复与token阈值同时触发",
            [first, repeated],
            [{"prompt_tokens": 80, "completion_tokens": 20}],
            {"token_limit": 100},
            "repeated_call",
        ),
        (
            "token恰好达到阈值",
            [first],
            [{"prompt_tokens": 80, "completion_tokens": 20}],
            {"token_limit": 100},
            "token_budget",
        ),
        ("usage缺失", [first], [None], {}, "usage_unknown"),
        ("请求次数达到上限", [first, changed], [], {"max_steps": 2}, "max_steps"),
    ]
    for label, events, usages, overrides, expected in cases:
        state = make_initial("停止判断固定输入", overrides=overrides)
        state["trace"] = events
        state["usages"] = usages
        state["steps"] = events[-1]["step"]
        before = deepcopy(state)
        print(f"\n=== C {label}；期望 stop_reason={expected} ===")
        update = check_limits(state)
        print(f"  返回字段={sorted(update)}；期望 ['stop_reason', 'trace']")
        expected_events = (
            [{"step": before["steps"], "event": "stop", "reason": expected}]
            if expected is not None
            else []
        )
        returned_trace = update.get("trace")
        new_events = (
            returned_trace[len(before["trace"]) :]
            if isinstance(returned_trace, list)
            else None
        )
        print(f"  新增轨迹={new_events}；期望 {expected_events}")
        print(
            f"  完整轨迹符合期望={returned_trace == before['trace'] + expected_events}；"
            "期望 True（旧项原序保留，停止才追加一条）"
        )
        result = apply_for_inspection(state, update)
        print(f"  请求次数={result['steps']}；期望仍为 {before['steps']}")
        print_state(result)
        print(f"  原输入未修改={state == before}；期望 True")


def inspect_graph(case_number: int | None) -> None:
    """打印完整图各情境的结果与预期对照。"""
    stale = make_initial("旧点单已处理，本轮已答复")
    stale["messages"].extend(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "old-call",
                        "name": "calculator",
                        "args": {"expression": "3 * 4"},
                    }
                ],
            ),
            ToolMessage(content="12", tool_call_id="old-call"),
            AIMessage(content="结果是12。"),
        ]
    )
    stale["answer"] = "结果是12。"
    stale["stop_reason"] = "final_answer"
    print(f"旧点单仍在历史、本轮已答复：实际路由={route_after_model(stale)}；期望 end")
    for index, case in enumerate(support.CASES, start=1):
        if case_number is not None and index != case_number:
            continue
        print(f"\n=== D{index} {case['label']} ===")
        print(f"问题：{case['question']}；限制覆盖：{case['overrides']}")
        result = run_graph_agent(
            case["question"], scenario=case["scenario"], **case["overrides"]
        )
        tools = [m for m in result["messages"] if m["role"] == "tool"]
        print(f"  停止原因={result['stop_reason']}；期望 {case['expected_reason']}")
        print(f"  请求次数={result['steps']}；期望 {case['expected_steps']}")
        print(f"  tool观察数={len(tools)}；期望 {case['expected_tools']}")
        print(
            f"  最终答复={result['answer']!r}；期望包含 {case['answer_fragment']!r}（None表示无答复）"
        )
        print(f"  usage={result['usage']}")
        for message in result["messages"]:
            print(f"  原生消息：{message}")
        for event in result["trace"]:
            print(f"  轨迹：{event}")


def main() -> None:
    """按命令行选项运行单节点或整图检查。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b", "c", "d"), default="a")
    parser.add_argument(
        "--case", type=int, help="仅 D 使用，从 1 到 16 选择一组；不填则全部"
    )
    args = parser.parse_args()
    if args.case is not None and (
        args.part != "d" or not 1 <= args.case <= len(support.CASES)
    ):
        parser.error("--case 仅用于 --part d，编号为 1～16")
    if args.part == "a":
        inspect_model()
    elif args.part == "b":
        inspect_tools()
    elif args.part == "c":
        inspect_limits()
    else:
        inspect_graph(args.case)


if __name__ == "__main__":
    main()


# === 闭卷短题：先不看旧实现，各用几句话或几行伪代码回答 ===
# 1. messages 只返回一条新消息，trace 也只返回一条新事件，旧内容都会保留吗？为什么？
# 我的回答：
#   messages 通过 add_messages 保留旧消息；trace 没有合并规则，旧列表会被替换
# 2. 两次工具名和参数相同，但观察由“缺货”变成“有货”，能判 repeated_call 吗？
#    与“参数键顺序不同、观察仍是缺货”的情境有何不同？
# 我的回答：
#   不能，观察变化就说明调用没有在原地踏步，参数键顺序不同、观察仍是缺货则是内容完全相同，参数顺序并不影响判断
# === 现象与原因：学员写；本日没有独立交付物 md ===
# 1. 图通过哪些节点和边代替原来的循环？
# 我的回答：
#   START 用普通边进入 model；model 用条件边决定去 tools 还是 END。
#   tools 执行工具后，用普通边进入 check；check 用条件边决定回到 model 还是 END。
#   model → tools → check → model 形成回路，代替原来的循环；条件边负责决定继续或结束。
# 2. 为什么模型已给出最终答复时，不再用预算或次数上限覆盖结果？
# 我的回答：
#   因为预算和次数上限本来就是在下一次循环开始前判断的，模型给出最终答复后就直接结束循环了
# 3. 为什么同轮的多条工具点单要全部回填后，再检查停止条件？
# 我的回答：
#   同轮的每条工具点单都需要对应的观察，避免留下未配对的调用。全部回填后，停止判断才能依据本轮完整结果进行，尤其是判断是否重复、是否有新进展。这些停止条件用于决定是否继续下一次模型请求，不应截断本轮的工具回填。
# 4. 怎样判断工具调用没有新进展？重复和预算同时触发时如何选择？
# 我的回答：
#   用repeated_call判断,工具名、解析后的参数和观察连续相同，达到重复限制，就判为没有新进展。先判断重复再判断预算
# 5. 请求前到期与请求中超时，在请求计数和用量记录上有什么区别？
# 我的回答：
#   请求前到期不会计入请求计数，请求中超时会
#   请求前到期的用量记录保持原状态，请求中超时没有收到响应时，不增加用量项，收到响应、其中 usage=None时追加 None
