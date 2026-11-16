"""Day60 运行环境：同一批题、同一次会话里对照「原证据」与「缩小证据」。

基线：8 行/重叠 2、取 3 条；优化：4 行/重叠 1、取 2 条。
两套索引共用一个向量模型；每轮交替先后顺序，减少时段偏差。
质量检查复用 Day57 的规则与 Day58 的裁判，不替学员写结论。
"""

import json
import os
import time
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
from weeks.week08_evaluation_reliability.demos.day59.day59_support import (
    NOTES,
    ROOT,
    answer_stream,
    load_cases,
    load_price,
)

DAY57 = ROOT / "weeks/week08_evaluation_reliability/demos/day57"
DAY60 = ROOT / "weeks/week08_evaluation_reliability/demos/day60"

BASELINE = {
    "name": "baseline",
    "chunk_lines": 8,
    "overlap_lines": 2,
    "retrieve_k": 3,
}
OPTIMIZED = {
    "name": "optimized",
    "chunk_lines": 4,
    "overlap_lines": 1,
    "retrieve_k": 2,
}


def build_index(model: Any, config: dict) -> tuple[QdrantClient, dict[str, Any]]:
    """按一组切分/检索参数建内存索引，返回客户端与索引信息。"""
    originals = load_sources(ROOT, [NOTES])
    chunks = chunk_documents(originals, config["chunk_lines"], config["overlap_lines"])
    client = QdrantClient(location=":memory:")
    collection = f"day60_{config['name']}"
    prepare_collection(client, collection)
    stored = store_chunks(client, collection, vectorize_chunks(chunks, model))
    info = {
        **config,
        "collection": collection,
        "chunks": stored,
        "source": NOTES,
    }
    return client, info


def retrieve_from(
    client: QdrantClient, collection: str, model: Any, question: str, k: int
) -> tuple[list[Any], float]:
    """编码问题并检索指定集合，返回片段与检索耗时（毫秒）。"""
    started = time.perf_counter()
    vector = vectorize_question(question, model)
    ranked = retrieve_chunks(client, collection, vector, k)
    elapsed = (time.perf_counter() - started) * 1000
    return [document for document, _score in ranked], elapsed


def measure_paired(rounds: int = 3, limit: int = 8) -> dict[str, Any]:
    """同一会话里交替测两套配置，逐轮保存每次结果。"""
    if type(rounds) is not int or rounds < 1:
        raise ValueError("rounds 必须是正整数")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit 必须是正整数")
    cases = load_cases()[:limit]
    price = load_price()
    model = create_embedding_model()
    clients: dict[str, QdrantClient] = {}
    indexes: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    try:
        for config in (BASELINE, OPTIMIZED):
            client, info = build_index(model, config)
            clients[config["name"]] = client
            indexes[config["name"]] = info
        with make_client() as api_client:
            for round_no in range(1, rounds + 1):
                order = (
                    (BASELINE, OPTIMIZED)
                    if round_no % 2 == 1
                    else (OPTIMIZED, BASELINE)
                )
                for config in order:
                    name = config["name"]
                    collection = indexes[name]["collection"]
                    for case in cases:
                        print(f"\n第 {round_no} 轮｜{name}｜{case['id']}")
                        try:
                            evidence, retrieval_ms = retrieve_from(
                                clients[name],
                                collection,
                                model,
                                case["question"],
                                config["retrieve_k"],
                            )
                            messages = build_grounded_messages(
                                case["question"], evidence
                            )
                            if not messages:
                                raise RuntimeError("没有检索到证据")
                            answer = answer_stream(
                                api_client,
                                messages,
                                os.environ.get("LLM_MODEL", "deepseek-flash"),
                            )
                        except Exception as error:  # noqa: BLE001 - 保留失败继续。
                            errors.append(
                                {
                                    "round": round_no,
                                    "condition": name,
                                    "id": case["id"],
                                    "error": f"{type(error).__name__}: {error}",
                                }
                            )
                            print(f"  失败={type(error).__name__}: {error}")
                            continue
                        usage = answer["usage"]
                        cost = cost_of_call(
                            usage["prompt_tokens"],
                            usage["completion_tokens"],
                            cached_tokens=usage["cached_tokens"],
                            price=price,
                        )
                        row = {
                            "condition": name,
                            "round": round_no,
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
                            "evidence": [
                                {
                                    "id": document.id,
                                    "text": document.page_content,
                                }
                                for document in evidence
                            ],
                        }
                        rows.append(row)
                        print(
                            f"  检索={row['retrieval_ms']:.0f}ms；"
                            f"首字={row['ttft_ms']:.0f}ms；"
                            f"端到端={row['end_to_end_ms']:.0f}ms；"
                            f"用量={row['prompt_tokens']}+{row['completion_tokens']}；"
                            f"费用={row['cost_cny']:.6f} 元"
                        )
    finally:
        for client in clients.values():
            client.close()
    return {
        "rounds": rounds,
        "limit": limit,
        "price": price,
        "indexes": {"baseline": BASELINE, "optimized": OPTIMIZED},
        "rows": rows,
        "errors": errors,
        "model": os.environ.get("LLM_MODEL", "deepseek-flash"),
    }


