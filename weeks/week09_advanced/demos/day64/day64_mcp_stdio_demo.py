"""Day64 演示二：stdio 传输——host 拉起 server 子进程，stdin/stdout 就是协议通道。

本演示让客户端真的启动一个子进程（day64_echo_server.py），再通过管道说 JSON-RPC。
看清三件事：谁启动谁、消息走哪两根管道、为什么 server 不能往 stdout 打印。

运行前不需要先开终端跑 server：客户端会自己拉起、用完关闭。全程离线、0 次模型调用。
"""

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER_PATH = Path(__file__).with_name("day64_echo_server.py")


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


async def talk_to_child_process() -> None:
    """拉起子进程 server，列工具并调用两次；返回 None。

    客户端参数说明：
        command 必填：要执行的程序，这里是当前虚拟环境的 python；
        args：传给程序的参数，第一项是脚本绝对路径（host 从别的工作目录启动，
              相对路径会找不到文件）；
        env：只额外补 PYTHONIOENCODING；其余环境变量按 SDK 的白名单继承，
             不会把整个终端环境原样带过去。
    """
    params = StdioServerParameters(
        command=sys.executable,
        args=["-X", "utf8", str(SERVER_PATH)],
        env={"PYTHONIOENCODING": "utf-8"},
    )
    say(f"实际启动的命令：{params.command} {' '.join(params.args)}")

    async with Client(params) as client:
        say(f"协议版本：{client.protocol_version}")
        say(f"服务端身份：{client.server_info.name} {client.server_info.version}")

        tools = await client.list_tools()
        say(f"工具清单：{[tool.name for tool in tools.tools]}")

        echoed = await client.call_tool("echo", {"text": "子进程里说的第一句话"})
        say(f"echo -> {echoed.content[0].text}")

        summed = await client.call_tool("add", {"a": 20, "b": 22})
        say(f"add -> structured_content={summed.structured_content}")

    say("离开 async with 后客户端关闭管道，子进程随之退出。")


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」讲 stdio，再真跑一次。"""
    say("Week09 要交付别人能用的 MCP Server。上次是同一进程内连接，这次走真实进程。")
    say("学完应能说清：谁启动谁、消息走哪两根管道、stdio 下为什么不能 print。")

    say("\n一、这是什么")
    say("stdio 是 MCP 的两种标准传输之一：host 把 server 当普通子进程启动，")
    say("往它的 stdin 写请求、从它的 stdout 读响应。每条消息是一行 JSON-RPC，")
    say("行内不能有换行，消息之间用换行分隔。")
    say(
        "另一种是 Streamable HTTP：server 监听端口，客户端用 HTTP 发请求，适合远程部署。"
    )

    say("\n二、为什么本地工具默认用它")
    say(
        "不用挑端口、不用管防火墙、不用证书；server 和应用同生共死，用户关掉应用就结束。"
    )
    say("代价是 server 必须由应用拉起，用户得在配置里写清「用什么命令启动它」。")
    say(
        "Claude Desktop 的 claude_desktop_config.json 里那个 command + args，就是这条命令。"
    )

    say("\n三、具体场景")
    say("用户在 Claude Desktop 里问「我的笔记里怎么处理流式块」。")
    say("Claude Desktop 按配置启动我们的 notes server，连上后列出工具，")
    say("模型决定调用检索工具，参数通过 stdout/stdin 往返，结果显示在对话里。")
    say("整个过程用户看不到终端，所以 server 绝不能往 stdout 打日志。")

    say("\n四、代码：客户端拉起子进程")
    asyncio.run(talk_to_child_process())

    say("\n五、注意什么")
    say("1. 脚本路径要绝对：host 从它自己的工作目录启动，相对路径会找不到文件。")
    say(
        "2. stdout 是协议。调试用 print 只会污染协议；要输出就写 stderr（logging 默认就是）。"
    )
    say("3. 环境变量不会整份继承：SDK 只带 PATH、USERPROFILE 这类白名单，")
    say("   需要 API key 之类必须显式写进 env，或者由宿主配置传。")
    say("4. server 退出要干净：stdin 关闭后应正常结束，挂住的话宿主会强杀进程树。")


if __name__ == "__main__":
    main()
