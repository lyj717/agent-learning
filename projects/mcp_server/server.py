"""notes 检索 MCP Server 的入口：创建 server、注册工具/资源/提示词、以 stdio 启动。

当前暴露：搜索工具 search_text 与 search_notes、笔记资源 note://index 与
note://{+path}、复盘提示词 review_note、按名字读笔记的工具 read_note。

运行（仓库根目录）：
    .venv\\Scripts\\python.exe -B -X utf8 -m projects.mcp_server.server

它启动后会阻塞等待客户端说话，这是正常的：stdio server 不会自己打印欢迎语。
"""

import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from projects.mcp_server.search import (
    DEFAULT_NOTES_ROOT,
    find_matches,
    list_note_paths,
    load_note,
    search_files,
)

mcp = MCPServer(
    name="notes-search",
    version="0.1.0",
    instructions=(
        "检索本地 Markdown 学习笔记。用 search_text 按关键词找命中行，"
        "返回文件名（后续版本）与行号出处；回答时请引用出处。"
    ),
    log_level="WARNING",
)


def notes_root() -> Path:
    """当前语料根：读环境变量 NOTES_ROOT，没有就用仓库里的 notes/。"""
    return Path(os.environ.get("NOTES_ROOT", str(DEFAULT_NOTES_ROOT)))


@mcp.tool()
def search_text(text: str, keyword: str, limit: int = 5) -> list[dict[str, int | str]]:
    """按行检索关键词，返回命中的行号与原文。"""
    try:
        return find_matches(text, keyword, limit)
    except ValueError as error:
        raise ToolError(str(error)) from error


@mcp.tool()
def search_notes(
    keyword: str, limit: int = 5, folder: str = ""
) -> list[dict[str, int | str]]:
    """在本地 Markdown 笔记本里按关键词检索，返回来源文件、行号与原文。"""
    try:
        return search_files(notes_root(), keyword, limit, folder)
    except ValueError as error:
        raise ToolError(str(error)) from error


@mcp.resource("note://index")
def note_index() -> str:
    """列出所有相对路径，用一个换行符连接。"""
    return "\n".join(list_note_paths(notes_root()))


@mcp.resource("note://{+path}")
def note_body(path: str) -> str:
    """按相对路径读一篇笔记的全文。"""
    return load_note(root=notes_root(), name=path)


@mcp.prompt()
def review_note(name: str) -> str:
    """返回一段请模型复盘 note://<name> 的文字。"""
    return f"请阅读 note://{name}，用三个要点复盘，并注明依据的行号。"


@mcp.tool(name="read_note")
def read_note_tool(name: str) -> str:
    """按名字读一篇笔记的全文，名字写错返回错误。"""
    try:
        return load_note(root=notes_root(), name=name)
    except ValueError as error:
        raise ToolError(str(error)) from error


def main() -> None:
    """以 stdio 传输启动 server，阻塞等待客户端请求；返回 None。"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
