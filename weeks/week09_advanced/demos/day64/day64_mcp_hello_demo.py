"""Day64 演示一：MCP 的 server 与 client 隔着协议说话，工具是 server 声明的能力。

Week09 要交付一个别人能装、能用的 MCP Server（把 notes/ 做成带出处的检索）。
本演示只负责第一环：认清楚 host / client / server 三个角色，以及「写一个函数 +
一个装饰器」之后，客户端到底能看到什么。

学完应能回答：
- 模型看到的工具长什么样（名字、描述、参数 schema 从哪来）；
- 工具执行失败时，客户端拿到的是异常还是结果；
- 为什么说「工具描述写得含糊，模型就会用错」。

本演示用进程内连接，不起子进程、不联网、不调用模型；练习的工具要求在
projects/mcp_server/ 里，演示用的是另一套「列标题」场景，不构成照抄。
"""

import asyncio
import json

from mcp import Client
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import TextContent


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def build_demo_server() -> MCPServer:
    """建一个最小 server，注册一个演示工具；返回可连接的 MCPServer。

    工具 outline 的返回类型是 list[str]，SDK 会据此生成 outputSchema；
    返回 list 时客户端看到的 structured_content 是 {"result": [...]} 包装。
    """
    server = MCPServer(
        name="notes-demo",
        version="0.0.1",
        instructions="演示用：把 Markdown 的标题列出来。",
        log_level="WARNING",
    )

    @server.tool()
    def outline(markdown: str, max_level: int = 3) -> list[str]:
        """列出 Markdown 的标题行，最多到第 max_level 级。"""
        if not markdown.strip():
            raise ToolError("文本为空，没有可列出的标题。")
        if type(max_level) is not int or max_level < 1:
            raise ToolError("max_level 必须是正整数。")
        headings = []
        for line in markdown.splitlines():
            stripped = line.lstrip()
            level = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= level <= max_level and stripped[level : level + 1] == " ":
                headings.append(line)
        return headings

    return server


