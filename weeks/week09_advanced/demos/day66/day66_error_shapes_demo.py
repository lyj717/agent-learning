"""Day66 演示三：三种原语的错误形态——同一个「文件不存在」，三种结果。

同样一件事（读一篇不存在的笔记），走工具、走资源、走提示词，客户端拿到的东西
完全不一样。这份演示把三条路并排跑一遍，看清「谁的错误、谁能看到、原因在哪」。

学完应能回答：为什么工具失败是 is_error 结果、资源失败却是异常、-32602 与 -32603
分别代表什么、想让模型看到「文件不存在」应该选哪种原语。演示用内存数据。
"""

import asyncio

from mcp import Client
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

NOTES = {"a.md": "# A\n第一行。"}

server = MCPServer("error-shapes-demo", log_level="WARNING")


@server.tool()
def read(name: str) -> str:
    """按名字读一篇笔记。"""
    if name not in NOTES:
        raise ToolError(f"笔记不存在：{name}")
    return NOTES[name]


@server.resource("note://{+path}")
def note(path: str) -> str:
    """按路径读一篇笔记。"""
    if path not in NOTES:
        raise ValueError(f"笔记不存在：{path}")
    return NOTES[path]


@server.prompt()
def review(name: str) -> str:
    """复盘一篇笔记。"""
    return f"请复盘 note://{name}。"


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def describe(error: Exception) -> str:
    """把异常的 code 与 message 摘出来，供打印。"""
    data = getattr(error, "error", None)
    return (
        f"{type(error).__name__}，code={getattr(data, 'code', None)}，"
        f"message={getattr(data, 'message', None)}"
    )


async def show() -> None:
    """并排跑三条失败路径，打印客户端看到的东西；返回 None。"""
    async with Client(server) as client:
        say("① 工具：read('nope.md')")
        result = await client.call_tool("read", {"name": "nope.md"})
        say(f"   返回 is_error={result.is_error}")
        say(f"   content={result.content[0].text!r}")
        say("   → 这是结果，模型能读到原因，可以换参数重试。")

        say("\n② 资源：note://nope.md")
        try:
            await client.read_resource("note://nope.md")
            say("   竟然成功了？")
        except Exception as error:  # noqa: BLE001 - 演示要展示异常类型
            say(f"   {describe(error)}")
        say("   → 这是协议错误，不是结果；真实原因只进 server 日志。")

        say("\n③ 资源：不存在的 URI 方案 doc://a.md")
        try:
            await client.read_resource("doc://a.md")
            say("   竟然成功了？")
        except Exception as error:  # noqa: BLE001
            say(f"   {describe(error)}")
        say("   → -32602 是「没有这个资源」，-32603 是「处理器自己出错」。")

        say("\n④ 提示词：缺参数取 review")
        try:
            await client.get_prompt("review", {})
            say("   竟然成功了？")
        except Exception as error:  # noqa: BLE001
            say(f"   {describe(error)}")
        say("   → 提示词的参数错误同样走协议错误，模型看不到。")


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」讲一遍错误形态，再跑一次。"""
    say("三种原语决定三种失败形态；选错原语，模型就看不到失败原因。")
    say("学完应能回答：is_error 结果与协议错误各给谁看、-32602/-32603 的区别。")

    say("\n一、这是什么")
    say("工具失败 = 一次调用的结果（is_error=True，content 里带原因）；")
    say(
        "资源/提示词失败 = 一次 JSON-RPC 错误（客户端抛 MCPError，带 code 与 message）。"
    )

    say("\n二、为什么这样设计")
    say("模型只读得到「工具结果」这一种东西；协议错误是给客户端/宿主处理的。")
    say("所以要让模型知道「文件不存在、换个名字」，就得走工具，而不是资源。")

    say("\n三、具体场景")
    say("模型想读某篇笔记：调 read 工具，失败能看到原因；")
    say("宿主想预加载一篇笔记：读资源，失败由宿主提示用户或换一份。")

    say("\n四、代码：同一个动作，两种暴露方式")
    say("  @server.tool()       读失败 -> raise ToolError(...)  -> is_error 结果")
    say("  @server.resource()   读失败 -> raise ValueError(...) -> -32603 协议错误")
    asyncio.run(show())

    say("\n五、注意什么")
    say("1. is_error 结果只有工具层有；资源和提示词的失败是异常，模型看不到。")
    say("2. 未知资源 URI -> -32602；处理器内部异常 -> -32603，消息会被泛化。")
    say("3. 想在协议错误里保留原因，就把它写进返回内容（比如 index 列出可选名字），")
    say("   或者另给一个工具让模型查。")
    say("4. 服务器日志里能看到真实原因；排查时先看日志，不要只看客户端那句泛化消息。")


if __name__ == "__main__":
    main()
