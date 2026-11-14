"""Day59 演示：先量清楚——检索、首字、生成各占多少，费用从哪来。

Week08 的 Day57～58 已经能判对错；今天不加新功能，只做测量：
一次问答的时间花在哪一段、钱花在输入还是输出、P50/P95 怎么算。
学完应能读懂 Day59 的逐题数据，并说出 Day60 该优化哪一项。
本演示用假的分段耗时和固定的 token 数，不调用模型、不加载向量库。
"""

import time


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def fake_retrieval() -> float:
    """模拟一次本地检索，返回耗时毫秒。"""
    started = time.perf_counter()
    time.sleep(0.012)
    return (time.perf_counter() - started) * 1000


def fake_generation() -> tuple[float, float]:
    """模拟一次流式生成，返回（首字毫秒，总生成毫秒）。"""
    started = time.perf_counter()
    time.sleep(0.08)
    first = time.perf_counter() - started
    time.sleep(0.12)
    total = time.perf_counter() - started
    return first * 1000, total * 1000


def main() -> None:
    """按时间线、百分位、费用、瓶颈、边界的顺序讲一次测量。"""
    say("Day57～58 解决了「怎么判」；今天回答「时间和钱花在哪」。")
    say("本演示用假耗时和固定 token 数，跑一遍就能看懂 Day59 的报告。")
    say("学完应能说清检索、首字、生成的区别，以及 P50/P95 和费用的算法。")

    say("\n一、这是什么")
    say("端到端延迟 = 检索耗时 + 生成耗时；生成里又分首字等待和正文输出。")
    say("首字延迟（TTFT）是用户看到第一个字的等待；总延迟是整段回答结束。")
    say("费用 = 输入 token × 输入单价 + 输出 token × 输出单价。")

    say("\n二、为什么分开量")
    say("只报一个总延迟，不知道是该换检索、换模型，还是改 prompt 缩短输入。")
    say("只报总费用，不知道是证据太长（输入）还是回答太长（输出）。")
    say("拆开量，才能让 Day60 的优化对准瓶颈，而不是凭感觉。")

    say("\n三、具体时间线（假耗时）")
    retrieval_ms = fake_retrieval()
    ttft_ms, generation_ms = fake_generation()
    end_to_end = retrieval_ms + generation_ms
    say(f"检索={retrieval_ms:.1f}ms")
    say(f"首字={ttft_ms:.1f}ms（从发起生成到第一个非空 delta）")
    say(f"生成总耗时={generation_ms:.1f}ms")
    say(f"端到端={end_to_end:.1f}ms")
    say("本例检索只占几毫秒，首字约 80ms，剩下 120ms 是正文输出。")

    say("\n四、P50 / P95 怎么算（最近秩法）")
    say("把样本从小到大排好；排名 = ceil(p/100 × 样本数)，取第几名（从 1 起）。")
    samples = [1850.0, 1920.0, 2010.0, 2100.0, 2250.0, 2400.0, 2600.0, 3900.0]
    ordered = sorted(samples)
    say(f"8 个总延迟样本={ordered}")
    for p in (50, 95):
        rank = -(-int(p * len(ordered)) // 100)  # ceil，避免浮点误差
        rank = max(1, rank)
        say(f"P{p}：排名=ceil({p}/100×8)={rank}，取值={ordered[rank - 1]}")
    say("8 个样本的 P95 基本就是最大值附近；它不能代表长尾，只能说这批里最慢。")

    say("\n五、费用怎么算")
    prompt_tokens = 778
    completion_tokens = 96
    price = {"input_hit": 0.04, "input_miss": 2.0, "output": 8.0}
    input_cost = prompt_tokens / 1_000_000 * price["input_miss"]
    output_cost = completion_tokens / 1_000_000 * price["output"]
    say(
        f"输入 {prompt_tokens} token × {price['input_miss']} 元/百万 = {input_cost:.6f} 元"
    )
    say(
        f"输出 {completion_tokens} token × {price['output']} 元/百万 = {output_cost:.6f} 元"
    )
    say(
        f"合计={input_cost + output_cost:.6f} 元；输入占 {input_cost / (input_cost + output_cost):.0%}"
    )
    say("这份输入很长，是因为每题带了三段原文证据；优化时要先看这个比例。")

    say("\n六、测完怎么读")
    say("1. 检索占端到端的比例：很小就别先换向量库。")
    say("2. 首字和总生成的比例：首字慢，用户在等；总生成长，多半是输出太长。")
    say("3. 输入/输出费用比例：输入贵先缩证据，输出贵先控回答长度。")
    say("4. 只有 8 个样本时，P50 能看典型值，P95 只能看这批最慢，不要外推线上。")

    say("\n七、注意什么")
    say("1. 第一次请求包含冷启动，别和后续请求混在一批算。")
    say("2. 网络波动比代码差异大时，多跑几轮或取中位数，不要拿单次下结论。")
    say("3. 计时边界写清楚：检索是否含编码、生成是否含建消息，报告里要注明。")
    say("4. 先测量再优化；否则不知道收益是改对了，还是这次网络快。")
    say("5. 费用按快照单价换算，不是账单；缓存命中和时段价差要另说。")

    say("\n下一步：实现 percentile 与 summarize_measurements；")
    say("离线检查通过后，再跑 --part live 测 8 题。")


if __name__ == "__main__":
    main()
