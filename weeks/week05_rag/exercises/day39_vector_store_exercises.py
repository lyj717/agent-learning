"""Day 39：把已有片段与向量存入 Qdrant，再取回带分数与出处的候选。

默认 --part a；--part b 可独立运行。--part sources 只显示原文行号。
两题完成后可用 --part query 在自己的 UTF-8 文本上准备检索基线。
观察只写在 demos/day39/day39_retrieval_记录.md，本文件末尾不再重复填。
"""

import argparse
import sys
from pathlib import Path

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day39.day39_support import (
    CHUNK_LINES,
    COLLECTION_NAME,
    DEFAULT_PATHS,
    MATERIALS,
    OVERLAP_LINES,
    QUERY_ORIGINALS,
    new_storage_path,
    prepare_collection,
    prepare_embedded_chunks,
    seed_query_fixture,
)
from weeks.week05_rag.exercises.day36_sources_exercises import load_sources
from weeks.week05_rag.exercises.day38_embeddings_exercises import vectorize_question


def store_chunks(
    client: QdrantClient,
    collection_name: str,
    embedded_chunks: list[tuple[Document, list[float]]],
) -> int:
    """将固定资料快照写入已有集合，返回本次提交数。"""
    if not embedded_chunks:
        return 0
    points = []
    count = 0
    for index, tup in enumerate(embedded_chunks, start=1):
        doc, vector = tup
        if len(vector) != VECTOR_SIZE:
            raise ValueError("向量维度错误！")
        point = PointStruct(
            id=index,
            vector=vector,
            payload={
                "chunk_id": doc.id,
                "text": doc.page_content,
                "source": doc.metadata["source"],
                "line_start": doc.metadata["line_start"],
                "line_end": doc.metadata["line_end"],
                "embedding_model": MODEL_NAME,
            },
        )
        points.append(point)
        count += 1
    client.upsert(collection_name=collection_name, points=points, wait=True)
    return count


def retrieve_chunks(
    client: QdrantClient,
    collection_name: str,
    query_vector: list[float],
    limit: int = 2,
) -> list[tuple[Document, float]]:
    """按问题向量查询，返回带原始出处和分数的片段。"""
    if limit < 1 or len(query_vector) != VECTOR_SIZE:
        raise ValueError
    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    retrieves: list[tuple] = []
    for hit in response.points:
        payload = hit.payload
        doc = Document(
            page_content=payload["text"],
            id=payload["chunk_id"],
            metadata={
                "source": payload["source"],
                "line_start": payload["line_start"],
                "line_end": payload["line_end"],
            },
        )
        retrieves.append((doc, hit.score))
    return retrieves[:limit]


# ===== 以下是 AI 检查环境：复用旧代码和准备输入，不实现上面两个函数 =====
def show_records(client: QdrantClient, collection_name: str, count: int) -> None:
    """按已知数据库编号查看 payload，不实现查询结果到 Document 的转换。"""
    # retrieve(集合名, ids=编号列表, with_payload=True, ...)：按编号读回 Record 列表。
    records = client.retrieve(
        collection_name, ids=list(range(1, count + 1)), with_payload=True
    )
    print(f"读回记录数实际={len(records)}，期望={count}")
    for record in records:
        payload = record.payload or {}
        print(f"数据库 id={record.id}；原片段 id={payload.get('chunk_id')}")
        print(
            f"来源={payload.get('source')}；原行={payload.get('line_start')}～{payload.get('line_end')}"
        )
        print(f"正文={payload.get('text')!r}；模型={payload.get('embedding_model')}")


def show_candidates(candidates: list[tuple[Document, float]]) -> None:
    """打印本次实际候选，供学员记录和核对原文。"""
    for rank, (document, score) in enumerate(candidates, start=1):
        print(f"  候选{rank}：原片段 id={document.id}；余弦={score:.6f}")
        print(
            f"    来源={document.metadata.get('source')}；原行={document.metadata.get('line_start')}～{document.metadata.get('line_end')}"
        )
        print(f"    正文={document.page_content!r}")


def run_a() -> None:
    """检查真实向量写入、同快照重写和关闭后重开。"""
    model = create_embedding_model()
    pairs = prepare_embedded_chunks(model)
    before = [(document.model_dump(), vector.copy()) for document, vector in pairs]
    storage_path = new_storage_path("exercise_a")
    print(f"本次独立库目录：{storage_path}")
    print(
        f"已有片段/向量对实际={len(pairs)}，期望=3；模型={MODEL_NAME}；每条期望维度={VECTOR_SIZE}"
    )
    client = QdrantClient(path=str(storage_path))
    try:
        prepare_collection(client, COLLECTION_NAME)
        submitted = store_chunks(client, COLLECTION_NAME, pairs)
        print(f"首次提交数实际={submitted}，期望=3")
        # count(集合名, exact=True)：返回 CountResult，.count 是准确记录数。
        print(
            f"首次库记录数实际={client.count(COLLECTION_NAME, exact=True).count}，期望=3"
        )
        repeated = store_chunks(client, COLLECTION_NAME, pairs)
        print(
            f"同快照再提交数实际={repeated}，期望=3；库记录数实际={client.count(COLLECTION_NAME).count}，期望=3"
        )
        print(f"空批次返回实际={store_chunks(client, COLLECTION_NAME, [])}，期望=0")
        print(
            f"输入未改动实际={before == [(d.model_dump(), v) for d, v in pairs]}，期望=True"
        )
        prepare_collection(client, "invalid_batch")
        invalid = [pairs[0], (pairs[1][0], pairs[1][1][:-1])]
        try:
            store_chunks(client, "invalid_batch", invalid)
        except ValueError:
            print("维度错误批次实际=ValueError，期望=ValueError")
        else:
            print("维度错误批次实际=未报错，期望=ValueError")
        print(
            f"错误批次后的空集合记录数实际={client.count('invalid_batch').count}，期望=0"
        )
    finally:
        client.close()
    reopened = QdrantClient(path=str(storage_path))
    try:
        print(f"关闭后重开记录数实际={reopened.count(COLLECTION_NAME).count}，期望=3")
        show_records(reopened, COLLECTION_NAME, len(pairs))
    finally:
        reopened.close()


