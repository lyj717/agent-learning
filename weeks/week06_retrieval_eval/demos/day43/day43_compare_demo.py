"""Day 43 用途回看：用已完成的 A/B 比较两份检索排名。

在完成 day43_metrics_exercises.py 后运行。复用学员已验收的指标函数，
只用人工排名展示它们如何服务 Week 6 的前后对比，不运行真实检索或回答模型。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.exercises.day43_metrics_exercises import (
    evaluate_queries,
    score_query,
)


def main() -> None:
    """固定问题、标签和 k，观察两个手工排名在单题与整批上的差异。"""
    print("Week 6 要用数据判断一次检索改动的影响，再决定是否保留。")
    print("本演示展示你写的 A 如何找出变好/变差的题，B 如何统计同一批题。")
    print("下面的问题、相关标签和两份排名均为 AI 人工教具，没有真实优化实验。")
    print("只改候选排名；资料、相关标签和 k=3 固定，不调用模型或数据库。")

    register = "library.md#L1-L2"
    give_back = "library.md#L3-L4"
    opening = "library.md#L5-L6"
    meals = "meals.md#L1-L2"
    parking = "parking.md#L1-L2"
    print("\n一、什么叫比较：同一道题，检查改动前后找回的依据是否变化。")
    print("不用指标，只看‘返回了三条’，就看不出有用的片段占多少。")
    print("人工资料：L1-L2 写借书登记，L3-L4 写归还物品，L5-L6 写开放时间。")
    print("meals 与 parking 两份资料和以下问题无关，全部资料没有写借书押金。")
    questions = [
        "借书在哪里登记，归还时交回什么？（两条相关片段）",
        "图书室几点开放？（一条相关片段）",
        "借书押金多少钱？（已确认无答案）",
    ]
    relevant = [{register, give_back}, {opening}, set()]
    before_rankings = [
        [register, meals, parking],
        [opening, meals, parking],
        [meals],
    ]
    after_rankings = [
        [register, give_back, meals],
        [meals, parking, register],
        [meals],
    ]

    print("\n二、复用 A：逐题检查变化")
    for index, question in enumerate(questions):
        print(f"\n第 {index + 1} 题：{question}")
        for name, rankings in [
            ("原版本", before_rankings),
            ("改动版本", after_rankings),
        ]:
            result = score_query(rankings[index], relevant[index], k=3)
            print(f"  {name}候选={rankings[index]}")
            print(
                f"  找回相关数={result['matched_count']}；标注相关数={result['relevant_count']}；"
                f"Hit={result['hit']}；Recall={result['recall']}；"
                f"Precision={result['precision']}"
            )

    print("\n三、复用 B：同一批题做汇总")
    for name, rankings in [("原版本", before_rankings), ("改动版本", after_rankings)]:
        samples = [
            {"ranked_ids": rankings[index], "relevant_ids": relevant[index]}
            for index in range(len(questions))
        ]
        report = evaluate_queries(samples, k=3)
        print(
            f"{name}：平均 Hit={report['mean_hit']:.2f}；"
            f"平均 Recall={report['mean_recall']:.2f}；"
            f"平均 Precision={report['mean_precision']:.2f}；"
            f"有答案题数={report['answerable_count']}；"
            f"无答案却有候选的题数={report['no_answer_with_candidates']}"
        )

    print("\n四、这些结果能帮助什么决定")
    print("第 1 题从找回一部分变为全找回；第 2 题却从找到依据变为完全没找到。")
    print("改动版本平均 Recall 从 0.75 降为 0.50，不能只凭第 1 题变好就宣称整体改善。")
    print("你写的函数让每次改动都能按同一口径检查，也能保存失败案例用于回归。")
    print("后续用真实检索输出替换这两份人工排名；今天尚未比较任何真实优化方法。")
    print("这些数只评价检索；回答是否漏答、引用是否支持仍要核对模型实际输出。")


if __name__ == "__main__":
    main()
