"""Day45：把已经排好的两路片段编号合成一张榜，独立手算 RRF。

用途：衔接原向量排名与 A 的关键词排名，为学员实现 B 准备。
榜单和片段编号均为 AI 手写教具，不对应仓库实存文件，也没有运行真实检索。
本文件直接展示三块的计分，不提供通用 fuse_rankings 实现。
规则参考：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
"""


def main() -> None:
    """手工算三个候选的贡献，不提供通用融合函数。"""
    print("Week6 要比较检索改动。Day45 用两种方法找候选，再合成一份最终排名。")
    print("本演示解释合并这一步：读懂两张输入榜，算清每块如何得分、为什么改变先后。")
    print("学完后，在 B 中把规则用于任意两张榜；A 的 BM25 评分已经在这一步之前完成。")

    print("\n一、RRF 在解决什么问题？")
    print("同一个问题交给向量检索和关键词检索，会得到两份可能不同的候选排名。")
    print("要交给后续问答的是一份候选列表，就需要决定：哪些块排前面、重复块怎样合并。")
    print("RRF（倒数排名融合）把每块在各榜的名次换成分数，再把同一块的分数加起来。")
    print(
        "本课的数据流：原向量排名 + A 返回的关键词排名 → B 用 RRF 合并 → 最终编号列表。"
    )
    print("它的输入就是两份排好序的 list[str]；列表第 0 项代表第 1 名。")

    print("\n二、为什么用名次，而不直接加两路原始分数？")
    print("BM25 分数和向量检索分数的计算规则、数值范围可能不同，不能只凭数值大小比较。")
    print("RRF 统一改看‘在自己那张榜排第几’，原来的 BM25 分数、向量分数不再参与计算。")
    print("排名越靠前，分母越小，得到的这一次贡献就越大。")

    print("\n三、先看清输入：同一个问题，两张榜")
    print("问题：设备复位要做什么？三个候选片段分别为设备概述、操作步骤、复位说明。")
    print("以下榜单由 AI 手写；文件名和行号只是示例编号，不需要在仓库寻找这些文件。")
    device_id = "device.md#L1-L2"
    steps_id = "steps.md#L1-L2"
    reset_id = "reset.md#L1-L2"
    vector_ids = [device_id, steps_id]
    keyword_ids = [reset_id, steps_id]
    print(f"  vector_ids={vector_ids}")
    print(f"  keyword_ids={keyword_ids}")
    print("  向量榜：设备概述第 1，操作步骤第 2。")
    print("  关键词榜：复位说明第 1，操作步骤第 2。")
    print("操作步骤在两路里都是第 2，但它是同一个片段，需要把两次推荐合在一起。")

    print("\n四、逐块手算：一次贡献 = 1 / (rank_constant + 名次)")
    print("‘贡献’就是这张榜根据该块名次给它记的一份分数；没出现在这张榜则贡献为 0。")
    print(
        "名次从 1 开始；本例 rank_constant=60，所以第 1 名得到 1/61，第 2 名得到 1/62。"
    )
    rank_constant = 60
    overview_score = 1 / (rank_constant + 1)
    steps_score = 1 / (rank_constant + 2) + 1 / (rank_constant + 2)
    reset_score = 1 / (rank_constant + 1)
    print(f"  {device_id}：向量榜给 1/61，关键词榜给 0，总分={overview_score:.8f}")
    print(f"  {steps_id}：向量榜给 1/62，关键词榜也给 1/62，总分={steps_score:.8f}")
    print(f"  {reset_id}：向量榜给 0，关键词榜给 1/61，总分={reset_score:.8f}")
    print(
        "本例两张榜各排第 2 的操作步骤，获得两次贡献，总分超过只在一路排第 1 的候选。"
    )
    print("所以它会升到合并榜的第 1 名。这里只是在按规则合并推荐，不是在判定正文正确。")

    print("\n五、总分排好后，输出什么？")
    print("本课按总分降序；设备概述与复位说明同分，再按完整编号字符串升序。")
    pairs = [
        (reset_id, reset_score),
        (steps_id, steps_score),
        (device_id, overview_score),
    ]
    # sorted(数据, key=函数)：本例先比较负分数以实现降序，相等时比较编号字符串。
    ordered = sorted(pairs, key=lambda pair: (-pair[1], pair[0]))
    for rank, (chunk_id, score) in enumerate(ordered, start=1):
        print(f"  合并后第 {rank} 名：{chunk_id}，总分={score:.8f}")
    ordered_ids = [chunk_id for chunk_id, _ in ordered]
    print(f"  limit=3 时返回={ordered_ids[:3]}")
    print(f"  limit=2 时返回={ordered_ids[:2]}")
    print(
        "B 返回的只是排好序的编号 list[str]，分数用于内部比较。steps 只保留一个编号。"
    )

    print("\n六、B 的参数各代表什么？")
    print("接口：fuse_rankings(vector_ids, keyword_ids, limit=3, rank_constant=60)。")
    print("两份编号列表必填，已经各自按相关程度排好。B 使用已有排名进行融合。")
    print("limit：最终最多保留几块；rank_constant：算每次贡献时加在名次前的常量。")
    print("60 不是返回 60 块；修改 limit 也不会改变各块已经算出的融合总分。")
    print("练习要求两个数都是正整数且拒绝 bool，空榜时也先校验参数。")

    print("\n七、容易混淆的边界")
    print("同一编号在两路各出现一次：两路分别推荐了它，正常累加两次，最终输出一次。")
    print("同一编号在同一路出现两次：这一张榜重复记了同一块，本题要求抛 ValueError。")
    print("比较的是完整片段编号；同一个文件中的不同片段分别计分。")
    print("两路都没返回的编号不会凭空出现。融合分数也不是相关标签或回答正确率。")
    print(
        "即使片段已入库，只要两路都没返回它，B 也不会补出它；最终是否更好仍要与标注对照。"
    )
    print("本例只是算清规则；真实融合可能变好，也可能变差，需要固定 k 对照评测。")


if __name__ == "__main__":
    main()
