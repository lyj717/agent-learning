"""Day70 资源补课：把本周的 resources 机制再走一遍，只读不写。

针对变式与面试里暴露的三处薄弱：模板 `{+path}` 与 `{path}` 的区别、
未知 URI（-32602）和 handler 异常（-32603）的区别、资源是「应用读」不是「模型看」。
全程进程内 Client，0 次模型调用，不需要网络。

学完应能回答：note://index 是什么、谁读它；模板参数带不带 + 差在哪；
两种错误码分别在什么情况下出现；模型要「知道有哪些笔记」得靠谁。
"""

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp import Client, MCPError
from mcp.server import MCPServer

from projects.mcp_server.server import mcp

CORPUS = REPO_ROOT / "weeks/week09_advanced/demos/day65/corpus"


def say(text: str = "") -> None:
    """打印一行。"""
    print(text)


def build_demo_server() -> MCPServer:
    """造一个小 server：同一路径分别挂 {path} 与 {+path} 两个模板。"""
    demo = MCPServer("template-demo", log_level="WARNING")

    @demo.resource("plain://{path}", name="plain")
    def plain(path: str) -> str:
        """普通展开：path 不吞斜杠。"""
        return f"plain 拿到：{path}"

    @demo.resource("reserved://{+path}", name="reserved")
    def reserved(path: str) -> str:
        """保留展开：path 可以带斜杠。"""
        return f"reserved 拿到：{path}"

    return demo


async def main() -> None:
    """按「清单 → index → 模板 → 错误 → 模型可见性」五节演示。"""
    say("Day70 资源补课：模板展开、错误码、资源给谁看。")
    say("学了应能说清：{path} 与 {+path}、-32602 与 -32603、index 谁读。")

    async with Client(mcp) as client:
        say("\n一、资源清单与模板")
        resources = (await client.list_resources()).resources
        for item in resources:
            say(f"  资源 {item.uri}  mime={item.mime_type}")
        templates = (await client.list_resource_templates()).resource_templates
        for item in templates:
            say(f"  模板 {item.uri_template}  mime={item.mime_type}")
        say("  清单是固定的；模板是按 URI 匹配后现算的。")

        say("\n二、index 是什么")
        text = (await client.read_resource("note://index")).contents[0].text
        lines = text.splitlines()
        say(f"  类型：整段文本，{len(lines)} 行")
        for line in lines:
            say(f"    {line}")
        say("  谁读它：宿主/应用。它不是工具，模型不会自己来读。")

        say("\n三、模板展开：{path} 与 {+path}")
        async with Client(build_demo_server()) as demo_client:
            single = (await demo_client.read_resource("plain://a.md")).contents[0].text
            say(f"  plain://a.md          -> {single}")
            say("  （{path} 只匹配「一段」，单段路径能过）")
            try:
                await demo_client.read_resource("plain://notes/a.md")
            except MCPError as error:
                say(
                    f"  plain://notes/a.md    -> code={error.error.code}（带斜杠匹配不上）"
                )
            two = (
                (await demo_client.read_resource("reserved://notes/a.md"))
                .contents[0]
                .text
            )
            say(f"  reserved://notes/a.md -> {two}")
            say("  （{+path} 保留展开，可以吞斜杠，所以嵌套路径也能过）")

        say("\n四、两种错误的区别")
        try:
            await client.read_resource("other://x")
        except MCPError as error:
            say(
                f"  other://x           -> code={error.error.code}（没有资源或模板匹配，-32602）"
            )
        try:
            await client.read_resource("note://missing.md")
        except MCPError as error:
            say(
                f"  note://missing.md   -> code={error.error.code}（模板匹配了，handler 抛错，-32603）"
            )
        say("  所以：找不到路由是 -32602；找到路由但处理失败是 -32603。")

        say("\n五、模型能看到资源吗")
        tools = (await client.list_tools()).tools
        say(f"  tools/list 只有：{[tool.name for tool in tools]}")
        say(
            "  模型没有 resources/read 能力；host 想让模型知道清单，得自己读 index 再塞进消息。"
        )
        say("  Day69 的 --with-index 做的就是这件事。")


if __name__ == "__main__":
    asyncio.run(main())
