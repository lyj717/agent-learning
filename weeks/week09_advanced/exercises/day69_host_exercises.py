"""Day69 检查器：验证宿主脚本可用，且有一次真实模型跑出的轨迹。

题目见 demos/day69/day69_题目说明.md。
检查器会离线跑一次 --fake（不调用模型），再检查你 --live 留下的轨迹文件；不联网。
每次运行在 demos/day69/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY69 = REPO_ROOT / "weeks/week09_advanced/demos/day69"
HOST = DAY69 / "day69_host.py"
OUTPUTS = DAY69 / "outputs"
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


def latest(pattern: str) -> Path | None:
    """按修改时间取最新的匹配轨迹文件。"""
    files = sorted(OUTPUTS.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def check_static() -> list[dict[str, object]]:
    """Part A：宿主脚本的结构（5 组）。"""
    checks: list[dict[str, object]] = []
    exists = HOST.is_file()
    checks.append(row(1, "A 宿主脚本存在", exists, "day69_host.py"))
    text = HOST.read_text(encoding="utf-8") if exists else ""
    checks.append(
        row(
            2,
            "A 用 stdio 启动 server",
            "StdioServerParameters" in text,
            "需要 StdioServerParameters",
        )
    )
    checks.append(
        row(
            3,
            "A 转换工具定义",
            "input_schema" in text and "tools" in text,
            "需要把 MCP 工具转成模型可用的 tools",
        )
    )
    checks.append(
        row(
            4,
            "A 工具结果回填",
            '"role": "tool"' in text or "'role': 'tool'" in text,
            "需要 tool 消息",
        )
    )
    checks.append(
        row(5, "A 保存轨迹", "outputs" in text and ".json" in text, "需要写轨迹 JSON")
    )
    return checks


def run_fake() -> list[dict[str, object]]:
    """Part B：离线跑一次 --fake，检查轨迹（2 组）。"""
    checks: list[dict[str, object]] = []
    before = set(OUTPUTS.glob("fake_*.json")) if OUTPUTS.exists() else set()
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(HOST), "--fake"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return [
            row(6, "B 离线自检", False, "120 秒没结束"),
            row(7, "B 假轨迹有一次工具调用", False, "同上"),
        ]
    checks.append(
        row(
            6,
            "B 离线自检",
            proc.returncode == 0,
            f"returncode={proc.returncode} {proc.stderr[-120:]!r}",
        )
    )
    after = set(OUTPUTS.glob("fake_*.json")) if OUTPUTS.exists() else set()
    new_files = sorted(after - before, key=lambda path: path.stat().st_mtime)
    if not new_files:
        checks.append(row(7, "B 假轨迹有一次工具调用", False, "没有新轨迹文件"))
        return checks
    data = json.loads(new_files[-1].read_text(encoding="utf-8"))
    calls = [
        call for step in data.get("steps", []) for call in step.get("tool_calls", [])
    ]
    ok = bool(calls) and bool(data.get("answer"))
    checks.append(
        row(
            7,
            "B 假轨迹有一次工具调用",
            ok,
            f"tool_calls={len(calls)} answer={bool(data.get('answer'))}",
        )
    )
    return checks


def check_live() -> list[dict[str, object]]:
    """Part C：检查一次 --live 留下的真实轨迹（3 组）。"""
    checks: list[dict[str, object]] = []
    path = latest("live_*.json")
    if path is None:
        return [
            row(8, "C 有真实轨迹", False, "outputs/ 下没有 live_*.json，先跑 --live"),
            row(9, "C 模型调用过工具", False, "没有真实轨迹"),
            row(10, "C 回答与用量", False, "没有真实轨迹"),
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = [
        call for step in data.get("steps", []) for call in step.get("tool_calls", [])
    ]
    answer = data.get("answer") or ""
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    checks.append(row(8, "C 有真实轨迹", True, str(path.relative_to(REPO_ROOT))))
    checks.append(
        row(9, "C 模型调用过工具", len(calls) >= 1, f"tool_calls={len(calls)}")
    )
    checks.append(
        row(
            10,
            "C 回答与用量",
            bool(answer.strip()) and prompt_tokens > 0 and "max" not in answer[:20],
            f"answer_len={len(answer)} prompt_tokens={prompt_tokens}",
        )
    )
    return checks


def main() -> None:
    """按 --part 跑 A/B/C，打印逐项结果并保存留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "c", "all"], default="all")
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        checks: list[dict[str, object]] = []
        parts = {
            "a": ("A 整体", check_static),
            "b": ("B 整体", run_fake),
            "c": ("C 整体", check_live),
        }
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
            print("全过。把结果与轨迹路径抄进记录，再回答观察题。")
        else:
            print("没过：先看每个 [X] 的期望，再回题目说明对要求。")

        payload = {"counts": {"passed": passed, "total": len(checks)}, "checks": checks}
        (run_dir / "results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    run_logged(
        args.part,
        action,
        config={"model_calls": 0, "cases": 10},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY69 / "outputs",
        origin_env="DAY69_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
