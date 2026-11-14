"""Day58 运行环境：读题面与回答、切原文、发一次裁判请求、汇总与人工标签的一致性。

这里不实现 build_judge_messages / parse_judge_verdict，也不替学员填人工判读。
密钥、服务商地址和模型继续读仓库根目录的 .env，不向屏幕打印凭据。
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from weeks.week02_tools.demos.shared.llm_client import make_client

ROOT = Path(__file__).resolve().parents[4]
DAY57 = ROOT / "weeks/week08_evaluation_reliability/demos/day57"
DAY58 = ROOT / "weeks/week08_evaluation_reliability/demos/day58"
NOTES = ROOT / "notes/python-notes.md"

_ID_PATTERN = re.compile(r"^(?P<source>.+?)#L(?P<start>\d+)-L(?P<end>\d+)$")


def load_json(path: Path) -> Any:
    """读取一个 UTF-8 JSON 文件，返回解析后的对象。"""
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases() -> list[dict]:
    """读取 Day57 的 8 道题，原样返回题面字段。"""
    return load_json(DAY57 / "day57_cases.json")


def load_answers() -> dict[str, dict]:
    """读取 Day57 的 v2 回答，返回题号到回答的映射。"""
    return load_json(DAY57 / "day57_answers_v2.json")


def _parse_chunk_id(chunk_id: str) -> tuple[str, int, int]:
    """把 notes/python-notes.md#L23-L25 拆成来源、起行、止行。"""
    match = _ID_PATTERN.match(chunk_id)
    if match is None:
        raise ValueError(f"无法解析片段编号：{chunk_id}")
    return match.group("source"), int(match.group("start")), int(match.group("end"))


def evidence_for(case: dict) -> list[dict[str, str]]:
    """按 retrieved_ids 切出原文，返回 [{"id": 片段编号, "text": 原文}]。"""
    lines = NOTES.read_text(encoding="utf-8").splitlines()
    evidence = []
    for chunk_id in case["retrieved_ids"]:
        source, start, end = _parse_chunk_id(chunk_id)
        if source != "notes/python-notes.md":
            raise ValueError(f"本课只准备了 notes/python-notes.md：{chunk_id}")
        text = "\n".join(lines[start - 1 : end])
        evidence.append({"id": chunk_id, "text": text})
    return evidence


def cases_with_evidence() -> list[dict]:
    """在每道题上附加 evidence 字段，供裁判阅读原文；不改 Day57 的数据文件。"""
    cases = load_cases()
    for case in cases:
        case["evidence"] = evidence_for(case)
    return cases


def judge_once(messages: list[dict[str, str]]) -> dict[str, Any]:
    """发一次裁判请求：温度 0、JSON 模式、关闭思考，返回原文与用量等。"""
    with make_client() as client:
        # make_client() 已加载 .env，所以模型名在它之后再读。
        model = os.environ.get("LLM_MODEL", "deepseek-flash")
        started = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=600,
            timeout=45,
            extra_body={"thinking": {"type": "disabled"}},
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
    if not response.choices:
        raise RuntimeError("模型响应没有 choices，无法取得正文与结束原因")
    choice = response.choices[0]
    usage = response.usage
    return {
        "raw_text": choice.message.content or "",
        "finish_reason": choice.finish_reason or "",
        "usage": (
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            if usage is not None
            else None
        ),
        "model": response.model,
        "latency_ms": latency_ms,
    }


def load_human_labels(path: Path | None = None) -> dict[str, dict]:
    """读取人工标签；answer_ok 仍为 null 时明确拒绝，不拿未判的题算一致率。"""
    data = load_json(path or (DAY58 / "day58_human_labels.json"))
    missing = [
        case_id for case_id, item in data.items() if item.get("answer_ok") is None
    ]
    if missing:
        raise ValueError(f"这些题还没填 answer_ok：{missing}")
    return data


def summarize_agreement(
    human: dict[str, dict], judge: dict[str, dict]
) -> dict[str, Any]:
    """逐题比较人工与裁判，返回行、一致数、适用引用数与分歧清单。

    human / judge：{题号: {"answer_ok": bool, "citation_ok": bool|None, "reason": str}}。
    answer_ok 在全部题上比较；citation_ok 只在人工填了 bool 的题上比较，
    人工填 None（没有引用）时记为不适用。
    """
    if set(human) != set(judge):
        raise ValueError("人工标签与裁判结果的题号集合不同")
    rows = []
    answer_agree = 0
    citation_applicable = 0
    citation_agree = 0
    disagreements = []
    for case_id in sorted(human):
        person = human[case_id]
        machine = judge[case_id]
        same_answer = person["answer_ok"] is machine["answer_ok"]
        answer_agree += int(same_answer)
        if not same_answer:
            disagreements.append(
                {
                    "id": case_id,
                    "field": "answer_ok",
                    "human": person["answer_ok"],
                    "judge": machine["answer_ok"],
                }
            )
        if person["citation_ok"] is not None:
            citation_applicable += 1
            same_citation = person["citation_ok"] is machine["citation_ok"]
            citation_agree += int(same_citation)
            if not same_citation:
                disagreements.append(
                    {
                        "id": case_id,
                        "field": "citation_ok",
                        "human": person["citation_ok"],
                        "judge": machine["citation_ok"],
                    }
                )
        rows.append(
            {
                "id": case_id,
                "human_answer_ok": person["answer_ok"],
                "human_citation_ok": person["citation_ok"],
                "judge_answer_ok": machine["answer_ok"],
                "judge_citation_ok": machine["citation_ok"],
                "answer_agree": same_answer,
                "judge_reason": machine.get("reason", ""),
            }
        )
    return {
        "total": len(human),
        "answer_agree": answer_agree,
        "citation_applicable": citation_applicable,
        "citation_agree": citation_agree,
        "disagreements": disagreements,
        "rows": rows,
    }
