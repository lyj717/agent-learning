"""Day65 检查器：验证文件检索与路径边界。

题目与全部判分情形见 demos/day65/day65_题目说明.md。
检查器只读你的函数和 server，不修改任何文件；全部离线，0 次模型调用。
每次运行在 demos/day65/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
"""

import argparse
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp import Client

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY65 = REPO_ROOT / "weeks/week09_advanced/demos/day65"
CORPUS = DAY65 / "corpus"

EXPECTED_ALL = [
    {"source": "archive/old.md", "line": 2, "text": "关键词：旧的也保留。"},
    {"source": "notes/agent-notes.md", "line": 3, "text": "关键词：描述写清用途。"},
    {"source": "notes/agent-notes.md", "line": 4, "text": "关键词：参数写清含义。"},
    {"source": "notes/python-notes.md", "line": 3, "text": "关键词：元组不可变。"},
]
EXPECTED_FIRST_TWO = EXPECTED_ALL[:2]
EXPECTED_NOTES = EXPECTED_ALL[1:]
EXPECTED_TOOL_HIT = [
    {"source": "notes/agent-notes.md", "line": 2, "text": "工具描述决定调用正确率。"}
]
EXPECTED_TOOL = EXPECTED_ALL[1:]


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组；detail 写实际值与期望值，失败时好定位。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


def outcome_of(call) -> tuple[object | None, str | None]:
    """执行一次调用，返回 (结果, 错误描述)；ValueError 单独标成「按预期拒绝」。"""
    try:
        return call(), None
    except ValueError as error:
        return None, f"ValueError: {error}"
    except NotImplementedError as error:
        return None, f"还没写：{error}"
    except Exception as error:  # noqa: BLE001 - 其他异常要报出来，不能吞
        return None, f"{type(error).__name__}: {error}"


def check_a() -> list[dict[str, object]]:
    """Part A：safe_subdir 的 8 组路径情形。"""
    from projects.mcp_server.search import safe_subdir

    cases: list[tuple[str, str, str]] = [
        ("空串取根", "", "dir"),
        ("子目录 notes", "notes", "dir"),
        ("notes/../notes 合法", "notes/../notes", "dir"),
        ("单个 .. 越界", "..", "error"),
        ("../outside 越界", "../outside", "error"),
        ("Windows 绝对路径", "C:\\Windows", "error"),
        ("不存在的目录", "missing", "error"),
        ("指向文件而不是目录", "notes/python-notes.md", "error"),
    ]
    checks: list[dict[str, object]] = []
    for number, (label, folder, kind) in enumerate(cases, start=1):
        result, error = outcome_of(lambda folder=folder: safe_subdir(CORPUS, folder))
        if kind == "error":
            ok = error is not None and error.startswith("ValueError")
            checks.append(
                row(number, f"A {label}", ok, error or f"没拒绝，返回={result}")
            )
            continue
        expected = (CORPUS / folder).resolve() if folder else CORPUS.resolve()
        ok = error is None and result == expected
        detail = error or f"实际={result} 期望={expected}"
        checks.append(row(number, f"A {label}", ok, detail))
    return checks


def check_b() -> list[dict[str, object]]:
    """Part B：search_files 的 10 组情形（命中、截断、过滤、跳过、参数）。"""
    from projects.mcp_server.search import search_files

    emptydir = CORPUS / "emptydir"
    cases: list[tuple[str, dict[str, object], object]] = [
        (
            "全量命中 4 条",
            {"root": CORPUS, "keyword": "关键词", "limit": 5},
            EXPECTED_ALL,
        ),
        (
            "全局 limit=2",
            {"root": CORPUS, "keyword": "关键词", "limit": 2},
            EXPECTED_FIRST_TWO,
        ),
        (
            "folder=notes",
            {"root": CORPUS, "keyword": "关键词", "limit": 5, "folder": "notes"},
            EXPECTED_NOTES,
        ),
        (
            "关键词 工具",
            {"root": CORPUS, "keyword": "工具", "limit": 5},
            EXPECTED_TOOL_HIT,
        ),
        ("无命中", {"root": CORPUS, "keyword": "不存在的词", "limit": 5}, []),
        ("空关键词", {"root": CORPUS, "keyword": "   ", "limit": 5}, "error"),
        ("limit=0", {"root": CORPUS, "keyword": "关键词", "limit": 0}, "error"),
        ("坏文件被跳过", {"root": CORPUS, "keyword": "坏文件", "limit": 5}, []),
        (
            "notes/../notes 合法",
            {
                "root": CORPUS,
                "keyword": "关键词",
                "limit": 5,
                "folder": "notes/../notes",
            },
            EXPECTED_NOTES,
        ),
        (
            "空目录里也要先校验参数",
            {"root": emptydir, "keyword": "   ", "limit": 5},
            "error",
        ),
    ]
    checks: list[dict[str, object]] = []
    for number, (label, kwargs, expected) in enumerate(cases, start=9):
        result, error = outcome_of(lambda kwargs=kwargs: search_files(**kwargs))
        if expected == "error":
            ok = error is not None and error.startswith("ValueError")
            checks.append(
                row(number, f"B {label}", ok, error or f"没拒绝，返回={result}")
            )
            continue
        ok = error is None and result == expected
        checks.append(
            row(number, f"B {label}", ok, error or f"实际={result} 期望={expected}")
        )
    return checks


