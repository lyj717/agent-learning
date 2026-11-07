"""Day52 C 已提供的工具与人工服务，不是学员要补写的答案。

索引：
iter_sse_events(lines)：把已收到的文本行按空行组成事件，供学员客户端调用。
make_stream_app()：提供固定人工情境，由运行入口启动；学员不用调用或修改。

事件名 delta/done/error/progress 是本题的应用约定，不是 SSE 强制的名字。
没有加载模型、请求服务商或改动 Day51 的应用、会话历史。
"""

import json
import time
from collections.abc import Iterable, Iterator

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent


def iter_sse_events(lines: Iterable[str]) -> Iterator[dict]:
    """按空行把本课的 JSON 数据事件交给调用方，已实现，无需学员补写。

    lines（必填）：字符串迭代对象，通常传 response.iter_lines()；不是方法本身。
    返回迭代器，每次给出 {"event": str, "data": dict}，只读取到下一条事件所需的行。
    例：['event: delta', 'data: {"text": "请"}', '']
        → 依次交出一个 {"event": "delta", "data": {"text": "请"}}。

    已处理：无内容空行、冒号开头的注释、data: 后可有或没有一个空格、多行 data。
    仅支持本课约定的 JSON 对象数据；非法 JSON 或不是对象时抛 ValueError。
    未命名事件按 message 返回；id/retry 等字段不参与本题。EOF 前没有结束空行的
    残段不作为完整事件交出。上游迭代发生的 httpx.ReadTimeout 原样传出，不吞异常。
    本工具不发送请求、不关闭响应、不判定业务最终状态；这些由学员的客户端负责。
    """
    event_name = "message"
    data_lines: list[str] = []
    for line in lines:
        if line == "":
            if data_lines:
                # loads：只解析已经按空行收齐的事件数据，不解析整个 SSE 响应。
                data = json.loads("\n".join(data_lines))
                if not isinstance(data, dict):
                    raise ValueError("本题事件 data 必须是 JSON 对象")
                yield {"event": event_name or "message", "data": data}
            event_name = "message"
            data_lines = []
            continue
        # startswith：判断字符串开头是否匹配；冒号开头是 SSE 注释行。
        if line.startswith(":"):
            continue
        # partition(分隔符)：按第一次出现的位置分为前段、分隔符、后段。
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")  # 协议允许冒号后一个空格，这里只去掉一个。
        if field == "event":
            event_name = value
        elif field == "data":
            data_lines.append(value)


def make_stream_app() -> FastAPI:
    """返回 C 的人工 SSE 服务，已实现；由检查入口在另一份程序中启动。

    无参数，返回 FastAPI。GET /health 用于启动检查；GET /answer/{mode} 提供事件。
    约定 mode 是 normal/error/truncated/slow 之一，本题入口保证有效。
    每次请求有独立生成器；所有正文均为人工数据，不代表真实模型生成或检索结果。
    """
    app = FastAPI()

    def health() -> dict[str, str]:
        """启动环境与检查入口使用。"""
        return {"status": "ok", "mode": "offline_sse_fixture"}

    def answer(mode: str) -> Iterable[ServerSentEvent]:
        """按题面约定产生人工事件，普通 def 的等待由框架放在工作线程执行。"""
        yield ServerSentEvent(comment="offline classroom fixture")
        yield ServerSentEvent(event="progress", data={"note": "准备回答"})
        yield ServerSentEvent(event="delta", data={"text": "请"})
        if mode == "error":
            yield ServerSentEvent(event="error", data={"error_type": "TimeoutError"})
            return
        if mode == "truncated":
            return  # HTTP 正常结束，但没有 done 或 error 事件。
        if mode == "slow":
            # sleep(秒)：人工制造读取下一段时的等待，超过题目规定的读超时。
            time.sleep(1.25)
        elif mode != "normal":
            raise ValueError("本题未约定的人工模式")
        yield ServerSentEvent(event="delta", data={"text": ""})
        time.sleep(0.04)
        yield ServerSentEvent(event="delta", data={"text": "到二楼取书。"})
        yield ServerSentEvent(event="done", data={})

    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_route(
        "/answer/{mode}", answer, methods=["GET"], response_class=EventSourceResponse
    )
    return app
