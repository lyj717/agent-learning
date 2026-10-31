"""Day 42：按回答的引用编号回查片段的原文出处。

学员作答与亲跑记录在 demos/day42/day42_验收.md。
--part sources 查看 AI 内存原文；--part b 运行对照并自动保存日志。
本单元没有模型请求、embedding 编码或数据库写入。
"""

import argparse
import sys
from pathlib import Path

from langchain_core.documents import Document

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.demos.day41.day41_run_logs import run_logged_check
from weeks.week05_rag.demos.day42.day42_support import run_checks, show_originals
from weeks.week05_rag.demos.shared.rag_functions import matches_source

DAY42 = REPO_ROOT / "weeks/week05_rag/demos/day42"


def trace_citations(
    cited_ids: list[str],
    candidates: list[tuple[Document, float]],
    originals: dict[str, Document],
) -> list[Document]:
    """按引用顺序核对片段的原文出处，返回通过核对的片段列表。"""
    count = 0
    trace = []
    for cited_id in cited_ids:
        source_ok = False
        count += 1  # noqa: SIM113 - 保留学员用已处理引用数校验返回条数的写法。
        for doc, _ in candidates:
            if doc.id == cited_id:
                for source, content in originals.items():
                    if not content:
                        raise ValueError
                    if doc.metadata["source"] == source:
                        source_ok = True
                        if matches_source(original=content, chunk=doc) is False:
                            raise ValueError
                        if (
                            doc.id
                            != f"{doc.metadata['source']}#L{doc.metadata['line_start']}-L{doc.metadata['line_end']}"
                        ):
                            raise ValueError
                if source_ok is False:
                    raise ValueError
                trace.append(doc)
        if count != len(trace):
            raise ValueError
    return trace


def main() -> None:
    """选择查看原文或运行独立变式检查。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["sources", "b"], default="sources")
    args = parser.parse_args()
    if args.part == "sources":
        show_originals()
    else:
        run_logged_check(
            "b",
            run_checks,
            trace_citations,
            log_root=DAY42 / "outputs/checks",
            exercise_path=Path(__file__).resolve(),
            origin_env="DAY42_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
