"""Day64 演示二/三的配套 server：一个最小、可被真实进程拉起的 MCP Server。

它只做两件事：echo 原样返回文本，add 把两个数相加。存在的意义是让客户端
真的拉起一个子进程、通过 stdin/stdout 说协议，而不是在同一个进程里假装。

注意：本文件运行时不能往 stdout 打印任何东西——stdout 就是协议通道，
多一行 print 就会让客户端解析失败（Day64 协议帧演示会看到原始消息长什么样）。
"""

import sys

from mcp.server import MCPServer

mcp = MCPServer(
    name="echo-server",
    version="0.1.0",
    instructions="演示用最小 server：echo 与 add。",
    log_level="WARNING",
)


@mcp.tool()
def echo(text: str) -> str:
    """原样返回输入的文本。"""
    return text


@mcp.tool()
def add(a: int, b: int) -> int:
    """把两个整数相加。"""
    return a + b


def main() -> None:
    """以 stdio 传输启动 server，阻塞等待客户端请求；返回 None。"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
