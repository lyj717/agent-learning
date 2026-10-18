"""Day 34：把手写 Agent 的行为迁入 LangGraph，综合实现由学员完成。

先用 10～15 分钟完成末尾两道闭卷短题，再读两份消息转换演示。
依次运行 --part a / b / c / d；D 可用 --case 1 只检查一组。
今天完全离线：模型回复与 usage 是教学数据，检索和计算使用已经学过的本地工具。
本文件不提供整张业务图的实现。文件检查点与人工确认接入留到下一单元，
先把本次单任务的消息、请求次数和停止行为接对。
复用函数不用跨文件查找：day34_support.py 内集中定义了六个公开接口及其完整说明，
直接运行该文件即可打印接口手册，或在 IDE 查看 support.函数名 的本地定义。
"""

import argparse
import sys
import time
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

# 写 build_agent_graph 时取消下面这一行的注释，其他建图接口与 Day 29～33 相同。
# from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from weeks.week04_frameworks.demos.day34 import day34_support as support


class AgentState(TypedDict):
    """AI 给定的数据接口；需要学员实现的是这些数据怎样被节点更新。"""

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


def model_node(state: AgentState) -> dict:
    """A：尝试一次模型请求，返回本轮消息、用量、次数与停止状态的部分更新。
    要做的：保留 Day 27 请求前检查任务时限、单次超时和最终答复的行为。
    每次实际尝试请求使 steps 加一；任务开始前到期不发请求，也不增加 steps。
    请求成功时，消息对象与 usage 都要保留；只有模型给出的最终文字能成为 answer。
    不在这里执行工具，不在这里提前用预算或 max_steps 抹掉已收到的最终答复。
    不修改传入的 state；trace / usages 是普通列表，更新中要保留旧项。
    接口：support.plan_next_call(started_at, now, task_limit, call_limit) 返回
    含 stop_reason / next_timeout 的字典；now 用 time.monotonic() 读取。
    support.request_model(原生消息字典列表, scenario=..., timeout_seconds=...)
    返回 {message: 原生assistant字典, finish_reason: 'tool_calls'或'stop',
    usage: {prompt_tokens: 数量, completion_tokens: 数量}或None}。
    用两份小演示里的转换接口衔接消息形状。
    使用 convert_to_messages 时，即使只有一条 response['message']，也传列表。
    转换对象是整条 message 字典，不是 message['content'] 字符串；转换结果已经是
    消息对象列表，放入 messages 即可。原生 tool_calls 含 function，不能直接当作
    AIMessage(tool_calls=...) 的 name / args 结构使用；整条消息转换会处理这些差异。
    answer 保持模型正文字符串，不调用消息转换函数。
    节点返回接口（2026-10-18 补齐）：本题四种分支统一返回下面六个键。
    这是给图更新 AgentState 的字典，不是直接返回 request_model 的原始响应。
      messages: list[AnyMessage] —— 只放本轮新 AIMessage；没收到响应时为 []。
                不复制旧消息，旧消息由 add_messages 保留。
      trace: list[dict] —— 旧轨迹加上本轮新事件；这个普通列表不会自动追加。
      usages: list[dict | None] —— 旧用量记录加上本轮收到的 usage；未收到响应则保持旧列表。
      steps: int —— 更新后的模型请求尝试次数。
      answer: str | None —— 仅最终答复分支放模型正文，其余分支为 None。
      stop_reason: str | None —— 本轮继续时 None，停止时为下面规定的原因。
    scenario、limits、started_at 由图保留，不必返回；不增加 message / usage /
    finish_reason 三个状态键。单次 usage 放进 usages，finish_reason 放进 request 轨迹。
    四种分支的返回要求：
      收到工具点单：messages 有一条新 AIMessage；trace 加 request；usages 加本轮 usage；
                    steps 比旧值加 1，answer=None，stop_reason=None。
      收到最终答复：messages 有一条新 AIMessage；trace 加 request 与 final；usages 加本轮 usage；
                    steps 比旧值加 1，answer 为模型正文，stop_reason='final_answer'。
      请求前任务到期：messages=[]；trace 只加 stop；usages、steps 保持旧值；
                      answer=None，stop_reason='task_timeout'，用返回字典表示停止。
      请求中单次超时：messages=[]；trace 加 request 与 stop；usages 保持旧值；
                      steps 比旧值加 1，answer=None，stop_reason='call_timeout'。
    收到响应但 usage=None 时，往 usages 加一项 None；请求超时没收到响应时，不加这一项。
    更新中用到的限制取 state['limits']，它已包含当前案例覆盖后的值；
    support.DEFAULT_LIMITS 只是默认模板，不能替代本次 state['limits']。

    期望结果：--part a 的三组分别为 (steps, stop_reason) =
    (1, None)、(0, 'task_timeout')、(1, 'call_timeout')。
    请求前发现 task_timeout 时只记 stop，没有 request。
    捕获请求中的 TimeoutError 时记 usage=None 的 request，再记 call_timeout 的 stop；
    此时不把未返回的 usage 加进 usages，沿用 Day 27。
    trace 沿用 Day 27：每条是事件字典，按 event 选择不同字段。
    A 写 request / final / stop，工具事件由 B 写；完整字段与 step 取值见
    day34_support.py 的 TRACE_GUIDE，直接运行支持文件也会先打印这一节。
    提示：day34_support.py 中两个 A 接口的本地定义有完整参数、返回字段与例子，
    无需逐个打开旧导入文件；消息转换看两份独立演示，不复制旧 for 循环。
    TimeoutError 是 Python 内置异常，无需导入；本题只捕获这次模型请求的超时。
    """
    step = state["steps"]
    trace = []
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
        message_dict = support.request_model(
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
            "messages": convert_to_messages(message),
            "trace": trace,
            "usages": state["usages"],
            "steps": step + 1,
            "answer": message["content"],
            "stop_reason": "final_answer",
        }
    return {
        "messages": convert_to_messages(message),
        "trace": trace,
        "usages": state["usages"],
        "steps": step + 1,
        "answer": None,
        "stop_reason": None,
    }


