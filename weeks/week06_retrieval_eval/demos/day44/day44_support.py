"""AI 维护的 Day44 资料展示、标注校验与旧结果回放，不实现新投影函数。"""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from langchain_core.documents import Document

from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import (
    chunk_documents,
    score_query,
)

DAY = Path(__file__).resolve().parent
SNAPSHOT = DAY / "materials/sources_snapshot.json"
LABELS = DAY / "day44_labels.json"
REPLAYS = DAY / "materials/baseline_retrievals.json"
SNAPSHOT_SHA256 = "923b660e3d09527cf9a54be9bee4a67c78fb0e5b7c67cc5cca8007ff92e623df"


def read_json(path: Path) -> dict:
    """读取 UTF-8 JSON 对象；文件或 JSON 错误原样抛出。"""
    return json.loads(path.read_text(encoding="utf-8"))


def load_originals() -> dict[str, Document]:
    """核对固定快照摘要并恢复全文；不读取变化后的 notes 文件。"""
    if hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError("固定全文快照被改动，请保留原始版本，不据此继续评测")
    return {source: Document(**value) for source, value in read_json(SNAPSHOT).items()}


def make_chunks(originals: dict[str, Document]) -> list[Document]:
    """复用已验收切分，固定旧版 8 行、重叠 2 行，返回全部 23 条片段。"""
    return chunk_documents(list(originals.values()), chunk_lines=8, overlap_lines=2)


def show_sources(originals: dict[str, Document]) -> None:
    """打印同一固定版本的全文行号与全部片段，供独立标注。"""
    print(f"全文快照 SHA256={SNAPSHOT_SHA256}")
    print("原文来自 Week05 同次快照；这里只显示资料，不显示任何检索排名。")
    for source, original in originals.items():
        print(f"\n来源={source}；{len(original.page_content.splitlines())} 行")
        for number, line in enumerate(original.page_content.splitlines(), start=1):
            print(f"{number:3}: {line}")
    print("\n旧版全部片段编号（不是某一道题的检索结果）：")
    for chunk in make_chunks(originals):
        print(f"  {chunk.id}")


def validate_labels(
    dataset: dict, originals: dict[str, Document], require_complete: bool = False
) -> dict:
    """检查格式、依据行与固定划分，返回就绪/待填数量；不自动判断语义正确性。"""
    if not isinstance(dataset, dict):
        raise TypeError("标注文件顶层应为 JSON 对象")
    if (
        type(dataset.get("schema_version")) is not int
        or dataset.get("schema_version") != 1
    ):
        raise ValueError("schema_version 应保持 1")
    if dataset.get("source_snapshot_sha256") != SNAPSHOT_SHA256:
        raise ValueError("标注文件的全文版本与固定快照不一致")
    cases = dataset.get("cases")
    expected_ids = [f"q{number:02d}" for number in range(1, 31)]
    if (
        not isinstance(cases, list)
        or not all(isinstance(row, dict) for row in cases)
        or [row.get("id") for row in cases] != expected_ids
    ):
        raise ValueError("cases 须按 q01～q30 排列，不能重复、缺失或调换编号")
    ready = {"dev": 0, "holdout": 0}
    answerable = {"dev": 0, "holdout": 0}
    no_answer = {"dev": 0, "holdout": 0}
    pending = []
    questions = set()
    for index, row in enumerate(cases, start=1):
        case_id = row["id"]
        split = "dev" if index <= 24 else "holdout"
        if row.get("split") != split:
            raise ValueError(f"{case_id} 应属于 {split}，保留预先划分，不看结果后换组")
        if not isinstance(row.get("question"), str) or not isinstance(
            row.get("expected"), str
        ):
            raise TypeError(f"{case_id} 的 question 与 expected 应为字符串")
        question = row["question"].strip()
        if question:
            normalized = question.casefold()
            if normalized in questions:
                raise ValueError(f"{case_id} 与另一题文字重复；同义改写还需人工核对")
            questions.add(normalized)
        state = row.get("answerable")
        if state is not None and type(state) is not bool:
            raise ValueError(f"{case_id} 的 answerable 只能是 true、false 或 null")
        evidence = row.get("evidence")
        if not isinstance(evidence, list):
            raise TypeError(f"{case_id} 的 evidence 应为列表")
        for span in evidence:
            if not isinstance(span, dict) or set(span) != {
                "source",
                "line_start",
                "line_end",
            }:
                raise ValueError(
                    f"{case_id} 的依据须含 source、line_start、line_end 三键"
                )
            source, start, end = span["source"], span["line_start"], span["line_end"]
            if not isinstance(source, str) or source not in originals:
                raise ValueError(f"{case_id} 的依据来源不在固定全文中")
            if type(start) is not int or type(end) is not int:
                raise ValueError(f"{case_id} 的依据行号须为整数，不接受 bool")
            lines = originals[source].page_content.splitlines()
            if not 1 <= start <= end <= len(lines):
                raise ValueError(f"{case_id} 的依据行范围越界或起止颠倒")
            if not "\n".join(lines[start - 1 : end]).strip():
                raise ValueError(f"{case_id} 的依据只有空白行")
        if state is None:
            pending.append(case_id)
            continue
        if not question or not row["expected"].strip():
            raise ValueError(
                f"{case_id} 已标 true/false，须同时填写问题与期望要点/无答案理由"
            )
        if state and not evidence:
            raise ValueError(f"{case_id} 有答案时至少标一处原文依据")
        if not state and evidence:
            raise ValueError(
                f"{case_id} 已确认无答案，evidence 应为 []，理由写在 expected"
            )
        ready[split] += 1
        (answerable if state else no_answer)[split] += 1
    report = {
        "total": 30,
        "ready": ready,
        "answerable": answerable,
        "no_answer": no_answer,
        "pending": pending,
    }
    if require_complete and pending:
        raise ValueError(
            f"仍有 {len(pending)} 题未标完：{pending}；null 不能当成无答案"
        )
    return report


