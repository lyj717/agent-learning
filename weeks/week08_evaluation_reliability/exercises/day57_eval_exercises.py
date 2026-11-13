"""Day57：用规则匹配判分，并按冻结基线判断回归。

--part a/b 运行人工对照，--part regression 重放两版回答并与冻结基线比较。
题目、完整规则与判分情形见 demos/day57/day57_题目说明.md；观察见 day57_记录.md。
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day57.day57_checks import run_a, run_b

DAY57 = REPO_ROOT / "weeks/week08_evaluation_reliability/demos/day57"


def judge_answer(
    case: dict[str, str | list[str]], answer: dict[str, str | list[str]]
) -> dict[str, str | bool | list[str]]:
    """按规则判一份回答，返回 id、passed 与失败项列表。"""
    passed = True
    failed = []
    content = answer["answer"]
    if answer["status"] != "answered":
        passed = False
        failed.append("not_answered")
        return {
            "id": case["id"],
            "passed": passed,
            "failed": failed,
        }
    if not content.strip():
        passed = False
        failed.append("empty_answer")
        return {
            "id": case["id"],
            "passed": passed,
            "failed": failed,
        }
    for key in case["must_include"]:
        if key not in content:
            passed = False
            failed.append("missing_points")
            break
    for key in case["must_not_include"]:
        if key in content:
            passed = False
            failed.append("forbidden_text")
            break
    if not answer["cited_ids"]:
        passed = False
        failed.append("no_citation")
    for cite in answer["cited_ids"]:
        if cite not in case["retrieved_ids"]:
            passed = False
            failed.append("citation_not_retrieved")
            break
    return {
        "id": case["id"],
        "passed": passed,
        "failed": failed,
    }


def compare_baseline(
    baseline: dict[str, dict[str, bool | str | list[str]]],
    current: dict[str, dict[str, bool | str | list[str]]],
) -> dict[str, list[str]]:
    """比较两版逐题结果，返回四类题号列表。"""
    regressed = []
    fixed = []
    still_failing = []
    unchanged_pass = []
    if baseline.keys() != current.keys():
        raise ValueError("题号集合不同！")
    for case in baseline.values():
        if not isinstance(case, dict):
            raise TypeError("内层不是字典！")
        if type(case["passed"]) is not bool:
            raise TypeError("passed不是bool！")
    for case in current.values():
        if not isinstance(case, dict):
            raise TypeError("内层不是字典！")
        if type(case["passed"]) is not bool:
            raise TypeError("passed不是bool！")
    for base_case_id, base_case in baseline.items():
        base_passed = base_case["passed"]
        for curr_case_id, curr_case in current.items():
            curr_passed = curr_case["passed"]
            if base_case_id == curr_case_id:
                if base_passed is True and curr_passed is False:
                    regressed.append(base_case_id)
                if base_passed is False and curr_passed is True:
                    fixed.append(base_case_id)
                if base_passed is False and curr_passed is False:
                    still_failing.append(base_case_id)
                if base_passed is True and curr_passed is True:
                    unchanged_pass.append(base_case_id)
    return {
        "regressed": sorted(regressed),
        "fixed": sorted(fixed),
        "still_failing": sorted(still_failing),
        "unchanged_pass": sorted(unchanged_pass),
    }


def _load(name: str) -> object:
    """读取 day57 目录下的 JSON 数据。"""
    return json.loads((DAY57 / name).read_text(encoding="utf-8"))


def _verdicts(
    cases: list[dict], answers: dict, judge_fn: Callable[..., dict]
) -> dict[str, dict]:
    """对一版回答逐题调用判分函数，返回题号到结果的映射。"""
    rows = [judge_fn(case, answers[case["id"]]) for case in cases]
    return {row["id"]: row for row in rows}


def _regression(run_dir: Path) -> None:
    """重放两版回答，先自检基线，再输出本次四类变化。"""
    cases = _load("day57_cases.json")
    baseline = _load("day57_baseline.json")
    v1 = _load("day57_answers_v1.json")
    v2 = _load("day57_answers_v2.json")

    current_v1 = _verdicts(cases, v1, judge_answer)
    current_v2 = _verdicts(cases, v2, judge_answer)
    self_check = compare_baseline(baseline, current_v1)
    diff = compare_baseline(baseline, current_v2)

    print("题号  v1    v2    v2 失败项")
    for case in cases:
        case_id = case["id"]
        old = current_v1[case_id]
        new = current_v2[case_id]
        print(
            f"{case_id}  {'通过' if old['passed'] else '失败'}  "
            f"{'通过' if new['passed'] else '失败'}  {new['failed']}"
        )

    passed_v1 = sum(1 for row in current_v1.values() if row["passed"])
    passed_v2 = sum(1 for row in current_v2.values() if row["passed"])
    print(f"\n通过数：v1={passed_v1}/{len(cases)}；v2={passed_v2}/{len(cases)}")
    print(f"基线自检（v1 对 baseline）：{self_check}")
    print(f"本次变化（v2 对 baseline）：{diff}")
    print("自检应 regressed/fixed 都为空；still_failing 是基线里原有的已知失败。")

    result = {
        "counts": {"v1_passed": passed_v1, "v2_passed": passed_v2, "total": len(cases)},
        "self_check": self_check,
        "diff": diff,
        "rows": {
            case_id: {
                "v1": current_v1[case_id],
                "v2": current_v2[case_id],
            }
            for case_id in current_v1
        },
    }
    path = run_dir / "regression.json"
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"结构化结果：{path}")


def main() -> None:
    """按 --part 运行人工对照或两版回归，保存控制台与运行信息。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "regression"], default="a")
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        if args.part == "a":
            run_a(judge_answer)
        elif args.part == "b":
            run_b(compare_baseline)
        else:
            _regression(run_dir)

    run_logged(
        args.part,
        action,
        config={"part": args.part, "model_calls": 0, "data_version": "day57-v1"},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY57 / "outputs",
        origin_env="DAY57_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
