"""Day68 检查器：验证 tests/test_notes_mcp.py 与 CI 接入。

题目与 10 个契约见 demos/day68/day68_题目说明.md。
检查器会真的跑一遍你的测试（超时 180 秒）；0 次模型调用，不改你的文件。
每次运行在 demos/day68/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY68 = REPO_ROOT / "weeks/week09_advanced/demos/day68"
TEST_FILE = REPO_ROOT / "tests/test_notes_mcp.py"
WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
CI_REQS = REPO_ROOT / "requirements-ci.txt"


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


def check_static() -> list[dict[str, object]]:
    """Part A：测试文件结构、CI 与依赖（7 组）。"""
    checks: list[dict[str, object]] = []
    exists = TEST_FILE.is_file()
    checks.append(
        row(
            1,
            "A 测试文件存在",
            exists,
            "tests/test_notes_mcp.py" if exists else "文件不存在",
        )
    )
    text = TEST_FILE.read_text(encoding="utf-8-sig") if exists else ""

    checks.append(
        row(
            2,
            "A 使用 Client",
            "from mcp import Client" in text,
            "需要 from mcp import Client",
        )
    )
    tests = re.findall(r"^def (test_\w+)\(", text, re.MULTILINE)
    checks.append(
        row(3, "A 至少 8 个测试", len(tests) >= 8, f"找到 {len(tests)} 个：{tests}")
    )

    env_ok = "NOTES_ROOT" in text and ("monkeypatch" in text or "os.environ" in text)
    checks.append(
        row(
            4,
            "A 切换 NOTES_ROOT",
            env_ok,
            "需要 monkeypatch 或 os.environ 设 NOTES_ROOT",
        )
    )

    smoke_ok = "subprocess" in text and "timeout=" in text
    checks.append(
        row(5, "A stdio 冒烟带超时", smoke_ok, "需要 subprocess 且写 timeout=")
    )

    workflow = WORKFLOW.read_text(encoding="utf-8-sig") if WORKFLOW.exists() else ""
    checks.append(
        row(
            6,
            "A CI 跑 MCP 测试",
            "tests/test_notes_mcp.py" in workflow,
            "ci.yml 需要引用测试文件",
        )
    )

    reqs = CI_REQS.read_text(encoding="utf-8-sig") if CI_REQS.exists() else ""
    checks.append(
        row(
            7,
            "A CI 依赖含 mcp",
            "mcp==" in reqs,
            f"requirements-ci.txt 内容={reqs.strip()[:60]!r}",
        )
    )
    return checks


def check_run() -> list[dict[str, object]]:
    """Part B：真跑一遍 pytest（2 组）。"""
    checks: list[dict[str, object]] = []
    if not TEST_FILE.is_file():
        return [
            row(8, "B pytest 通过", False, "测试文件不存在"),
            row(9, "B 没有 failed/skipped", False, "测试文件不存在"),
        ]
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "tests/test_notes_mcp.py",
            ],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=180,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return [
            row(
                8, "B pytest 通过", False, "180 秒没跑完：测试里可能有挂住的连接或输入"
            ),
            row(9, "B 没有 failed/skipped", False, "同上"),
        ]

    output = (proc.stdout or "") + (proc.stderr or "")
    passed = int((re.search(r"(\d+) passed", output) or [0, 0])[1])
    failed = int((re.search(r"(\d+) failed", output) or [0, 0])[1])
    skipped = int((re.search(r"(\d+) skipped", output) or [0, 0])[1])
    checks.append(
        row(
            8,
            "B pytest 通过",
            proc.returncode == 0 and passed >= 8,
            f"passed={passed} returncode={proc.returncode}",
        )
    )
    checks.append(
        row(
            9,
            "B 没有 failed/skipped",
            failed == 0 and skipped == 0,
            f"failed={failed} skipped={skipped}",
        )
    )
    return checks


def main() -> None:
    """按 --part 跑 A/B，打印逐项结果并保存留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "all"], default="all")
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        checks: list[dict[str, object]] = []
        parts = {"a": ("A 整体", check_static), "b": ("B 整体", check_run)}
        selected = list(parts) if args.part == "all" else [args.part]
        for key in selected:
            label, runner = parts[key]
            try:
                checks.extend(runner())
            except Exception as error:  # noqa: BLE001 - 结构错误整段报出来
                checks.append(row(0, label, False, f"{type(error).__name__}: {error}"))

        passed = sum(1 for item in checks if item["ok"])
        print("\n逐项结果：")
        for item in checks:
            mark = "[OK]" if item["ok"] else "[X] "
            print(f"{mark} 第 {item['no']:>2} 组 {item['label']}：{item['detail']}")
        print(f"\n合计：{passed}/{len(checks)}")
        if passed == len(checks):
            print("全过。把结果和日志目录抄进记录，再回答观察题。")
        else:
            print("没过：先看每个 [X] 的期望，再回题目说明对要求。")

        payload = {"counts": {"passed": passed, "total": len(checks)}, "checks": checks}
        (run_dir / "results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    run_logged(
        args.part,
        action,
        config={"model_calls": 0, "cases": 9},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY68 / "outputs",
        origin_env="DAY68_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