def result_text(result: object) -> str:
    """取出工具结果里的第一段文本，用来区分「工具没注册」和「工具自己拒绝」。"""
    content = getattr(result, "content", None) or []
    if content and isinstance(getattr(content[0], "text", None), str):
        return content[0].text
    return ""


async def check_c() -> list[dict[str, object]]:
    """Part C：通过 MCP 工具调用，验证 NOTES_ROOT 与越界拒绝。"""
    from projects.mcp_server.server import mcp

    checks: list[dict[str, object]] = []
    saved = os.environ.get("NOTES_ROOT")

    async def call_tool(
        arguments: dict[str, object],
    ) -> tuple[object | None, str | None]:
        """调用 search_notes，返回 (结果, 错误描述)。"""
        try:
            return await client.call_tool("search_notes", arguments), None
        except Exception as error:  # noqa: BLE001 - 协议层异常要报出来
            return None, f"{type(error).__name__}: {error}"

    try:
        async with Client(mcp) as client:
            os.environ["NOTES_ROOT"] = str(CORPUS)
            result, error = await call_tool(
                {"keyword": "关键词", "limit": 3, "folder": "notes"}
            )
            text = "" if result is None else str(getattr(result, "content", ""))
            if error or result is None:
                checks.append(row(19, "C 工具检索 notes", False, error or "没有结果"))
            else:
                ok = result.is_error is False and result.structured_content == {
                    "result": EXPECTED_TOOL
                }
                checks.append(
                    row(
                        19,
                        "C 工具检索 notes",
                        ok,
                        f"is_error={result.is_error} 内容={text[:80]}",
                    )
                )

            result, error = await call_tool(
                {"keyword": "关键词", "folder": "../outside"}
            )
            text = result_text(result)
            ok = (
                result is not None
                and getattr(result, "is_error", None) is True
                and "Error executing tool search_notes:" in text
            )
            checks.append(
                row(20, "C 越界 folder", error is None and ok, error or text[:80])
            )

            os.environ["NOTES_ROOT"] = str(CORPUS / "no-such-dir")
            result, error = await call_tool({"keyword": "关键词"})
            text = result_text(result)
            ok = (
                result is not None
                and getattr(result, "is_error", None) is True
                and "Error executing tool search_notes:" in text
            )
            checks.append(
                row(21, "C 语料根不存在", error is None and ok, error or text[:80])
            )

            os.environ.pop("NOTES_ROOT", None)
            result, error = await call_tool({"keyword": "流式", "limit": 2})
            if error or result is None:
                checks.append(row(22, "C 默认语料 notes/", False, error or "没有结果"))
            else:
                payload = getattr(result, "structured_content", None) or {}
                items = payload.get("result", [])
                sources = [item.get("source") for item in items]
                ok = (
                    getattr(result, "is_error", None) is False
                    and len(items) >= 1
                    and all(
                        isinstance(source, str) and not source.startswith(("/", "\\"))
                        for source in sources
                    )
                    and any(str(source).endswith(".md") for source in sources)
                )
                checks.append(row(22, "C 默认语料 notes/", ok, f"sources={sources}"))
    finally:
        if saved is None:
            os.environ.pop("NOTES_ROOT", None)
        else:
            os.environ["NOTES_ROOT"] = saved

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
            "c": ("C 整体", lambda: asyncio.run(check_c())),
        }
        selected = list(parts) if args.part == "all" else [args.part]
        for key in selected:
            label, runner = parts[key]
            try:
                checks.extend(runner())
            except Exception as error:  # noqa: BLE001 - 导入或结构错误要整段报出来
                traceback.print_exc()
                checks.append(row(0, label, False, f"{type(error).__name__}: {error}"))

        passed = sum(1 for item in checks if item["ok"])
        print("\n逐项结果：")
        for item in checks:
            mark = "[OK]" if item["ok"] else "[X] "
            print(f"{mark} 第 {item['no']:>2} 组 {item['label']}：{item['detail']}")
        print(f"\n合计：{passed}/{len(checks)}")
        if passed == len(checks):
            print("全过。把这组结果和日志目录抄进记录，再回答观察题。")
        else:
            print("没过：先看每个 [X] 的「实际=... 期望=...」，再回题目说明对接口。")

        payload = {"counts": {"passed": passed, "total": len(checks)}, "checks": checks}
        (run_dir / "results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    run_logged(
        args.part,
        action,
        config={"model_calls": 0, "corpus": str(CORPUS), "cases": 22},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY65 / "outputs",
        origin_env="DAY65_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