async def show_client_view(server: MCPServer) -> None:
    """用客户端连上 server，打印工具定义、正常调用与三种失败形态；返回 None。

    这个函数不写业务逻辑，只把「客户端看到什么」原样打印出来：
    参数 schema、content 与 structured_content、is_error。
    """
    async with Client(server) as client:
        say(f"协议版本：{client.protocol_version}")
        say(f"服务端身份：{client.server_info.name} {client.server_info.version}")
        say(
            "服务端声明的能力："
            f"tools={client.server_capabilities.tools is not None}，"
            f"resources={client.server_capabilities.resources is not None}，"
            f"prompts={client.server_capabilities.prompts is not None}"
        )
        say(
            "（MCPServer 会固定声明这三类能力；具体有没有内容，要看下面 list 的返回。）"
        )

        listed = await client.list_tools()
        say("\n五、模型看到的工具定义（tools/list 的返回）")
        for tool in listed.tools:
            say(f"名字：{tool.name}")
            say(f"描述：{tool.description}")
            say("参数 schema：")
            say(json.dumps(tool.input_schema, ensure_ascii=False, indent=2))

        say("\n六、正常调用一次")
        markdown = "# 周记\n\n正文一行\n## 本周问题\n### 细节\n"
        result = await client.call_tool("outline", {"markdown": markdown})
        texts = [
            block.text for block in result.content if isinstance(block, TextContent)
        ]
        say(f"content 里的文本块（给模型看）：{texts}")
        say(f"structured_content（给代码用）：{result.structured_content}")
        say(f"is_error：{result.is_error}")

        say("\n七、三种失败形态：它们都不是异常，而是结果")
        empty = await client.call_tool("outline", {"markdown": "   "})
        say(f"[业务拒绝] is_error={empty.is_error}；内容={empty.content[0].text}")
        bad_level = await client.call_tool(
            "outline", {"markdown": "# 标题", "max_level": 0}
        )
        say(
            f"[参数越界] is_error={bad_level.is_error}；内容={bad_level.content[0].text}"
        )
        wrong_type = await client.call_tool("outline", {"markdown": 123})
        say(
            f"[类型不对] is_error={wrong_type.is_error}；内容={wrong_type.content[0].text}"
        )
        missing = await client.call_tool("no_such_tool", {})
        say(f"[工具不存在] is_error={missing.is_error}；内容={missing.content[0].text}")


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」的顺序讲一遍，再跑一次连接。"""
    say("Week09 要交付一个别人能装、能用的 MCP Server：把 notes/ 做成带出处的检索。")
    say("本演示只做第一环：认清三个角色，看清「注册一个工具」之后客户端能看到什么。")
    say("学完应能说出工具定义从哪来、失败为什么是结果不是异常。")
    say("赶时间可以只看第五～七节：工具定义、一次调用、三种失败；一～四节是背景。")

    say("\n一、这是什么")
    say("MCP（Model Context Protocol）是一套让模型应用连外部工具和数据源的协议。")
    say("它规定三类角色：")
    say("  host   —— 用户直接对话的那个应用（Claude Desktop、IDE、你自己写的 agent）；")
    say("  client —— host 内部负责说协议的那一半，一个 server 一个 client；")
    say("  server —— 你写的这个进程：声明自己会什么，等客户端来问、来调。")
    say(
        "消息层是 JSON-RPC 2.0：请求带 id 和 method，响应带回同一个 id 和 result/error。"
    )
    say("server 从不直接找模型；它只回答客户端的请求。")

    say("\n二、为什么需要它")
    say("没有协议时，M 个模型应用接 N 个工具要写 M×N 套对接代码。")
    say("有了协议，工具方按协议实现一次，所有支持协议的应用都能用（M+N）。")
    say("代价是：协议只解决「怎么接」，不解决「接了之后效果好不好」。")
    say("工具描述写得含糊、参数 schema 不严，模型照样会调错——这是 server 作者的责任。")

    say("\n三、具体场景：把学习笔记做成可检索的工具")
    say("目标用户：在本仓库里写笔记、又用 Claude Desktop 或 IDE 的人。")
    say("不装它：每次要翻笔记，只能自己 grep，再复制粘贴给模型。")
    say("装上之后：模型可以直接调用检索工具，拿到「文件名 + 行号 + 原文」。")
    say("第一版最小接口只要一个工具：给关键词，回命中行和出处。")

    say("\n四、代码：一个函数 + 一个装饰器就是全部注册")
    say("MCPServer 从模型名、docstring、类型注解里自动生成工具定义：")
    say("  函数名      -> 工具名（可用 name= 覆盖）")
    say("  docstring   -> 工具描述（这是模型判断「什么时候该用它」的唯一依据）")
    say("  类型注解    -> inputSchema（JSON Schema，客户端据此画表单、模型据此给参数）")
    say("  返回类型    -> outputSchema / structured_content")
    say("下面读代码，再跑客户端看结果。")

    server = build_demo_server()
    asyncio.run(show_client_view(server))

    say("\n八、注意什么")
    say(
        "1. 描述和 schema 不是文档，是接口。模型只看得到它们；写清「什么时候用、参数什么含义、"
    )
    say("   返回什么」，比多写一句业务逻辑更能减少调用错误。")
    say(
        "2. 工具失败不要抛给客户端当崩溃：raise ToolError 会变成 is_error=True 的结果，"
    )
    say(
        "   message 会回到模型手里，它可以改参数重试。协议层错误（JSON-RPC error）才走异常。"
    )
    say(
        "3. 返回 list 时 structured_content 是 {'result': [...]} 包装；dict 直接返回时反而"
    )
    say("   可能没有 structured_content。写测试时别想当然，跑一次看实际形状。")
    say(
        "4. server 的 stdout 是协议通道（下一个演示会看到）。调试信息一律走 stderr 或日志。"
    )
    say("5. 进程内连接（本演示）为了测试方便，SDK 用 DirectDispatcher 直接调函数，")
    say("   根本不过 JSON-RPC；想验证真正的协议行为，要跑 stdio 与协议帧演示。")


if __name__ == "__main__":
    main()
