"""Day 9 练习：token 与成本。

跑法：.venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_exercises.py
价格数据抄自官方价格页（2026-10-04，deepseek-flash，空闲时段）。
"""

# 单价：元 / 百万 token
PRICE_IDLE = {"input_hit": 0.02, "input_miss": 1.0, "output": 4.0}
PRICE_PEAK = {"input_hit": 0.04, "input_miss": 2.0, "output": 8.0}


def cost_of_call(
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
    price: dict[str, float] = PRICE_IDLE,
) -> float:
    """算一次调用花多少钱（元）。

    输入（区分缓存命中）和输出各按 price 里的单价算。
    """
    miss = prompt_tokens - cached_tokens
    return (
        miss / 10**6 * price["input_miss"]
        + cached_tokens / 10**6 * price["input_hit"]
        + completion_tokens / 10**6 * price["output"]
    )


def simulate_input_tokens(
    system_tokens: int, user_tokens: int, assistant_tokens: int, turns: int
) -> list[int]:
    """算出每一轮请求发出去的输入 token 数。

    历史每一轮都要重发，所以输入会一轮比一轮大。
    """
    history = system_tokens
    tokens: list[int] = []
    for _ in range(turns):
        now = history + user_tokens
        tokens.append(now)
        history = now + assistant_tokens
    return tokens


def session_cost(
    input_per_turn: list[int], output_per_turn: list[int], price: dict[str, float]
) -> float:
    """算一整段会话的花费（元）。

    逐轮用 price 里的单价累加。这就是 /cost 的核心。
    """
    cost: float = 0.00
    for prompt_tokens, output_tokens in zip(input_per_turn, output_per_turn):
        cost += cost_of_call(prompt_tokens, output_tokens, price=price)
    return cost


if __name__ == "__main__":
    print("=== 第 1 题：一次调用多少钱 ===")
    print(f"  输入 100 万、输出 0        -> {cost_of_call(1_000_000, 0)}")
    print(f"  输入 0、输出 100 万        -> {cost_of_call(0, 1_000_000)}")
    print(
        f"  输入 100 万全命中缓存      -> {cost_of_call(1_000_000, 0, cached_tokens=1_000_000)}"
    )
    print(
        f"  输入 100 万、输出 0，高峰价 -> {cost_of_call(1_000_000, 0, price=PRICE_PEAK)}"
    )
    print("  预期：1.0 / 4.0 / 0.02 / 2.0")

    print("\n=== 第 2 题：多轮对话的输入怎么涨 ===")
    rows = simulate_input_tokens(30, 10, 50, 20)
    print(f"  前三轮：{rows[:3]}")
    print(f"  最后一轮：{rows[-1]}")
    print(f"  20 轮总输入：{sum(rows)}（预期前三轮是 [40, 100, 160]）")
    print("  对照：如果不重复发，20 轮的内容总量只有 1230 个 token")

    print("\n=== 第 3 题：整段会话多少钱 ===")
    print(f"  单轮 100 万输入，空闲价 -> {session_cost([1_000_000], [0], PRICE_IDLE)}")
    print(
        f"  单轮 100 万输入 + 100 万输出，空闲价 -> {session_cost([1_000_000], [1_000_000], PRICE_IDLE)}"
    )
    print(f"  同一笔账按高峰价 -> {session_cost([1_000_000], [0], PRICE_PEAK)}")
    print("  预期：1.0 / 5.0 / 2.0")

    print("\n=== 做完三题，回到 day09_token_demo.py 对照它的算法 ===")


# ============================================================
# 现象与原因（做完之后填，用自己的话）
# ============================================================
#
# 1. 你模拟的 20 轮对话里，总输入 token 是多少？对话内容总量是多少？差几倍？
#    为什么会有这个差？
#   总输入：12200，对话总量：1230。差了大概十倍，因为每多对话一轮，就要将原历史记录重新上传，每次的输入会越来越大
# 2. 为什么「输出」的单价是「输入」的 4 倍？想一想思考 token 记在哪一档，
#    这对你选模型、设 max_tokens 有什么影响？
#   输出更加值钱，思考token在输出中
#   同等性能下，选输出便宜的模型；max_tokens过低会导致模型在思考时就把token用完，无输出还花钱
# 3. 官方换算：1 个中文字符 ≈ 0.6 个 token。你随手写一句 20 个字的话，
#    估算大概多少 token？实际调用时，怎么知道估得准不准？
#   约12个token，实际调用时要用usage查看
# 4. 你要给用户做 /cost 命令，会显示哪些信息？（每次调用 / 本次会话累计 /
#    下一次的预估，挑你觉得有用的说，并说明为什么）
#   本次调用花费的token：将输入未命中,输入命中和输出的都打印出来；本次调用花费的钱
#   用户需要知道这次调用花费了多少钱、花费在哪，还需要知道累计花费了多少
