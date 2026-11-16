"""Day60：缩小证据后的前后对照。

--part a 离线检查，measure/quality 调模型，report 汇总对照。
题目、字段与全部判分情形见 demos/day60/day60_题目说明.md；观察见 day60_record.md。
"""

import argparse
import json
import statistics  # statistics.median(可迭代对象)：返回中位数；偶数个取中间两个的平均
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day60.day60_checks import run_a
from weeks.week08_evaluation_reliability.demos.day60.day60_support import (
    DAY60,
    describe_condition,
    evaluate_quality,
    measure_paired,
)

METRICS = ("ttft_ms", "end_to_end_ms", "cost_cny")


def compare_conditions(
    baseline: list[dict], optimized: list[dict]
) -> dict[str, object]:
    """按题汇总两套条件，返回逐题中位数、差值与整体均值/费用。"""
    if not isinstance(baseline, list) or not isinstance(optimized, list):
        raise TypeError("条件不是列表")
    if not baseline or not optimized:
        raise ValueError("列表为空")
    required = {"id", "ttft_ms", "end_to_end_ms", "cost_cny"}
    check = {"ttft_ms", "end_to_end_ms", "cost_cny"}
    b_id = []
    o_id = []
    for case in baseline:
        if not required <= case.keys():
            raise ValueError("字段缺失")
        new = {k: case[k] for k in check}
        for value in new.values():
            if type(value) not in (int, float):
                raise ValueError("值不是数字")
        b_id.append(case["id"])
    for case in optimized:
        if not required <= case.keys():
            raise ValueError("字段缺失")
        new = {k: case[k] for k in check}
        for value in new.values():
            if type(value) not in (int, float):
                raise ValueError("值不是数字")
        o_id.append(case["id"])
    if set(b_id) != set(o_id):
        raise ValueError("题号集合不同")
    questions = []
    baseline_by_id = {}
    optimized_by_id = {}
    for row in baseline:
        baseline_by_id.setdefault(row["id"], []).append(row)
    for row in optimized:
        optimized_by_id.setdefault(row["id"], []).append(row)
    total_baseline_ttft = 0
    total_optimized_ttft = 0
    total_baseline_end_to_end = 0
    total_optimized_end_to_end = 0
    baseline_total_cost = 0
    optimized_total_cost = 0
    for case_id in sorted(baseline_by_id):
        base = baseline_by_id[case_id]
        op = optimized_by_id[case_id]
        baseline_ttft = statistics.median(item["ttft_ms"] for item in base)
        optimized_ttft = statistics.median(item["ttft_ms"] for item in op)
        baseline_end_to_end = statistics.median(item["end_to_end_ms"] for item in base)
        optimized_end_to_end = statistics.median(item["end_to_end_ms"] for item in op)
        baseline_cost = statistics.median(item["cost_cny"] for item in base)
        optimized_cost = statistics.median(item["cost_cny"] for item in op)
        total_baseline_ttft += baseline_ttft
        total_optimized_ttft += optimized_ttft
        total_baseline_end_to_end += baseline_end_to_end
        total_optimized_end_to_end += optimized_end_to_end
        baseline_total_cost += baseline_cost
        optimized_total_cost += optimized_cost
        questions.append(
            {
                "id": case_id,
                "baseline_ttft": baseline_ttft,
                "optimized_ttft": optimized_ttft,
                "ttft_delta": optimized_ttft - baseline_ttft,
                "baseline_end_to_end": baseline_end_to_end,
                "optimized_end_to_end": optimized_end_to_end,
                "end_to_end_delta": optimized_end_to_end - baseline_end_to_end,
                "baseline_cost": baseline_cost,
                "optimized_cost": optimized_cost,
                "cost_delta": optimized_cost - baseline_cost,
            }
        )
    count = len(baseline_by_id)
    return {
        "questions": questions,
        "baseline_mean_end_to_end": total_baseline_end_to_end / count,
        "optimized_mean_end_to_end": total_optimized_end_to_end / count,
        "end_to_end_delta_mean": (
            total_optimized_end_to_end - total_baseline_end_to_end
        )
        / count,
        "baseline_total_cost": baseline_total_cost,
        "optimized_total_cost": optimized_total_cost,
        "cost_delta_total": optimized_total_cost - baseline_total_cost,
    }


