"""Day 43：认识片段级检索指标，为 Week 6 的固定口径对比报告做准备。

只有人工教学数据；不调用模型、embedding 或数据库，不计算学员的真实基线。
"""


def main() -> None:
    """按用途、定义、场景、计算和边界展示一次固定切分的评测。"""
    print("Week 6 要给已有 RAG 加分层评测，再用同一口径比较一种改动。")
    print("本演示只负责检索层：判断排在前面的片段找回了多少标注相关项。")
    print("学完应能解释 Hit、Recall、Precision 的分母；练习再独立实现单题与跨题统计。")

    print("\n一、这是什么")
    print("检索评测是把返回的片段编号，与事先读原文标注的相关片段编号比较。")
    print(
        "本次判分单位是固定切分后的唯一片段，不是文件、事实条数或模型的 answered 状态。"
    )
    print("@k 表示只看排名最前面的 k 条；k 由评测者指定，不是相关项总数。")

    print("\n二、为什么需要")
    print("拿到一条有用片段和找回所有相关片段是两回事，单看有候选或有命中会掩盖遗漏。")
    print("先标注，再看检索；如果只把本次返回的东西当作全部相关项，就无法发现漏检。")

    print("\n三、具体场景：设备借用问答（AI 人工资料与排名）")
    print("问题：借用投影仪时，在哪里登记、归还时交回什么？")
    print("预先读完全部三条片段，确认其中两条相关：")
    print("  equipment.md#L1-L2：借用前在前台登记。")
    print("  equipment.md#L3-L4：归还时交回遥控器与电源线。")
    print("  meals.md#L1-L2：餐补报销需附支付凭证。（不相关）")

    print("\n四、代码：一次计算，不封装练习的函数")
    relevant_ids = {"equipment.md#L1-L2", "equipment.md#L3-L4"}
    ranked_ids = ["equipment.md#L1-L2", "meals.md#L1-L2", "equipment.md#L3-L4"]
    k = 2
    top_ids = ranked_ids[:k]
    # 集合交集只留下两边都有的编号；先切前 k 条，再比较。
    found_ids = set(top_ids) & relevant_ids
    hit = int(bool(found_ids))
    recall = len(found_ids) / len(relevant_ids)
    precision = len(found_ids) / k
    print(f"排名={ranked_ids}；k={k}；实际取回={top_ids}")
    print(f"相关总数={len(relevant_ids)}；前 k 条中的相关数={len(found_ids)}")
    print(f"Hit@{k}={hit}：至少找到一条记 1，否则记 0。")
    print(f"Recall@{k}=1/2={recall:.2f}：分母是全部标注相关片段数。")
    print(f"Precision@{k}=1/2={precision:.2f}：本课固定按 k 个位置计算。")

    print("\n五、注意什么")
    print("1. 两条片段来自同一文件，仍是两个相关项；把 source 当编号会把它们混为一个。")
    print("2. 返回不足 k 条，Precision 仍除以 k；不能临时改成实际条数。")
    print("3. 空相关集合只有在已确认资料无答案时才有效，不能把未标注当无答案。")
    print("   本课对此三指标均返回 None，单独计数；跨题平均只包含有答案题。")
    print("4. 每题先算指标再求平均，每道有答案题权重相同；空分组返回 None。")
    print("5. 排名里的重复编号是数据错误，练习要求 ValueError，不靠去重挪动排名。")
    print("6. 相关片段找齐不保证模型回答正确；重叠片段也可能重复同一个事实。")
    print("   完整回答与引用支持要另查原始回答和实际引用，不能拿这些数代替。")
    print("7. 这些片段标签仅适用于同一资料快照与切分；改变切分会改变编号和相关项总数。")
    print("   后续先保留原文位置与事实依据，再为各版本建立可核对的判分映射。")
    print("\n下一步：完成练习 A，再用 A 完成 B；观察只写 day43_metrics_记录.md。")


if __name__ == "__main__":
    main()
