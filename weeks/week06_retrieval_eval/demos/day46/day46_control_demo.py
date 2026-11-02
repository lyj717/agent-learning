"""Day46：用一道人造题说明固定 k 的控制变量，不实现批量整合练习。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import score_query


def main() -> None:
    """比较相同候选在不同 k 下的读数，说明为何需固定比较条件。"""
    print("Week6 要交一组有依据的检索对比，Day46 把已学机制接成批量入口。")
    print("本演示只解释比较条件：学完能判断是不是只改变了检索方案。")
    print("练习会复用你写过的函数；这里不实现筛选开发题、回调检索或整批汇总。")
    print("以下文件编号、标签、排名均为 AI 人工教具，没有真实检索或模型请求。")

    print("\n一、是什么：同一道题在相同条件下比较两个方案，才看得出方案本身的影响。")
    print("为什么：多取一些候选也可能提高 Recall，不能把改 k 的效果算成融合的效果。")
    print("场景：手册两处分别写登记与归还，本题两处都需要；原排名先返回停车说明。")
    registration = "manual.md#L1-L1"
    returning = "manual.md#L2-L2"
    parking = "parking.md#L1-L1"
    relevant = {registration, returning}
    ranking = [parking, registration, returning]
    print(f"预先标注相关编号={sorted(relevant)}；同一份候选排名={ranking}")

    print("\n二、先看旧函数签名：score_query(ranked_ids, relevant_ids, k=3) -> dict。")
    print("两个编号容器必填；k 默认 3，这里显式传值。返回匹配计数及三项指标。")
    for k in (2, 3):
        metrics = score_query(ranking, relevant, k=k)
        print(
            f"相同排名，k={k}：匹配数={metrics['matched_count']}，"
            f"Recall={metrics['recall']}，Precision={metrics['precision']}"
        )
    print("候选顺序没有变化，Recall 却从 0.5 变成 1；这不是优化了检索排序。")

    print("\n三、今天怎么固定：原文/切分/题目/标注/每路上限/最终 k 都保持。")
    print("同题只调用一次 vector_search(question, k)，得到一份向量编号榜。")
    print("仅向量组直接评价该榜；融合组把同一份榜与关键词榜送入旧 RRF 函数。")
    print("唯一改动是加入固定的关键词/RRF 流程，不同时调切分、k 或分词规则。")

    print("\n四、注意：新 24 题不能直接拿来与上周 10 题的均值相比。")
    print("本轮两组都用同样的 24 道开发题；6 道留出题不检索、不评分。")
    print("无答案题不进入有答案题均值，但保留‘仍返回候选’的独立计数。")
    print("片段指标不能证明回答完整或引用支持；本课没有调用回答模型。")
    print("接下来独立写 compare_retrievals，真实批量运行后再判断收益或退化。")


if __name__ == "__main__":
    main()