def _latest(kind: str, filename: str) -> Path:
    """找最近一次某类运行中含指定文件的目录。"""
    candidates = sorted(
        (DAY60 / "outputs").glob(f"{kind}_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if (path / filename).is_file():
            return path
    raise FileNotFoundError(f"没有找到 {kind} 结果，先运行 --part {kind}")


def _median_by_id(rows: list[dict], condition: str) -> list[dict]:
    """取一个条件的逐题中位数，供打印使用。"""
    return describe_condition(rows, condition)


def _measure(run_dir: Path, rounds: int, limit: int) -> None:
    """交替跑两套配置，保存逐次结果并打印各自中位数。"""
    print(
        f"将跑 {rounds} 轮 × 2 套配置；每轮 {limit} 题，"
        f"共 {rounds * limit * 2} 次调用。"
    )
    data = measure_paired(rounds=rounds, limit=limit)
    path = run_dir / "paired_measurements.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n成功 {len(data['rows'])} 次；失败 {len(data['errors'])} 次")
    for condition in ("baseline", "optimized"):
        subset = [row for row in data["rows"] if row["condition"] == condition]
        counts: dict[str, int] = {}
        for row in subset:
            counts[row["id"]] = counts.get(row["id"], 0) + 1
        sample_id = min(counts) if counts else "-"
        print(
            f"{condition}：{len(subset)} 行；"
            f"每个 id 行数示例 {sample_id}={counts.get(sample_id, 0)}"
        )
        print(f"\n{condition}：题号｜次数｜首字中位｜端到端中位｜费用中位")
        for item in _median_by_id(data["rows"], condition):
            print(
                f"{item['id']}｜{item['count']}｜{item['ttft_median']:.0f}｜"
                f"{item['end_to_end_median']:.0f}｜{item['cost_median']:.6f}"
            )
    print(f"结构化结果：{path}")


def _quality(run_dir: Path) -> None:
    """读最近一次 measure，跑规则与裁判质量检查，保存并打印。"""
    measure_dir = _latest("measure", "paired_measurements.json")
    data = json.loads(
        (measure_dir / "paired_measurements.json").read_text(encoding="utf-8")
    )
    print("将用 Day57 规则和 Day58 裁判检查两套条件中每题最后一轮可解析的回答。")
    quality = evaluate_quality(data["rows"])
    path = run_dir / "quality.json"
    path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("题号｜规则 baseline｜规则 optimized｜裁判答案 b/o｜裁判引用 b/o")
    grouped: dict[str, dict] = {}
    for row in quality["rows"]:
        grouped.setdefault(row["id"], {})[row["condition"]] = row

    def fmt_rule(item: dict) -> str:
        if item is None or item["rule"] is None:
            return "错误"
        return "通过" if item["rule"]["passed"] else "失败"

    def fmt_judge(item: dict, key: str) -> str:
        if item is None or item["judge"] is None:
            return "错误"
        value = item["judge"][key]
        if value is None:
            return "不适用"
        return "通过" if value else "失败"

    for case_id in sorted(grouped):
        pair = grouped[case_id]
        left = pair.get("baseline")
        right = pair.get("optimized")
        print(
            f"{case_id}｜{fmt_rule(left)}｜{fmt_rule(right)}｜"
            f"{fmt_judge(left, 'answer_ok')}/{fmt_judge(right, 'answer_ok')}｜"
            f"{fmt_judge(left, 'citation_ok')}/{fmt_judge(right, 'citation_ok')}"
        )

    for condition in ("baseline", "optimized"):
        items = [row for row in quality["rows"] if row["condition"] == condition]
        rule_pass = sum(1 for row in items if row["rule"] and row["rule"]["passed"])
        judge_pass = sum(
            1 for row in items if row["judge"] and row["judge"]["answer_ok"] is True
        )
        print(
            f"\n{condition}：规则通过 {rule_pass}/{len(items)}；"
            f"裁判 answer_ok {judge_pass}/{len(items)}"
        )
    print(f"结构化结果：{path}")


def _report(run_dir: Path, measure_dir: Path) -> None:
    """合并两套条件的测量，打印逐题对照与整体差值。"""
    data = json.loads(
        (measure_dir / "paired_measurements.json").read_text(encoding="utf-8")
    )
    baseline = [row for row in data["rows"] if row["condition"] == "baseline"]
    optimized = [row for row in data["rows"] if row["condition"] == "optimized"]
    comparison = compare_conditions(baseline, optimized)

    print("题号｜端到端 b/o/差值｜费用 b/o/差值")
    for item in comparison["questions"]:
        print(
            f"{item['id']}｜{item['baseline_end_to_end']:.0f}/"
            f"{item['optimized_end_to_end']:.0f}/{item['end_to_end_delta']:+.0f}｜"
            f"{item['baseline_cost']:.6f}/{item['optimized_cost']:.6f}/"
            f"{item['cost_delta']:+.6f}"
        )
    print(
        f"\n端到端均值：{comparison['baseline_mean_end_to_end']:.0f} → "
        f"{comparison['optimized_mean_end_to_end']:.0f}ms，"
        f"差值 {comparison['end_to_end_delta_mean']:+.0f}ms"
    )
    print(
        f"费用合计（按题中位数）：{comparison['baseline_total_cost']:.6f} → "
        f"{comparison['optimized_total_cost']:.6f} 元，"
        f"差值 {comparison['cost_delta_total']:+.6f} 元"
    )
    path = run_dir / "comparison.json"
    path.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"结构化结果：{path}")


def main() -> None:
    """按 --part 运行离线检查、成对测量、质量检查或对照报告。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=["a", "measure", "quality", "report"], default="a"
    )
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--measure-dir", type=Path, default=None)
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        if args.part == "a":
            run_a(compare_conditions)
        elif args.part == "measure":
            _measure(run_dir, args.rounds, args.limit)
        elif args.part == "quality":
            _quality(run_dir)
        else:
            _report(
                run_dir,
                args.measure_dir or _latest("measure", "paired_measurements.json"),
            )

    run_logged(
        args.part,
        action,
        config={
            "part": args.part,
            "rounds": args.rounds,
            "limit": args.limit,
            "temperature": 0,
            "model_calls": (
                args.rounds * args.limit * 2
                if args.part == "measure"
                else 16
                if args.part == "quality"
                else 0
            ),
            "price_snapshot": "day47_price_snapshot.json",
        },
        exercise_path=Path(__file__).resolve(),
        log_root=DAY60 / "outputs",
        origin_env="DAY60_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