def tools_node(state: AgentState) -> dict:
    """B：执行最新一条 assistant 的整批点单，返回工具观察与工具轨迹。

    要做的：只处理最新一条 AIMessage 的点单；一条 assistant 可以点多个工具。
    每条都执行并回填一条 ToolMessage，保留对应调用 ID；steps 不增加。
    messages 的更新只包含新工具观察；trace 的更新须保留旧轨迹。
    不把工具结果写成 answer，不在批内处理完第一条后就提前做停止判断。

    节点返回接口：字典含 messages、trace 两个键。
      messages: list[AnyMessage] —— 本批新产生的全部 ToolMessage，不复制旧消息。
      trace: list[dict] —— 旧轨迹加上本批全部工具事件。
    其他状态字段由图保留，不在本节点更新。

    接口：convert_to_openai_messages(一条AIMessage) 返回一条原生字典；
    其中 tool_calls 每项含 id / function.name / function.arguments(JSON文本)。
    support.execute_call(call, allow_code=state['limits']['allow_code'])
    执行一条原生点单，返回含 role / tool_call_id / content 的原生工具字典。
    它负责已学的参数错误回填和代码权限；不是图节点，不会修改状态。
    工具轨迹沿用 Day 27 的 step / event='tool' / tool / arguments /
    tool_call_id / observation，其中 arguments 保留 JSON 文本，observation 为 content。

    期望结果：--part b 打印单点单、多点单、坏参数和代码权限对照。
    多点单组应一次交回两条工具观察，请求次数仍为 1；错误观察也有原调用 ID。
    提示：转换改变表示方式，不执行工具；执行工具不代表模型已经给了最终答复。
    """
    raise NotImplementedError("第 B 题还没写：tools_node")


def check_limits(state: AgentState) -> dict:
    """C：整批工具已回填后，决定是否允许再请求模型。

    要做的：保留 Day 27 停止优先级：连续无进展重复 → 预算 → 最大请求次数。
    repeated_call 比较工具轨迹；不能拿 request / final / stop 事件一起比较。
    预算使用已发生的 usages 汇总；达到阈值就停，用量缺失不能当 0。
    没有触发停止时保持 stop_reason=None；触发时追加一条 stop 轨迹。
    不增加 steps，不重新执行工具，也不能拿最后一条工具观察冒充 answer。

    节点返回接口：字典含 stop_reason、trace 两个键。
      stop_reason: str | None —— 本次选出的停止原因，继续时为 None。
      trace: list[dict] —— 停止时为旧轨迹加 stop；继续时保持旧轨迹。
    其他状态字段由图保留，不在本节点更新。

    接口：support.repeat_stop_reason(工具轨迹列表, repeat_limit)；
    support.summarize_usage(usages, price=support.TEACHING_PRICE)；
    support.stop_before_next_request(summary, total_token_limit, cost_limit_yuan)，
    其中 total_token_limit 取 state['limits']['token_limit']。
    三个接口都在 day34_support.py 有本地定义、参数说明与例子，无需查旧文件。
    期望结果：--part c 核对同观察重复、观察更新、多个条件同时到达等对照。
    提示：本题的 state 已经包含整批工具结果，不负责请求前的任务时限。
    """
    raise NotImplementedError("第 C 题还没写：check_limits")


def route_after_model(state: AgentState) -> Literal["tools", "end"]:
    """D：按本轮模型节点的结果选择继续处理工具或结束。

    要做的：正常点单继续；最终答复、任务时限或单次超时都结束。
    只读取状态，不执行模型或工具，也不在路由函数里改状态。
    期望结果：旧历史里有点单、本轮已答复的额外对照必须返回 end。
    提示：条件边的选择依据是本轮结果，不能搜索整段历史中有没有旧点单。
    """
    raise NotImplementedError("第 D 题还没写：route_after_model")


