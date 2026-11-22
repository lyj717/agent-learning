"""notes 检索 MCP Server 的入口：创建 server、注册工具、以 stdio 启动。

当前只暴露 search_text：按关键词找命中行并返回行号。文件检索、资源与提示词
在后续几天加上。

运行（仓库根目录）：
    .venv\\Scripts\\python.exe -B -X utf8 -m projects.mcp_server.server

它启动后会阻塞等待客户端说话，这是正常的：stdio server 不会自己打印欢迎语。
"""

from mcp.server import MCPServer

mcp = MCPServer(
    name="notes-search",
    version="0.1.0",
    instructions=(
        "检索本地 Markdown 学习笔记。用 search_text 按关键词找命中行，"
        "返回文件名（后续版本）与行号出处；回答时请引用出处。"
    ),
    log_level="WARNING",
)

from mcp.server.mcpserver.exceptions import ToolError

from projects.mcp_server.search import find_matches


@mcp.tool()
def search_text(text: str, keyword: str, limit: int = 5) -> list[dict[str, int | str]]:
    """按行检索关键词，返回命中的行号与原文。"""
    try:
        return find_matches(text, keyword, limit)
    except ValueError as error:
        raise ToolError(str(error)) from error


def main() -> None:
    """以 stdio 传输启动 server，阻塞等待客户端请求；返回 None。"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
