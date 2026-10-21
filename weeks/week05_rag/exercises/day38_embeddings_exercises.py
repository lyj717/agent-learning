"""Day 38：把已有片段与问题向量化，保留正文和来源的对应。

从仓库根目录运行：本文件 --part a 或 --part b，默认 a。
A 复用自己已完成的 Day 36/37；B 有独立输入，可单独做。
模型环境由 AI 准备；A/B 实现与末尾三道观察由学员完成。
"""

import argparse
import sys
from pathlib import Path

from fastembed import TextEmbedding
from langchain_core.documents import Document

REPO_ROOT = Path(__file__).resolve().parents[3]
DAY38 = Path(__file__).resolve().parents[1] / "demos" / "day38"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day38.day38_vector_meaning_demo import cosine_similarity
from weeks.week05_rag.exercises.day36_sources_exercises import load_sources
from weeks.week05_rag.exercises.day37_chunks_exercises import chunk_documents


def vectorize_chunks(
    chunks: list[Document], model: TextEmbedding
) -> list[tuple[Document, list[float]]]:
    """批量编码片段，保留向量与原片段的对应。"""
    if not chunks:
        return []

    # 1. 校验输入，并收集需要编码的原始正文。
    texts = []
    for chunk in chunks:
        if not chunk.page_content.strip():
            raise ValueError(f"片段 {chunk.id} 的正文不能为空白")
        texts.append(chunk.page_content)

    # 2. 调用模型、收集向量数组，并核对条数。
    embedding_generator = model.embed(documents=texts)
    vector_arrays = list(embedding_generator)
    if len(vector_arrays) != len(chunks):
        raise ValueError(
            f"模型返回向量条数不符：片段 {len(chunks)} 条，向量 {len(vector_arrays)} 条"
        )

    # 3. 转为普通数值列表，核对维度，再与原片段配对。
    chunk_vector_pairs = []
    for index, vector_array in enumerate(vector_arrays):
        vector_values = vector_array.tolist()
        if len(vector_values) != VECTOR_SIZE:
            raise ValueError(
                f"第 {index + 1} 条向量维度不符：期望 {VECTOR_SIZE}，实际 {len(vector_values)}"
            )
        chunk_vector_pairs.append((chunks[index], vector_values))
    return chunk_vector_pairs


def vectorize_question(question: str, model: TextEmbedding) -> list[float]:
    """用兼容模型编码单个问题，返回普通数值向量。"""
    if not question.strip():
        raise ValueError("问题不能为空！")
    generator = model.embed(question)
    vectors = list(generator)
    if len(vectors) != 1:
        raise ValueError("问题数不为1！")
    vector = vectors[0]
    if len(vector) != VECTOR_SIZE:
        raise ValueError("向量长度不匹配！")
    return vector.tolist()


# ===== 以下是 AI 提供的检查环境，不是学员函数的参考实现 =====
def run_a(model: TextEmbedding) -> None:
    """展示真实编码后的对应关系与输入边界，供学员自己核对。"""
    originals = load_sources(
        DAY38 / "materials", ["notes/equipment.md", "archive/equipment.md"]
    )
    chunks = chunk_documents(originals)
    before = [chunk.model_dump() for chunk in chunks]
    print(
        f"模型={MODEL_NAME}；每条期望维度={VECTOR_SIZE}；输入片段数实际={len(chunks)}，期望=3"
    )
    result = vectorize_chunks(chunks, model)
    print(f"返回配对数实际={len(result)}，期望=3")
    # 另用原始 API 得到校对值，只检查对应关系，不硬编码具体浮点数。
    expected_vectors = list(model.embed([chunk.page_content for chunk in chunks]))
    for index, (document, vector) in enumerate(result):
        print(f"\n配对[{index}] id={document.id}")
        print(
            f"source={document.metadata['source']}；原行={document.metadata['line_start']}～{document.metadata['line_end']}"
        )
        print(f"正文={document.page_content!r}")
        print(
            f"向量为普通列表实际={isinstance(vector, list)}，期望=True；维度实际={len(vector)}，期望=512"
        )
        print(
            f"所有元素为 Python float 实际={all(isinstance(n, float) for n in vector)}，期望=True"
        )
        print(f"保留相应原片段对象实际={document is chunks[index]}，期望=True")
        print(
            f"与相应原文单独校对一致实际={all(abs(a - b) < 1e-5 for a, b in zip(vector, expected_vectors[index]))}，期望=True"
        )
        print(f"向量前 5 项={vector[:5]}")
    print(
        f"\n输入未改动实际={[chunk.model_dump() for chunk in chunks] == before}，期望=True"
    )
    print(
        f"第 0/2 条正文相同实际={chunks[0].page_content == chunks[2].page_content}，期望=True"
    )
    print(f"第 0/2 条 id 不同实际={chunks[0].id != chunks[2].id}，期望=True")
    print(f"空清单实际={vectorize_chunks([], model)}，期望=[]")
    blank = Document(page_content=" \n ", id="blank", metadata={"source": "blank.md"})
    try:
        vectorize_chunks([chunks[0], blank, chunks[1]], model)
    except ValueError:
        print("夹有空白片段的批次实际=ValueError，期望=ValueError")
    else:
        print("夹有空白片段的批次实际=未报错，期望=ValueError")


