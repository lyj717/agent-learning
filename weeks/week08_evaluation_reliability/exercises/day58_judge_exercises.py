"""Day58：模型裁判的 prompt、解析，以及与人工标签的比较。

--part a/b 跑离线检查，--part live 调用裁判，--part compare 与人工标签比较。
题目、字段与全部判分情形见 demos/day58/day58_题目说明.md；观察见 day58_record.md。
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day58.day58_checks import run_a, run_b
from weeks.week08_evaluation_reliability.demos.day58.day58_support import (
    DAY58,
    cases_with_evidence,
    judge_once,
    load_answers,
    load_human_labels,
    summarize_agreement,
)

LABELS = DAY58 / "day58_human_labels.json"


def build_judge_messages(case: dict, answer: dict) -> list[dict[str, str]]:
    """组装发给裁判的 system 与 user 两条消息。"""
    messages = [
        {
            "role": "system",
            "content": "你是一个评分裁判，只输出一个 JSON 对象，键恰好是以下这三个："
            "answer_ok：回答是否正确且完整，只依据给出的原文；citation_ok：引用的原文是否支持回答，没有引用时填 null； reason：一两句话说明依据；",
        }
    ]
    lines = [f"问题：{case['question']}", f"回答：{answer['answer']}"]
    for item in case["evidence"]:
        lines.append(f"证据 {item['id']}：{item['text']}")
    content = "\n".join(lines)
    messages.append({"role": "user", "content": content})
    return messages


def parse_judge_verdict(raw: str) -> dict[str, bool | str | None]:
    """解析裁判返回的文本，校验后返回三个键。"""
    if not isinstance(raw, str):
        raise TypeError("raw不是str！")
    striped = raw.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        encode_dict = json.loads(striped)
    except json.JSONDecodeError:
        raise ValueError("解析失败！")
    if set(encode_dict) != {"answer_ok", "citation_ok", "reason"}:
        raise ValueError("键错误！")
    if type(encode_dict["answer_ok"]) is not bool:
        raise ValueError("answer_ok不是bool")
    if (
        type(encode_dict["citation_ok"]) is not bool
        and encode_dict["citation_ok"] is not None
    ):
        raise ValueError("citation_ok不是bool或None")
    if not isinstance(encode_dict["reason"], str) or not encode_dict["reason"].strip():
        raise ValueError("reason不是非空字符串")
    return encode_dict


def _latest_live_dir() -> Path:
    """找最近一次 live 运行目录；找不到时明确报错。"""
    candidates = sorted(
        (DAY58 / "outputs").glob("live_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if (path / "judge_results.json").is_file():
            return path
    raise FileNotFoundError("没有找到 live 结果，先运行 --part live")


def _format_ok(value: object) -> str:
    """把 bool / None 显示成中文。"""
    if value is None:
        return "不适用"
    return "通过" if value is True else "失败"


def _live(run_dir: Path, limit: int, labels_path: Path) -> None:
    """逐题发裁判请求，保存原文、解析结果、用量与失败；不自动重试。"""
    load_human_labels(labels_path)
    cases = cases_with_evidence()
    answers = load_answers()
    selected = cases[:limit]
    print(f"将调用模型 {len(selected)} 次；失败也保存原文，不自动重试。")
    results = []
    for case in selected:
        case_id = case["id"]
        print(f"\n{case_id}｜{case['question']}")
        messages = build_judge_messages(case, answers[case_id])
        call = judge_once(messages)
        error = None
        parsed = None
        try:
            parsed = parse_judge_verdict(call["raw_text"])
        except (ValueError, TypeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
        print(f"  原始返回={call['raw_text']}")
        print(f"  解析结果={parsed}")
        if error is not None:
            print(f"  解析失败={error}")
        print(f"  用量={call['usage']}；耗时={call['latency_ms']}ms")
        results.append({"id": case_id, **call, "parsed": parsed, "error": error})

    path = run_dir / "judge_results.json"
    path.write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n结构化结果：{path}")
    failures = [item["id"] for item in results if item["parsed"] is None]
    print(f"调用 {len(results)} 次；解析失败 {len(failures)} 次：{failures}")


def _compare(run_dir: Path, live_dir: Path, labels_path: Path) -> None:
    """比较人工标签与裁判结论，打印逐题表，保存一致数与分歧清单。"""
    human = load_human_labels(labels_path)
    data = json.loads((live_dir / "judge_results.json").read_text(encoding="utf-8"))
    results = data["results"]
    judge = {}
    failures = []
    for item in results:
        if item.get("parsed") is None:
            failures.append(item["id"])
        else:
            judge[item["id"]] = item["parsed"]
    if failures:
        raise ValueError(f"这些题解析失败，先处理再比较：{failures}")
    summary = summarize_agreement(human, judge)

    print("题号｜人工答案｜人工引用｜裁判答案｜裁判引用｜一致｜裁判理由")
    for row in summary["rows"]:
        reason = str(row["judge_reason"]).replace("\n", " ")[:40]
        print(
            f"{row['id']}｜{_format_ok(row['human_answer_ok'])}｜"
            f"{_format_ok(row['human_citation_ok'])}｜{_format_ok(row['judge_answer_ok'])}｜"
            f"{_format_ok(row['judge_citation_ok'])}｜{row['answer_agree']}｜{reason}"
        )
    print(
        f"\n答案一致 {summary['answer_agree']}/{summary['total']}；"
        f"引用一致 {summary['citation_agree']}/{summary['citation_applicable']}"
    )
    print(f"分歧：{summary['disagreements']}")

    path = run_dir / "agreement.json"
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"结构化结果：{path}")


def main() -> None:
    """按 --part 运行离线对照、真实裁判或与人工标签的比较。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "live", "compare"], default="a")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--live-dir", type=Path, default=None)
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        if args.part == "a":
            run_a(build_judge_messages)
        elif args.part == "b":
            run_b(parse_judge_verdict)
        elif args.part == "live":
            _live(run_dir, args.limit, args.labels)
        else:
            _compare(run_dir, args.live_dir or _latest_live_dir(), args.labels)

    run_logged(
        args.part,
        action,
        config={
            "part": args.part,
            "limit": args.limit,
            "temperature": 0,
            "model_calls": args.limit if args.part == "live" else 0,
            "labels": str(args.labels),
        },
        exercise_path=Path(__file__).resolve(),
        log_root=DAY58 / "outputs",
        origin_env="DAY58_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
