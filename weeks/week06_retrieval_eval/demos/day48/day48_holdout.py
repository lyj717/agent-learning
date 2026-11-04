"""Day48 运行环境：冻结选择、留出检索与单方案回答、汇总；判断和报告由学员完成。"""

import argparse
import hashlib
import json
import os
import sys
import time
from collections.abc import Callable
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day39.day39_support import prepare_collection
from weeks.week05_rag.demos.day40.day40_model_io import request_grounded_json
from weeks.week05_rag.demos.shared.rag_functions import (
    retrieve_chunks,
    store_chunks,
    vectorize_chunks,
    vectorize_question,
)
from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    LABELS,
    SNAPSHOT,
    load_originals,
)
from weeks.week06_retrieval_eval.demos.day45.day45_support import TOKENIZER_VERSION
from weeks.week06_retrieval_eval.demos.day46.day46_support import load_data
from weeks.week06_retrieval_eval.demos.day47.day47_support import (
    PRICE_SNAPSHOT,
    collect_answer,
    digest,
    resource_summary,
    save_json,
    write_review_pack,
)
from weeks.week06_retrieval_eval.demos.shared.answer_functions import summarize_reviews
from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import (
    check_ranked_ids,
    evaluate_queries,
    fuse_rankings,
    project_relevance,
    rank_keywords,
    score_query,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY = Path(__file__).resolve().parent
HOLDOUT_IDS = [f"q{number:02d}" for number in range(25, 31)]
GROUPS = ("vector", "fused")
PROTECTED_FILES = (
    "frozen.json",
    "cases_snapshot.json",
    "sources_snapshot.json",
    "price_snapshot.json",
    "retrieval.json",
    "responses.json",
    "holdout_started.json",
)
FROZEN_FILES = [
    SNAPSHOT,
    LABELS,
    Path(__file__),
    ROOT / "weeks/week06_retrieval_eval/demos/shared/evaluation_functions.py",
    ROOT / "weeks/week06_retrieval_eval/demos/shared/answer_functions.py",
    ROOT / "weeks/week05_rag/demos/shared/rag_functions.py",
    ROOT / "weeks/week05_rag/demos/day38/day38_embedding_support.py",
    ROOT / "weeks/week05_rag/demos/day39/day39_support.py",
    ROOT / "weeks/week05_rag/demos/day40/day40_model_io.py",
    ROOT / "weeks/week02_tools/demos/shared/llm_client.py",
    ROOT / "weeks/week06_retrieval_eval/demos/day44/day44_support.py",
    ROOT / "weeks/week06_retrieval_eval/demos/day46/day46_support.py",
    ROOT / "weeks/week06_retrieval_eval/demos/day47/day47_support.py",
    ROOT / "weeks/week06_retrieval_eval/demos/day47/day47_price_snapshot.json",
    ROOT / "weeks/week06_retrieval_eval/demos/day47/day47_判分说明.md",
]


def read_json(path: Path) -> dict | list:
    """读取已指定的 UTF-8 JSON；只用于本日环境，不修改输入文件。"""
    return json.loads(path.read_text(encoding="utf-8"))


def value_digest(value: object) -> str:
    """用稳定的 JSON 顺序识别冻结内容；不是对未见结果的自动证明。"""
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def current_settings() -> dict:
    """读取可公开的配置与版本；不创建客户端、不打印密钥或服务地址。"""
    load_dotenv(ROOT / ".env")
    endpoint = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    return {
        "files": {str(path.relative_to(ROOT)): digest(path) for path in FROZEN_FILES},
        "chunk_lines": 8,
        "overlap_lines": 2,
        "k": 3,
        "rank_constant": 60,
        "tokenizer": TOKENIZER_VERSION,
        "embedding_model": MODEL_NAME,
        "vector_size": VECTOR_SIZE,
        "embedding_method": "embed",
        "distance": "COSINE",
        "requested_model": os.environ.get("LLM_MODEL", "deepseek-flash"),
        "endpoint_digest": hashlib.sha256(endpoint.encode("utf-8")).hexdigest(),
        "max_tokens": 1024,
        "thinking": "disabled",
        "temperature": "not_set_by_request_layer",
        "timeout_s": 45,
        "sdk_retries": 0,
        "versions": {
            name: version(name)
            for name in ("rank-bm25", "fastembed", "qdrant-client", "openai")
        },
    }


def freeze_choice(run_dir: Path) -> None:
    """只保存学员预先填写的选择和固定配置，不查看留出检索或回答结果。"""
    choice = read_json(DAY / "day48_choice.json")
    if (
        not isinstance(choice, dict)
        or choice.get("selected_group") not in GROUPS
        or not isinstance(choice.get("reason"), str)
        or not choice["reason"].strip()
    ):
        raise ValueError(
            "先填 day48_choice.json：selected_group 选 vector/fused，reason 写选择理由"
        )
    frozen = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "selected_group": choice["selected_group"],
        "reason": choice["reason"],
        "settings": current_settings(),
    }
    frozen["fingerprint"] = value_digest(frozen)
    save_json(run_dir / "frozen.json", frozen)
    print(f"已冻结：{frozen['selected_group']}；理由：{frozen['reason']}")
    print("本步没有检索或生成留出回答。下一步 run 的 --freeze-dir 指向本目录。")


