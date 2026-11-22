"""Day64 演示三：手写 JSON-RPC 帧——看清 SDK 到底替你发了什么、收了什么。

前两个演示都经过 SDK：进程内连接甚至不走协议，stdio 连接也被封装好了。
本演示不用 SDK 客户端，直接往子进程的 stdin 写四段 JSON，从 stdout 读回响应，
把「initialize 握手 / tools/list / tools/call / 调用失败」的原始消息摆在屏幕上。

学完应能指出：每条请求的 id 怎么和响应配对、capabilities 是谁声明的、
工具失败为什么仍是 result、以及为什么这个 server 能同时服务两代客户端。
全程离线、0 次模型调用。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SERVER_PATH = Path(__file__).with_name("day64_echo_server.py")


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def send(proc: subprocess.Popen, message: dict[str, object]) -> None:
    """把一条 JSON-RPC 消息写进子进程 stdin，一行一条；返回 None。"""
    line = json.dumps(message, ensure_ascii=False)
    say(f"  --> {line}")
    assert proc.stdin is not None
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def receive(proc: subprocess.Popen) -> dict[str, object]:
    """从子进程 stdout 读一行并解析成字典；读不到就报错，返回该字典。"""
    assert proc.stdout is not None
    line = proc.stdout.readline()
    if not line.strip():
        raise RuntimeError(
            "子进程没有返回内容——server 可能启动失败，或往 stdout 打了别的东西"
        )
    say(f"  <-- {line.rstrip()}")
    return json.loads(line)


def start_server() -> subprocess.Popen:
    """启动子进程 server，返回可读写的进程对象；不经过 SDK。"""
    return subprocess.Popen(
        [sys.executable, "-X", "utf8", str(SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def main() -> None:
    """按「是什么、为什么看原始帧、场景、一段真实会话、注意」讲一遍；返回 None。"""
    say("前两个演示都被 SDK 包好了；这一个把协议帧直接打印出来。")
    say("学完应能说清：id 怎么配对、capabilities 谁声明、失败为什么还是 result。")

    say("\n一、这是什么")
    say("MCP 的消息层就是 JSON-RPC 2.0：")
    say('  请求  {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{...}}')
    say('  响应  {"jsonrpc":"2.0","id":1,"result":{...}} 或 error 字段')
    say(
        '  通知  {"jsonrpc":"2.0","method":"notifications/initialized"}（没有 id，不需要回应）'
    )
    say("stdio 传输要求一行一条消息、行内不能有换行。")

    say("\n二、为什么值得看一次原始帧")
    say("SDK 帮你省掉了 schema 生成、参数校验、能力声明、版本协商；")
    say("但排查「宿主为什么连不上」「模型为什么调错工具」时，最终都要回到这几条消息。")
    say("另外，网上大量 1.x 教程和现在的 2.x SDK 说法不同，看得懂帧才不会被版本带偏。")

    say("\n三、具体场景")
    say("宿主启动我们的 server 后，第一件事是握手：问对方说什么版本、有哪些能力。")
    say("然后按声明的能力决定能问什么：有 tools 能力才去 tools/list。")

    say("\n四、一段真实会话（legacy 握手，2025-11-25）")
    proc = start_server()
    try:
        say("[1] initialize：客户端报自己的版本和身份，等 server 回它支持的版本")
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "raw-frame-demo", "version": "0.1.0"},
                },
            },
        )
        init = receive(proc)
        result = init["result"]
        say(
            f"  说明：server 同意了 {result['protocolVersion']}，"
            f"身份 {result['serverInfo']['name']}；"
            f"capabilities 键={sorted(result['capabilities'])}"
        )

        say("\n[2] notifications/initialized：告诉 server「握手完成，可以发请求了」")
        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        say("  说明：这一条没有 id，server 不会回应。")

        say("\n[3] tools/list：要工具清单")
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        listed = receive(proc)
        tools = listed["result"]["tools"]
        say(f"  说明：工具名={[tool['name'] for tool in tools]}")
        say(
            f"  echo 的 inputSchema={json.dumps(tools[0]['inputSchema'], ensure_ascii=False)}"
        )

        say("\n[4] tools/call：调用 echo")
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"text": "原始帧里的一行字"}},
            },
        )
        called = receive(proc)
        text = called["result"]["content"][0]["text"]
        say(
            f"  说明：成功调用也是一个 result，text={text!r}，"
            "里面还有 structuredContent 和 isError。"
        )

        say("\n[5] tools/call：调一个不存在的工具")
        send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "no_such_tool", "arguments": {}},
            },
        )
        missing = receive(proc)
        say(
            f"  说明：工具不存在仍走 result，isError={missing['result']['isError']}；"
            "请求到了工具分发环节，只是没有这个名字的工具，模型能看到并换个参数。"
        )

        say("\n[6] 发一个不存在的 method：这才是协议层错误")
        send(proc, {"jsonrpc": "2.0", "id": 5, "method": "tools/bogus"})
        error_frame = receive(proc)
        error = error_frame["error"]
        say(
            f"  说明：没有 result，只有 error，code={error['code']}，"
            f"message={error['message']}；请求没走到任何工具函数。"
        )
    finally:
        proc.kill()
        proc.wait(timeout=5)

    say("\n五、和 SDK 客户端的关系")
    say("上一个演示里 SDK 客户端报的是 2026-07-28：它先发 server/discover 探测，")
    say("这个 server 两种时代的消息都答，所以两代客户端能同时工作。")
    say("本演示手写的是 2025-11-25 的 initialize 握手，所以拿到的是握手时代版本。")
    say(
        "协议版本不是「谁更新谁赢」，而是双方谈出来的；server 兼容旧客户端是发布时的加分项。"
    )

    say("\n六、注意什么")
    say("1. id 必须原样带回：并发时靠它把响应配回请求。")
    say(
        "2. capabilities 由 server 声明，客户端只该按声明的能力问；没声明 resources 就别问 resources/list。"
    )
    say(
        "3. 两层失败要分清：工具层是 result + isError（[5]），协议层是 error + code/message（[6]）。"
    )
    say(
        "   判据：请求有没有走到 server 的工具调用环节。走到了（哪怕没找到工具），"
        "失败都是 isError 结果；"
    )
    say("   连方法名都不认识、或会话状态不对，才是 error。")
    say("4. stdout 只放协议：本演示能跑，是因为 server 一个 print 都没有。")


if __name__ == "__main__":
    main()
