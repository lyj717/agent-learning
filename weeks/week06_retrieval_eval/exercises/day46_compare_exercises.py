"""Day46：固定同一批开发题，整合仅向量与 RRF 融合的逐题、整批评测。

--part a 跑人工对照；--part batch 对固定开发集重新检索并保存对比结果。
已完成的短复验、亲跑数据与观察见 demos/day46/day46_记录.md。
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.day46.day46_support import run_entry
from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import (
    check_ranked_ids,
    evaluate_queries,
    fuse_rankings,
    project_relevance,
    rank_keywords,
    score_query,
)


def compare_retrievals(
    cases: list[dict],
    chunks: list[Document],
    vector_search: Callable[[str, int], list[str]],
    k: int = 3,
    rank_constant: int = 60,
) -> dict:
    """比较开发题的向量与融合排名，返回逐题指标和两份整批汇总。"""
    if type(k) != int or k < 1:
        raise ValueError
    if type(rank_constant) != int or rank_constant < 1:
        raise ValueError
    ids = [case["id"] for case in cases if case["split"] == "dev"]
    if len(ids) != len(set(ids)):
        raise ValueError
    rows = []
    vector_samples = []
    fused_samples = []
    for case in cases:
        if (
            case["split"] == "dev"
            and case["answerable"]
            and not project_relevance(evidence=case["evidence"], chunks=chunks)
        ):
            raise ValueError
    for case in cases:
        if case["split"] == "dev":
            id = case["id"]
            question = case["question"]
            evidence = case["evidence"]
            relevant_ids = project_relevance(evidence=evidence, chunks=chunks)
            vector_ids = vector_search(case["question"], k)
            keyword_ids = rank_keywords(query=question, chunks=chunks, limit=k)
            fused_ids = fuse_rankings(
                keyword_ids=keyword_ids,
                vector_ids=vector_ids,
                rank_constant=rank_constant,
                limit=k,
            )
            vector_metrics = score_query(
                ranked_ids=vector_ids, relevant_ids=relevant_ids, k=k
            )
            fused_metrics = score_query(
                ranked_ids=fused_ids, relevant_ids=relevant_ids, k=k
            )
            vector_sample = {"ranked_ids": vector_ids, "relevant_ids": relevant_ids}
            fused_sample = {"ranked_ids": fused_ids, "relevant_ids": relevant_ids}
            allowed_ids = {chunk.id for chunk in chunks}
            check_ranked_ids(value=vector_ids, allowed=allowed_ids, limit=k)
            vector_samples.append(vector_sample)
            check_ranked_ids(value=fused_ids, allowed=allowed_ids, limit=k)
            fused_samples.append(fused_sample)
            rows.append(
                {
                    "id": id,
                    "question": question,
                    "relevant_ids": sorted(relevant_ids),
                    "vector_ids": vector_ids,
                    "keyword_ids": keyword_ids,
                    "fused_ids": fused_ids,
                    "vector_metrics": vector_metrics,
                    "fused_metrics": fused_metrics,
                }
            )
    vector_metrics = evaluate_queries(samples=vector_samples, k=k)
    fused_metrics = evaluate_queries(samples=fused_samples, k=k)
    return {
        "rows": rows,
        "vector_summary": vector_metrics,
        "fused_summary": fused_metrics,
    }


def main() -> None:
    """AI 运行环境：选择人工对照或固定开发集，保留每次配置与日志。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "batch"], default="a")
    args = parser.parse_args()
    run_entry(args.part, compare_retrievals, Path(__file__))


if __name__ == "__main__":
    main()