def check_freeze(path: Path, *, check_current: bool) -> dict:
    """核对冻结内容；开始实验时还核对当前代码配置，汇总历史结果时只核对原快照。"""
    frozen = read_json(path)
    if not isinstance(frozen, dict):
        raise TypeError("冻结记录应为 JSON 对象")
    content = {key: value for key, value in frozen.items() if key != "fingerprint"}
    if (
        type(frozen.get("schema_version")) is not int
        or frozen.get("schema_version") != 1
        or frozen.get("selected_group") not in GROUPS
        or not isinstance(frozen.get("reason"), str)
        or not frozen["reason"].strip()
        or not isinstance(frozen.get("settings"), dict)
        or frozen.get("fingerprint") != value_digest(content)
    ):
        raise ValueError("冻结记录不完整或已改变，请保留原文件，不回写历史记录")
    if check_current and frozen["settings"] != current_settings():
        raise ValueError("代码、资料、模型或参数已变化；旧冻结记录不能用于这个新版本")
    return frozen


def compare_holdout(
    cases: list[dict],
    chunks: list[Document],
    vector_search: Callable[[str, int], list[str]],
    save_row: Callable[[dict], None],
) -> dict:
    """AI 编排旧函数：保留 holdout 标签，先检查整批依据，再逐题比较两路检索。"""
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)) or any(case["split"] != "holdout" for case in cases):
        raise ValueError("只接受不重复的 holdout 题，不改成 dev 标签复用旧入口")
    relevance = {}
    for case in cases:
        related = project_relevance(case["evidence"], chunks)
        if bool(related) != case["answerable"]:
            raise ValueError("有答案标注与当前全库依据不一致；整批检索前拒绝")
        relevance[case["id"]] = related
    rows = []
    samples = {group: [] for group in GROUPS}
    allowed = {chunk.id for chunk in chunks}
    for case in cases:
        started = time.perf_counter()
        vector_ids = vector_search(case["question"], 3)
        vector_ms = (time.perf_counter() - started) * 1000
        check_ranked_ids(vector_ids, allowed, 3)
        started = time.perf_counter()
        keyword_ids = rank_keywords(case["question"], chunks, limit=3)
        check_ranked_ids(keyword_ids, allowed, 3)
        fused_ids = fuse_rankings(vector_ids, keyword_ids, limit=3, rank_constant=60)
        extra_ms = (time.perf_counter() - started) * 1000
        check_ranked_ids(fused_ids, allowed, 3)
        related = relevance[case["id"]]
        row = {
            "id": case["id"],
            "split": "holdout",
            "question": case["question"],
            "relevant_ids": sorted(related),
            "vector_ids": vector_ids,
            "keyword_ids": keyword_ids,
            "fused_ids": fused_ids,
            "vector_metrics": score_query(vector_ids, related, k=3),
            "fused_metrics": score_query(fused_ids, related, k=3),
            "vector_retrieval_ms": vector_ms,
            "fused_retrieval_ms": vector_ms + extra_ms,
        }
        for group in GROUPS:
            samples[group].append(
                {"ranked_ids": row[f"{group}_ids"], "relevant_ids": related}
            )
        rows.append(row)
        save_row(row)
    return {
        "rows": rows,
        "vector_summary": evaluate_queries(samples["vector"], k=3),
        "fused_summary": evaluate_queries(samples["fused"], k=3),
        "mean_retrieval_ms": {
            group: sum(row[f"{group}_retrieval_ms"] for row in rows) / len(rows)
            if rows
            else None
            for group in GROUPS
        },
        "timing_scope": "query_embedding_and_search; fused_reuses_vector_time_plus_keyword_and_rrf; excludes_model_loading_indexing_generation_and_review",
    }


