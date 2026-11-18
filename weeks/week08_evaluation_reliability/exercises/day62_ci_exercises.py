"""Day62：运行 CI 配置检查器；学员的答案是 .github/workflows/ci.yml。

检查器只读 YAML，不调用模型。先把 workflow 写好，再运行本入口：

    .venv\\Scripts\\python.exe -B -X utf8 weeks\\week08_evaluation_reliability\\exercises\\day62_ci_exercises.py

完整验收点见 demos/day62/day62_题目说明.md。
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week08_evaluation_reliability.demos.day62.day62_ci_checks import (
    WORKFLOW,
    run_checks,
)

DAY62 = REPO_ROOT / "weeks/week08_evaluation_reliability/demos/day62"


def main() -> None:
    """按 --part 运行 YAML 检查；默认只跑 check。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["check"], default="check")
    args = parser.parse_args()

    def action(_run_dir: Path) -> None:
        run_checks(WORKFLOW)

    run_logged(
        args.part,
        action,
        config={"part": args.part, "model_calls": 0},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY62 / "outputs",
        origin_env="DAY62_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
