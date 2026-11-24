"""Day66 检查器：验证资源、提示词与三种错误形态。

题目与全部判分情形见 demos/day66/day66_题目说明.md。
检查器只读你的函数和 server，不修改任何文件；全部离线，0 次模型调用。
每次运行在 demos/day66/outputs/ 下新建目录，保存 console.log、run_info.json 与 results.json。
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

from mcp import Client, MCPError

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged

DAY66 = REPO_ROOT / "weeks/week09_advanced/demos/day66"
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"
EXPECTED_PATHS = [
    "archive/old.md",
    "binary.md",
    "empty.md",
    "notes/agent-notes.md",
    "notes/python-notes.md",
]


def row(number: int, label: str, ok: bool, detail: str) -> dict[str, object]:
    """组装一条检查组；detail 写实际值与期望值，失败时好定位。"""
    return {"no": number, "label": label, "ok": ok, "detail": detail}


def outcome_of(call) -> tuple[object | None, str | None]:
    """执行一次调用，返回 (结果, 错误描述)；ValueError 标成按预期拒绝。"""
    try:
        return call(), None
    except ValueError as error:
        return None, f"ValueError: {error}"
    except NotImplementedError as error:
        return None, f"还没写：{error}"
    except Exception as error:  # noqa: BLE001 - 其他异常要报出来，不能吞
        return None, f"{type(error).__name__}: {error}"


def result_text(result: object) -> str:
    """取出工具结果里的第一段文本。"""
    content = getattr(result, "content", None) or []
    if content and isinstance(getattr(content[0], "text", None), str):
        return content[0].text
    return ""


def check_a() -> list[dict[str, object]]:
    """Part A：resolve_note / list_note_paths / load_note 的 12 组。"""
    from projects.mcp_server.search import list_note_paths, load_note, resolve_note

    agent = CORPUS / "notes/agent-notes.md"
    cases: list[tuple[str, str, str]] = [
        ("解析普通相对路径", "notes/agent-notes.md", "file"),
        ("notes/../notes 仍合法", "notes/../notes/agent-notes.md", "file"),
        ("../outside 越界", "../outside/secret.md", "error"),
        ("Windows 绝对路径", "C:\\Windows", "error"),
        ("文件不存在", "missing.md", "error"),
        ("指向目录", "notes", "error"),
    ]
    checks: list[dict[str, object]] = []
    for number, (label, name, kind) in enumerate(cases, start=1):
        result, error = outcome_of(lambda name=name: resolve_note(CORPUS, name))
        if kind == "error":
            ok = error is not None and error.startswith("ValueError")
            checks.append(
                row(number, f"A {label}", ok, error or f"没拒绝，返回={result}")
            )
            continue
        expected = agent.resolve()
        ok = error is None and result == expected
        checks.append(
            row(number, f"A {label}", ok, error or f"实际={result} 期望={expected}")
        )

    result, error = outcome_of(lambda: list_note_paths(CORPUS))
    checks.append(
        row(
            7,
            "A 列出全部笔记",
            error is None and result == EXPECTED_PATHS,
            error or f"实际={result}",
        )
    )

    result, error = outcome_of(lambda: list_note_paths(CORPUS / "no-such-dir"))
    ok = error is not None and error.startswith("ValueError")
    checks.append(row(8, "A 根不存在", ok, error or f"没拒绝，返回={result}"))

    expected_text = agent.read_text(encoding="utf-8")
    result, error = outcome_of(lambda: load_note(CORPUS, "notes/agent-notes.md"))
    checks.append(
        row(
            9,
            "A 读笔记全文",
            error is None and result == expected_text,
            error or "内容不一致",
        )
    )

    result, error = outcome_of(lambda: load_note(CORPUS, "binary.md"))
    ok = error is not None and error.startswith("ValueError")
    checks.append(row(10, "A 坏编码拒绝", ok, error or f"没拒绝，返回={result!r}"))

    result, error = outcome_of(lambda: load_note(CORPUS, "missing.md"))
    ok = error is not None and error.startswith("ValueError")
    checks.append(row(11, "A 缺失文件拒绝", ok, error or f"没拒绝，返回={result!r}"))

    return checks


async def check_b() -> list[dict[str, object]]:
    """Part B：资源、提示词与工具的错误形态（11 组，编号 12 起）。"""
    from projects.mcp_server.server import mcp

    checks: list[dict[str, object]] = []
    saved = os.environ.get("NOTES_ROOT")
    os.environ["NOTES_ROOT"] = str(CORPUS)
    agent_text = (CORPUS / "notes/agent-notes.md").read_text(encoding="utf-8")

    async with Client(mcp) as client:
        listed = await client.list_resources()
        uris = [item.uri for item in listed.resources]
        checks.append(
            row(12, "B 具体资源 index", "note://index" in uris, f"实际={uris}")
        )

        templates = await client.list_resource_templates()
        found = [item.uri_template for item in templates.resource_templates]
        checks.append(
            row(13, "B 资源模板 {+path}", "note://{+path}" in found, f"实际={found}")
        )

        try:
            result = await client.read_resource("note://index")
            text = result.contents[0].text if result.contents else None
            checks.append(
                row(14, "B 读索引", text == "\n".join(EXPECTED_PATHS), f"实际={text!r}")
            )
        except Exception as error:  # noqa: BLE001
            checks.append(
                row(14, "B 读索引", False, f"{type(error).__name__}: {error}")
            )

        try:
            result = await client.read_resource("note://notes/agent-notes.md")
            text = result.contents[0].text if result.contents else None
            checks.append(row(15, "B 读正文", text == agent_text, "内容与源文件不一致"))
        except Exception as error:  # noqa: BLE001
            checks.append(
                row(15, "B 读正文", False, f"{type(error).__name__}: {error}")
            )

        readable = all(item["ok"] for item in checks if item["no"] in (12, 14, 15))

        try:
            await client.read_resource("note://nope.md")
            checks.append(row(16, "B 缺笔记是协议错误", False, "没有抛异常"))
        except MCPError as error:
            code = getattr(error.error, "code", None)
            ok = code == -32603 and readable
            checks.append(
                row(16, "B 缺笔记是协议错误", ok, f"code={code}，资源可读={readable}")
            )

        try:
            await client.read_resource("unknown://x")
            checks.append(row(17, "B 未知 URI 是 -32602", False, "没有抛异常"))
        except MCPError as error:
            code = getattr(error.error, "code", None)
            ok = code == -32602 and readable
            checks.append(
                row(17, "B 未知 URI 是 -32602", ok, f"code={code}，资源可读={readable}")
            )

        try:
            prompt = await client.get_prompt("review_note", {"name": "python-notes.md"})
            text = prompt.messages[0].content.text
            prompt_ok = "python-notes.md" in text and text.strip() != ""
            checks.append(row(18, "B 渲染复盘提示词", prompt_ok, f"实际={text!r}"))
        except Exception as error:  # noqa: BLE001
            prompt_ok = False
            checks.append(
                row(18, "B 渲染复盘提示词", False, f"{type(error).__name__}: {error}")
            )

        try:
            await client.get_prompt("no_such_prompt", {})
            checks.append(row(19, "B 未知提示词是错误", False, "没有抛异常"))
        except MCPError:
            checks.append(
                row(19, "B 未知提示词是错误", prompt_ok, f"提示词可渲染={prompt_ok}")
            )

        for number, label, name in (
            (20, "B 工具读缺失笔记", "missing.md"),
            (21, "B 工具读坏编码", "binary.md"),
        ):
            result = await client.call_tool("read_note", {"name": name})
            text = result_text(result)
            if "Unknown tool" in text:
                checks.append(row(number, label, False, "read_note 未注册"))
                continue
            checks.append(
                row(
                    number,
                    label,
                    getattr(result, "is_error", None) is True,
                    f"is_error={getattr(result, 'is_error', None)}，{text[:60]}",
                )
            )

    if saved is None:
        os.environ.pop("NOTES_ROOT", None)
    else:
        os.environ["NOTES_ROOT"] = saved
    return checks


def main() -> None:
    """按 --part 跑 A/B，打印逐项结果并保存留证。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "all"], default="all")
    args = parser.parse_args()

    def action(run_dir: Path) -> None:
        checks: list[dict[str, object]] = []
        parts = {
            "a": ("A 整体", check_a),
            "b": ("B 整体", lambda: asyncio.run(check_b())),
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
        config={"model_calls": 0, "corpus": str(CORPUS), "cases": 21},
        exercise_path=Path(__file__).resolve(),
        log_root=DAY66 / "outputs",
        origin_env="DAY66_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
