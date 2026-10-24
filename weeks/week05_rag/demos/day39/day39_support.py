"""Day 39 的检查环境：复用旧加载/切分/编码，准备独立查询教学数据。

不实现练习的批量写入函数或查询结果到 Document 的转换。
"""

import tempfile
from pathlib import Path

from fastembed import TextEmbedding
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from weeks.week05_rag.demos.day38.day38_embedding_support import MODEL_NAME, VECTOR_SIZE
from weeks.week05_rag.exercises.day36_sources_exercises import load_sources
from weeks.week05_rag.exercises.day37_chunks_exercises import chunk_documents
from weeks.week05_rag.exercises.day38_embeddings_exercises import vectorize_chunks

DAY39 = Path(__file__).resolve().parent
MATERIALS = DAY39 / "materials"
OUTPUTS = DAY39 / "outputs"
COLLECTION_NAME = "chunks"
DEFAULT_PATHS = ["notes/office.md", "archive/office.md"]
CHUNK_LINES = 3
OVERLAP_LINES = 1

# B 的原文是内存教学数据，键是教学来源名，不声称这些文件已经写到磁盘。
QUERY_ORIGINALS = {
    "rooms/guide.txt": "会议室使用说明\n会议结束后请关闭投影仪和空调。\n下班前检查门窗。",
    "archive/rooms.txt": "旧版会议室说明\n登记\n检查\n签字\n会议结束后请关闭投影仪和空调。",
    "finance/guide.txt": "报销说明\n餐补报销应附支付凭证。",
}


def new_storage_path(label: str) -> Path:
    """为一次检查创建独立目录并保留，避免覆盖上次练习的数据。"""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    # mkdtemp(prefix=名前缀, dir=父目录)：创建唯一子目录并返回路径；这里不使用系统 TEMP。
    return Path(tempfile.mkdtemp(prefix=f"{label}_", dir=OUTPUTS))


def prepare_collection(client: QdrantClient, collection_name: str) -> None:
    """在新客户端中准备 512 维余弦集合，供练习函数直接使用。"""
    # create_collection(集合名, vectors_config=配置)：创建集合；此处客户端/集合由检查环境提供。
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def prepare_embedded_chunks(
    model: TextEmbedding, source_root: Path = MATERIALS, paths: list[str] | None = None
) -> list[tuple[Document, list[float]]]:
    """直接复用学员已完成的 Day 36～38，不重写旧机制。"""
    originals = load_sources(
        source_root.resolve(), DEFAULT_PATHS if paths is None else paths
    )
    return vectorize_chunks(
        chunk_documents(originals, CHUNK_LINES, OVERLAP_LINES), model
    )


def seed_query_fixture(client: QdrantClient, model: TextEmbedding) -> None:
    """手工准备 B 的三个固定 point，使 B 无需先完成 A 即可独立运行。"""
    room_text = QUERY_ORIGINALS["rooms/guide.txt"].splitlines()[1]
    finance_text = QUERY_ORIGINALS["finance/guide.txt"].splitlines()[1]
    vectors = list(model.embed([room_text, finance_text]))
    # 这里逐条手工给出教学 point，不提供从 (Document, vector) 批量转换的练习实现。
    # upsert(集合名, points=记录列表, wait=True)：写入并等待完成，返回 UpdateResult。
    client.upsert(
        collection_name=COLLECTION_NAME,
        wait=True,
        points=[
            PointStruct(
                id=17,
                vector=vectors[0].tolist(),
                payload={
                    "chunk_id": "rooms/guide.txt#L2-L2",
                    "text": room_text,
                    "source": "rooms/guide.txt",
                    "line_start": 2,
                    "line_end": 2,
                    "embedding_model": MODEL_NAME,
                },
            ),
            PointStruct(
                id=29,
                vector=vectors[0].tolist(),
                payload={
                    "chunk_id": "archive/rooms.txt#L5-L5",
                    "text": room_text,
                    "source": "archive/rooms.txt",
                    "line_start": 5,
                    "line_end": 5,
                    "embedding_model": MODEL_NAME,
                },
            ),
            PointStruct(
                id=43,
                vector=vectors[1].tolist(),
                payload={
                    "chunk_id": "finance/guide.txt#L2-L2",
                    "text": finance_text,
                    "source": "finance/guide.txt",
                    "line_start": 2,
                    "line_end": 2,
                    "embedding_model": MODEL_NAME,
                },
            ),
        ],
    )
