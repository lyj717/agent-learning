"""Day59 运行环境：建本地检索索引，测一次问答的检索/首字/总延迟与费用。

这里不实现 percentile / summarize_measurements，也不替学员判断瓶颈。
模型与检索都走本机已有缓存，不下载模型；密钥从仓库根目录 .env 读取，不打印。
"""

import json
import os
import time
from pathlib import Path
from statistics import median
from typing import Any

from qdrant_client import QdrantClient

from weeks.week02_tools.demos.shared.llm_client import make_client
from weeks.week05_rag.demos.day38.day38_embedding_support import create_embedding_model
from weeks.week05_rag.demos.day39.day39_support import prepare_collection
from weeks.week05_rag.demos.shared.rag_functions import (
    build_grounded_messages,
    chunk_documents,
    load_sources,
    retrieve_chunks,
    store_chunks,
    vectorize_chunks,
    vectorize_question,
)
from weeks.week06_retrieval_eval.demos.shared.answer_functions import cost_of_call

ROOT = Path(__file__).resolve().parents[4]
DAY57 = ROOT / "weeks/week08_evaluation_reliability/demos/day57"
DAY59 = ROOT / "weeks/week08_evaluation_reliability/demos/day59"
NOTES = "notes/python-notes.md"
PRICE_PATH = ROOT / "weeks/week06_retrieval_eval/demos/day47/day47_price_snapshot.json"
COLLECTION = "day59_chunks"
CHUNK_LINES = 8
OVERLAP_LINES = 2
RETRIEVE_K = 3


def load_price() -> dict[str, float]:
    """读取 Day47 的价格快照，返回 input_hit/input_miss/output 三项。"""
    data = json.loads(PRICE_PATH.read_text(encoding="utf-8"))
    return data["price"]


def load_cases() -> list[dict]:
    """读取 Day57 的 8 道题，只取题号与问题。"""
    cases = json.loads((DAY57 / "day57_cases.json").read_text(encoding="utf-8"))
    return [{"id": case["id"], "question": case["question"]} for case in cases]


def build_index() -> tuple[QdrantClient, Any, dict[str, Any]]:
    """建内存索引，返回客户端、向量模型与索引配置；不发起模型请求。"""
    model = create_embedding_model()
    originals = load_sources(ROOT, [NOTES])
    chunks = chunk_documents(originals, CHUNK_LINES, OVERLAP_LINES)
    client = QdrantClient(location=":memory:")
    prepare_collection(client, COLLECTION)
    stored = store_chunks(client, COLLECTION, vectorize_chunks(chunks, model))
    config = {
        "collection": COLLECTION,
        "chunks": stored,
        "chunk_lines": CHUNK_LINES,
        "overlap_lines": OVERLAP_LINES,
        "retrieve_k": RETRIEVE_K,
        "source": NOTES,
    }
    return client, model, config


def retrieve(
    client: QdrantClient, model: Any, question: str
) -> tuple[list[Any], float]:
    """编码问题并检索，返回证据片段与检索耗时（毫秒）。"""
    started = time.perf_counter()
    query_vector = vectorize_question(question, model)
    ranked = retrieve_chunks(client, COLLECTION, query_vector, RETRIEVE_K)
    retrieval_ms = (time.perf_counter() - started) * 1000
    return [document for document, _score in ranked], retrieval_ms


def answer_stream(
    client: Any, messages: list[dict[str, str]], model_name: str
) -> dict[str, Any]:
    """流式请求一次回答，测首字与总耗时，并返回正文、用量与结束原因。"""
    started = time.perf_counter()
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=1024,
        timeout=60,
        stream=True,
        stream_options={"include_usage": True},
        extra_body={"thinking": {"type": "disabled"}},
    )
    first_token: float | None = None
    text = ""
    usage = None
    finish_reason = ""
    for chunk in stream:
        if chunk.usage is not None:
            usage = chunk.usage
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        if choice.finish_reason:
            finish_reason = choice.finish_reason
        delta = choice.delta.content
        if delta:
            if first_token is None:
                first_token = time.perf_counter() - started
            text += delta
    total_seconds = time.perf_counter() - started
    if first_token is None:
        raise RuntimeError("流式响应没有收到任何正文")
    if usage is None:
        raise RuntimeError("流式响应没有返回 usage，无法计算费用")
    return {
        "raw_text": text,
        "ttft_ms": first_token * 1000,
        "generation_ms": total_seconds * 1000,
        "finish_reason": finish_reason,
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cached_tokens": getattr(usage, "prompt_cache_hit_tokens", 0) or 0,
        },
    }


