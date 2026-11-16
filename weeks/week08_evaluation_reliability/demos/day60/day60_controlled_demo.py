"""Day60 演示：一次只改一处，前后同批对照，既看收益也看质量代价。

Week08 走到最后一项：按 Day59 的数据缩小证据。今天不追求「一定更快」，
而是把改动、收益、代价和回退条件写清楚。
本演示用示意数字讲配对对照，不调用模型。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、配对、差值、质量、边界的顺序讲一次前后对照。"""
    say("Day59 量出首字和输入费用是大头；今天把证据从 3 条 × 8 行缩到 2 条 × 4 行。")
    say("本演示讲怎么对照：同批题、同一次会话、交替跑，比中位数，同时检查质量。")
    say("学完应能说清收益、代价、混淆因素和回退条件。")

    say("\n一、这是什么")
    say("配对对照：同一批题在两种配置下各跑几轮，逐题比较。")
    say("因为题相同，题与题之间的难易差异被抵消，只剩配置差异和噪声。")

    say("\n二、为什么不能只跑一遍")
    say("Day59 的 q07 三轮首字是 711 / 2230 / 711ms；单次差几百毫秒，")
    say("可能只是排队或网络，不是配置造成的。")
    say("所以两套配置要在同一次会话里交替跑，比同题的中位数，而不是比单次。")
    say("measure 过滤出一个条件后，每个题号有 3 行（round=1/2/3）；")
    say("例如 baseline 的 q01 是 1247 / 1455 / 1289ms，中位数 1289ms。")
    say("三行先合成一个代表值，才能和另一套的同题号比。")

    say("\n三、示意对照（数字仅用于演示）")
    baseline = {"q01": 1247, "q02": 1009, "q03": 661, "q04": 1040}
    optimized = {"q01": 1090, "q02": 880, "q03": 620, "q04": 930}
    for case_id in sorted(baseline):
        delta = optimized[case_id] - baseline[case_id]
        say(f"{case_id}：{baseline[case_id]} → {optimized[case_id]}ms（{delta:+d}）")
    baseline_mean = sum(baseline.values()) / len(baseline)
    optimized_mean = sum(optimized.values()) / len(optimized)
    say(
        f"平均：{baseline_mean:.0f} → {optimized_mean:.0f}ms，"
        f"差值 {optimized_mean - baseline_mean:+.0f}ms"
    )

    say("\n四、收益之外还要看代价")
    say("缩小证据会减少输入 token，但可能漏掉回答所需的事实。")
    say("所以同一批回答还要过三层：")
    say("1. Day57 规则：要点、禁词、引用编号；")
    say("2. Day58 裁判：answer_ok 与 citation_ok；")
    say("3. 人工：抽查裁判与规则不一致的题。")
    say("示意：8 题里 7 题仍然正确，1 题因为少了一段证据答错——这是要记录的代价。")

    say("\n五、注意什么")
    say("1. 这次同时改了「每块 8→4 行」和「取 3→2 条」，是两个变量。")
    say("   若结果变好或变差，不能只归因于其中一个；要拆开就再各做一次单变量对照。")
    say("2. 两套配置要交替顺序（A/B、B/A、A/B），减少时段和负载偏差。")
    say("3. 报收益用中位数和差值，不用单次最好成绩；8 题仍不是线上长尾。")
    say("4. 先定回退条件：例如规则通过数下降或裁判 answer_ok 下降，就不采纳。")
    say("5. 保留基线数据和原始回答，回退时不用重跑。")

    say("\n下一步：实现 compare_conditions，跑 measure、quality、report，")
    say("把收益、质量变化和是否采纳写进记录。")


if __name__ == "__main__":
    main()
