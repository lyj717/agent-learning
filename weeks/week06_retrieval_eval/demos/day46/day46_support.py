"""AI 运行环境：固定资料与开发题，提供一次一题的向量回调和留证，不写批量整合答案。"""

import hashlib
import json
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path

from langchain_core.documents import Document
from qdrant_client import QdrantClient

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day39.day39_support import prepare_collection
from weeks.week05_rag.demos.shared.rag_functions import (
    retrieve_chunks,
    store_chunks,
    vectorize_chunks,
    vectorize_question,
)
from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    LABELS,
    SNAPSHOT_SHA256,
    load_originals,
    make_chunks,
    read_json,
    validate_labels,
)
from weeks.week06_retrieval_eval.demos.day45.day45_support import TOKENIZER_VERSION
from weeks.week06_retrieval_eval.demos.day46.day46_checks import run_comparison_checks
from weeks.week06_retrieval_eval.demos.shared import evaluation_functions
from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import (
    check_ranked_ids,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY = Path(__file__).resolve().parent
LABELS_SHA256 = "46b7b4312e2597f73a9a0cb6c906e30bfe4e9cfc861f5b0c687b15139613ee2b"


def load_data() -> tuple[list[dict], list[Document]]:
    """严格核对固定原文与三十题标注，返回全部题与旧切分；不进行任何检索。"""
    if hashlib.sha256(LABELS.read_bytes()).hexdigest() != LABELS_SHA256:
        raise ValueError("标注版本已变化，请先核对，不直接继续这组固定对比")
    originals = load_originals()
    dataset = read_json(LABELS)
    validate_labels(dataset, originals, require_complete=True)
    return dataset["cases"], make_chunks(originals)


def describe_report(report: dict) -> dict[str, list[str]]:
    """打印已有报告中的客观数据，按 Recall 列有答案题变化；不解释原因或替学员下结论。"""
    changes = {"improved": [], "unchanged": [], "regressed": []}
    for row in report["rows"]:
        before = row["vector_metrics"]
        after = row["fused_metrics"]
        print(
            f"\n题号={row['id']}；问题={row['question']}；相关编号={row['relevant_ids']}"
        )
        for name in ("vector", "keyword", "fused"):
            print(f"  {name} 排名={row[f'{name}_ids']}")
        print(f"  仅向量指标={before}；融合指标={after}")
        if before["recall"] is not None:
            if after["recall"] > before["recall"]:
                changes["improved"].append(row["id"])
            elif after["recall"] < before["recall"]:
                changes["regressed"].append(row["id"])
            else:
                changes["unchanged"].append(row["id"])
    print("\n同一批开发题的汇总（有答案题均值，无答案题独立计数）：")
    print(f"仅向量={report['vector_summary']}")
    print(f"融合={report['fused_summary']}")
    print(f"按 Recall 的有答案题变化={changes}")
    print("没有生成回答；这些数不判断回答完整、引用支持或幻觉。")
    return changes


def run_batch(compare_fn: Callable[..., dict], run_dir: Path) -> dict:
    """给学员函数提供固定全库及 vector_search(question,k)，保存逐次真实本地检索。"""
    cases, chunks = load_data()
    dev = [row for row in cases if row["split"] == "dev"]
    print(
        f"开发题={len(dev)}；留出题={len(cases) - len(dev)}，留出题不检索；全库片段={len(chunks)}"
    )
    print("本轮仅向量组为新运行对照；每题取得一次向量榜，同时供融合组使用。")
    print("沿用 BAAI/bge-small-zh-v1.5、512 维、embed 方式、COSINE；只读已缓存模型。")
    model = create_embedding_model(download=False)
    index = {chunk.id: chunk for chunk in chunks}
    calls = []
    # location=:memory: 创建内存库；只在本次运行使用，不改 Week05 旧数据库。
    client = QdrantClient(location=":memory:")
    try:
        prepare_collection(client, "chunks")
        store_chunks(client, "chunks", vectorize_chunks(chunks, model))

        def vector_search(question: str, k: int) -> list[str]:
            """本题一次真实本地编码/检索，返回 list[str]；记录榜单后交给学员整合函数。"""
            if (
                len(calls) >= len(dev)
                or question != dev[len(calls)]["question"]
                or k != 3
            ):
                raise ValueError("应按开发题原顺序每题检索一次，固定 k=3，不检索留出题")
            candidates = retrieve_chunks(
                client, "chunks", vectorize_question(question, model), limit=k
            )
            ranking = []
            for chunk, _score in candidates:
                if chunk.id not in index or chunk != index[chunk.id]:
                    raise ValueError("向量候选与固定全库的出处或正文不一致")
                ranking.append(chunk.id)
            check_ranked_ids(ranking, set(index), k)
            trace = {
                "id": dev[len(calls)]["id"],
                "question": question,
                "k": k,
                "ranked_ids": ranking,
                "scores": [score for _, score in candidates],
            }
            # 逐次追加 JSON 行：中途失败也保留此前完成的检索，不覆盖其他运行。
            with (run_dir / "vector_calls.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps(trace, ensure_ascii=False) + "\n")
            calls.append(trace)
            return ranking

        report = compare_fn(cases, chunks, vector_search, k=3, rank_constant=60)
    finally:
        # QdrantClient 不是上下文管理器；close() 显式释放客户端，异常时也执行。
        client.close()
    if len(calls) != len(dev) or [row["id"] for row in report["rows"]] != [
        row["id"] for row in dev
    ]:
        raise ValueError("实际检索数或结果题号与开发集不一致，不能保存为成功评测")
    report["recall_changes"] = describe_report(report)
    report["retrieved_case_ids"] = [call["id"] for call in calls]
    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def run_entry(part: str, compare_fn: Callable[..., dict], exercise_path: Path) -> None:
    """记录配置与代码摘要，先过人工对照；batch 才加载本地模型运行开发题。"""
    config = {
        "part": part,
        "source_snapshot_sha256": SNAPSHOT_SHA256,
        "labels_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "evaluation_functions_sha256": hashlib.sha256(
            Path(evaluation_functions.__file__).read_bytes()
        ).hexdigest(),
        "support_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "chunk_lines": 8,
        "overlap_lines": 2,
        "channel_limit": 3,
        "final_k": 3,
        "rank_constant": 60,
        "tokenizer": TOKENIZER_VERSION,
        "embedding_model": MODEL_NAME,
        "vector_size": VECTOR_SIZE,
        "embedding_method": "embed",
        "distance": "COSINE",
        "vector_origin": "day46_fresh_once_per_dev",
        "split": "dev",
        "generation_calls": 0,
        "versions": {
            name: version(name) for name in ("rank-bm25", "fastembed", "qdrant-client")
        },
    }

    def execute(run_dir: Path) -> None:
        """对照未通过不进入真实批量分支；题干尚未写时明确报错。"""
        run_comparison_checks(compare_fn)
        if part == "batch":
            run_batch(compare_fn, run_dir)

    run_logged(
        part,
        execute,
        config,
        exercise_path,
        DAY / "outputs",
        origin_env="DAY46_RUN_ORIGIN",
    )
