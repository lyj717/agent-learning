"""Day59：测量检索、首字与生成延迟，并汇总 token 与费用。

--part a/b 跑离线检查，--part live/repeat 调模型测量，--part report 汇总。
题目、字段与全部判分情形见 demos/day59/day59_题目说明.md；观察见 day59_record.md。
"""

import argparse
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day59.day59_checks import run_a, run_b
from weeks.week08_evaluation_reliability.demos.day59.day59_support import (
    DAY59,
    describe_repeats,
    measure_all,
    measure_repeated,
)


def percentile(values: list[float], p: float) -> float:
    """按最近秩法计算百分位。"""
    if not isinstance(values, list) or not values:
        raise ValueError("values不是非空列表")
    for value in values:
        if type(value) not in (int, float):
            raise ValueError("values元素不是int或float")
    if type(p) not in (int, float):
        raise ValueError("p不是int或float")
    if p <= 0 or p > 100:
        raise ValueError("p取值错误")
    sort = sorted(values)
    rank = math.ceil(p / 100 * len(values))
    return sort[rank - 1]


def summarize_measurements(rows: list[dict]) -> dict[str, float | int]:
    """汇总逐题测量，返回计数、P50/P95、token 合计与费用。"""
    if not isinstance(rows, list):
        raise TypeError("rows不是列表")
    if not rows:
        raise ValueError("rows为空")
    count = 0
    retrieval_ms = []
    ttft_ms = []
    generation_ms = []
    end_to_end_ms = []
    prompt_tokens = 0
    completion_tokens = 0
    total_cost = 0
    for row in rows:
        count += 1
        if not isinstance(row, dict):
            raise ValueError("row不是字典")  # noqa: TRY004 - 本题数据错误统一 ValueError。
        required = {
            "retrieval_ms",
            "ttft_ms",
            "generation_ms",
            "end_to_end_ms",
            "prompt_tokens",
            "completion_tokens",
            "cost_cny",
        }
        if not required <= set(row):
            raise ValueError("键错误")
        new = {k: row[k] for k in required}
        for value in new.values():
            if type(value) not in (int, float):
                raise ValueError("值不是数字")
        retrieval_ms.append(row["retrieval_ms"])
        ttft_ms.append(row["ttft_ms"])
        generation_ms.append(row["generation_ms"])
        end_to_end_ms.append(row["end_to_end_ms"])
        prompt_tokens += row["prompt_tokens"]
        completion_tokens += row["completion_tokens"]
        total_cost += row["cost_cny"]
    return {
        "count": count,
        "retrieval_p50": percentile(retrieval_ms, 50),
        "retrieval_p95": percentile(retrieval_ms, 95),
        "ttft_p50": percentile(ttft_ms, 50),
        "ttft_p95": percentile(ttft_ms, 95),
        "generation_p50": percentile(generation_ms, 50),
        "generation_p95": percentile(generation_ms, 95),
        "end_to_end_p50": percentile(end_to_end_ms, 50),
        "end_to_end_p95": percentile(end_to_end_ms, 95),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "total_cost": total_cost,
        "mean_cost": total_cost / count,
    }


def _latest_measure_dir() -> Path:
    """找最近一次 live 测量目录；找不到时明确报错。"""
    candidates = sorted(
        (DAY59 / "outputs").glob("live_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if (path / "measurements.json").is_file():
            return path
    raise FileNotFoundError("没有找到 live 测量结果，先运行 --part live")


def _live(run_dir: Path, limit: int) -> None:
    """跑一次真实测量并保存逐题结果；失败题也写进 errors。"""
    print(f"将调用模型 {limit} 次，并做一次本地检索索引构建；失败也保留。")
    data = measure_all(limit=limit)
    path = run_dir / "measurements.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n成功 {len(data['rows'])} 题；失败 {len(data['errors'])} 题")
    for error in data["errors"]:
        print(f"  {error['id']}：{error['error']}")
    print(f"结构化结果：{path}")


def _report(run_dir: Path, measure_dir: Path) -> None:
    """读一次测量，打印逐题表与汇总，保存 summary.json。"""
    data = json.loads((measure_dir / "measurements.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    summary = summarize_measurements(rows)

    print("题号｜检索ms｜首字ms｜生成ms｜端到端ms｜输入tok｜输出tok｜费用元")
    for row in rows:
        print(
            f"{row['id']}｜{row['retrieval_ms']:.0f}｜{row['ttft_ms']:.0f}｜"
            f"{row['generation_ms']:.0f}｜{row['end_to_end_ms']:.0f}｜"
            f"{row['prompt_tokens']}｜{row['completion_tokens']}｜{row['cost_cny']:.6f}"
        )
    print(
        f"\n样本={summary['count']}；输入={summary['prompt_tokens']} token；"
        f"输出={summary['completion_tokens']} token"
    )
    print(
        f"P50/P95：检索 {summary['retrieval_p50']:.0f}/{summary['retrieval_p95']:.0f}ms；"
        f"首字 {summary['ttft_p50']:.0f}/{summary['ttft_p95']:.0f}ms；"
        f"端到端 {summary['end_to_end_p50']:.0f}/{summary['end_to_end_p95']:.0f}ms"
    )
    print(
        f"费用合计={summary['total_cost']:.6f} 元；"
        f"单题均值={summary['mean_cost']:.6f} 元"
    )

    path = run_dir / "summary.json"
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"结构化结果：{path}")


def _repeat(run_dir: Path, times: int, limit: int) -> None:
    """按轮重复测量，保存每次结果并打印每题 min/median/max。"""
    print(f"将跑 {times} 轮 × 前 {limit} 题，共 {times * limit} 次调用。")
    data = measure_repeated(times, limit)
    path = run_dir / "repeat_measurements.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows = data["rows"]
    print(f"\n成功 {len(rows)} 次；失败 {len(data['errors'])} 次")
    for error in data["errors"]:
        print(f"  第 {error['round']} 轮 {error['id']}：{error['error']}")

    print("\n题号｜次数｜首字 min/median/max｜端到端 min/median/max")
    for item in describe_repeats(rows):
        print(
            f"{item['id']}｜{item['count']}｜"
            f"{item['ttft_min']:.0f}/{item['ttft_median']:.0f}/{item['ttft_max']:.0f}｜"
            f"{item['end_to_end_min']:.0f}/{item['end_to_end_median']:.0f}/"
            f"{item['end_to_end_max']:.0f}"
        )
    print(f"结构化结果：{path}")


def main() -> None:
    """按 --part 运行离线对照、真实测量或汇总报告。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=["a", "b", "live", "repeat", "report"], default="a"
    )
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--times", type=int, default=3)
    parser.add_argument("--measure-dir", type=Path, default=None)
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        if args.part == "a":
            run_a(percentile)
        elif args.part == "b":
            run_b(summarize_measurements)
        elif args.part == "live":
            _live(run_dir, args.limit)
        elif args.part == "repeat":
            _repeat(run_dir, args.times, args.limit)
        else:
            _report(run_dir, args.measure_dir or _latest_measure_dir())

    run_logged(
        args.part,
        action,
        config={
            "part": args.part,
            "limit": args.limit,
            "times": args.times,
            "temperature": 0,
            "model_calls": (
                args.times * args.limit
                if args.part == "repeat"
                else args.limit
                if args.part == "live"
                else 0
            ),
            "price_snapshot": "day47_price_snapshot.json",
        },
        exercise_path=Path(__file__).resolve(),
        log_root=DAY59 / "outputs",
        origin_env="DAY59_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
