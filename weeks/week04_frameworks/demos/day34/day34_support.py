"""Day 34 接口集中说明：做题只需 import day34_support as support。

按题目找这六个本地接口，不用逐个打开 Week 03 的导入文件：
  A：plan_next_call（时间计划）、request_model（一次模型响应）。
  B：execute_call（执行一条点单）。
  C：summarize_usage（用量汇总）、repeat_stop_reason（重复判断）、
     stop_before_next_request（预算判断）。
  D：复用以上接口；DEFAULT_LIMITS、QUESTION、TEACHING_PRICE、CASES 是给定数据。
轨迹格式集中在下方 TRACE_GUIDE，沿用 Day 27 的四类事件。

六个函数都在本文件定义，参数、返回字段和例子写在各自的 docstring 中；
在练习中查看 support.函数名 的定义或 IDE 提示，就能看到说明。
直接运行本文件只打印接口说明，不执行模型、工具或学员的图。

下方导入是 AI 维护的复用实现；只在想研究旧代码时才需要继续追进去。
学员负责消息转换、状态更新、节点、停止顺序、选路和整理返回结果。
CASES 是预先给定的验收目标，不是学员运行记录；教学用量和价格不是实际账单。
"""

import inspect
import json
import sys
from pathlib import Path

# 从脚本目录启动时也能找到仓库的 weeks 包；编辑器可以直接按完整包路径定位。
# sys.path.insert(0, 路径) 只补运行时的模块查找位置，不运行旧脚本入口。
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Day 27 模块已经集中了下方要复用的旧函数；这里统一通过一个内部模块访问。
# 前导下划线表示实现细节，做题只调用下面有完整说明的六个公开函数。
from weeks.week03_agent_loop.exercises import day27_integrated_exercises as _week03

QUESTION = _week03.QUESTION
TEACHING_PRICE = _week03.TEACHING_PRICE

__all__ = [
    "CASES",
    "DEFAULT_LIMITS",
    "QUESTION",
    "TEACHING_PRICE",
    "TRACE_GUIDE",
    "execute_call",
    "plan_next_call",
    "repeat_stop_reason",
    "request_model",
    "stop_before_next_request",
    "summarize_usage",
]

DEFAULT_LIMITS = {
    "max_steps": 4,
    "token_limit": 1000,
    "cost_limit_yuan": 1.0,
    "task_limit_seconds": 60.0,
    "call_limit_seconds": 1.0,
    "repeat_limit": 2,
    "allow_code": False,
}

TRACE_GUIDE = """trace 的格式：沿用 Day 27，不是 LangGraph 自动规定的字段。
trace 是 list[dict]：整个值是列表，每条事件才是一个字典。
不同事件有不同字段，不要求每条字典都塞入所有字段。

共同字段：
  step: int —— 这条记录对应的模型请求尝试次数，不是图节点编号。
  event: str —— 'request' / 'tool' / 'final' / 'stop' 四种之一。

1. request：一次模型请求的记录，由 A 写。
  字段：step、event、finish_reason、usage。
  finish_reason 为 'tool_calls' 或 'stop'；请求超时未收到响应时为 None。
  usage 为 {'prompt_tokens': 数量, 'completion_tokens': 数量} 或 None。
  格式示例：{'step': 1, 'event': 'request', 'finish_reason': 'tool_calls',
             'usage': {'prompt_tokens': 19, 'completion_tokens': 7}}

2. tool：执行一条工具点单后的观察，由 B 写。
  字段：step、event、tool、arguments、tool_call_id、observation。
  tool 是工具名；arguments 是原生点单的参数 JSON 文本；
  tool_call_id 是原点单 ID；observation 是工具返回的 content 字符串。
  格式示例：{'step': 1, 'event': 'tool', 'tool': 'calculator',
             'arguments': '{"expression":"2 * 3"}',
             'tool_call_id': 'example-call', 'observation': '6'}

3. final：模型已经给出最终答复，由 A 写。
  字段：step、event、answer；answer 是模型最终答复的文字。
  格式示例：{'step': 2, 'event': 'final', 'answer': '计算结果为 6。'}

4. stop：因限制或失败停止，由负责该停止原因的 A 或 C 写。
  字段：step、event、reason；reason 是停止原因字符串。
  格式示例：{'step': 2, 'event': 'stop', 'reason': 'max_steps'}

step 的取值：
  A 请求前任务到期：没有新请求，step 用已有的 state['steps']。
  A 已尝试本轮请求：本轮 request / final / 超时 stop 用更新后的请求次数。
  B 的工具记录与 C 的停止记录：沿用该轮 state['steps']，不增加请求次数。
  因此一次模型请求可产生多条事件；trace 的长度不等于 steps。

保留旧轨迹：trace 是普通列表，返回更新时要包含旧事件和本轮新事件。
上面是字段格式示例，不是学员运行记录，也不是一段完整 Agent 执行轨迹。
"""