def route_after_limits(state: AgentState) -> Literal["model", "end"]:
    """D：根据本次停止判断选择允许下一次模型请求或结束。

    要做的：读取 check_limits 已写入的 stop_reason，保持判断与执行分离。
    期望结果：未触发上限返回 model；已触发上限返回 end。
    提示：路由标签必须与 build_agent_graph 的 path_map 对应。
    """
    raise NotImplementedError("第 D 题还没写：route_after_limits")


def build_agent_graph() -> CompiledStateGraph:
    """D：把模型、整批工具和停止判断组成可循环的单任务图。

    要做的：使用上面的 AgentState 与自己写的节点、路由；由图推动后续执行。
    本题不再给完整接线，需求是先请求模型，按本轮结果执行整批工具或结束；
    整批工具后决定能否再次请求。给每条路径正确的终点，不保留旧 for/while 总循环。
    期望结果：--part d 的原 12 组与 4 组新对照都得到指定停止原因、请求数与工具数。
    提示：仅使用已学的 StateGraph / add_node / add_edge /
    add_conditional_edges / compile；END 是结束位置，end 只是你返回的路由标签。
    """
    raise NotImplementedError("第 D 题还没写：build_agent_graph")


def run_graph_agent(question: str, *, scenario: str = "normal", **overrides) -> dict:
    """D：从新任务运行图，交回与手写版可比较的六项结果。

    要做的：make_initial(question, scenario=scenario, overrides=overrides)
    已负责输入准备；使用自己的图运行，返回 answer / stop_reason / steps /
    messages / trace / usage。这里 messages 要转回原生字典列表，usage 是汇总字典。
    overrides 只覆盖 support.DEFAULT_LIMITS 中同名限制，例如 max_steps=2。
    每次调用都是独立新任务；今天不接文件检查点，也不接真实模型。
    期望结果：D 每组同时打印预期与实际，并保留足够的消息和轨迹填写末尾观察。
    提示：invoke 交回的是图状态；公开结果的 usage 需要汇总，不能返回 usages 原列表。
    """
    raise NotImplementedError("第 D 题还没写：run_graph_agent")


# 以下是 AI 提供的输入与输出检查环境，不包含待实现的 Agent 图。
def make_initial(
    question: str, *, scenario: str = "normal", overrides: dict | None = None
) -> AgentState:
    """为每一组准备独立输入；所有状态字段一次给齐。"""
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
    """只为 A～C 查看单节点的部分更新，模拟已学的消息合并规则。"""
    # add_messages 会给没有消息 ID 的对象补 ID；检查环境不能因此改动被测原输入。
    old = deepcopy(state)
    new = deepcopy(update)
    result = {**old, **new}
    if "messages" in new:
        result["messages"] = add_messages(old["messages"], new["messages"])
    return result


def print_state(state: AgentState) -> None:
    """逐项打印节点检查需要的字段、消息身份与完整轨迹。"""
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
    """A 只检查单次模型节点，不执行后续工具或整图。"""
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
    """B 的输入是固定教学点单，不依赖 A 已写好。"""
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
    """C 使用预制轨迹，只测试停止判断，不冒充学员已经执行过的实验。"""
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
        print_state(apply_for_inspection(state, check_limits(state)))
        print(f"  原输入未修改={state == before}；期望 True")


def inspect_graph(case_number: int | None) -> None:
    """D 对照原行为和新情境，打印可供学员核对的真实结果。"""
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
    """选择单节点检查，或运行学员完成的综合图。"""
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
#   会保留，应该新消息并不是覆盖旧消息得来的
# 2. 两次工具名和参数相同，但观察由“缺货”变成“有货”，能判 repeated_call 吗？
#    与“参数键顺序不同、观察仍是缺货”的情境有何不同？
# 我的回答：
#   不能，观察变化就说明调用没有在原地踏步，参数键顺序不同、观察仍是缺货则是内容完全相同，参数顺序并不影响判断
# === 现象与原因：学员写；本日没有独立交付物 md ===
# 1. 选正常链条，记录 assistant 点单和对应 tool 观察的 ID，引用消息顺序与请求数。
#    从图中指出哪部分对应原 for 循环，messages 与 trace 分别怎样保留旧项？
# 我的回答：
#
# 2. 对照“到最大步数”和“直接最终答复且阈值已到”：为什么前者 answer=None，后者成功？
#    用请求数、最后消息和 stop/final 轨迹支持判断，不能只贴停止原因。
# 我的回答：
#
# 3. 对照同轮两条点单的正常与 max_steps=1 情境：请求数和 tool 观察数各是多少？
#    若处理第一条工具后就检查 max_steps，会破坏哪条消息配对？
# 我的回答：
#
# 4. 从 C 的两组相近输入说明：参数键顺序、调用ID、观察更新分别会怎样影响重复判断？
#    再记录重复和 token 阈值同时触发时的实际原因。
# 我的回答：
#
# 5. 对照任务开始前到期与单次请求超时：steps、request 轨迹、usage['requests'] 各是多少？
#    为什么超时的请求尝试次数可以大于已收到 usage 的次数？
# 我的回答：
