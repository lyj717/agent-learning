"""Day68 演示：给 MCP server 写「确定性测试」和一条真实 stdio 冒烟。

前几天的检查器是给练习判分用的；今天要交的是项目自己的 pytest 测试：
别人改了代码，跑一遍就知道有没有把工具、资源、提示词弄坏。本演示不写 pytest 文件，
只把三件事跑给你看：进程内 Client 怎么断言、NOTES_ROOT 怎么临时换、stdio 冒烟怎么防挂死。

学完应能回答：为什么测试不用真实模型、为什么进程内连接够快、stdio 冒烟为什么要超时。
依赖仓库里的 projects/mcp_server 与 day65 的固定语料；0 次模型调用。
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"

sys.path.insert(0, str(REPO_ROOT))

from mcp import Client

from projects.mcp_server.server import mcp


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


async def inprocess_checks() -> None:
    """用进程内 Client 逐项断言工具、资源、提示词；返回 None。"""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert {"search_text", "search_notes", "read_note"} <= names
        assert all(tool.description for tool in tools.tools)
        say("PASS 工具清单与描述")

        result = await client.call_tool(
            "search_text", {"text": "a\nb 关键词", "keyword": "关键词"}
        )
        assert result.is_error is False
        assert result.structured_content == {
            "result": [{"line": 2, "text": "b 关键词"}]
        }
        say("PASS search_text 命中")

        bad = await client.call_tool("search_text", {"text": "a", "keyword": " "})
        assert bad.is_error is True
        say("PASS search_text 空关键词是 is_error")

        resources = await client.list_resources()
        assert "note://index" in {item.uri for item in resources.resources}
        index = await client.read_resource("note://index")
        assert "notes/agent-notes.md" in index.contents[0].text
        say("PASS 资源 index")

        prompt = await client.get_prompt("review_note", {"name": "python-notes.md"})
        assert "python-notes.md" in prompt.messages[0].content.text
        say("PASS 提示词渲染")


def with_notes_root() -> None:
    """临时把 NOTES_ROOT 指向固定语料，跑完恢复；返回 None。"""
    saved = os.environ.get("NOTES_ROOT")
    os.environ["NOTES_ROOT"] = str(CORPUS)
    try:
        say(f"NOTES_ROOT 临时设为：{CORPUS}")
    finally:
        if saved is None:
            os.environ.pop("NOTES_ROOT", None)
        else:
            os.environ["NOTES_ROOT"] = saved
    say("已恢复原来的 NOTES_ROOT")


def stdio_smoke() -> None:
    """起一个真实子进程，空 stdin 下应在超时内退出；返回 None。"""
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
    assert proc.returncode == 0, proc.stderr
    say(f"PASS stdio 冒烟：returncode={proc.returncode}")


def main() -> None:
    """按「为什么、怎么写、注意」讲一遍，再跑三类检查。"""
    say("Day68 给项目补 pytest：进程内 client 的确定性检查 + 一条 stdio 冒烟。")
    say("学完应能说清：为什么不用真实模型、进程内为什么快、冒烟为什么要超时。")

    say("\n一、测试测什么")
    say(
        "测「协议契约」：工具在不在、参数对不对、返回结构变没变、资源/提示词还能不能读。"
    )
    say("不测「模型答得好不好」——那要花 token 且有波动，属于评测（Week08）的事。")

    say("\n二、进程内 Client 为什么快")
    say("Client(mcp) 直接把 server 对象接上，不起进程、不走网络；一次断言几毫秒。")
    say("代价：它不经过 JSON-RPC，协议层问题要另外用 stdio 冒烟兜。")

    say("\n三、跑三类检查")
    saved = os.environ.get("NOTES_ROOT")
    os.environ["NOTES_ROOT"] = str(CORPUS)
    try:
        asyncio.run(inprocess_checks())
    finally:
        if saved is None:
            os.environ.pop("NOTES_ROOT", None)
        else:
            os.environ["NOTES_ROOT"] = saved
    with_notes_root()
    stdio_smoke()

    say("\n四、写进 pytest 文件时的形状")
    say("  def test_tools_list():          # 普通函数，名字 test_ 开头")
    say("      asyncio.run(_check())        # 或装 pytest-asyncio")
    say("  def test_stdio_smoke():          # subprocess + timeout=20")
    say("  monkeypatch.setenv('NOTES_ROOT', str(CORPUS))  # 用 fixture 改环境变量")

    say("\n五、注意什么")
    say("1. 每个断言独立：一个测试只验一件事，挂了能立刻知道是哪条契约破了。")
    say("2. 环境变量用 monkeypatch 或 try/finally 恢复，别污染其他测试。")
    say("3. stdio 冒烟必须带超时：server 挂住时，测试不能跟着挂住。")
    say("4. 测试用固定语料（day65/corpus），不依赖仓库 notes/ 的当前内容。")


if __name__ == "__main__":
    main()