def plan_next_call(
    started_at: float, now: float, task_limit: float, call_limit: float
) -> dict:
    """A：检查任务剩余时间，给出下一次请求可用的超时秒数。

    参数（四项都必填，单位都是秒）：
      started_at：任务开始时的 time.monotonic() 读数，来自 state['started_at']。
      now：现在的 time.monotonic() 读数，与 started_at 使用同一种时钟。
      task_limit：整个任务的时限，来自 limits['task_limit_seconds']。
      call_limit：单次模型请求时限，来自 limits['call_limit_seconds']。

    返回字典：
      elapsed：已经经过的秒数。
      remaining：任务剩余秒数，最小为 0。
      next_timeout：下一次请求的超时秒数；到期时是 None。
      stop_reason：尚有时间时 None，到期时 'task_timeout'。

    例：plan_next_call(10.0, 13.5, 5.0, 3.0)
    得到 elapsed=3.5、remaining=1.5、next_timeout=1.5、stop_reason=None。
    now 改成 15.0 时，remaining=0、next_timeout=None、stop_reason='task_timeout'。
    这里只计算时间，不发请求；None 不是让模型无限等待，而是没有可用的下一次请求。
    """
    return _week03.plan_next_call(started_at, now, task_limit, call_limit)


def summarize_usage(usages: list[dict | None], price: dict[str, float]) -> dict:
    """C、D：汇总各次已收到响应的用量记录，不执行预算判断。

    参数（两项都必填）：
      usages：列表；每项是 {'prompt_tokens': 数量, 'completion_tokens': 数量}，
              已收到响应但没有 usage 时，该项为 None。
      price：{'input': 输入单价, 'output': 输出单价}，单位为元/百万 token。
             本课传 support.TEACHING_PRICE，不能当作实际账单价格。

    返回字典的五个字段：
      requests：usages 的项数，包含 None；不一定等于所有模型请求尝试的次数。
      prompt_tokens / completion_tokens：已知的输入 / 输出 token 总数。
      missing_usage：None 的个数。
      known_cost_yuan：只根据已知用量算出的教学金额。

    例：summarize_usage([{'prompt_tokens': 80, 'completion_tokens': 20}],
                         price=TEACHING_PRICE)
    得到 requests=1、prompt_tokens=80、completion_tokens=20、
    missing_usage=0、known_cost_yuan=0.00016。
    [None] 会得到 requests=1、missing_usage=1；已知 token 为 0 不代表实际没消耗。
    """
    return _week03.summarize_usage(usages, price)


def repeat_stop_reason(trace: list[dict], repeat_limit: int = 2) -> str | None:
    """C：判断末尾连续的工具观察是否一直没有新进展。

    参数：
      trace（必填）：只含工具事件的列表，每项至少有 tool、arguments、observation。
                    tool 是工具名，arguments 是 JSON 文本，observation 是观察正文。
      repeat_limit（可选，默认 2）：末尾连续相同观察达到几条时停止；本课取 limits 同名项。

    返回：达到上限是 'repeated_call'，否则 None；不会修改轨迹或状态。
    比较工具名、解析后的参数和观察；调用 ID 与参数 JSON 的键顺序不影响结果。

    例：同一查询连续两次得到 '[]'，默认上限下返回 'repeated_call'。
    相同查询第二次得到新库存，返回 None；旧历史里重复过、末尾已变化也不能据此停。
    不要传混有 request / final / stop 的完整 trace，这个接口只读工具事件。
    """
    return _week03.repeat_stop_reason(trace, repeat_limit)