def generate_selected(
    run_dir: Path,
    cases: list[dict],
    ranking: dict,
    chunks: list[Document],
    originals: dict[str, Document],
    group: str,
    request_fn: Callable[[list[dict[str, str]]], dict],
) -> list[dict]:
    """复用 Day47 请求与评阅材料；只为既定方案逐次保存回答，不填语义判断。"""
    index = {chunk.id: chunk for chunk in chunks}
    rows = []
    for case, ranked in zip(cases, ranking["rows"], strict=True):
        if case["id"] != ranked["id"]:
            raise ValueError("题号与固定排名不一致")
        evidence = [index[chunk_id] for chunk_id in ranked[f"{group}_ids"]]
        row = collect_answer(
            case["id"], group, case["question"], evidence, originals, request_fn
        )
        rows.append(row)
        save_json(run_dir / "responses.json", rows)
        print(f"{case['id']}/{group}：请求={row['request_count']}；错误={row['error']}")
    save_json(
        run_dir / "reviews.json",
        {
            "items": [
                {
                    "id": row["id"],
                    "group": group,
                    "reviewed": False,
                    "answer_ok": None,
                    "citation_ok": None,
                    "reason": "",
                }
                for row in rows
            ]
        },
    )
    write_review_pack(run_dir, cases, originals, rows)
    return rows


