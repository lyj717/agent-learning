"""Day66 演示一：资源（resources）——应用决定加载什么数据。

Day65 的检索是工具：模型决定调不调。资源相反：由宿主应用决定「把哪份数据放进上下文」，
模型不主动调用。本演示只看两件事：清单（index）与按名字读（模板），
以及读一个不存在的资源时客户端拿到什么。

学完应能回答：具体资源与资源模板在列表里为什么分开、URI 里的 {+path} 为什么带加号、
读不到的资源为什么不是 is_error 而是异常。演示用内存里的两篇笔记，不读文件。
"""

import asyncio

from mcp import Client
from mcp.server import MCPServer

NOTES = {
    "python-notes.md": "# Python 笔记\n元组不可变。",
    "notes/agent-notes.md": "# Agent 笔记\n工具描述决定调用正确率。",
}

server = MCPServer("resources-demo", log_level="WARNING")


@server.resource("note://index")
def note_index() -> str:
    """列出所有笔记的相对路径。"""
    return "\n".join(sorted(NOTES))


@server.resource("note://{+path}")
def note_body(path: str) -> str:
    """按相对路径读一篇笔记的全文。"""
    if path not in NOTES:
        raise ValueError(f"没有这篇笔记：{path}")
    return NOTES[path]


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


async def show() -> None:
    """连上 server，分别看清单、模板、读取与读不到；返回 None。"""
    async with Client(server) as client:
        listed = await client.list_resources()
        say(f"具体资源（list_resources）：{[item.uri for item in listed.resources]}")

        templates = await client.list_resource_templates()
        say(
            "资源模板（list_resource_templates）："
            f"{[item.uri_template for item in templates.resource_templates]}"
        )
        say("（模板要填了参数才能读，所以和具体资源分两张表。）")

        read_index = await client.read_resource("note://index")
        say(f"\n读索引 note://index：{read_index.contents[0].text!r}")

        read_note = await client.read_resource("note://notes/agent-notes.md")
        say(f"读正文 note://notes/agent-notes.md：{read_note.contents[0].text!r}")

        for uri in ("note://nope.md", "unknown://x"):
            try:
                await client.read_resource(uri)
                say(f"读 {uri}：竟然成功了？")
            except Exception as error:  # noqa: BLE001 - 演示要展示异常类型
                data = getattr(error, "error", None)
                say(
                    f"读 {uri}：{type(error).__name__}，"
                    f"code={getattr(data, 'code', None)}，"
                    f"message={getattr(data, 'message', None)}"
                )


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」讲一遍资源，再跑一次。"""
    say("Day65 的工具由模型决定调用；资源由宿主应用决定加载。今天把笔记做成资源。")
    say("学完应能说清：具体资源 vs 资源模板、{+path} 的作用、读不到时的错误形态。")

    say("\n一、这是什么")
    say(
        "资源是 server 暴露的「可读取数据」，用 URI 标识，例如 note://python-notes.md。"
    )
    say("宿主的应用可以列出资源、挑一份读进上下文；模型不需要发起工具调用。")

    say("\n二、为什么需要它")
    say("有些数据是「背景资料」，比如某篇笔记、一份配置、一张表；")
    say("让模型自己调工具去取，既多一轮往返，也不保证它取对。宿主直接加载更稳。")

    say("\n三、具体场景")
    say("用户打开某个笔记想讨论，宿主把 note://python-notes.md 读进上下文；")
    say("再让模型基于这份资源回答，而不是先 search 再读。")

    say("\n四、代码：清单 + 模板")
    say("  @server.resource('note://index')     固定 URI，列清单")
    say(
        "  @server.resource('note://{+path}')   带参数，{+path} 能匹配 notes/a.md 这种带斜杠的路径"
    )
    say("  {path} 不匹配斜杠，读 notes/a.md 会变成 Unknown resource。")
    asyncio.run(show())

    say("\n五、注意什么")
    say("1. 具体资源（固定 URI）和资源模板（带参数）是两张列表；模板不填参数不能读。")
    say("2. 参数用 {+path}（保留斜杠），不要用 {path}；后者只匹配一段。")
    say("3. 读不到的资源走 JSON-RPC 错误：未知 URI 是 -32602，处理器抛异常是 -32603，")
    say("   客户端拿到的是异常，不是 is_error 结果。下一份演示专门对比。")
    say("4. 资源内容适合宿主直接放进上下文，不适合「让模型做动作」；要动作就用工具。")


if __name__ == "__main__":
    main()
