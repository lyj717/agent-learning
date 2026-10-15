"""Day 27：用虚构商品资料和离线假模型运行完整 Agent 循环。"""

import time
from collections.abc import Callable
from pathlib import Path

# 离线假模型与前几日完成的工具、停止判断。
from day24_observation_exercises import build_tool_message
from day24_retrieval_demo import calculator, find_in_text
from day25_code_demo import run_limited_code
from day25_permission_exercises import build_code_observation
from day26a_budget_exercises import stop_before_next_request, summarize_usage
from day26b_repeat_exercises import repeat_stop_reason
from day26b_timeout_exercises import plan_next_call
from day27_fake_model import fake_chat

NOTES_DIR = Path(__file__).resolve().with_name("day27_notes")
TEACHING_PRICE = {"input": 1.0, "output": 4.0}  # 教学假价：元 / 百万 token
QUESTION = "蓝湾便签买 5 本多少钱？请说明单价出处。"


def search_notes(keyword: str, limit: int = 3) -> list[dict]:
    """按文件名顺序检索两份资料，返回最多 limit 条带出处的命中。"""
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("关键词必须是非空字符串！")
    if type(limit) != int or limit < 1:
        raise ValueError("结果数必须是正整数！")
    count = 0
    results = []
    for path in sorted(NOTES_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        hits = find_in_text(text, keyword.strip(), path.name)
        results.extend(hits)
        if len(hits):
            count += len(hits)
        if count >= limit:
            break
    return results[: min(count, limit)]


def run_agent(
    question: str,
    *,
    scenario: str = "normal",
    max_steps: int = 4,
    token_limit: int = 1000,
    cost_limit_yuan: float = 1.0,
    task_limit_seconds: float = 60.0,
    call_limit_seconds: float = 1.0,
    repeat_limit: int = 2,
    allow_code: bool = False,
    chat_fn: Callable[..., dict] = fake_chat,
) -> dict:
    """运行 Agent 循环，返回答复、停止原因、消息、轨迹和累计用量。"""
    if type(max_steps) != int or max_steps < 1:
        raise ValueError("最大步数必须是正整数！")
    messages: list[dict] = [{"role": "user", "content": question}]
    trace = []
    usages = []
    started_at = time.monotonic()
    for step in range(1, max_steps + 1):
        now = time.monotonic()
        time_dict = plan_next_call(
            started_at, now, task_limit_seconds, call_limit_seconds
        )
        if time_dict["stop_reason"] == "task_timeout":
            trace.append({"step": step - 1, "event": "stop", "reason": "task_timeout"})
            return {
                "answer": None,
                "stop_reason": "task_timeout",
                "steps": step - 1,
                "messages": messages,
                "trace": trace,
                "usage": summarize_usage(usages, price=TEACHING_PRICE),
            }
        try:
            message = chat_fn(
                messages, scenario=scenario, timeout_seconds=time_dict["next_timeout"]
            )
            usage = message["usage"]
            usages.append(usage)
            finish_reason = message["finish_reason"]
            summary = summarize_usage(usages, price=TEACHING_PRICE)
            trace.append(
                {
                    "step": step,
                    "event": "request",
                    "finish_reason": finish_reason,
                    "usage": usage,
                }
            )
        except TimeoutError:
            trace.append(
                {
                    "step": step,
                    "event": "request",
                    "finish_reason": None,
                    "usage": None,
                }
            )
            trace.append({"step": step, "event": "stop", "reason": "call_timeout"})
            return {
                "answer": None,
                "stop_reason": "call_timeout",
                "steps": step,
                "messages": messages,
                "trace": trace,
                "usage": summarize_usage(usages, price=TEACHING_PRICE),
            }
        messages.append(message["message"])
        if finish_reason == "stop":
            trace.append(
                {
                    "step": step,
                    "event": "final",
                    "answer": message["message"]["content"],
                }
            )
            return {
                "answer": messages[-1]["content"],
                "stop_reason": "final_answer",
                "steps": step,
                "messages": messages,
                "trace": trace,
                "usage": summary,
            }
        for call in message["message"]["tool_calls"]:
            tool_table = {
                "search_notes": search_notes,
                "calculator": calculator,
                "run_code": run_limited_code,
            }
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            if name == "run_code":
                tool_message = build_code_observation(
                    call=call, allow_code=allow_code, tool_table=tool_table
                )
            else:
                tool_message = build_tool_message(call=call, tool_table=tool_table)
            observation = tool_message["content"]
            tool_call_id = call["id"]
            trace.append(
                {
                    "step": step,
                    "event": "tool",
                    "tool": name,
                    "arguments": arguments,
                    "tool_call_id": tool_call_id,
                    "observation": observation,
                }
            )
            messages.append(tool_message)
        tool_trace = []
        for t in trace:
            if t["event"] == "tool":
                tool_trace.append(t)
        if repeat_stop_reason(tool_trace, repeat_limit):
            trace.append({"step": step, "event": "stop", "reason": "repeated_call"})
            return {
                "answer": None,
                "stop_reason": "repeated_call",
                "steps": step,
                "messages": messages,
                "trace": trace,
                "usage": summary,
            }
        stop_reason = stop_before_next_request(summary, token_limit, cost_limit_yuan)
        if stop_reason is not None:
            trace.append({"step": step, "event": "stop", "reason": stop_reason})
            return {
                "answer": None,
                "stop_reason": stop_reason,
                "steps": step,
                "messages": messages,
                "trace": trace,
                "usage": summary,
            }
    trace.append({"step": step, "event": "stop", "reason": "max_steps"})
    return {
        "answer": None,
        "stop_reason": "max_steps",
        "steps": step,
        "messages": messages,
        "trace": trace,
        "usage": summary,
    }


def main() -> None:
    """逐组打印目标和实际；从新资料迁移开始，再核对完整循环。"""
    print("=== A：新资料与结果总上限 ===")
    for keyword, limit, expected in [
        ("蓝湾便签", 2, "catalog.txt:2、stock.txt:2"),
        ("蓝湾便签", 1, "仅 catalog.txt:2"),
        ("不存在的商品", 2, "[]"),
    ]:
        print(f"检索 {keyword!r}，总上限 {limit}；期望 {expected}")
        print(f"实际：{search_notes(keyword, limit)}")
    for keyword, limit in [("  ", 2), ("蓝湾便签", 0), ("蓝湾便签", True)]:
        print(f"检索 {keyword!r}，总上限 {limit}；期望 ValueError")
        try:
            search_notes(keyword, limit)
        except ValueError as error:
            print(f"实际：ValueError: {error}")
        else:
            print("实际：没有拒绝，请检查输入校验")

    print("\n=== B：循环和停止条件 ===")
    cases = [
        ("正常先查后算", "normal", {}, "final_answer；3 次请求；55 元及出处"),
        ("无命中且重复检索", "no_hit", {}, "repeated_call；2 次请求"),
        ("坏参数回填", "bad_args", {}, "final_answer；错误观察保留原 id"),
        ("连续失败", "continuous_error", {}, "repeated_call；2 次请求"),
        ("获准的数值代码", "code", {"allow_code": True}, "final_answer；55 元及出处"),
        ("未授权的数值代码", "code", {}, "final_answer；权限错误回填；代码未执行"),
        ("用量缺失", "usage_unknown", {}, "usage_unknown；1 次请求"),
        (
            "到 token 上限",
            "token_budget",
            {"token_limit": 100},
            "token_budget；1 次请求",
        ),
        ("到成本上限", "normal", {"cost_limit_yuan": 0.00004}, "cost_budget；1 次请求"),
        ("到最大步数", "normal", {"max_steps": 2}, "max_steps；2 次请求"),
        (
            "任务时限已到（0 表示立即到期）",
            "normal",
            {"task_limit_seconds": 0.0},
            "task_timeout；0 次请求",
        ),
        (
            "单次请求超时",
            "slow_model",
            {"call_limit_seconds": 0.05},
            "call_timeout；1 次请求",
        ),
    ]
    for label, scenario, overrides, expected in cases:
        print(f"\n{label}；期望：{expected}")
        result = run_agent(QUESTION, scenario=scenario, **overrides)
        print(
            f"实际：{result['stop_reason']}；请求 {result['steps']} 次；"
            f"答复 {result['answer']}；用量 {result['usage']}"
        )
        for item in result["trace"]:
            print(f"  轨迹：{item}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行后填写；下面的问题不要由 AI 代答）
# 1. 新资料里同一关键词出现两次，limit=1 为什么只能得到 catalog.txt:2？
#    再给一组旧演示未展示过的检索输入，记下实际出处和行号。
# 我的回答：
#   达到limit上限后只会按顺序给出前limit个结果
#   search_notes("松塔文件袋", 2)
#   [{'source': 'catalog.txt', 'line': 3, 'text': '松塔文件袋：单价 9 元/个，规格 A4。'}, {'source': 'stock.txt', 'line': 3, 'text': '松塔文件袋：现货，按个销售。'}]
# 2. 正常情境第二次点单的算式从哪里得到两个数字？贴出对应的检索观察和算式。
# 我的回答：
#   单价出处 catalog.txt:2，数量出处 问题
#   {"source": "catalog.txt", "line": 2, "text": "蓝湾便签：单价 11 元/本，规格 80 页。"}
#   "expression": "11 * 5"
# 3. 未授权代码情境中，哪条工具观察证明权限来自应用？与获准情境的观察有何区别？
# 我的回答：
#   '工具执行失败：PermissionError: 本次请求未获代码执行权限'
#   获准情境的观察:{"ok": true, "value": 55}
# 4. 无命中和连续失败都停在 repeated_call，两个 observation 分别是什么？
#    为什么第一次工具结果后都还没有停？
# 我的回答：
#   无命中："[]"   连续失败：”'工具执行失败：ValueError: 计算器只支持数字、括号和 + - * /，不支持变量或函数调用'“
#   repeat限制为2，连续两次相同的结果才会停止
# 5. 预算、任务时限与单次超时各在什么时候拦住请求？
#    从 request / stop 轨迹以及 steps 找证据；任务时限一开始就到时应没有 request。
# 我的回答：
#   预算：工具调用结束后 任务时限：调用前 单次超时：调用中
#   预算：
#   轨迹：{'step': 1, 'event': 'request', 'finish_reason': 'tool_calls', 'usage': {'prompt_tokens': 19, 'completion_tokens': 7}}
#   轨迹：{'step': 1, 'event': 'tool', 'tool': 'search_notes', 'arguments': '{"keyword": "蓝湾便签", "limit": 2}', 'tool_call_id': 'call_search', 'observation': '[{"source": "catalog.txt", "line": 2, "text": "蓝湾便签：单价 11 元/本，规格 80 页。"}, {"source": "stock.txt", "line": 2, "text": "蓝湾便签：现货，按本销售。"}]'}
#   轨迹：{'step': 1, 'event': 'stop', 'reason': 'cost_budget'}
#   任务时限:
#   轨迹：{'step': 0, 'event': 'stop', 'reason': 'task_timeout'}
#   单次超时：
#   轨迹：{'step': 1, 'event': 'request', 'finish_reason': None, 'usage': None}
#   轨迹：{'step': 1, 'event': 'stop', 'reason': 'call_timeout'}
# 6. 选一条未得到最终答复的情境，解释为何 answer 仍是 None，不能拿工具值代替。
# 我的回答：
#   到达最大步数时，虽然工具已经得出了55，但已经达到了最大步数模型无法再次发送请求，结果依然为None
