"""Day44：把人工标注的原文位置转换成当前切分版本的相关片段编号。

用固定全文、问题标注和旧候选核对映射与检索指标，观察见 day44_labels_记录.md。
所有入口离线，输出与异常自动保存。
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.day44.day44_checks import run_checks
from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    LABELS,
    SNAPSHOT_SHA256,
    load_originals,
    preview_legacy,
    read_json,
    show_sources,
    show_validation,
    validate_labels,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def project_relevance(evidence: list[dict], chunks: list[Document]) -> set[str]:
    """将同源且行范围相交的片段编号收集为集合。"""
    set_id = set()
    for e in evidence:
        for chunk in chunks:
            if e["source"] == chunk.metadata["source"] and max(
                e["line_start"], chunk.metadata["line_start"]
            ) <= min(e["line_end"], chunk.metadata["line_end"]):
                set_id.add(chunk.id)
    return set_id


def main() -> None:
    """选择资料展示、函数对照、标注校验或旧结果回放。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=["sources", "a", "validate", "preview"], default="sources"
    )
    parser.add_argument(
        "--case", choices=[f"q{i:02d}" for i in range(1, 11)], default="q01"
    )
    parser.add_argument(
        "--require-complete", action="store_true", help="validate 时要求三十题全部标完"
    )
    args = parser.parse_args()
    if args.require_complete and args.part != "validate":
        parser.error("--require-complete 只与 --part validate 一起使用")
    config = {
        "part": args.part,
        "case": args.case,
        "require_complete": args.require_complete,
        "labels_path": str(LABELS),
        "labels_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "source_snapshot_sha256": SNAPSHOT_SHA256,
        "chunk_lines": 8,
        "overlap_lines": 2,
        "k": 3,
    }

    def execute(run_dir: Path) -> None:
        """执行当前入口并把结构化结果与控制台一同留证。"""
        if args.part == "a":
            run_checks(project_relevance)
            return
        originals = load_originals()
        if args.part == "sources":
            show_sources(originals)
            return
        dataset = read_json(LABELS)
        if args.part == "validate":
            report = validate_labels(dataset, originals, args.require_complete)
            show_validation(report)
        else:
            report = preview_legacy(args.case, dataset, originals, project_relevance)
        (run_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    run_logged(args.part, execute, config, Path(__file__), LABELS.parent / "outputs")


if __name__ == "__main__":
    main()
