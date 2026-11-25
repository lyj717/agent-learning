"""Day68 测试：notes MCP Server 的协议契约。

10 个契约见 weeks/week09_advanced/demos/day68/day68_题目说明.md。
每个函数只写断言，不打印；夹具数据用 day65/corpus，不依赖仓库 notes/ 的当前内容。
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import Client, MCPError

from projects.mcp_server.server import mcp

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"


def test_tools_list() -> None:
    """契约 1：tools/list 同时有 search_text、search_notes、read_note，且描述都非空。"""

    async def check() -> None:
        async with Client(mcp) as client:
            tools = (await client.list_tools()).tools
            assert {"search_text", "search_notes", "read_note"} <= {
                t.name for t in tools
            }
            assert all(t.description for t in tools)

    asyncio.run(check())


def test_search_text_hit() -> None:
    """契约 2：search_text 传两行文本（第一行普通、第二行含关键词），structured_content 是 {"result": [{"line": 2, "text": "b 关键词"}]}。"""

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_text", {"text": "a\nb 关键词", "keyword": "关键词"}
            )
            assert result.structured_content == {
                "result": [{"line": 2, "text": "b 关键词"}]
            }

    asyncio.run(check())


def test_search_text_empty_keyword() -> None:
    """契约 3：search_text 空关键词时 is_error 为 True。"""

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_text", {"text": "a\\nb 关键词", "keyword": ""}
            )
            assert result.is_error is True

    asyncio.run(check())


def test_search_notes_returns_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 4：NOTES_ROOT 指到 CORPUS，search_notes 返回的每项含 source、line、text。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_notes", {"keyword": "关键词", "limit": 2}
            )
            items = result.structured_content["result"]
            assert items and all(
                {"source", "line", "text"} <= set(item) for item in items
            )

    asyncio.run(check())


def test_search_notes_rejects_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 5：NOTES_ROOT 指到 CORPUS，folder="../outside" 时 is_error 为 True。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_notes", {"keyword": "关键词", "folder": "../outside"}
            )
            assert result.is_error is True

    asyncio.run(check())


def test_read_note_missing_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 6：NOTES_ROOT 指到 CORPUS，read_note("missing.md") 的 is_error 为 True、消息非空。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool("read_notes", {"name": "missing.md"})
            assert result.is_error is True and result.content[0].text

    asyncio.run(check())


def test_resources_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 7：list_resources 含 note://index；读它得到 5 条相对路径。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            resources = await client.list_resources()
            assert "note://index" in {item.uri for item in resources.resources}
            text = (await client.read_resource("note://index")).contents[0].text
            assert text.splitlines() == [
                "archive/old.md",
                "binary.md",
                "empty.md",
                "notes/agent-notes.md",
                "notes/python-notes.md",
            ]

    asyncio.run(check())


def test_resource_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 8：读 note://nope.md 抛 MCPError（不是 is_error 结果）。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            with pytest.raises(MCPError) as exc:
                await client.read_resource("note://nope.md")
            assert exc.value.error.code == -32603

    asyncio.run(check())


def test_prompt_review_note(monkeypatch: pytest.MonkeyPatch) -> None:
    """契约 9：get_prompt("review_note", {"name": "python-notes.md"}) 的消息含该名字。"""
    monkeypatch.setenv("NOTES_ROOT", str(CORPUS))

    async def check() -> None:
        async with Client(mcp) as client:
            prompt = await client.get_prompt("review_note", {"name": "python-notes.md"})
            assert "python-notes.md" in prompt.messages[0].content.text

    asyncio.run(check())


def test_stdio_smoke() -> None:
    """契约 10：subprocess 跑 python -m projects.mcp_server.server，空 stdin 下 returncode 为 0。"""
    proc = subprocess.run(
        [sys.executable, "-m", "projects.mcp_server.server"],
        cwd=REPO_ROOT,
        input="",
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=20,
        check=False,
        env={**os.environ, "NOTES_ROOT": str(CORPUS), "PYTHONIOENCODING": "utf-8"},
    )
    assert proc.returncode == 0
