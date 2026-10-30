"""Day 41：把已完成的加载、检索和证据回答组合成自有资料问答。

默认 --part a；--part b 是独立的离线接口替身对照。
--part sources 显示所选笔记的原行；ask/batch 加 --live 才发真实请求。
学员记录在 demos/day41/day41_rag_记录.md；十条基线继续使用 Day 39 原表。
A/B 会自动保存终端输出到 demos/day41/outputs/checks/，不需要手动复制。
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from fastembed import TextEmbedding
from langchain_core.documents import Document
from qdrant_client import QdrantClient

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.demos.day41.day41_checks import run_a, run_b
from weeks.week05_rag.demos.day41.day41_run_logs import run_logged_check
from weeks.week05_rag.demos.day41.day41_support import (
    DEFAULT_PATHS,
    DEFAULT_SOURCE_ROOT,
    read_baseline_questions,
    run_questions,
    run_sources,
)
from weeks.week05_rag.demos.shared.rag_functions import (
    build_grounded_messages,
    check_grounded_reply,
    chunk_documents,
    load_sources,
    matches_source,
    retrieve_chunks,
    store_chunks,
    vectorize_chunks,
    vectorize_question,
)


def build_knowledge_base(
    source_root: Path,
    relative_paths: list[str],
    client: QdrantClient,
    collection_name: str,
    model: TextEmbedding,
    chunk_lines: int = 8,
    overlap_lines: int = 2,
) -> dict[str, Document]:
    """将指定资料建库，并返回按来源索引的全文快照。"""
    doc_list = load_sources(root=source_root, relative_paths=relative_paths)
    chunk_list = chunk_documents(
        documents=doc_list, chunk_lines=chunk_lines, overlap_lines=overlap_lines
    )
    embedded_chunks = vectorize_chunks(chunks=chunk_list, model=model)
    store_chunks(
        client=client, collection_name=collection_name, embedded_chunks=embedded_chunks
    )
    return {doc.metadata["source"]: doc for doc in doc_list}


def answer_question(
    question: str,
    originals: dict[str, Document],
    client: QdrantClient,
    collection_name: str,
    model: TextEmbedding,
    request_fn: Callable[[list[dict[str, str]]], dict],
    limit: int = 3,
) -> dict:
    """检索并核对原文证据，最多请求一次并保留过程结果。"""
    if not question.strip() or limit < 1:
        raise ValueError
    request_count = 0
    embedded_chunks = []
    response = None
    checked = None
    try:
        query_vector = vectorize_question(question=question, model=model)
        embedded_chunks = retrieve_chunks(
            client=client,
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        if not embedded_chunks:
            return {
                "candidates": embedded_chunks,
                "response": response,
                "checked": checked,
                "request_count": request_count,
                "error": None,
            }
        evidence_list = []
        for evidence, _ in embedded_chunks:
            evidence_list.append(evidence)
            source_ok: bool = False
            for source, doc in originals.items():
                if evidence.metadata["source"] == source:
                    source_ok = True
                    if not matches_source(original=doc, chunk=evidence):
                        raise ValueError("检查不通过！")
                    if (
                        evidence.id
                        != f"{source}#L{evidence.metadata['line_start']}-L{evidence.metadata['line_end']}"
                    ):
                        raise ValueError("id不匹配！")
            if source_ok is False:
                raise ValueError("找不到对应全文！")
        messages = build_grounded_messages(question=question, evidence=evidence_list)
        request_count = 1
        response = request_fn(messages)
        if response["finish_reason"] != "stop":
            return {
                "candidates": embedded_chunks,
                "response": response,
                "checked": checked,
                "request_count": request_count,
                "error": f"未正常结束!结束原因: {response['finish_reason']}",
            }
        else:
            checked = check_grounded_reply(
                raw_text=response["raw_text"], evidence=evidence_list
            )
    except Exception as error:  # noqa: BLE001 - 本题要求捕获普通运行异常，并返回错误现场。
        return {
            "candidates": embedded_chunks,
            "response": response,
            "checked": checked,
            "request_count": request_count,
            "error": f"{type(error).__name__}: {error}",
        }
    return {
        "candidates": embedded_chunks,
        "response": response,
        "checked": checked,
        "request_count": request_count,
        "error": None,
    }


def main() -> None:
    """选择独立对照、查看原文，或对固定资料运行真实问答。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=["a", "b", "sources", "ask", "batch"], default="a"
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--paths", nargs="+", default=DEFAULT_PATHS)
    parser.add_argument("--question", help="ask 必填；问题内容由学员给出")
    parser.add_argument(
        "--live", action="store_true", help="ask/batch 明确启用真实模型请求"
    )
    parser.add_argument("--chunk-lines", type=int, default=8)
    parser.add_argument("--overlap-lines", type=int, default=2)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=REPO_ROOT / "weeks/week05_rag/demos/day39/day39_retrieval_记录.md",
        help="batch 读取此文件原基线表中的编号与问题，不读取期望答案",
    )
    args = parser.parse_args()
    if args.part == "a":
        run_logged_check("a", run_a, build_knowledge_base)
    elif args.part == "b":
        run_logged_check("b", run_b, answer_question)
    elif args.part == "sources":
        run_sources(args.source_root, args.paths)
    else:
        if not args.live:
            parser.error("ask/batch 需要 --live；先用 --part a/b 完成独立离线对照")
        if args.part == "ask":
            if not args.question or not args.question.strip():
                parser.error("--part ask 必须同时提供非空的 --question")
            questions = [(1, args.question)]
        else:
            questions = read_baseline_questions(args.baseline)
        run_questions(
            build_knowledge_base,
            answer_question,
            args.source_root,
            args.paths,
            questions,
            args.chunk_lines,
            args.overlap_lines,
            args.limit,
        )


if __name__ == "__main__":
    main()