def run_b() -> None:
    """在独立真实向量输入上检索，不依赖 A 是否完成。"""
    model = create_embedding_model()
    client = QdrantClient(":memory:")
    print("B 使用内存教学原文，下面来源名不声称是磁盘文件：")
    for source, text in QUERY_ORIGINALS.items():
        print(f"\n来源={source}")
        for number, line in enumerate(text.splitlines(), start=1):
            print(f"  {number}: {line}")
    try:
        prepare_collection(client, COLLECTION_NAME)
        seed_query_fixture(client, model)
        print(
            "数据库 point id=17/29/43；原片段 id 保存于各自 payload.chunk_id，结果应恢复原编号。"
        )
        for question in ("会议结束后需要关闭哪些设备？", "会议室空调最低温度是多少？"):
            query_vector = vectorize_question(question, model)
            print(f"\n问题：{question}")
            for limit in (1, 2, 5):
                candidates = retrieve_chunks(
                    client, COLLECTION_NAME, query_vector, limit
                )
                print(
                    f"limit={limit}，候选数实际={len(candidates)}，期望={min(limit, 3)}；同分顺序不作答案"
                )
                show_candidates(candidates)
        prepare_collection(client, "empty")
        query_vector = vectorize_question("会议室怎么使用？", model)
        print(f"空集合实际={retrieve_chunks(client, 'empty', query_vector)}，期望=[]")
        for label, vector, limit in (
            ("limit=0", query_vector, 0),
            ("511维查询", query_vector[:-1], 2),
        ):
            try:
                retrieve_chunks(client, COLLECTION_NAME, vector, limit)
            except ValueError:
                print(f"{label} 实际=ValueError，期望=ValueError")
            else:
                print(f"{label} 实际=未报错，期望=ValueError")
    finally:
        client.close()


def run_query(source_root: Path, paths: list[str], question: str, limit: int) -> None:
    """两题完成后，将学员函数用于选定资料，打印实际候选以填基线。"""
    model = create_embedding_model()
    pairs = prepare_embedded_chunks(model, source_root, paths)
    query_vector = vectorize_question(question, model)
    storage_path = new_storage_path("baseline")
    print(f"本次独立库目录：{storage_path}")
    client = QdrantClient(path=str(storage_path))
    try:
        prepare_collection(client, COLLECTION_NAME)
        submitted = store_chunks(client, COLLECTION_NAME, pairs)
        print(f"资料根目录={source_root.resolve()}；相对路径列表={paths}")
        print(
            f"切分：每段 {CHUNK_LINES} 行、重叠 {OVERLAP_LINES} 行；模型={MODEL_NAME}，embed 无额外前缀"
        )
        print(f"提交记录数={submitted}；本次库目录={storage_path}")
    finally:
        client.close()
    reopened = QdrantClient(path=str(storage_path))
    try:
        print(f"问题：{question}；limit={limit}")
        candidates = retrieve_chunks(reopened, COLLECTION_NAME, query_vector, limit)
        print(f"候选数={len(candidates)}；是否支持问题由你核对原文，不自动判定。")
        show_candidates(candidates)
    finally:
        reopened.close()


def main() -> None:
    """提供独立 A/B、带行号原文和自有资料候选检查入口。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b", "query", "sources"), default="a")
    parser.add_argument(
        "--source-root", type=Path, default=MATERIALS, help="query/sources 的资料根目录"
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=DEFAULT_PATHS,
        help="相对于资料根目录的 UTF-8 文件路径",
    )
    parser.add_argument("--question", help="query 必填：学员自己的问题")
    parser.add_argument(
        "--limit", type=int, default=2, help="query 最多候选条数，默认 2"
    )
    args = parser.parse_args()
    if args.part == "sources":
        for document in load_sources(args.source_root.resolve(), args.paths):
            print(
                f"\n来源={document.metadata['source']}；根目录={args.source_root.resolve()}"
            )
            for number, line in enumerate(document.page_content.splitlines(), start=1):
                print(f"{number}: {line}")
    elif args.part == "a":
        run_a()
    elif args.part == "b":
        run_b()
    else:
        if not args.question:
            parser.error("--part query 必须同时传 --question")
        run_query(args.source_root, args.paths, args.question, args.limit)


if __name__ == "__main__":
    main()
