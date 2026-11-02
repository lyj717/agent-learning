"""AI 运行环境：固定词项规则与旧题探查，不实现学员的关键词排序或 RRF。"""

import re
from collections.abc import Callable

from langchain_core.documents import Document

from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    LABELS,
    REPLAYS,
    SNAPSHOT_SHA256,
    load_originals,
    make_chunks,
    read_json,
    validate_labels,
)
from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import (
    project_relevance,
    score_query,
)

TOKENIZER_VERSION = "zh-char-ascii-v1"


def tokenize_text(text: str) -> list[str]:
    """提供给 A 的固定辅助：统一大小写，保留英文标识符、整数词项与中文单字。

    text（str，必填）为问题或片段正文。返回 list[str]，按原顺序保留重复词项；
    空白或纯标点返回 []。不修改字符串，不做同义词扩展或停用词过滤。
    对应 day45_tokenize_demo.py；本课保持该规则不变。
    """
    # re.findall(模式, 文本)：返回全部匹配；casefold() 统一大小写，均不修改原文。
    return re.findall(r"[a-z_][a-z_0-9]*|[0-9]+|[\u4e00-\u9fff]", text.casefold())


def check_ranked_ids(value: list[str], allowed: set[str], limit: int) -> None:
    """环境校验排名返回值的类型、上限、唯一编号和编号来源。"""
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TypeError("排名应返回 list[str]")
    if len(value) > limit or len(value) != len(set(value)):
        raise ValueError("排名不能超过 limit，也不能重复编号")
    if not set(value) <= allowed:
        raise ValueError("排名中含有不属于本批输入的编号")


def probe_case(
    case_id: str,
    keyword_fn: Callable[..., list[str]],
    fuse_fn: Callable[..., list[str]],
) -> dict:
    """探查旧开发题：调用 A 得到新关键词排名，再调用 B 融合，与旧向量排名同 k 比较。

    case_id 为 q01～q10；keyword_fn、fuse_fn 是学员 A、B 函数，不是模型请求函数。
    三参数必填。固定 8 行切块/重叠 2、每路最多 3 条、最终 k=3、rank_constant=60。
    返回含问题、词项、依据、相关编号和三路排名/指标的 dict，供主入口保存 report.json。
    只用固定全文和旧向量候选；不重新查询向量库、不请求回答模型、不探查留出题。
    输入版本或回调返回值不符时抛错，由外层日志保留现场。
    """
    originals = load_originals()
    dataset = read_json(LABELS)
    validate_labels(dataset, originals, require_complete=True)
    replay = read_json(REPLAYS)
    if replay["source_snapshot_sha256"] != SNAPSHOT_SHA256:
        raise ValueError("旧向量结果的原文版本不一致")
    if case_id not in {f"q{i:02d}" for i in range(1, 11)}:
        raise ValueError("本入口只探查旧开发题 q01～q10，不探查留出题")
    row = next(row for row in dataset["cases"] if row["id"] == case_id)
    saved = replay["cases"][case_id]
    if row["split"] != "dev" or row["question"] != saved["question"]:
        raise ValueError("题目或分组已变化，不能沿用旧向量排名")
    chunks = make_chunks(originals)
    index = {chunk.id: chunk for chunk in chunks}
    vector_ids = []
    for raw, score in saved["candidates"]:
        chunk = Document(**raw)
        if chunk.id not in index or chunk != index[chunk.id]:
            raise ValueError("旧候选与固定全文及切分不一致")
        vector_ids.append(chunk.id)
        print(f"旧向量候选={chunk.id}；原始向量分数={score}")
    check_ranked_ids(vector_ids, set(index), 3)
    relevant = project_relevance(row["evidence"], chunks)
    print(f"问题={row['question']}")
    print(f"固定问题词项={tokenize_text(row['question'])}")
    print(f"标注原文依据={row['evidence']}；相关编号={sorted(relevant)}")
    print("接下来执行学员 A、B；新结果与旧向量结果分开保存。")
    keyword_ids = keyword_fn(row["question"], chunks, limit=3)
    check_ranked_ids(keyword_ids, set(index), 3)
    fused_ids = fuse_fn(vector_ids, keyword_ids, limit=3, rank_constant=60)
    check_ranked_ids(fused_ids, set(vector_ids) | set(keyword_ids), 3)
    channels = {}
    for name, ranking in [
        ("vector", vector_ids),
        ("keyword", keyword_ids),
        ("fused", fused_ids),
    ]:
        metrics = score_query(ranking, relevant, k=3)
        channels[name] = {"ranked_ids": ranking, "metrics": metrics}
        print(f"\n{name} 的有序编号={ranking}")
        for chunk_id in ranking:
            print(f"  {chunk_id}；原文片段={index[chunk_id].page_content!r}")
        print(f"{name} 的指标={metrics}")
    print("\n本次只探查一个开发题；向量分支读旧结果，关键词与融合分支为本次新运行。")
    print("资料、标签、切分、最终 k 保持；本次没有比较切分或重排，也没有调用回答模型。")
    print("单题变化不能代替整批开发集结果；留出题的效果仍等待方案冻结后再看。")
    return {
        "case_id": case_id,
        "question": row["question"],
        "query_tokens": tokenize_text(row["question"]),
        "evidence": row["evidence"],
        "relevant_ids": sorted(relevant),
        "channels": channels,
    }
