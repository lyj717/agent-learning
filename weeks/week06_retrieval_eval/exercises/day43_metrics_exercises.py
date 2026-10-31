"""Day 43：独立实现固定切分的片段级检索评测。

score_query 计算单题指标，evaluate_queries 汇总有答案题并单列无答案题。
--part a/b 运行人工教学对照，保存控制台、异常与配置；默认 a。
学员观察保留在 demos/day43/day43_metrics_记录.md。
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.demos.day41.day41_run_logs import run_logged_check
from weeks.week06_retrieval_eval.demos.day43.day43_checks import run_a, run_b

DAY43 = REPO_ROOT / "weeks/week06_retrieval_eval/demos/day43"


def score_query(
    ranked_ids: list[str], relevant_ids: set[str], k: int = 3
) -> dict[str, int | float | None]:
    """计算前 k 条片段的单题检索指标，已确认无答案时三指标返回 None。"""
    if type(k) is not int or k < 1:
        raise ValueError("K必须为正整数！")
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("id不能有重复编号！")
    retrieved = ranked_ids[:k]
    retrieved_count = len(retrieved)
    relevant_count = len(relevant_ids)
    matched = set(retrieved) & relevant_ids
    matched_count = len(matched)
    if not relevant_ids:
        return {
            "retrieved_count": retrieved_count,
            "relevant_count": relevant_count,
            "matched_count": matched_count,
            "hit": None,
            "recall": None,
            "precision": None,
        }
    hit = int(bool(matched))
    recall = matched_count / relevant_count
    precision = matched_count / k
    return {
        "retrieved_count": retrieved_count,
        "relevant_count": relevant_count,
        "matched_count": matched_count,
        "hit": hit,
        "recall": recall,
        "precision": precision,
    }


def evaluate_queries(
    samples: list[dict[str, list[str] | set[str]]], k: int = 3
) -> dict[str, int | float | None]:
    """按有答案题平均检索指标，单列无答案题及其中仍返回候选的题数。"""
    if type(k) is not int or k < 1:
        raise ValueError("K必须为正整数！")
    answerable_count = 0
    no_answer_count = 0
    no_answer_with_candidates = 0
    hits = []
    recalls = []
    precisions = []
    for sample in samples:
        ranked_ids = sample["ranked_ids"]
        relevant_ids = sample["relevant_ids"]
        answer = score_query(ranked_ids=ranked_ids, relevant_ids=relevant_ids, k=k)
        if answer["relevant_count"] == 0:
            no_answer_count += 1
            if answer["retrieved_count"] > 0:
                no_answer_with_candidates += 1
        else:
            answerable_count += 1
            hits.append(answer["hit"])
            recalls.append(answer["recall"])
            precisions.append(answer["precision"])
    if answerable_count == 0:
        return {
            "total": len(samples),
            "answerable_count": answerable_count,
            "no_answer_count": no_answer_count,
            "mean_hit": None,
            "mean_recall": None,
            "mean_precision": None,
            "no_answer_with_candidates": no_answer_with_candidates,
        }
    mean_hit = sum(hits) / len(hits)
    mean_recall = sum(recalls) / len(recalls)
    mean_precision = sum(precisions) / len(precisions)
    return {
        "total": len(samples),
        "answerable_count": answerable_count,
        "no_answer_count": no_answer_count,
        "mean_hit": mean_hit,
        "mean_recall": mean_recall,
        "mean_precision": mean_precision,
        "no_answer_with_candidates": no_answer_with_candidates,
    }


def main() -> None:
    """运行人工样本对照，沿用已有日志工具，不发起网络请求。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b"], default="a")
    args = parser.parse_args()
    check_fn = run_a if args.part == "a" else run_b
    learner_fn = score_query if args.part == "a" else evaluate_queries
    run_logged_check(
        args.part,
        check_fn,
        learner_fn,
        log_root=DAY43 / "outputs/checks",
        exercise_path=Path(__file__).resolve(),
        origin_env="DAY43_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
