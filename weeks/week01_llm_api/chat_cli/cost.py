"""成本估算：单价表 + 两个算了钱的函数。

要做的：把你在 Day 9（weeks/week01_llm_api/day09_exercises.py）写好的
`cost_of_call` 和 `session_cost` **原样搬过来**，填在下面两个函数里。
搬完顺便想一下：为什么这两个函数放在单独的模块里，而不是塞进 chat_cli.py？

单价：元 / 百万 token，抄自官方价格页（2026-10-04，deepseek-flash）。
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
    raise NotImplementedError("把 Day 9 写好的 cost_of_call 搬过来")


def session_cost(
    input_per_turn: list[int], output_per_turn: list[int], price: dict[str, float]
) -> float:
    """算一整段会话的花费（元）：逐轮用 price 里的单价累加。"""
    raise NotImplementedError("把 Day 9 写好的 session_cost 搬过来")
