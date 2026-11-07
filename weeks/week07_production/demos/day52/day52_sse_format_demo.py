"""Day52 SSE 第一步：一次 HTTP 响应怎样装下多条事件。

只认识 ServerSentEvent、EventSourceResponse 与实际文本格式。
本例自带两条人工通知和最小应用，不依赖其他小演示的业务。
客户端暂用已学的 get 收完整正文；边到边读与终止判断留给下一步。
"""

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_runtime import running_server


def notices() -> Iterable[ServerSentEvent]:
    """本例的 GET 处理函数：由 FastAPI 逐项读取，交出两条固定通知事件。"""
    # ServerSentEvent(data=内容, event=事件名)：构造事件对象；这里尚未发网络请求。
    # data 接收能转成 JSON 的值；event 可省略，本例显式命名为 notice。
    yield ServerSentEvent(event="notice", data={"text": "明天上午开放"})
    yield ServerSentEvent(event="notice", data={"text": "请携带借书证"})


def make_app() -> FastAPI:
    """创建本例自己的应用；登记返回 SSE 的业务路径与运行环境的健康检查。"""
    app = FastAPI()
    # response_class 接收类本身，故 EventSourceResponse 后不写括号。
    # 这告诉 FastAPI：逐项读取 notices 的 yield，并编码为 SSE 响应。
    app.add_api_route(
        "/notices", notices, methods=["GET"], response_class=EventSourceResponse
    )

    def health() -> dict[str, str]:
        """只供共用环境等待服务就绪，不属于通知业务。"""
        return {"status": "ok"}

    app.add_api_route("/health", health, methods=["GET"])
    return app


def demonstrate(run_dir: Path) -> None:
    """请求本例自己的 SSE 路径，对照对象、响应头、文本字段和事件边界。"""
    print("本阶段要把已有服务扩展为分段响应；前置 A 的角色和启动位置已经核对。")
    print("本例只认识 SSE 事件和实际正文格式；之后才练边到边读、成功/失败/断开。")
    print("学完应能区分一次 HTTP 响应、其中一条事件，以及事件内部的数据。")
    print("\n一、是什么：SSE 是服务端在一次 HTTP 响应中连续发送文本事件的格式。")
    print("为什么：通知或回答分段产生时，可以逐条交给客户端，不必先凑成整份结果。")
    print("场景：一个读者请求一次 /notices，服务端交出两条图书馆通知。")
    print("本例是人工固定通知，不请求模型；健康检查另走 /health。")
    print("\n二、先看服务端的关键调用（本文件 notices 和 make_app）")
    print("  from fastapi.sse import ServerSentEvent, EventSourceResponse")
    print('  yield ServerSentEvent(event="notice", data={"text": "明天上午开放"})')
    print('  app.add_api_route("/notices", notices, methods=["GET"],')
    print("                    response_class=EventSourceResponse)")
    print("ServerSentEvent 构造一条事件：data 是内容，event 是你起的事件名。")
    print("库中二者都有默认值；本例显式给出。id/retry 等可选字段本次不使用。")
    print("notice 这个名字由本例自定，不是必须记住的 Python 关键字。")
    print("EventSourceResponse 是响应类型：让 FastAPI 按 SSE 编码，并设置响应头。")
    print("这里的类由 FastAPI 使用；不需要你手工把它实例化成一次响应。")
    print("\n三、接上旧生成器知识")
    print("Day6 已练过 yield：调用含 yield 的函数先得到生成器，逐项取值才执行函数体。")
    print("这里由 FastAPI 逐项取 notices 交出的事件；函数正常结束就不再交出下一项。")
    print("return 整个列表与逐项 yield 的执行方式不同；本例使用普通 def，不另学异步。")
    print("\n四、实际运行：只发送一次 GET /notices")
    # 进入 with 后另起本文件 --serve --port N；它的 main 执行 serve(port)。
    # 环境确认服务就绪后交出地址，离开 with 自动停止；不要求重写这份运行背景。
    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        # httpx.get(完整 URL)：本节沿用已学接口，等正文读完后再返回 Response。
        response = httpx.get(base_url + "/notices", timeout=3, trust_env=False)
        content_type = response.headers["content-type"]
        raw_text = response.text
        print("HTTP 状态码：", response.status_code)
        print("Content-Type：", content_type)
        print("实际正文如下；两条事件之间确实有空行：")
        print(raw_text, end="")
        print("正文结束。")
        print("原始 JSON 里的中文可能显示为反斜杠 u 加编码，这是文本转义，不是加密。")
        print("下面的留证检查会解析本例 data 部分，再显示可读中文；原始正文照常保留。")
        print("event: 后面是事件名；data: 后面是本条事件的数据；空行结束一条事件。")
        print(
            "SSE 的 data 不限于 JSON；但本例传 data 字典，FastAPI 会把它编码为 JSON。"
        )
        print("HTTP 状态码属于整次响应；event: notice 是正文中的事件字段。")
        print("\n五、为什么不能对整个 SSE 正文调用 response.json()？")
        try:
            response.json()
        except ValueError as error:
            whole_body_json_error = type(error).__name__
            print("实际异常类型：", whole_body_json_error)
            print("整个正文有 event:/data: 和事件间的空行，不是一份完整的 JSON 文本。")
        else:
            raise AssertionError("SSE 正文不应被当成一份普通 JSON 解析")

    # 以下只是本例固定格式的留证检查，不是通用 SSE 解析器，也不是学员任务。
    # split(分隔文本)：按本例实际的空行切开；只检查已知的两条简单事件。
    blocks = [block for block in raw_text.split("\n\n") if block]
    assert len(blocks) == 2
    assert response.status_code == 200
    assert content_type.startswith("text/event-stream")
    payloads = []
    for block in blocks:
        lines = block.splitlines()
        assert lines[0] == "event: notice"
        # loads：只解析本例 data: 后的那段 JSON，不解析整条 SSE 响应。
        payloads.append(json.loads(lines[1].removeprefix("data: ")))
    assert payloads == [{"text": "明天上午开放"}, {"text": "请携带借书证"}]
    print("本例两条 data 解析后的内容：")
    for index, payload in enumerate(payloads, 1):
        print(f"  第 {index} 条通知：{payload['text']}")
    print("\n六、本例到这里说明了什么")
    print("一次 HTTP 业务响应里有两条 SSE 事件，每条事件都有自己的数据和结束空行。")
    print("本节 get 等整份正文读完才显示，所以本节不测量各条事件的到达时间。")
    print("下一步再单独认识客户端的 stream/iter_lines，以及业务完成与连接结束的区别。")
    result = {
        "status": response.status_code,
        "content_type": content_type,
        "raw_text": raw_text,
        "event_count": len(blocks),
        "payloads": payloads,
        "whole_body_json_error": whole_body_json_error,
    }
    # dumps：把本次可核对结果保存为 JSON；原始 SSE 正文也保留在 raw_text 中。
    (run_dir / "sse_format_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def serve(port: int) -> None:
    """运行背景：另一个程序在这里启动本例应用。"""
    uvicorn.run(
        make_app(), host="127.0.0.1", port=port, access_log=False, log_level="warning"
    )


def main() -> None:
    """默认运行并留证；另一个程序带 --serve 时只执行 serve。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="内部服务入口")
    parser.add_argument("--port", type=int, default=8000, help="内部服务端口")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        run_logged(
            "sse_format_demo",
            demonstrate,
            {"model_calls": 0, "transport": "real_loopback_http"},
            Path(__file__),
            Path(__file__).parent / "outputs",
            origin_env="DAY52_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
