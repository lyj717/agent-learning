"""AI 运行环境：复用固定候选生成回答并留证，人工判断及汇总实现由学员完成。"""

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path

from langchain_core.documents import Document

from weeks.week05_rag.demos.day40.day40_model_io import request_grounded_json
from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    SNAPSHOT,
    load_originals,
)
from weeks.week06_retrieval_eval.demos.day46.day46_support import load_data
from weeks.week06_retrieval_eval.demos.day47.day47_checks import run_checks
from weeks.week06_retrieval_eval.demos.shared.answer_functions import (
    build_grounded_messages,
    check_grounded_reply,
    cost_of_call,
    trace_citations,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY = Path(__file__).resolve().parent
ROOT = DAY.parents[3]
GROUPS = ("vector", "fused")
CASE_IDS = ["q01", "q03", "q06", "q08"]
PRICE_SNAPSHOT = json.loads(
    (DAY / "day47_price_snapshot.json").read_text(encoding="utf-8")
)


def save_json(path: Path, value: object) -> None:
    """保存客观运行数据，不覆盖其他运行目录或填写人工判分。"""
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def digest(path: Path) -> str:
    """返回文件字节的 SHA256，用于识别固定输入与原始响应版本。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs() -> tuple[list[dict], dict[str, Document], dict[str, Document]]:
    """严格核对四道 dev 的问题与候选，返回样本、全库索引和固定全文；不检索。"""
    fixture = json.loads((DAY / "day47_inputs.json").read_text(encoding="utf-8"))
    if (
        fixture["source_snapshot_sha256"]
        != "923b660e3d09527cf9a54be9bee4a67c78fb0e5b7c67cc5cca8007ff92e623df"
        or fixture["labels_sha256"]
        != "46b7b4312e2597f73a9a0cb6c906e30bfe4e9cfc861f5b0c687b15139613ee2b"
    ):
        raise ValueError("候选资料的原文或标注版本不匹配")
    cases, chunks = load_data()
    originals = load_originals()
    by_id = {case["id"]: case for case in cases}
    index = {chunk.id: chunk for chunk in chunks}
    if (
        fixture["case_ids"] != CASE_IDS
        or [row["id"] for row in fixture["rows"]] != CASE_IDS
    ):
        raise ValueError("本次只使用固定的四道开发题，不换题或查看留出结果")
    samples = []
    for row in fixture["rows"]:
        case = by_id[row["id"]]
        if case["split"] != "dev" or case["question"] != row["question"]:
            raise ValueError("固定题目或分组不匹配")
        for group in GROUPS:
            ranking = row[f"{group}_ids"]
            if (
                len(ranking) != 3
                or len(set(ranking)) != 3
                or not set(ranking) <= set(index)
            ):
                raise ValueError("固定候选必须是三个已入库且不重复的片段编号")
        samples.append(
            {**case, "vector_ids": row["vector_ids"], "fused_ids": row["fused_ids"]}
        )
    return samples, index, originals


def usage_and_cost(response: dict | None) -> dict:
    """从旧响应提取已知用量，按固定高峰价报缓存未知时的费用范围；缺失保留 None。"""
    result = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "cost_low_yuan": None,
        "cost_high_yuan": None,
    }
    usage = response.get("usage") if isinstance(response, dict) else None
    if not isinstance(usage, dict):
        return result
    prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
    if any(type(value) is not int or value < 0 for value in (prompt, completion)):
        return result
    result.update(prompt_tokens=prompt, completion_tokens=completion)
    if str(response.get("model", "")).casefold() in PRICE_SNAPSHOT["model_names"]:
        price = PRICE_SNAPSHOT["price"]
        result["cost_low_yuan"] = cost_of_call(
            prompt, completion, cached_tokens=prompt, price=price
        )
        result["cost_high_yuan"] = cost_of_call(
            prompt, completion, cached_tokens=0, price=price
        )
    return result


def collect_answer(
    case_id: str,
    group: str,
    question: str,
    evidence: list[Document],
    originals: dict[str, Document],
    request_fn: Callable[[list[dict[str, str]]], dict] = request_grounded_json,
) -> dict:
    """AI 请求环境：核对给定候选，最多请求一次，保留响应、异常及生成调用耗时。

    五个内容参数必填；request_fn 默认旧真实请求层，测试可传独立替身。
    返回客观过程字典，不含 answer_ok/citation_ok。候选/结构出错也保留已收到的响应。
    计时只包住 request_fn；异常请求也计入一次。无候选或前置检查失败不调用模型。
    """
    row = {
        "id": case_id,
        "group": group,
        "question": question,
        "candidates": [doc.model_dump() for doc in evidence],
        "response": None,
        "checked": None,
        "cited_evidence": [],
        "request_count": 0,
        "generation_ms": None,
        "error": None,
    }
    try:
        if not evidence:
            raise ValueError("候选为空，本次不请求模型")
        candidates = [(doc, 0.0) for doc in evidence]
        trace_citations([doc.id for doc in evidence], candidates, originals)
        messages = build_grounded_messages(question, evidence)
        # perf_counter() 无参数，返回单调计时的秒数；只有两次读数的差值表示耗时。
        started = time.perf_counter()
        row["request_count"] = 1
        try:
            row["response"] = request_fn(messages)
        finally:
            row["generation_ms"] = (time.perf_counter() - started) * 1000
        if row["response"]["finish_reason"] != "stop":
            raise ValueError(f"未正常结束：{row['response']['finish_reason']}")
        checked = check_grounded_reply(row["response"]["raw_text"], evidence)
        cited = trace_citations(checked["cited_ids"], candidates, originals)
        row["checked"] = checked
        row["cited_evidence"] = [doc.model_dump() for doc in cited]
    except Exception as error:  # noqa: BLE001 - 保留失败现场，继续其他题，不代判语义。
        row["error"] = f"{type(error).__name__}: {error}"
    row.update(usage_and_cost(row["response"]))
    return row


def write_review_pack(
    run_dir: Path, samples: list[dict], originals: dict[str, Document], rows: list[dict]
) -> None:
    """将实际原文与响应排成只读评阅材料；不生成学员语义判断。"""
    text = [
        "# 本次人工评阅材料",
        "",
        "请只填写同目录 reviews.json；此处是原始材料，不是判分答案。",
        "",
        "## 固定全文（含编号，供查 expected 与回答事实）",
        "",
    ]
    for source, original in originals.items():
        text.extend([f"### {source}", "", "````text"])
        text.extend(
            f"{number}: {line}"
            for number, line in enumerate(original.page_content.splitlines(), 1)
        )
        text.extend(["````", ""])
    by_id = {sample["id"]: sample for sample in samples}
    for row in rows:
        case = by_id[row["id"]]
        text.extend(
            [
                f"## {row['id']} / {row['group']}",
                "",
                f"问题：{row['question']}",
                f"预先期望：{case['expected']}",
                f"原文有答案：{case['answerable']}",
                f"原文依据：{case['evidence']}",
                "",
                "候选：",
                "",
            ]
        )
        for doc in row["candidates"]:
            text.extend(
                [f"- {doc['id']}：", "", "````text", doc["page_content"], "````", ""]
            )
        text.extend(
            [
                "原始响应（模型自己填写的状态不是人工结论）：",
                "",
                "```json",
                json.dumps(row["response"], ensure_ascii=False, indent=2),
                "```",
                "",
                f"运行错误：{row['error']}",
                "",
                "实际引用片段：",
                "",
            ]
        )
        for doc in row["cited_evidence"]:
            text.extend(
                [f"- {doc['id']}：", "", "````text", doc["page_content"], "````", ""]
            )
        if not row["cited_evidence"]:
            text.extend(
                ["没有通过结构/出处检查的引用片段；请连同原始回答和错误核对。", ""]
            )
    (run_dir / "review_pack.md").write_text("\n".join(text), encoding="utf-8")


def generate(run_dir: Path, request_fn: Callable = request_grounded_json) -> None:
    """复用四题的旧排名，生成八份回答；逐次保存失败与响应，不重新检索或代判。"""
    samples, index, originals = load_inputs()
    rows = []
    save_json(run_dir / "cases_snapshot.json", samples)
    (run_dir / "sources_snapshot.json").write_bytes(SNAPSHOT.read_bytes())
    (run_dir / "inputs_snapshot.json").write_bytes(
        (DAY / "day47_inputs.json").read_bytes()
    )
    save_json(run_dir / "price_snapshot.json", PRICE_SNAPSHOT)
    for number, sample in enumerate(samples):
        # 交替两组先后顺序；只跑一次的小样本仍不能消除缓存、网络或随机性影响。
        order = GROUPS if number % 2 == 0 else tuple(reversed(GROUPS))
        for group in order:
            evidence = [index[chunk_id] for chunk_id in sample[f"{group}_ids"]]
            row = collect_answer(
                sample["id"], group, sample["question"], evidence, originals, request_fn
            )
            rows.append(row)
            save_json(run_dir / "responses.json", rows)
            print(
                f"{row['id']}/{group}：请求={row['request_count']}；生成调用毫秒={row['generation_ms']}；错误={row['error']}"
            )
    save_json(
        run_dir / "response_manifest.json",
        {
            "responses_sha256": digest(run_dir / "responses.json"),
            "price_sha256": digest(run_dir / "price_snapshot.json"),
            "sources_sha256": digest(run_dir / "sources_snapshot.json"),
            "cases_sha256": digest(run_dir / "cases_snapshot.json"),
            "pairs": [[row["id"], row["group"]] for row in rows],
        },
    )
    save_json(
        run_dir / "reviews.json",
        {
            "items": [
                {
                    "id": row["id"],
                    "group": row["group"],
                    "reviewed": False,
                    "answer_ok": None,
                    "citation_ok": None,
                    "reason": "",
                }
                for row in rows
            ]
        },
    )
    write_review_pack(run_dir, samples, originals, rows)
    print(f"共保存 {len(rows)} 份结果；请打开 {run_dir / 'review_pack.md'}")
    print("只填写同目录 reviews.json；人工判断未完成前不输出正确率。")


def resource_summary(rows: list[dict]) -> dict:
    """汇总客观用量及生成耗时；同时列已记录条数，缺失不补零，不称全流程成本。"""
    result = {}
    for group in GROUPS:
        selected = [row for row in rows if row["group"] == group]
        usage = [row for row in selected if row["prompt_tokens"] is not None]
        costs = [row for row in selected if row["cost_low_yuan"] is not None]
        timed = [row for row in selected if row["generation_ms"] is not None]
        result[group] = {
            "rows": len(selected),
            "request_count": sum(row["request_count"] for row in selected),
            "failed_count": sum(row["error"] is not None for row in selected),
            "usage_known_count": len(usage),
            "known_prompt_tokens": sum(row["prompt_tokens"] for row in usage)
            if usage
            else None,
            "known_completion_tokens": sum(row["completion_tokens"] for row in usage)
            if usage
            else None,
            "cost_known_count": len(costs),
            "known_cost_low_yuan": sum(row["cost_low_yuan"] for row in costs)
            if costs
            else None,
            "known_cost_high_yuan": sum(row["cost_high_yuan"] for row in costs)
            if costs
            else None,
            "timed_count": len(timed),
            "mean_generation_ms": sum(row["generation_ms"] for row in timed)
            / len(timed)
            if timed
            else None,
            "retrieval_ms": None,
        }
    return result


def report(run_dir: Path, source_dir: Path, summarize_fn: Callable) -> None:
    """核对同次客观输出和八份完整人工判分，在新的报告目录调用学员汇总函数。"""
    source_dir = (
        source_dir if source_dir.is_absolute() else ROOT / source_dir
    ).resolve()
    manifest = json.loads(
        (source_dir / "response_manifest.json").read_text(encoding="utf-8")
    )
    if (
        digest(source_dir / "responses.json") != manifest["responses_sha256"]
        or digest(source_dir / "price_snapshot.json") != manifest["price_sha256"]
        or digest(source_dir / "sources_snapshot.json") != manifest["sources_sha256"]
        or digest(source_dir / "cases_snapshot.json") != manifest["cases_sha256"]
    ):
        raise ValueError("原始响应或价格版本变化，请保留现场，不把修改后内容当原运行")
    rows = json.loads((source_dir / "responses.json").read_text(encoding="utf-8"))
    reviews = json.loads((source_dir / "reviews.json").read_text(encoding="utf-8"))[
        "items"
    ]
    expected = {(case_id, group) for case_id in CASE_IDS for group in GROUPS}
    if len(rows) != 8 or {(row["id"], row["group"]) for row in rows} != expected:
        raise ValueError("客观结果必须是本次固定四题的八份结果")
    if len(reviews) != 8 or {(row["id"], row["group"]) for row in reviews} != expected:
        raise ValueError("人工判分不能漏项、换题、重复或增加留出题")
    if any(
        not isinstance(row.get("reason"), str) or not row["reason"].strip()
        for row in reviews
    ):
        raise ValueError("每份人工判分请补一两句实际依据，不能只改布尔值")
    by_pair = {(row["id"], row["group"]): row for row in reviews}
    for row in rows:
        review = by_pair[(row["id"], row["group"])]
        if row["error"] is not None and (
            review["answer_ok"] is not False or review["citation_ok"] is not None
        ):
            raise ValueError("运行失败须计回答失败，引用无可评价结果；请核对原始错误")
    result = {
        "scope": "four_selected_dev_cases_only",
        "source_run": str(source_dir),
        "source_run_origin": json.loads(
            (source_dir / "run_info.json").read_text(encoding="utf-8")
        )["origin"],
        "judgments": summarize_fn(reviews),
        "resources": resource_summary(rows),
    }
    save_json(run_dir / "report.json", result)
    save_json(run_dir / "reviews_snapshot.json", reviews)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("此为四道选定开发题的单次生成对照，不代表全部开发题、留出题或统计稳定提升。")


def run_entry(
    part: str, summarize_fn: Callable, exercise: Path, source_dir: Path | None
) -> None:
    """统一留证；人工对照未过不运行真实生成，不自动填写学员人工结论。"""
    fixture = json.loads((DAY / "day47_inputs.json").read_text(encoding="utf-8"))
    config = {
        "scope": "four_selected_dev_cases_only",
        "case_ids": CASE_IDS,
        "groups": list(GROUPS),
        "generation_limit": 8,
        "retrieval_calls": 0,
        "inputs_sha256": digest(DAY / "day47_inputs.json"),
        "source_snapshot_sha256": fixture["source_snapshot_sha256"],
        "labels_sha256": fixture["labels_sha256"],
        "source_batch": fixture["source_batch"],
        "source_report_sha256": fixture["source_report_sha256"],
        "price_sha256": digest(DAY / "day47_price_snapshot.json"),
        "support_sha256": digest(Path(__file__)),
        "answer_functions_sha256": digest(DAY.parent / "shared/answer_functions.py"),
        "request_layer_sha256": digest(
            ROOT / "weeks/week05_rag/demos/day40/day40_model_io.py"
        ),
        "request_settings": {
            "max_tokens": 1024,
            "thinking": "disabled",
            "timeout_s": 45,
            "sdk_retries": 0,
            "temperature": "not_set_by_request_layer",
        },
        "source_run": str(source_dir) if source_dir else None,
    }

    def execute(run_dir: Path) -> None:
        """执行所选模式；generate 才使用真实回答请求。"""
        run_checks(summarize_fn)
        if part == "generate":
            generate(run_dir)
        elif part == "report":
            report(run_dir, source_dir, summarize_fn)

    run_logged(
        part, execute, config, exercise, DAY / "outputs", origin_env="DAY47_RUN_ORIGIN"
    )
