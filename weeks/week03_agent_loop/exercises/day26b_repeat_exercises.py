"""Day 26B 后半练习：比较两条观察、计数连续重复、决定何时停止。"""

import json


def same_stalled_call(previous: dict, current: dict) -> bool:
    """判断两条相邻工具结果是否同工具、同参数且同观察。"""
    previous_args = json.loads(previous["arguments"])
    current_args = json.loads(current["arguments"])
    return (
        previous["tool"] == current["tool"]
        and previous_args == current_args
        and previous["observation"] == current["observation"]
    )


def repeated_tail_count(trace: list[dict]) -> int:
    """返回工具轨迹末尾连续相同且无新观察的条数。"""
    count = 0
    previous = None
    for current in trace:
        if previous is not None and same_stalled_call(previous, current):
            count += 1
        else:
            count = 1
        previous = current
    return count


def repeat_stop_reason(trace: list[dict], repeat_limit: int = 2) -> str | None:
    """末尾重复达到上限时返回停止原因，否则允许继续。"""
    if repeated_tail_count(trace) >= repeat_limit:
        return "repeated_call"
    return None


def main() -> None:
    """按 A、B、C 顺序打印实际与期望；未写的下一题会明确报错。"""
    first = {
        "step": 1,
        "tool": "file_search",
        "arguments": '{"query":"订单","limit":2}',
        "tool_call_id": "call_1",
        "observation": "未找到资料",
    }
    repeated = {
        "step": 2,
        "tool": "file_search",
        "arguments": '{"limit":2,"query":"订单"}',
        "tool_call_id": "call_2",
        "observation": "未找到资料",
    }
    third = {
        "step": 3,
        "tool": "file_search",
        "arguments": '{"query":"订单","limit":2}',
        "tool_call_id": "call_3",
        "observation": "未找到资料",
    }
    changed_query = {
        "step": 2,
        "tool": "file_search",
        "arguments": '{"query":"运费","limit":2}',
        "tool_call_id": "call_4",
        "observation": "未找到资料",
    }
    calculator = {
        "step": 2,
        "tool": "calculator",
        "arguments": '{"expression":"18*5"}',
        "tool_call_id": "call_5",
        "observation": "90",
    }
    search_after_calculator = {
        "step": 3,
        "tool": "file_search",
        "arguments": '{"query":"订单","limit":2}',
        "tool_call_id": "call_8",
        "observation": "未找到资料",
    }
    job_pending = {
        "step": 1,
        "tool": "check_job",
        "arguments": '{"job_id":"J7"}',
        "tool_call_id": "call_6",
        "observation": "处理中",
    }
    job_finished = {
        "step": 2,
        "tool": "check_job",
        "arguments": '{"job_id":"J7"}',
        "tool_call_id": "call_7",
        "observation": "已完成",
    }

    print("=== A：比较两条工具结果 ===")
    for label, previous, current, expected in [
        ("键顺序和调用 ID 不同，内容仍相同", first, repeated, True),
        ("查询内容改变", first, changed_query, False),
        ("工具名改变", first, calculator, False),
        ("相同参数，但观察已经更新", job_pending, job_finished, False),
    ]:
        actual = same_stalled_call(previous, current)
        print(f"{label}：实际 {actual}；期望 {expected}")

    print("\n=== B：数轨迹末尾的连续次数 ===")
    for label, trace, expected in [
        ("空轨迹", [], 0),
        ("只有一次检索", [first], 1),
        ("连续两次没有新结果", [first, repeated], 2),
        ("连续三次没有新结果", [first, repeated, third], 3),
        ("中途做了计算", [first, calculator, search_after_calculator], 1),
        ("同参数但观察改变", [job_pending, job_finished], 1),
    ]:
        actual = repeated_tail_count(trace)
        print(f"{label}：实际 {actual}；期望 {expected}")

    print("\n=== C：是否停止后续请求 ===")
    for label, trace, repeat_limit, expected in [
        ("上限 2，已连续两次", [first, repeated], 2, "repeated_call"),
        ("上限 3，目前两次", [first, repeated], 3, None),
        ("上限 3，已连续三次", [first, repeated, third], 3, "repeated_call"),
        ("中途做了计算", [first, calculator, search_after_calculator], 2, None),
        ("观察已经更新", [job_pending, job_finished], 2, None),
    ]:
        actual = repeat_stop_reason(trace, repeat_limit)
        print(f"{label}：实际 {actual}；期望 {expected}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行并填写）
# 1. 两条检索的 tool_call_id 不同、JSON 键顺序也不同，为什么 A 仍应得到 True？
# 答：tool_call_id是用来判断配对的，不在判断的范围里，json键顺序并不影响内容，只判断解析后的内容
# 2. “中途做了计算”的轨迹末尾为什么只算连续 1 次，而不是把两次检索相加？
# 答：中途做了计算说明内容可能有进展，只能算一次
# 3. check_job 使用同样参数查同一任务，为什么“处理中 → 已完成”不应停止？
# 答：“处理中 → 已完成”说明任务有进展，不应该停止
# 4. 上限为 2 时，是第二次检索执行前就拦住了它，还是第二次观察后才停止后续请求？
# 答：第二次观察后才停止后续请求