def run_b(model: TextEmbedding) -> None:
    """用独立短文本打印问题向量和相似度，不进行检索排序或回答。"""
    passages = [
        "访客需要在前台登记后领取临时通行证。",
        "会议室的投影设备由行政人员统一维护。",
    ]
    questions = ["外来人员怎样进入办公区？", "访客通行证可以连续使用多少天？"]
    print("资料和问题都是 AI 教学输入，不是学员自有资料的问答基线。")
    for index, passage in enumerate(passages):
        print(f"资料[{index}]：{passage}")
    passage_vectors = list(model.embed(passages))
    for question in questions:
        vector = vectorize_question(question, model)
        print(f"\n问题：{question}")
        print(
            f"普通列表实际={isinstance(vector, list)}，期望=True；维度实际={len(vector)}，期望=512"
        )
        print(
            f"所有元素为 Python float 实际={all(isinstance(n, float) for n in vector)}，期望=True"
        )
        print(f"向量前 5 项={vector[:5]}")
        for index, passage_vector in enumerate(passage_vectors):
            score = cosine_similarity(vector, passage_vector.tolist())
            print(
                f"与资料[{index}]的余弦={score:.6f}；只记录实际分数，不预设哪句必胜。"
            )
    for question in ("", " \n "):
        try:
            vectorize_question(question, model)
        except ValueError:
            print(f"空白问题 {question!r} 实际=ValueError，期望=ValueError")
        else:
            print(f"空白问题 {question!r} 实际=未报错，期望=ValueError")


def main() -> None:
    """初始化已缓存的模型，再运行选中的题目。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("a", "b"), default="a", help="只运行一道题")
    args = parser.parse_args()
    print("正在加载当天缓存的中文模型；本入口不下载，不调用 DeepSeek。", flush=True)
    model = create_embedding_model()
    if args.part == "a":
        run_a(model)
    else:
        run_b(model)


if __name__ == "__main__":
    main()


# ===== 现象与原因：请亲自运行后，用自己的话写在下面 =====
# 1. A 中两个正文相同的片段分别来自哪里，id 与原行范围是什么？为什么仍返回两条记录？
#    我的实际输出与原因：
#   分别来自notes/equipment.md和archive/equipment.md
#   id:notes/equipment.md#L1-L3和archive/equipment.md#L1-L3
#   原行范围：原行=1～3和原行=1～3
#   因为这出自两个不一样的文本
# 2. A 返回几对记录，每条几维；B 返回的外层形状和 A 有什么不同？为什么问题与片段
#    只检查维度一样仍不够，还需要记录模型与生成方式？
#    我的实际输出与原因：
#   A返回三对记录，每条512维
#   B只返回向量，A返回向量和对应的原片段
#   维度相同，只能说明每条向量的数字个数相同，不能说明这些数字可以直接比较。
#   不同模型可能把文本映射到不同的表示空间；即使都输出 512 维，混用后算出的余弦值也未必能反映文本的相关性。因此，还要记录模型名称、版本和生成方式，用于确认资料向量与问题向量采用了兼容的方案，并方便复现和排错。
# 3. B 的“访客通行证可以连续使用多少天”与资料的实际分数是多少？原文是否给出了天数？
#    这些结果说明相似度分数能判断什么、不能保证什么？
#    我的实际输出与原因：
#   与资料[0]的余弦=0.638380  与资料[1]的余弦=0.383729 原文没有给出分数
#   能判断资料中是否有意思相近的语料，不能保证资料的实际可用程度
