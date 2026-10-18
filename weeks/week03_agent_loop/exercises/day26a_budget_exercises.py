"""Day 26A 小练习：累计已发生的模型用量，再决定能否请求下一轮。"""


def teaching_cost_yuan(usage: dict, price: dict[str, float]) -> float:
    """按教学单价算一次已知用量的成本，单位为元。"""
    return (
        usage["prompt_tokens"] * price["input"]
        + usage["completion_tokens"] * price["output"]
    ) / 1000**2


def summarize_usage(usages: list[dict | None], price: dict[str, float]) -> dict:
    """汇总每次模型请求的已知用量与未知次数。"""
    requests = len(usages)
    missing_usage = 0
    prompt_tokens = 0
    completion_tokens = 0
    known_cost_yuan = 0.0
    for usage in usages:
        if usage is None:
            missing_usage += 1
        else:
            prompt_tokens += usage["prompt_tokens"]
            completion_tokens += usage["completion_tokens"]
            known_cost_yuan += teaching_cost_yuan(usage, price)
    return {
        "requests": requests,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "missing_usage": missing_usage,
        "known_cost_yuan": known_cost_yuan,
    }


def stop_before_next_request(
    summary: dict, total_token_limit: int, cost_limit_yuan: float
) -> str | None:
    """根据已发生的请求，决定下一次模型请求前是否停止。"""
    if summary["prompt_tokens"] + summary["completion_tokens"] >= total_token_limit:
        return "token_budget"
    if summary["known_cost_yuan"] >= cost_limit_yuan:
        return "cost_budget"
    if summary["missing_usage"]:
        return "usage_unknown"
    return None


def main() -> None:
    """打印每轮用量、累计结果和下一次请求前的停止原因。"""
    price = {"input": 1.0, "output": 4.0}  # 教学假价格，元 / 百万 token
    print("\n=== 单次成本小练习 ===")
    print("输入 400、输出 100 token；期望成本：¥0.0008")
    one_call = {"prompt_tokens": 400, "completion_tokens": 100}
    print(f"实际成本：¥{teaching_cost_yuan(one_call, price):.4f}")
    cases = [
        (
            "还没到预算",
            [
                {"prompt_tokens": 400, "completion_tokens": 100},
                {"prompt_tokens": 500, "completion_tokens": 100},
            ],
            1500,
            0.003,
            "None",
        ),
        (
            "恰好到 token 上限",
            [
                {"prompt_tokens": 600, "completion_tokens": 100},
                {"prompt_tokens": 700, "completion_tokens": 100},
            ],
            1500,
            0.003,
            "token_budget",
        ),
        (
            "金额先到",
            [
                {"prompt_tokens": 400, "completion_tokens": 100},
                {"prompt_tokens": 500, "completion_tokens": 100},
            ],
            1500,
            0.0015,
            "cost_budget",
        ),
        (
            "第二次缺 usage",
            [{"prompt_tokens": 400, "completion_tokens": 100}, None],
            1500,
            0.003,
            "usage_unknown",
        ),
        (
            "上一次请求使预算超支",
            [
                {"prompt_tokens": 800, "completion_tokens": 100},
                {"prompt_tokens": 700, "completion_tokens": 200},
            ],
            1500,
            0.003,
            "token_budget",
        ),
    ]
    for label, usages, token_limit, cost_limit, expected in cases:
        print(f"\n=== {label} ===")
        for index, usage in enumerate(usages, start=1):
            # enumerate(列表, start=1) 同时给出请求序号和这轮的用量。
            if usage is None:
                print(f"第 {index} 次：usage 未返回，实际消耗未知")
            else:
                print(
                    f"第 {index} 次：输入 {usage['prompt_tokens']}、"
                    f"输出 {usage['completion_tokens']} token"
                )
        print(f"预算：总 token 上限 {token_limit}；金额上限 ¥{cost_limit:.4f}")
        summary = summarize_usage(usages, price)
        print(
            f"累计：请求 {summary['requests']} 次；已知输入 "
            f"{summary['prompt_tokens']}、输出 {summary['completion_tokens']} token；"
            f"已知成本 ¥{summary['known_cost_yuan']:.4f}；"
            f"缺失 usage {summary['missing_usage']} 次"
        )
        reason = stop_before_next_request(summary, token_limit, cost_limit)
        print(f"下一次请求前停止原因：{reason}；期望：{expected}")


if __name__ == "__main__":
    main()


# 热身复述、现象与原因（学员填写）
# 热身：不看 Day 22 时，我记得的 assistant 点单 → tool 回填 → 再请求流程：assistant点单需要的工具，程序收到点单后，对assistant的点单进行格式，工具名等校验，
# 如果校验都通过就在本地执行函数，执行后由程序来配对assistant点单的id以及tool回填，模型在下一次请求中读取回填后的消息历史，再决定下一步
# 对照 Day 22 后，我发现遗漏或说错的是：要维护一个轨迹变量，将模型和工具的返回记录下来
# 1. “恰好到 token 上限”用了几次请求、累计多少 token、停止原因是什么？
# 答：用了两次请求，累计1500token，停止原因是token_budget
# 2. “金额先到”时已知成本是多少？为什么没等 token 到 1500 才停？
# 答：已知成本：0.0017，因为已经超预算了，直接返回
# 3. 第二次缺 usage 时，requests 和 missing_usage 各是多少？为什么不能把它当 0？
# 答：requests：2 missing_usage:1 未知并不是0，并不能当作0，因为不能判断此时有没有超出预期
# 4. “上一次请求使预算超支”累计多少 token？为什么这时停止也不能追回超出的部分？
# 答：累计1800token，因为token已经被模型消耗掉了，只是还没有生成最终答复