def stop_before_next_request(
    summary: dict, total_token_limit: int, cost_limit_yuan: float
) -> str | None:
    """C：根据用量汇总，判断预算是否允许下一次模型请求。

    参数（三项都必填）：
      summary：summarize_usage 返回的完整字典。
      total_token_limit：输入加输出的 token 上限，取 limits['token_limit']。
      cost_limit_yuan：教学金额上限，取 limits['cost_limit_yuan']，单位是元。

    返回：'token_budget'、'cost_budget'、'usage_unknown' 或 None。
    达到阈值就停；多项同时触发时依次按 token、成本、用量缺失选择。

    例：summary 已知输入 80、输出 20，total_token_limit=100，返回 'token_budget'。
    token 和成本均未达阈值但 missing_usage>0 时，返回 'usage_unknown'。
    这里只判断预算，不检查重复、任务时间或最大请求次数，也不修改状态。
    """
    return _week03.stop_before_next_request(summary, total_token_limit, cost_limit_yuan)


def execute_call(call: dict, *, allow_code: bool) -> dict:
    """B：执行一条原生工具点单，交回带原调用 ID 的 tool 消息字典。

    参数（两项都必填）：
      call：原生点单字典，含 id 和 function；function 含 name 与 arguments。
            arguments 是 JSON 文本，不能直接传 AIMessage 中的 args 字典。
            支持 search_notes、calculator、run_code 三个已学工具。
      allow_code：必须写参数名传入，取 limits['allow_code']；授权来自应用。
                  False 时，run_code 只产生权限错误观察，其他工具照常工作。

    返回：{'role': 'tool', 'tool_call_id': 原点单id, 'content': 观察字符串}。
    成功时 content 是结果的 JSON 文本；已处理的参数/权限错误是错误文字。
    例：calculator 的 arguments 为 '{"expression":"2 * 3"}'，content 为 '6'。
    这个函数一次只执行一条点单，不追加图消息，不改 steps，也不给模型最终答复。
    """
    tool_table = {
        "search_notes": _week03.search_notes,
        "calculator": _week03.calculator,
        "run_code": _week03.run_limited_code,
    }
    if call["function"]["name"] == "run_code":
        return _week03.build_code_observation(
            call=call, allow_code=allow_code, tool_table=tool_table
        )
    return _week03.build_tool_message(call=call, tool_table=tool_table)


def _calculator_call(expression: str, call_id: str) -> dict:
    """为离线多点单情境制作一条原生计算器点单。"""
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "calculator",
            # json.dumps(对象, ensure_ascii=False) 沿用旧接口的参数 JSON 文本。
            "arguments": json.dumps({"expression": expression}, ensure_ascii=False),
        },
    }


