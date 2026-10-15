"""Day 28：闭卷复现旧判断，再用新问题验收已写的 Agent 循环。"""

import day27_integrated_exercises as day27
import day28_fake_model as variant_model
from day26a_budget_exercises import stop_before_next_request, summarize_usage
from day26b_repeat_exercises import repeat_stop_reason, repeated_tail_count

# Day 26A 与 Day 26B 的跨天复验输入。
REVIEW_USAGES = [
    {"prompt_tokens": 220, "completion_tokens": 40},
    {"prompt_tokens": 310, "completion_tokens": 30},
]
REVIEW_TOKEN_LIMIT = 650
REVIEW_COST_LIMIT_YUAN = 0.0008

REVIEW_TOOL_TRACE = [
    {
        "step": 1,
        "tool": "search_notes",
        "arguments": '{"keyword":"库存","limit":2}',
        "tool_call_id": "review_1",
        "observation": "待补货",
    },
    {
        "step": 2,
        "tool": "search_notes",
        "arguments": '{"limit":2,"keyword":"库存"}',
        "tool_call_id": "review_2",
        "observation": "待补货",
    },
    {
        "step": 3,
        "tool": "search_notes",
        "arguments": '{"keyword":"库存","limit":2}',
        "tool_call_id": "review_3",
        "observation": "已补货",
    },
    {
        "step": 4,
        "tool": "search_notes",
        "arguments": '{"limit":2,"keyword":"库存"}',
        "tool_call_id": "review_4",
        "observation": "已补货",
    },
]


def run_variant(
    question: str,
    *,
    scenario: str = "normal",
    max_steps: int = 4,
    token_limit: int = 1000,
    cost_limit_yuan: float = 1.0,
    repeat_limit: int = 2,
    allow_code: bool = False,
) -> dict:
    """复用 Day 27 主循环，以本日模型函数回答新问题。"""
    return day27.run_agent(
        question=question,
        scenario=scenario,
        max_steps=max_steps,
        token_limit=token_limit,
        cost_limit_yuan=cost_limit_yuan,
        repeat_limit=repeat_limit,
        allow_code=allow_code,
        chat_fn=variant_model.fake_chat,
    )


def print_trace(trace: list[dict]) -> None:
    """按事件顺序分开打印点单与观察，供验收记录引用。"""
    for item in trace:
        step = item["step"]
        if item["event"] == "request":
            print(
                f"  第 {step} 次请求：结束原因 {item['finish_reason']}；"
                f"单次用量 {item['usage']}"
            )
        elif item["event"] == "tool":
            print(
                f"  第 {step} 次 assistant 点单：{item['tool']}"
                f"({item['arguments']})；ID {item['tool_call_id']}"
            )
            print(
                f"  第 {step} 次 tool 观察：ID {item['tool_call_id']}；"
                f"content {item['observation']}"
            )
        elif item["event"] == "final":
            print(f"  第 {step} 次最终答复：{item['answer']}")
        else:
            print(f"  第 {step} 次停止：{item['reason']}")


def main() -> None:
    """先打印跨天复验，再打印新问题的实际运行结果。"""
    print("=== 跨天复验：请先在验收记录里写预测，再看这里的实际值 ===")
    summary = summarize_usage(REVIEW_USAGES, day27.TEACHING_PRICE)
    reason = stop_before_next_request(
        summary, REVIEW_TOKEN_LIMIT, REVIEW_COST_LIMIT_YUAN
    )
    print(f"用量汇总：{summary}")
    print(f"下一次请求前的停止原因：{reason}")
    for count in (3, 4):
        trace = REVIEW_TOOL_TRACE[:count]
        tail = repeated_tail_count(trace)
        reason = repeat_stop_reason(trace, repeat_limit=2)
        print(f"工具轨迹前 {count} 条：末尾连续 {tail} 条；停止原因 {reason}")

    print("\n=== 新问题：暮云贴纸买 6 包多少钱？ ===")
    print(f"新商品检索：{day27.search_notes('暮云贴纸', 2)}")
    cases = [
        ("正常先查后算", "normal", {}, "final_answer；3 次请求"),
        ("算式报错后修正", "recover", {}, "final_answer；4 次请求"),
        ("代码未授权", "code", {}, "final_answer；权限错误观察"),
        ("代码获准", "code", {"allow_code": True}, "final_answer；42 元"),
        ("第二步后到上限", "normal", {"max_steps": 2}, "max_steps；2 次请求"),
        (
            "检索后到成本上限",
            "normal",
            {"cost_limit_yuan": 0.00006},
            "cost_budget；1 次请求",
        ),
    ]
    for label, scenario, options, expected in cases:
        print(f"\n{label}；期望：{expected}")
        result = run_variant(variant_model.QUESTION, scenario=scenario, **options)
        print(
            f"实际：{result['stop_reason']}；请求 {result['steps']} 次；"
            f"答复 {result['answer']}；累计用量 {result['usage']}"
        )
        print_trace(result["trace"])


if __name__ == "__main__":
    main()