def run_holdout(run_dir: Path, freeze_dir: Path) -> None:
    """真实入口：冻结核对通过后才加载本地向量模型，对六题检索并最多生成六次。"""
    frozen = check_freeze(freeze_dir / "frozen.json", check_current=True)
    cases, chunks = load_data()
    cases = [case for case in cases if case["split"] == "holdout"]
    if [case["id"] for case in cases] != HOLDOUT_IDS:
        raise ValueError("留出题应保持 q25～q30，不混入开发题或换题")
    originals = load_originals()
    save_json(run_dir / "frozen.json", frozen)
    save_json(run_dir / "cases_snapshot.json", cases)
    save_json(
        run_dir / "sources_snapshot.json",
        {key: doc.model_dump() for key, doc in originals.items()},
    )
    save_json(run_dir / "price_snapshot.json", PRICE_SNAPSHOT)
    model = create_embedding_model(download=False)
    client = QdrantClient(location=":memory:")
    index = {chunk.id: chunk for chunk in chunks}
    calls = []

    def vector_search(question: str, k: int) -> list[str]:
        """沿用旧检索接口；每道留出题编码、检索一次，两组共享该向量榜。"""
        if (
            len(calls) >= len(cases)
            or question != cases[len(calls)]["question"]
            or k != 3
        ):
            raise ValueError("应按固定留出顺序每题检索一次，k=3")
        found = retrieve_chunks(
            client, "chunks", vectorize_question(question, model), limit=k
        )
        if any(
            chunk.id not in index or chunk != index[chunk.id] for chunk, _score in found
        ):
            raise ValueError("候选与固定全库不一致")
        calls.append(question)
        return [chunk.id for chunk, _score in found]

    def save_row(row: dict) -> None:
        """计时结束后逐题落盘；失败也保留已完成的检索，不修改其他运行。"""
        with (run_dir / "retrieval_rows.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['id']}：vector={row['vector_ids']}；fused={row['fused_ids']}")

    try:
        prepare_collection(client, "chunks")
        store_chunks(client, "chunks", vectorize_chunks(chunks, model))
        prior = [
            str(path.parent)
            for path in (DAY / "outputs").glob("run_*/holdout_started.json")
        ]
        save_json(
            run_dir / "holdout_started.json",
            {
                "started_at": datetime.now().astimezone().isoformat(),
                "freeze_fingerprint": frozen["fingerprint"],
                "prior_exposures": prior,
                "note": "本机首次或重复运行记录不证明此前未手动看过结果；看后调参须说明已参与开发。",
            },
        )
        ranking = compare_holdout(cases, chunks, vector_search, save_row)
    finally:
        client.close()
    save_json(run_dir / "retrieval.json", ranking)
    print(
        f"留出检索汇总：vector={ranking['vector_summary']}；fused={ranking['fused_summary']}"
    )
    generate_selected(
        run_dir,
        cases,
        ranking,
        chunks,
        originals,
        frozen["selected_group"],
        request_grounded_json,
    )
    save_json(
        run_dir / "artifact_manifest.json",
        {name: digest(run_dir / name) for name in PROTECTED_FILES},
    )
    print(
        "六份结果已保存。只填 reviews.json 的 reviewed/answer_ok/citation_ok；reason 可选。"
    )
    print(
        "纯拒答引用填 null；请求失败填 answer_ok=false、citation_ok=null。保持旧判分口径。"
    )