def show_validation(report: dict) -> None:
    """解释数量及适用范围；格式通过不等于标注内容正确。"""
    for split, name in [("dev", "开发集"), ("holdout", "留出集")]:
        print(
            f"{name}就绪={report['ready'][split]}；有答案={report['answerable'][split]}；"
            f"无答案={report['no_answer'][split]}"
        )
    print(f"待填={len(report['pending'])}：{report['pending']}")
    print(
        "校验只检查格式、行号与划分；依据能否支持期望、是否重复考同一事实，由人工核对。"
    )
    if report["pending"]:
        print("当前仍是待填数据，不能作为完整三十题评测集报告结果。")
    print("本入口不会对留出题运行检索或计算效果指标。")


def preview_legacy(
    case_id: str,
    dataset: dict,
    originals: dict[str, Document],
    project_fn: Callable[..., set[str]],
) -> dict:
    """仅回放旧十题的既有候选，复用学员 A；不发新请求，不评测留出集。"""
    validate_labels(dataset, originals)
    replay = read_json(REPLAYS)
    if replay["source_snapshot_sha256"] != SNAPSHOT_SHA256:
        raise ValueError("旧检索结果与全文快照版本不一致")
    if case_id not in replay["cases"]:
        raise ValueError("这里只回放 q01～q10；新增题的真实检索在后续单元接入")
    row = next(row for row in dataset["cases"] if row["id"] == case_id)
    if row["split"] != "dev" or row["answerable"] is None:
        raise ValueError("只回放已标注的旧开发题，不对留出题试跑")
    previous = replay["cases"][case_id]
    if row["question"] != previous["question"]:
        raise ValueError("旧问题已变化，不能把旧候选冒充新问题的检索结果")
    chunks = make_chunks(originals)
    chunk_index = {chunk.id: chunk for chunk in chunks}
    ranked_ids = []
    for saved, score in previous["candidates"]:
        chunk = Document(**saved)
        if chunk.id not in chunk_index or chunk != chunk_index[chunk.id]:
            raise ValueError("旧候选与同一快照切分不一致")
        ranked_ids.append(chunk.id)
        print(f"实际旧候选={chunk.id}；旧分数={score}；正文={chunk.page_content!r}")
    relevant_ids = project_fn(row["evidence"], chunks)
    if not isinstance(relevant_ids, set) or not relevant_ids <= set(chunk_index):
        raise ValueError("project_relevance 应返回本批片段编号组成的 set[str]")
    print(f"问题={row['question']}；预先标注的依据={row['evidence']}")
    print(f"全部标注相关片段编号={sorted(relevant_ids)}")
    result = score_query(ranked_ids, relevant_ids, k=3)
    print(f"检索指标={result}")
    print(
        "这是旧候选回放；新真实检索尚未发生。以上是片段相关性指标，不是事实完整覆盖率。"
    )
    return {
        "case_id": case_id,
        "ranked_ids": ranked_ids,
        "relevant_ids": sorted(relevant_ids),
        "metrics": result,
    }
