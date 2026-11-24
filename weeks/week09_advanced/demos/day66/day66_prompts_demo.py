"""Day66 演示二：提示词（prompts）——用户挑一个模板，server 渲染成消息。

工具由模型决定，资源由应用决定，提示词由**用户**决定：用户在宿主里点一个名字
（类似斜杠命令），server 把它渲染成一段消息交给模型。本演示看清单、看参数、
看渲染结果，以及参数缺失/名字不存在时发生什么。

学完应能回答：提示词和资源差在哪、提示词的参数为什么都是字符串、
渲染出来的消息交给谁。演示用内存模板，不读文件、不调用模型。
"""

import asyncio

from mcp import Client
from mcp.server import MCPServer

server = MCPServer("prompts-demo", log_level="WARNING")


@server.prompt()
def review_note(name: str) -> str:
    """生成「复盘一篇笔记」的提示词。"""
    return f"请阅读 note://{name}，用三个要点复盘，并注明依据的行号。"


@server.prompt()
def compare_notes(left: str, right: str) -> str:
    """生成「对比两篇笔记」的提示词。"""
    return f"对比 note://{left} 与 note://{right}，列出相同点与不同点。"


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


async def show() -> None:
    """连上 server，看提示词清单、渲染结果与两种失败；返回 None。"""
    async with Client(server) as client:
        listed = await client.list_prompts()
        for item in listed.prompts:
            args = [(arg.name, arg.required) for arg in (item.arguments or [])]
            say(f"提示词 {item.name}：参数={args}，描述={item.description}")

        say("")
        rendered = await client.get_prompt("review_note", {"name": "python-notes.md"})
        message = rendered.messages[0]
        say(f"渲染 review_note：role={message.role}，text={message.content.text!r}")

        rendered = await client.get_prompt(
            "compare_notes", {"left": "a.md", "right": "b.md"}
        )
        say(f"渲染 compare_notes：{rendered.messages[0].content.text!r}")

        for name, arguments in (
            ("review_note", {}),
            ("no_such_prompt", {}),
        ):
            try:
                await client.get_prompt(name, arguments)
                say(f"取 {name}：竟然成功了？")
            except Exception as error:  # noqa: BLE001 - 演示要展示异常类型
                data = getattr(error, "error", None)
                say(
                    f"取 {name}：{type(error).__name__}，"
                    f"code={getattr(data, 'code', None)}，"
                    f"message={getattr(data, 'message', None)}"
                )


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」讲一遍提示词，再跑一次。"""
    say("三种原语各由谁决定：工具是模型，资源是应用，提示词是用户。")
    say("学完应能说清：提示词参数长什么样、渲染出什么、失败时客户端拿到什么。")

    say("\n一、这是什么")
    say("提示词是 server 提供的「消息模板」：有名字、有参数、渲染成一条或多条消息。")
    say("它不执行动作，也不返回数据，只生成给模型看的文字。")

    say("\n二、为什么需要它")
    say("同一类任务（复盘一篇笔记、对比两篇）每次都要用户重复写一大段要求；")
    say("把模板放在 server 里，用户点一下名字、填两个参数就行，措辞也可统一维护。")

    say("\n三、具体场景")
    say("用户在宿主里选「复盘这篇笔记」，填上笔记名；宿主调用 get_prompt，")
    say("把渲染出的 user 消息直接发给模型，模型再决定要不要调工具/读资源。")

    say("\n四、代码：一个函数就是一个模板")
    say("  @server.prompt()  def review_note(name: str) -> str")
    say("  函数名 -> 提示词名；docstring -> 描述；类型注解 -> 参数表。")
    say(
        "  参数在协议里都是字符串（客户端传 dict[str, str]），返回字符串就是 user 消息。"
    )
    asyncio.run(show())

    say("\n五、注意什么")
    say("1. 提示词只生成消息，不执行查询；需要数据就交给资源或工具。")
    say("2. 参数缺失、名字不存在都会变成 JSON-RPC 错误（-32603），客户端抛异常；")
    say("   这不是 is_error 结果，模型看不到。")
    say("3. 提示词里要写清「依据哪份资源、要引用什么」，否则模型还是自由发挥。")
    say("4. 不要用提示词存放会变的业务数据；它只是模板。")


if __name__ == "__main__":
    main()