def make_report(run_dir: Path, source_dir: Path) -> None:
    """汇总同轮六份人工判分；不把未生成的另一方案回答当成失败或零分。"""
    manifest = read_json(source_dir / "artifact_manifest.json")
    if not isinstance(manifest, dict) or set(manifest) != set(PROTECTED_FILES):
        raise ValueError("原始产物摘要清单不完整")
    for name, expected in manifest.items():
        if digest(source_dir / name) != expected:
            raise ValueError(f"原始产物 {name} 发生变化，不能作为同一轮结果汇总")
    frozen = check_freeze(source_dir / "frozen.json", check_current=False)
    summary_path = ROOT / "weeks/week06_retrieval_eval/demos/shared/answer_functions.py"
    summary_key = str(summary_path.relative_to(ROOT))
    if digest(summary_path) != frozen["settings"]["files"].get(summary_key):
        raise ValueError("汇总代码已变动，不能把新版口径用于旧轮；请保留原始判分与报告")
    group = frozen["selected_group"]
    rows = read_json(source_dir / "responses.json")
    cases = read_json(source_dir / "cases_snapshot.json")
    reviews = read_json(source_dir / "reviews.json")["items"]
    expected_pairs = {(case_id, group) for case_id in HOLDOUT_IDS}
    if (
        [case["id"] for case in cases] != HOLDOUT_IDS
        or any(case["split"] != "holdout" for case in cases)
        or len(rows) != 6
        or {(row["id"], row["group"]) for row in rows} != expected_pairs
        or len(reviews) != 6
        or {(row["id"], row["group"]) for row in reviews} != expected_pairs
    ):
        raise ValueError("必须是同一冻结方案、q25～q30 的六份结果与六份判分")
    by_pair = {(item["id"], item["group"]): item for item in reviews}
    for row in rows:
        review = by_pair[(row["id"], row["group"])]
        if row["error"] is not None and (
            review["answer_ok"] is not False or review["citation_ok"] is not None
        ):
            raise ValueError("运行失败应计回答失败，引用不适用；不能按模型状态算正确")
    resources = resource_summary(rows)[group]
    # 旧生成汇总的占位字段不混入本日结果；真实检索计时单独见 retrieval。
    del resources["retrieval_ms"]
    report = {
        "scope": "six_holdout_cases_retrieval_both_answer_selected_only",
        "source_run": str(source_dir),
        "source_run_origin": read_json(source_dir / "run_info.json")["origin"],
        "selected_group": group,
        "freeze_fingerprint": frozen["fingerprint"],
        "exposure": read_json(source_dir / "holdout_started.json"),
        "retrieval": read_json(source_dir / "retrieval.json"),
        "judgments": summarize_reviews(reviews)[group],
        "resources": resources,
        "limitations": "只给所选方案生成六份回答；费用沿用 Day47 固定价格范围；检索与生成分开计时，非端到端延迟。",
    }
    save_json(run_dir / "reviews_snapshot.json", reviews)
    save_json(run_dir / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("下一步：AI 转录客观数据，学员写 day48_报告.md 第3节三段报告。")


def probe(run_dir: Path) -> None:
    """仅供交付验证：一条 AI 人工资料走相同生成函数，不使用真实留出题。"""
    original = Document(
        id="probe/guide.md",
        page_content="在前台领取。",
        metadata={"source": "probe/guide.md"},
    )
    chunk = Document(
        id="probe/guide.md#L1-L1",
        page_content=original.page_content,
        metadata={"source": "probe/guide.md", "line_start": 1, "line_end": 1},
    )
    case = {
        "id": "probe01",
        "split": "holdout",
        "question": "在哪里领取？",
        "answerable": True,
        "expected": "在前台领取。",
        "evidence": [chunk.metadata],
    }
    rows = generate_selected(
        run_dir,
        [case],
        {"rows": [{"id": "probe01", "fused_ids": [chunk.id]}]},
        [chunk],
        {original.id: original},
        "fused",
        request_grounded_json,
    )
    if rows[0]["error"]:
        raise RuntimeError(rows[0]["error"])
    print("本次只有一条 AI 教具请求，不是学员留出实验。")


def main() -> None:
    """选择冻结、真实留出运行或汇总；所有命令独立留证，路径不依赖工作目录。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=["freeze", "run", "report", "probe"], required=True
    )
    parser.add_argument("--freeze-dir", type=Path, help="run 必填：freeze 打印的目录")
    parser.add_argument("--run-dir", type=Path, help="report 必填：run 打印的目录")
    parser.add_argument(
        "--live", action="store_true", help="run/probe 必须显式启用真实请求"
    )
    args = parser.parse_args()
    if args.part in {"run", "probe"} and not args.live:
        parser.error(
            "run/probe 需要 --live；run 最多请求六次，probe 只请求一条 AI 教具"
        )
    if args.part == "run" and args.freeze_dir is None:
        parser.error("run 需要 --freeze-dir，先冻结选择再查看留出结果")
    if args.part == "report" and args.run_dir is None:
        parser.error("report 需要 --run-dir 指向同一次 run 目录")

    def execute(run_dir: Path) -> None:
        """运行选定环节，不自动决定方案、填写人工判分或写报告结论。"""
        if args.part == "freeze":
            freeze_choice(run_dir)
        elif args.part == "run":
            freeze_dir = (
                args.freeze_dir
                if args.freeze_dir.is_absolute()
                else ROOT / args.freeze_dir
            )
            run_holdout(run_dir, freeze_dir.resolve())
        elif args.part == "report":
            source_dir = (
                args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
            )
            make_report(run_dir, source_dir.resolve())
        else:
            probe(run_dir)

    run_logged(
        args.part,
        execute,
        {
            "scope": "AI_probe_only" if args.part == "probe" else "holdout_six",
            "live": args.live,
        },
        Path(__file__),
        DAY / "outputs",
        origin_env="DAY48_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