def measure_one(
    client: QdrantClient, model: Any, api_client: Any, case: dict, price: dict
) -> dict[str, Any]:
    """测一道题：检索、流式生成、用量与费用；失败原样抛出。"""
    evidence, retrieval_ms = retrieve(client, model, case["question"])
    messages = build_grounded_messages(case["question"], evidence)
    if not messages:
        raise RuntimeError(f"{case['id']} 没有检索到证据，无法生成")
    answer = answer_stream(
        api_client, messages, os.environ.get("LLM_MODEL", "deepseek-flash")
    )
    usage = answer["usage"]
    cost = cost_of_call(
        usage["prompt_tokens"],
        usage["completion_tokens"],
        cached_tokens=usage["cached_tokens"],
        price=price,
    )
    return {
        "id": case["id"],
        "question": case["question"],
        "retrieval_ms": retrieval_ms,
        "ttft_ms": answer["ttft_ms"],
        "generation_ms": answer["generation_ms"],
        "end_to_end_ms": retrieval_ms + answer["generation_ms"],
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "cached_tokens": usage["cached_tokens"],
        "cost_cny": cost,
        "finish_reason": answer["finish_reason"],
        "raw_text": answer["raw_text"],
        "evidence_ids": [document.id for document in evidence],
    }


def measure_all(limit: int = 8) -> dict[str, Any]:
    """建一次索引，按题逐条测量；失败题记录错误并继续，原始返回一并保存。"""
    cases = load_cases()[:limit]
    price = load_price()
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    qdrant, model, index_config = build_index()
    try:
        with make_client() as api_client:
            for case in cases:
                print(f"\n{case['id']}｜{case['question']}")
                try:
                    row = measure_one(qdrant, model, api_client, case, price)
                except Exception as error:  # noqa: BLE001 - 测量失败要保留并继续。
                    errors.append(
                        {"id": case["id"], "error": f"{type(error).__name__}: {error}"}
                    )
                    print(f"  失败={type(error).__name__}: {error}")
                    continue
                rows.append(row)
                print(
                    f"  检索={row['retrieval_ms']:.0f}ms；首字={row['ttft_ms']:.0f}ms；"
                    f"生成={row['generation_ms']:.0f}ms；"
                    f"用量={row['prompt_tokens']}+{row['completion_tokens']}；"
                    f"费用={row['cost_cny']:.6f} 元"
                )
    finally:
        qdrant.close()
    return {
        "index": index_config,
        "price": price,
        "rows": rows,
        "errors": errors,
        "model": os.environ.get("LLM_MODEL", "deepseek-flash"),
    }


def measure_repeated(times: int, limit: int = 8) -> dict[str, Any]:
    """建一次索引，按轮重复测全部题；每行记 round，失败题也保留。

    times 表示跑几轮，limit 表示每轮测前几题（默认全部 8 题）。
    轮次在外层：第 1 轮 q01…q08，第 2 轮再 q01…q08，让负载在题间分布更均匀，
    第 1 轮同时充当预热。
    """
    if type(times) is not int or times < 1:
        raise ValueError("times 必须是正整数")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit 必须是正整数")
    cases = load_cases()[:limit]
    price = load_price()
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    qdrant, model, index_config = build_index()
    try:
        with make_client() as api_client:
            for round_no in range(1, times + 1):
                for case in cases:
                    print(f"\n第 {round_no} 轮｜{case['id']}｜{case['question']}")
                    try:
                        row = measure_one(qdrant, model, api_client, case, price)
                    except Exception as error:  # noqa: BLE001 - 失败保留并继续。
                        errors.append(
                            {
                                "round": round_no,
                                "id": case["id"],
                                "error": f"{type(error).__name__}: {error}",
                            }
                        )
                        print(f"  失败={type(error).__name__}: {error}")
                        continue
                    row["round"] = round_no
                    rows.append(row)
                    print(
                        f"  检索={row['retrieval_ms']:.0f}ms；"
                        f"首字={row['ttft_ms']:.0f}ms；"
                        f"生成={row['generation_ms']:.0f}ms；"
                        f"费用={row['cost_cny']:.6f} 元"
                    )
    finally:
        qdrant.close()
    return {
        "index": index_config,
        "price": price,
        "rows": rows,
        "errors": errors,
        "model": os.environ.get("LLM_MODEL", "deepseek-flash"),
        "times": times,
    }


def describe_repeats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按题汇总重复测量，返回每题样本数、首字与端到端的 min/median/max。"""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["id"], []).append(row)
    summary = []
    for case_id in sorted(grouped):
        items = grouped[case_id]
        ttft = sorted(item["ttft_ms"] for item in items)
        end_to_end = sorted(item["end_to_end_ms"] for item in items)
        summary.append(
            {
                "id": case_id,
                "count": len(items),
                "ttft_min": ttft[0],
                "ttft_median": median(ttft),
                "ttft_max": ttft[-1],
                "end_to_end_min": end_to_end[0],
                "end_to_end_median": median(end_to_end),
                "end_to_end_max": end_to_end[-1],
            }
        )
    return summary
