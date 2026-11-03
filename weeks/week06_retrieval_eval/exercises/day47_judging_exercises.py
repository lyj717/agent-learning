"""Day47：汇总答案与引用的人工判分，保留生成和报告入口。"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.day47.day47_support import run_entry


def summarize_reviews(reviews: list[dict]) -> dict:
    """按方案汇总已评阅回答的正确率与引用支持率，不修改输入。"""
    id_group = []
    for review in reviews:
        id = review["id"]
        group = review["group"]
        reviewed = review["reviewed"]
        answer_ok = review["answer_ok"]
        citation_ok = review["citation_ok"]
        id_group.append((id, group))
        if group not in {"vector", "fused"}:
            raise ValueError("未知group！")
        if not isinstance(id, str) or not id.strip():
            raise ValueError("id必须是非空字符串！")
        if reviewed is not True:
            raise ValueError("还没有判断！")
        if type(answer_ok) is not bool:
            raise ValueError("answer_ok必须是bool！")
        if type(citation_ok) is not bool and citation_ok is not None:
            raise ValueError("citation_ok必须是bool或None！")
    if len(id_group) != len(set(id_group)):
        raise ValueError("有重复的(id,group)!")
    vector_total = 0
    fused_total = 0
    v_answer_correct = 0
    f_answer_correct = 0
    v_citation_applicable = 0
    f_citation_applicable = 0
    v_citation_supported = 0
    f_citation_supported = 0
    for review in reviews:
        group = review["group"]
        answer_ok = review["answer_ok"]
        citation_ok = review["citation_ok"]
        if group == "vector":
            vector_total += 1
            if answer_ok:
                v_answer_correct += 1
            if citation_ok is not None:
                v_citation_applicable += 1
            if citation_ok:
                v_citation_supported += 1
        else:
            fused_total += 1
            if answer_ok:
                f_answer_correct += 1
            if citation_ok is not None:
                f_citation_applicable += 1
            if citation_ok:
                f_citation_supported += 1
    if vector_total > 0:
        v_answer_accuracy = v_answer_correct / vector_total
    else:
        v_answer_accuracy = None
    if v_citation_applicable > 0:
        v_citation_support_rate = v_citation_supported / v_citation_applicable
    else:
        v_citation_support_rate = None
    vector = {
        "total": vector_total,
        "answer_correct": v_answer_correct,
        "answer_accuracy": v_answer_accuracy,
        "citation_applicable": v_citation_applicable,
        "citation_supported": v_citation_supported,
        "citation_support_rate": v_citation_support_rate,
    }
    if fused_total > 0:
        f_answer_accuracy = f_answer_correct / fused_total
    else:
        f_answer_accuracy = None
    if f_citation_applicable > 0:
        f_citation_support_rate = f_citation_supported / f_citation_applicable
    else:
        f_citation_support_rate = None
    fused = {
        "total": fused_total,
        "answer_correct": f_answer_correct,
        "answer_accuracy": f_answer_accuracy,
        "citation_applicable": f_citation_applicable,
        "citation_supported": f_citation_supported,
        "citation_support_rate": f_citation_support_rate,
    }
    return {"vector": vector, "fused": fused}


def main() -> None:
    """选择人工对照、生成或读取同一次运行的人工判分。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "generate", "report"], default="a")
    parser.add_argument("--live", action="store_true", help="generate 必须显式启用")
    parser.add_argument("--run-dir", type=Path, help="report 必填：已生成结果的目录")
    args = parser.parse_args()
    if args.part == "generate" and not args.live:
        parser.error("generate 需要 --live，会对 4 道开发题的两组候选各请求一次")
    if args.part == "report" and args.run_dir is None:
        parser.error("report 需要 --run-dir 指向本次生成结果目录")
    run_entry(args.part, summarize_reviews, Path(__file__), args.run_dir)


if __name__ == "__main__":
    main()
