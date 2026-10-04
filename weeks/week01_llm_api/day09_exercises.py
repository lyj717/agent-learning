"""Day 9 练习：token 与成本（自己动手，别抄）。

先跑完 day09_token_demo.py，再来做这里的题：
    .venv\\Scripts\\python.exe weeks\\week01_llm_api\\day09_exercises.py

三个考点：
  - 一次调用的费用 = 输入 + 输出（含思考）分别乘单价
  - 多轮对话的输入 token 会滚雪球（历史要重新发）
  - 估算函数是 /cost 命令的地基

价格数据抄自官方价格页（2026-10-04，deepseek-flash，空闲时段）。
卡住就按 notes/卡住了怎么办.md 里的六招走，还不行再问我。
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
    """第 1 题：算一次调用花多少钱（单位：元）。
    要做的：
        1. 没命中缓存的输入 = prompt_tokens - cached_tokens
        2. 三部分分别算钱，再相加（单价是「元 / 百万 token」）：
             未命中输入 × price["input_miss"]
             命中缓存    × price["input_hit"]
             输出        × price["output"]
           注意：都要先除以 1_000_000
        3. 返回合计（元）
    期望结果（不传 price 时，默认用空闲价的 PRICE_IDLE）：
        cost_of_call(1_000_000, 0) == 1.0
        cost_of_call(0, 1_000_000) == 4.0
        cost_of_call(1_000_000, 0, cached_tokens=1_000_000) == 0.02
        cost_of_call(1_000_000, 0, price=PRICE_PEAK) == 2.0
    提示：1_000_000 也可以写成 10 ** 6；
          输出那一档最贵，别忘了 completion_tokens 里包含思考；
          单价一律从 price 里取——别在函数里写死是哪张表。
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
    """第 2 题：算出每一轮请求发出去的输入 token 数。
    要做的：
        1. 维护一个变量 history，初始值是 system_tokens
        2. 循环 turns 次，每次：
             本轮输入 = history + user_tokens，把它记进结果列表
             然后 history 变成 本轮输入 + assistant_tokens
           （因为下一轮要把本轮的回答也一起带上）
        3. 返回结果列表，长度是 turns
    期望结果：
        simulate_input_tokens(30, 10, 50, 3) == [40, 100, 160]
    提示：这题就是「上下文越用越贵」的数学形式，别用公式硬推，用上一轮的结果算下一轮。
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
    """第 3 题：算一整段会话的花费（元）。
    要做的：
        1. input_per_turn[i] 和 output_per_turn[i] 是第 i 轮的输入、输出 token 数
        2. 每一轮的费用 = 未命中输入 × price["input_miss"] + 输出 × price["output"]
           （都是「元 / 百万 token」，记得除以 1_000_000）
        3. 把每一轮的费用累加，返回总额
    期望结果：
        session_cost([1_000_000], [0], PRICE_IDLE) == 1.0
        session_cost([1_000_000], [1_000_000], PRICE_IDLE) == 5.0
        session_cost([1_000_000], [0], PRICE_PEAK) == 2.0
    提示：可以复用第 1 题的 cost_of_call；price 直接传 PRICE_IDLE 或 PRICE_PEAK。
          传法就是 cost_of_call(..., price=price)，别再判断 price 等于哪张表——
          那样换一张价目表（比如以后加个 pro 的价格）就会失效。
          逐轮遍历时可以用 zip(input_per_turn, output_per_turn) 一次拿两个数。
          第 3 题做完，你的 /cost 核心就齐了——Day 10 把它接进 CLI。
    """
    cost: float = 0.00
    for index in range(len(input_per_turn)):
        cost += cost_of_call(input_per_turn[index], output_per_turn[index], 0, price)
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
