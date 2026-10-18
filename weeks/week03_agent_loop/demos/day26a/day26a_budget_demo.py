"""Day 26A：从一次模型响应的 usage，走到下一次请求前的预算判断。

直接运行并按输出顺序读 main。全部数据是固定的离线教学数据，
价格只为算得清楚，不代表今天任何服务商的实际价格。
"""

TEACHING_PRICE = {"input": 1.0, "output": 4.0}  # 元 / 百万 token，教学假价格


def section(title: str) -> None:
    """打印分节标题。"""
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


def main() -> None:
    """按响应、累计、停止位置和缺失数据讲解预算。"""
    section("1. usage 是一次模型请求的用量")
    print("这是什么：模型响应除了 assistant 消息，还可能带本次请求的 usage。")
    print("为什么需要：Day 22 的 steps 只数请求次数；两次请求可能花不同的 token。")
    print("场景：Agent 先请模型点检索工具，再带上检索观察请模型点计算工具。")
    first_response = {
        "message": "assistant 点检索工具",
        "usage": {"prompt_tokens": 800, "completion_tokens": 200},
    }
    second_response = {
        "message": "assistant 点计算工具",
        "usage": {"prompt_tokens": 900, "completion_tokens": 100},
    }
    print("代码：每次收到 response 后，分别读取 message 和 usage。")
    for index, response in enumerate([first_response, second_response], start=1):
        # enumerate(列表, start=1) 同时给出从 1 开始的请求序号和本次响应。
        usage = response["usage"]
        print(
            f"第 {index} 次：{response['message']}；输入 {usage['prompt_tokens']}、"
            f"输出 {usage['completion_tokens']} token"
        )
    print(
        "注意：中间的本地检索是工具调用，不是第三次模型请求。这里的数字是固定假数据。"
    )

    section("2. 累计用量与成本")
    print("这是什么：每次模型请求结束后，把已知用量加进同一本账。")
    print("为什么需要：单轮没超限，累计多轮后仍可能用完任务预算。")
    print("场景：沿用上面两次请求，按教学单价折算已知成本。")
    prompt_total = 0
    completion_total = 0
    cost_total = 0.0
    responses = [first_response, second_response]
    print("代码：for response in responses: 累加 usage，再比较预算。")
    for index, response in enumerate(responses, start=1):
        # enumerate(列表, start=1) 同时给出从 1 开始的请求序号和本次响应。
        usage = response["usage"]
        prompt_total += usage["prompt_tokens"]
        completion_total += usage["completion_tokens"]
        call_cost = teaching_cost_yuan(usage, TEACHING_PRICE)
        cost_total += call_cost
        print(
            f"第 {index} 次：本轮 {usage['prompt_tokens']} 输入 + "
            f"{usage['completion_tokens']} 输出；本轮 ¥{call_cost:.4f}；"
            f"累计 {prompt_total + completion_total} token、¥{cost_total:.4f}"
        )
    print("注意：这里不计算缓存折扣；真实账单要按实际模型、价格和用量字段核对。")

    section("3. 停在下一次模型请求之前")
    print("这是什么：已有用量达到预算后，程序不再发下一次请求。")
    print("为什么需要：只限制 Day 22 的最大步数，不能限制每步的消耗。")
    print("场景：任务总上限是 1900 token，两次响应累计已到 2000。")
    total_token_limit = 1900
    print("代码：if 已知累计 token >= 总上限: 停止下一次模型请求")
    print(f"预算 {total_token_limit}；实际已用 {prompt_total + completion_total}")
    if prompt_total + completion_total >= total_token_limit:
        # 到限后只能阻止后续请求，不能撤销刚刚已经发生的消耗。
        print("停止原因：token_budget；第三次模型请求不发送，暂时拿不到最终答复。")
    print("注意：第二次请求使总量越过上限；调用前后检查不能保证绝不超支。")
    print("这里的总上限是整个任务的账，与单次请求的 max_tokens 不是同一个参数。")

    section("4. usage 缺失时不能记成零")
    print("这是什么：某次响应没有 usage，表示那次用量未知，不表示免费。")
    print("为什么需要：把未知写成 0，会让预算判断误以为还能继续。")
    print("场景：第二次响应的 message 已拿到，usage 却是 None。")
    missing_usage = None
    print("代码：if usage is None: 记录缺失次数，并停止自动继续。")
    print(f"第二次 usage：{missing_usage}；已知用量只覆盖第一次请求。")
    if missing_usage is None:
        # 没有用量就无法证明预算未到；不把未知的那次记为零。
        print("停止原因：usage_unknown；是否重试由更外层的策略决定。")
    print("注意：估算值可以另记为估算，但不能冒充响应报告的实测 usage。")

    section("接下来动手")
    print("先闭卷复述一次 assistant 点单、tool 回填、再请求的关系，随后对照 Day 22。")
    print("再做 day26a_budget_exercises.py：先累计已知用量，再决定能否发下一次请求。")
    print("Day 26B 才练单次超时、任务时限与重复调用，不在今天叠加。")


def teaching_cost_yuan(usage: dict, price: dict[str, float]) -> float:
    """按教学单价计算一次已知用量的成本，单位为元。"""
    return (
        usage["prompt_tokens"] * price["input"]
        + usage["completion_tokens"] * price["output"]
    ) / 1_000_000


if __name__ == "__main__":
    main()