def describe_condition(rows: list[dict], condition: str) -> list[dict[str, Any]]:
    """按题汇总一个条件的 ttft/端到端/费用中位数。"""
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if row["condition"] == condition:
            grouped.setdefault(row["id"], []).append(row)
    summary = []
    for case_id in sorted(grouped):
        items = grouped[case_id]
        summary.append(
            {
                "id": case_id,
                "count": len(items),
                "ttft_median": median(item["ttft_ms"] for item in items),
                "end_to_end_median": median(item["end_to_end_ms"] for item in items),
                "cost_median": median(item["cost_cny"] for item in items),
            }
        )
    return summary


def parse_generated(raw: str) -> dict[str, Any]:
    """解析生成回答的 JSON；失败抛 ValueError，保留原文由调用方保存。"""
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {
        "status",
        "answer",
        "cited_ids",
    }:
        raise ValueError("回答 JSON 键不是 status/answer/cited_ids")
    if data["status"] not in {"answered", "insufficient"}:
        raise ValueError("status 不是 answered/insufficient")
    if not isinstance(data["answer"], str):
        raise ValueError("answer 不是字符串")  # noqa: TRY004 - 模型输出按数据错误处理。
    if not isinstance(data["cited_ids"], list) or any(
        not isinstance(item, str) for item in data["cited_ids"]
    ):
        raise ValueError("cited_ids 不是字符串列表")
    return data


def selected_rows(rows: list[dict], condition: str) -> dict[str, dict]:
    """每个条件每题取最后一轮能解析的回答，返回题号到行。"""
    selected: dict[str, dict] = {}
    for row in rows:
        if row["condition"] != condition:
            continue
        try:
            row["parsed"] = parse_generated(row["raw_text"])
        except ValueError:
            continue
        current = selected.get(row["id"])
        if current is None or row["round"] > current["round"]:
            selected[row["id"]] = row
    return selected


def evaluate_quality(rows: list[dict]) -> dict[str, Any]:
    """用 Day57 规则和 Day58 裁判检查两套条件下的回答，各 8 题。"""
    from weeks.week08_evaluation_reliability.demos.day58.day58_support import (
        judge_once,
    )
    from weeks.week08_evaluation_reliability.exercises.day57_eval_exercises import (
        judge_answer,
    )
    from weeks.week08_evaluation_reliability.exercises.day58_judge_exercises import (
        build_judge_messages,
        parse_judge_verdict,
    )

    cases = {
        case["id"]: case
        for case in json.loads((DAY57 / "day57_cases.json").read_text(encoding="utf-8"))
    }
    results = []
    for condition in ("baseline", "optimized"):
        selected = selected_rows(rows, condition)
        for case_id in sorted(selected):
            row = selected[case_id]
            case = cases[case_id]
            answer = row["parsed"]
            rule = None
            rule_error = None
            try:
                rule_case = {**case, "retrieved_ids": row["evidence_ids"]}
                rule = judge_answer(rule_case, answer)
            except Exception as error:  # noqa: BLE001 - 质量检查失败要保留。
                rule_error = f"{type(error).__name__}: {error}"
            judge = None
            judge_error = None
            try:
                judge_case = {
                    "id": case_id,
                    "question": case["question"],
                    "evidence": row["evidence"],
                }
                call = judge_once(build_judge_messages(judge_case, answer))
                judge = parse_judge_verdict(call["raw_text"])
            except Exception as error:  # noqa: BLE001 - 裁判失败要保留。
                judge_error = f"{type(error).__name__}: {error}"
            results.append(
                {
                    "condition": condition,
                    "id": case_id,
                    "rule": rule,
                    "rule_error": rule_error,
                    "judge": judge,
                    "judge_error": judge_error,
                    "evidence_ids": row["evidence_ids"],
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                }
            )
    return {"rows": results, "model": os.environ.get("LLM_MODEL", "deepseek-flash")}