def request_model(
    messages: list[dict], *, scenario: str, timeout_seconds: float
) -> dict:
    """A：根据已有原生消息返回一次离线模型响应，不执行其中的工具。

    参数（三项都必填；星号后的两项必须写参数名）：
      messages：完整的原生消息字典列表，不是 LangChain 消息对象。
                每条用 role / content；工具观察还要有对应的 tool_call_id。
      scenario：固定情境名称，取 state['scenario']；默认练习输入为 'normal'。
      timeout_seconds：本次请求可用秒数，取时间计划的 next_timeout；到期后不调用。

    返回字典的三项：
      message：一条原生 assistant 消息字典，含 role / content / tool_calls。
               点单的 function.arguments 为 JSON 文本；点单时 content 可以是 None。
      finish_reason：'tool_calls' 表示给了点单，'stop' 表示给了最终答复。
      usage：{'prompt_tokens': 数量, 'completion_tokens': 数量} 或 None。

    例：只含一个用户问题的消息列表，scenario='normal'、timeout_seconds=1.0，
    会返回 search_notes 点单，usage 为输入 19、输出 7；检索尚未执行。
    'slow_model' 在上限小于 0.2 时抛 TimeoutError，模拟请求失败，不是真的等待。
    这里的响应和用量都是教学数据；它一次只回复一轮，不实现学员的 Agent 图。
    """
    if scenario not in {"multi_call", "terminal_budget"}:
        return _week03.fake_chat(
            messages, scenario=scenario, timeout_seconds=timeout_seconds
        )

    assistant_count = sum(message.get("role") == "assistant" for message in messages)
    if scenario == "terminal_budget":
        if assistant_count:
            raise AssertionError("terminal_budget 已给最终答复，不应再次请求")
        return {
            "message": {
                "role": "assistant",
                "content": "这是一条直接完成的最终答复。",
                "tool_calls": [],
            },
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 80, "completion_tokens": 20},
        }

    calls = [
        _calculator_call("18 * 2", "call_multi_product"),
        _calculator_call("81 / 9", "call_multi_quotient"),
    ]
    if assistant_count == 0:
        return {
            "message": {"role": "assistant", "content": None, "tool_calls": calls},
            "finish_reason": "tool_calls",
            "usage": {"prompt_tokens": 19, "completion_tokens": 7},
        }
    if assistant_count != 1 or len(messages) != 4:
        raise AssertionError("multi_call 第二轮应有 user、assistant、两条 tool 消息")
    if messages[-3].get("role") != "assistant":
        raise AssertionError("两条 tool 之前必须保留原 assistant 点单")
    if messages[-3].get("tool_calls") != calls:
        raise AssertionError("multi_call 原 assistant 的两条点单被修改或缺失")
    for observation, call, expected in zip(messages[-2:], calls, (36, 9), strict=True):
        if observation.get("role") != "tool":
            raise AssertionError("multi_call 没有收到两条 tool 观察")
        if observation.get("tool_call_id") != call["id"]:
            raise AssertionError("multi_call 的 tool 观察没有保留对应原调用 ID")
        if not isinstance(observation.get("content"), str):
            raise TypeError("multi_call 的 tool content 必须是字符串")
        # json.loads(JSON 文本) 只核对已回填的数值，不在这里执行工具。
        if json.loads(observation["content"]) != expected:
            raise AssertionError(f"multi_call 的工具观察应得到 {expected}")
    return {
        "message": {
            "role": "assistant",
            "content": "两次计算结果分别为 36 与 9。",
            "tool_calls": [],
        },
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 20, "completion_tokens": 7},
    }


