"""Day 38 的运行环境：固定中文模型和缓存位置，不实现学员的向量配对。"""

from pathlib import Path

from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
VECTOR_SIZE = 512
MODEL_CACHE = Path(__file__).resolve().parent / "outputs" / "embedding_model"


def create_embedding_model(download: bool = False) -> TextEmbedding:
    """初始化本课 CPU 模型；默认只读本地缓存，download=True 才允许下载。"""
    # TextEmbedding(模型名, 缓存目录等)：加载模型，返回能调用 embed 的对象。
    # local_files_only=True 禁止下载；threads=2 控制 CPU 线程数，cuda=False 使用 CPU。
    return TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE),
        threads=2,
        cuda=False,
        local_files_only=not download,
    )
