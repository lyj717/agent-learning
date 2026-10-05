"""成本估算：单价表 + 两个算了钱的函数。

单价：元 / 百万 token，抄自官方价格页（2026-10-04，deepseek-flash）。
账算不准时先回官网看价格页，别照抄二手文章。
"""

# 空闲时段：工作日 9-12、14-18 之外都算空闲；高峰时段正好翻倍
PRICE_IDLE = {"input_hit": 0.02, "input_miss": 1.0, "output": 4.0}
PRICE_PEAK = {"input_hit": 0.04, "input_miss": 2.0, "output": 8.0}


def cost_of_call(
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
    price: dict[str, float] = PRICE_IDLE,
) -> float:
    """算一次调用花多少钱（元）：输入（区分缓存命中）与输出各按 price 里的单价算。"""
    miss = prompt_tokens - cached_tokens
    return (
        miss / 10**6 * price["input_miss"]
        + cached_tokens / 10**6 * price["input_hit"]
        + completion_tokens / 10**6 * price["output"]
    )


def session_cost(
    input_per_turn: list[int],
    output_per_turn: list[int],
    price: dict[str, float] = PRICE_IDLE,
) -> float:
    """算一整段会话的花费（元）：逐轮用 price 里的单价累加。

    不传 price 就按**空闲时段价**算（和 cost_of_call 的默认一致）。
    对外展示时要注明是按空闲价估的——高峰时段是它的两倍。
    """
    cost: float = 0.00
    for prompt_tokens, output_tokens in zip(input_per_turn, output_per_turn):
        cost += cost_of_call(prompt_tokens, output_tokens, price=price)
    return cost