# expected_tools 是所有模型请求产生的工具观察总数，不是工具节点执行次数。
# answer_fragment=None 表示没有最终答复；其他字符串应出现在最终答复中。
CASES: list[dict] = [
    {
        "label": "正常先查后算",
        "question": QUESTION,
        "scenario": "normal",
        "overrides": {},
        "expected_reason": "final_answer",
        "expected_steps": 3,
        "expected_tools": 2,
        "answer_fragment": "55",
    },
    {
        "label": "无命中且重复检索",
        "question": QUESTION,
        "scenario": "no_hit",
        "overrides": {},
        "expected_reason": "repeated_call",
        "expected_steps": 2,
        "expected_tools": 2,
        "answer_fragment": None,
    },
    {
        "label": "坏参数回填",
        "question": QUESTION,
        "scenario": "bad_args",
        "overrides": {},
        "expected_reason": "final_answer",
        "expected_steps": 2,
        "expected_tools": 1,
        "answer_fragment": "参数错误",
    },
    {
        "label": "连续失败",
        "question": QUESTION,
        "scenario": "continuous_error",
        "overrides": {},
        "expected_reason": "repeated_call",
        "expected_steps": 2,
        "expected_tools": 2,
        "answer_fragment": None,
    },
    {
        "label": "获准的数值代码",
        "question": QUESTION,
        "scenario": "code",
        "overrides": {"allow_code": True},
        "expected_reason": "final_answer",
        "expected_steps": 3,
        "expected_tools": 2,
        "answer_fragment": "55",
    },
    {
        "label": "未授权的数值代码",
        "question": QUESTION,
        "scenario": "code",
        "overrides": {},
        "expected_reason": "final_answer",
        "expected_steps": 3,
        "expected_tools": 2,
        "answer_fragment": "未获代码执行权限",
    },
    {
        "label": "用量缺失",
        "question": QUESTION,
        "scenario": "usage_unknown",
        "overrides": {},
        "expected_reason": "usage_unknown",
        "expected_steps": 1,
        "expected_tools": 1,
        "answer_fragment": None,
    },
    {
        "label": "到 token 上限",
        "question": QUESTION,
        "scenario": "token_budget",
        "overrides": {"token_limit": 100},
        "expected_reason": "token_budget",
        "expected_steps": 1,
        "expected_tools": 1,
        "answer_fragment": None,
    },
    {
        "label": "到成本上限",
        "question": QUESTION,
        "scenario": "normal",
        "overrides": {"cost_limit_yuan": 0.00004},
        "expected_reason": "cost_budget",
        "expected_steps": 1,
        "expected_tools": 1,
        "answer_fragment": None,
    },
    {
        "label": "到最大步数",
        "question": QUESTION,
        "scenario": "normal",
        "overrides": {"max_steps": 2},
        "expected_reason": "max_steps",
        "expected_steps": 2,
        "expected_tools": 2,
        "answer_fragment": None,
    },
    {
        "label": "任务时限已到，0 表示立即到期",
        "question": QUESTION,
        "scenario": "normal",
        "overrides": {"task_limit_seconds": 0.0},
        "expected_reason": "task_timeout",
        "expected_steps": 0,
        "expected_tools": 0,
        "answer_fragment": None,
    },
    {
        "label": "单次请求超时",
        "question": QUESTION,
        "scenario": "slow_model",
        "overrides": {"call_limit_seconds": 0.05},
        "expected_reason": "call_timeout",
        "expected_steps": 1,
        "expected_tools": 0,
        "answer_fragment": None,
    },
    {
        "label": "只改购买数量，检查是否仍使用当前问题",
        "question": "蓝湾便签买 7 本多少钱？请说明单价出处。",
        "scenario": "normal",
        "overrides": {},
        "expected_reason": "final_answer",
        "expected_steps": 3,
        "expected_tools": 2,
        "answer_fragment": "77",
    },
    {
        "label": "一轮两条点单，全部回填后再请求",
        "question": "请分别计算 18 * 2 和 81 / 9，再一起回答。",
        "scenario": "multi_call",
        "overrides": {},
        "expected_reason": "final_answer",
        "expected_steps": 2,
        "expected_tools": 2,
        "answer_fragment": "36 与 9",
    },
    {
        "label": "一轮两条点单，步数上限不截断本轮工具",
        "question": "请分别计算 18 * 2 和 81 / 9，再一起回答。",
        "scenario": "multi_call",
        "overrides": {"max_steps": 1},
        "expected_reason": "max_steps",
        "expected_steps": 1,
        "expected_tools": 2,
        "answer_fragment": None,
    },
    {
        "label": "本轮已有最终答复，同时达到 token 与步数上限",
        "question": "请直接给出最终答复，不调用工具。",
        "scenario": "terminal_budget",
        "overrides": {"token_limit": 100, "max_steps": 1},
        "expected_reason": "final_answer",
        "expected_steps": 1,
        "expected_tools": 0,
        "answer_fragment": "直接完成的最终答复",
    },
]


def main() -> None:
    """直接运行时集中打印六个接口的签名与说明，不运行案例。"""
    print("Day 34 接口手册：做题统一写 support.函数名，不用追读旧文件。")
    print("找当前题即可：A 看时间与模型，B 看工具，C 看用量、重复与预算。")
    print(f"\n=== trace 事件字段 ===\n{TRACE_GUIDE}")
    interfaces = [
        ("A：时间计划", plan_next_call),
        ("A：一次模型响应", request_model),
        ("B：执行一条工具点单", execute_call),
        ("C、D：用量汇总", summarize_usage),
        ("C：重复判断", repeat_stop_reason),
        ("C：预算判断", stop_before_next_request),
    ]
    for label, function in interfaces:
        # inspect.signature(函数) 读取参数与返回类型，不执行该函数。
        print(
            f"\n=== {label} ===\nsupport.{function.__name__}{inspect.signature(function)}"
        )
        # inspect.getdoc(函数) 读取并整理 docstring 缩进，便于直接在终端看接口说明。
        print(inspect.getdoc(function))


if __name__ == "__main__":
    main()
