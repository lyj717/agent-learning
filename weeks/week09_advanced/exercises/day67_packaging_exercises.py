"""Day67 检查器：验证打包配置与 README 是否能让别人装得上、配得进宿主。

题目与全部判分情形见 demos/day67/day67_题目说明.md。
检查器只读文件、跑一次模块冒烟，不安装、不改文件、不联网；0 次模型调用。
每次运行在 demos/day67/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY67 = REPO_ROOT / "weeks/week09_advanced/demos/day67"
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"
PROJECT = REPO_ROOT / "projects/mcp_server"
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = PROJECT / "README.md"


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


def load_pyproject() -> tuple[dict | None, str | None]:
    """读仓库根的 pyproject.toml，返回 (内容, 错误)。"""
    if not PYPROJECT.exists():
        return None, "仓库根没有 pyproject.toml"
    try:
        return tomllib.loads(PYPROJECT.read_text(encoding="utf-8-sig")), None
    except tomllib.TOMLDecodeError as error:
        return None, f"TOML 解析失败：{error}"


def check_a() -> list[dict[str, object]]:
    """Part A：pyproject 与包发现（8 组）。"""
    checks: list[dict[str, object]] = []
    data, error = load_pyproject()
    checks.append(row(1, "A pyproject 存在且可解析", data is not None, error or "OK"))
    if data is None:
        for number, label in (
            (2, "A 项目名"),
            (3, "A 版本与代码一致"),
            (4, "A Python 版本要求"),
            (5, "A mcp 依赖下限"),
            (6, "A 入口点"),
            (7, "A 打包的包列表"),
        ):
            checks.append(row(number, label, False, "pyproject 不可用"))
    else:
        project = data.get("project", {})
        name = project.get("name")
        checks.append(
            row(
                2,
                "A 项目名",
                isinstance(name, str) and bool(name.strip()),
                f"name={name!r}",
            )
        )

        version = project.get("version")
        version_text = (
            (PROJECT / "__init__.py").read_text(encoding="utf-8")
            if (PROJECT / "__init__.py").exists()
            else ""
        )
        match = re.search(r'__version__\s*=\s*"([^"]+)"', version_text)
        code_version = match.group(1) if match else None
        ok = isinstance(version, str) and version == code_version
        checks.append(
            row(
                3,
                "A 版本与代码一致",
                ok,
                f"pyproject={version!r} 代码={code_version!r}",
            )
        )

        requires = project.get("requires-python")
        checks.append(
            row(
                4,
                "A Python 版本要求",
                isinstance(requires, str) and ">=" in requires,
                f"requires-python={requires!r}",
            )
        )

        deps = project.get("dependencies", [])
        mcp = [
            item for item in deps if isinstance(item, str) and item.startswith("mcp")
        ]
        ok = bool(mcp) and ">=2.3" in mcp[0] and "<3" in mcp[0]
        checks.append(row(5, "A mcp 依赖下限", ok, f"dependencies={deps}"))

        scripts = project.get("scripts", {})
        entry = scripts.get("notes-mcp-server")
        ok = entry == "projects.mcp_server.server:main"
        checks.append(row(6, "A 入口点", ok, f"notes-mcp-server={entry!r}"))

        packages = data.get("tool", {}).get("setuptools", {}).get("packages", [])
        ok = isinstance(packages, list) and {"projects", "projects.mcp_server"} <= set(
            packages
        )
        checks.append(row(7, "A 打包的包列表", ok, f"packages={packages}"))

    init_ok = (REPO_ROOT / "projects/__init__.py").is_file()
    checks.append(
        row(8, "A projects 包标记", init_ok, f"projects/__init__.py 存在={init_ok}")
    )
    return checks


def check_b() -> list[dict[str, object]]:
    """Part B：README 与许可证（8 组）。"""
    checks: list[dict[str, object]] = []
    if not README.exists():
        return [row(9, "B README 存在", False, "projects/mcp_server/README.md 不存在")]
    text = README.read_text(encoding="utf-8-sig")
    lowered = text.lower()
    blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.DOTALL)

    checks.append(row(9, "B README 存在", True, f"{len(text)} 字符"))
    checks.append(
        row(
            10,
            "B 安装命令",
            any("pip install" in block.lower() for block in blocks),
            "需要一个包含 pip install 的代码块",
        )
    )
    checks.append(
        row(
            11,
            "B Claude Desktop 配置",
            any("mcpServers" in block and "command" in block for block in blocks),
            "需要一个含 mcpServers 与 command 的 JSON 块",
        )
    )
    checks.append(
        row(
            12,
            "B Cursor 配置",
            ".cursor/mcp.json" in text,
            "需要写明 .cursor/mcp.json",
        )
    )
    checks.append(
        row(
            13,
            "B VS Code 配置",
            any(
                '"servers"' in block and '"type": "stdio"' in block for block in blocks
            ),
            "需要一个含 servers 与 type stdio 的 JSON 块",
        )
    )
    checks.append(
        row(14, "B 环境变量说明", "NOTES_ROOT" in text, "README 要写 NOTES_ROOT")
    )
    checks.append(
        row(15, "B 入口命令", "notes-mcp-server" in text, "README 要写装好后的命令名")
    )
    license_file = any(
        (REPO_ROOT / name).is_file()
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")
    )
    license_text = any(
        word in lowered for word in ("license", "许可证", "mit", "apache")
    )
    checks.append(
        row(
            16,
            "B 许可证",
            license_file and license_text,
            f"LICENSE 文件={license_file} README 提及={license_text}",
        )
    )
    return checks


def check_c() -> list[dict[str, object]]:
    """Part C：模块能启动、入口函数可调用（2 组）。"""
    checks: list[dict[str, object]] = []
    env = {**os.environ, "NOTES_ROOT": str(CORPUS), "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "projects.mcp_server.server"],
            cwd=REPO_ROOT,
            input="",
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=20,
            check=False,
            env=env,
        )
        ok = proc.returncode == 0
        detail = f"returncode={proc.returncode} stderr={proc.stderr.strip()[:80]!r}"
    except subprocess.TimeoutExpired:
        ok = False
        detail = "20 秒没退出：stdio server 可能在空 stdin 下挂住"
    checks.append(row(17, "C 模块冒烟（空 stdin）", ok, detail))

    try:
        sys.path.insert(0, str(REPO_ROOT))
        from projects.mcp_server.server import main

        ok = callable(main)
        detail = "main 可调用" if ok else "main 不是函数"
    except Exception as error:  # noqa: BLE001 - 导入错误要报出来
        ok = False
        detail = f"{type(error).__name__}: {error}"
    checks.append(row(18, "C 入口函数可导入", ok, detail))
    return checks


def main() -> None:
    """按 --part 跑 A/B/C，打印逐项结果并保存留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "c", "all"], default="all")
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        checks: list[dict[str, object]] = []
        parts = {
            "a": ("A 整体", check_a),
            "b": ("B 整体", check_b),
            "c": ("C 整体", check_c),
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
        config={"model_calls": 0, "cases": 18},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY67 / "outputs",
        origin_env="DAY67_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
