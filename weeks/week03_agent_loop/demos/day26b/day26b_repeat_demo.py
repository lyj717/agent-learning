"""Day 26B 后半演示：从工具轨迹中发现连续、相同且没有新观察的调用。"""

import json


def main() -> None:
    """先解释重复判据，再打印正常推进与原地重复的离线轨迹。"""
    print("=== 1. 这是什么 ===")
    print(
        "如果 Agent 连续调用同一工具、传同样的参数、又得到同样的观察，就可能没有推进。"
    )
    print("这里把这类连续结果计数；达到上限后，不再请求下一轮模型。")

    print("\n=== 2. 为什么需要 ===")
    print("最大步数最终能截停循环，但相同的检索若一直重复，仍会浪费前面的请求。")
    print("单看工具名不够：先检索订单、再检索运费，虽然工具相同，任务却在推进。")

    print("\n=== 3. 具体场景 ===")
    print("以下记录是假定参数已校验、调用已完成的工具结果；没有真实模型或检索。")
    print("每条记录都保留 Day 22 的 step、tool、arguments、tool_call_id、observation。")

    print("\n=== 4. 看代码对应的结果 ===")
    print("判断只看工具名、解析后的参数、观察；step 和调用 ID 不参与比较。")
    print(
        "关键判断就在下面的 same_stalled_call、repeated_tail_count、repeat_stop_reason。"
    )
    for label, trace, repeat_limit in example_traces():
        show_trace(label, trace, repeat_limit)

    print("\n=== 5. 注意什么 ===")
    print("JSON 参数文字的键顺序可以不同；解析后内容相同，仍算相同参数。")
    print("不同的 tool_call_id 用来配对点单与观察，不能拿它判断是否重复。")
    print("本检测在工具观察写入轨迹后运行：第二次已执行，拦住的是后续模型请求。")
    print("若观察每次都带不同时间戳，这条规则可能漏报；最大步数仍要保留。")
    print("这里只模拟只读工具；会修改数据的工具还需要自己的防重复执行措施。")


def same_stalled_call(previous: dict, current: dict) -> bool:
    """判断两条相邻工具结果是否同工具、同参数且同观察。"""
    # json.loads(JSON 文本)：把 Day 22 保存的参数字符串还原成字典，便于比较内容。
    previous_args = json.loads(previous["arguments"])
    current_args = json.loads(current["arguments"])
    return (
        previous["tool"] == current["tool"]
        and previous_args == current_args
        and previous["observation"] == current["observation"]
    )


def repeated_tail_count(trace: list[dict]) -> int:
    """返回轨迹末尾连续相同且无新观察的工具结果条数。"""
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


def show_trace(label: str, trace: list[dict], repeat_limit: int) -> None:
    """逐条打印 assistant 点单、tool 观察和最终停止判断。"""
    print(f"\n{label}；连续上限 {repeat_limit}：")
    for item in trace:
        print(
            f"  第 {item['step']} 步 assistant 点单：{item['tool']}，"
            f"参数 {item['arguments']}，ID {item['tool_call_id']}"
        )
        print(f"  tool 观察：{item['observation']}")
    print(
        f"  末尾连续次数 {repeated_tail_count(trace)}；"
        f"停止原因 {repeat_stop_reason(trace, repeat_limit)}"
    )


def example_traces() -> list[tuple[str, list[dict], int]]:
    """提供五组固定的示意工具轨迹，不调用真实工具或模型。"""
    first_search = {
        "step": 1,
        "tool": "file_search",
        "arguments": '{"query":"订单","limit":2}',
        "tool_call_id": "call_1",
        "observation": "未找到资料",
    }
    repeated_search = {
        "step": 2,
        "tool": "file_search",
        "arguments": '{"limit":2,"query":"订单"}',
        "tool_call_id": "call_2",
        "observation": "未找到资料",
    }
    third_search = {
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
    pending = {
        "step": 1,
        "tool": "check_job",
        "arguments": '{"job_id":"J7"}',
        "tool_call_id": "call_6",
        "observation": "处理中",
    }
    finished = {
        "step": 2,
        "tool": "check_job",
        "arguments": '{"job_id":"J7"}',
        "tool_call_id": "call_7",
        "observation": "已完成",
    }
    return [
        ("同参数同观察，连续两次", [first_search, repeated_search], 2),
        ("查询内容改变", [first_search, changed_query], 2),
        ("相同参数但观察更新", [pending, finished], 2),
        ("中间做了别的事", [first_search, calculator, search_after_calculator], 2),
        ("阈值设为三次", [first_search, repeated_search, third_search], 3),
    ]


if __name__ == "__main__":
    main()
