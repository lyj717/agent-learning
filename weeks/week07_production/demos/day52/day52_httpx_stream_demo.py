"""Day52 SSE 第二步：HTTPX 怎样逐行读取响应，以及怎样停止本次读取。

本例自带延时计数通知和最小应用，不导入格式演示的业务。
先读 demonstrate 中的 stream/iter_lines；serve/main 是已有启动方式。
只观察客户端读取与响应关闭，不把它写成服务端业务已经立即取消。
"""

import argparse
import json
import sys
import time
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


def ticks() -> Iterable[ServerSentEvent]:
    """本例的人工服务：每次请求依次产生三个计数事件，不调用模型。"""
    for number in range(1, 4):
        # sleep(秒)：在本例普通 def 的工作线程中模拟等待，不是在 async def 中阻塞。
        time.sleep(0.25)
        yield ServerSentEvent(event="tick", data={"number": number})


def make_app() -> FastAPI:
    """本例自己的两个路径；不需要先跑其他演示。"""
    app = FastAPI()
    app.add_api_route(
        "/ticks", ticks, methods=["GET"], response_class=EventSourceResponse
    )

    def health() -> dict[str, str]:
        """供启动等待和检查整份服务仍在运行。"""
        return {"status": "ok"}

    app.add_api_route("/health", health, methods=["GET"])
    return app


def demonstrate(run_dir: Path) -> None:
    """关键客户端调用都直接写在这里，对照完整读取与提前停止。"""
    print("本阶段要判断流式响应的读取结果，后面由你独立处理完成/错误/中断。")
    print("上一份认识 SSE 正文格式；这一份只解决客户端怎样边到边读和关闭响应。")
    print("学完应能区分读一行、读一条事件、退出循环和关闭整份服务器。")
    print("\n一、是什么：HTTPX 的 stream 让你开始处理响应时，不必先读完整份正文。")
    print("为什么：普通 get 默认读完整份正文才返回，不适合观察每段到达后立即处理。")
    print("场景：服务端隔一会儿交出一个计数；客户端收到一行就打印一行。")
    print("\n二、导入、参数、拿到什么")
    print("  import httpx")
    print('  with httpx.stream("GET", url, timeout=3, trust_env=False) as response:')
    print("      for line in response.iter_lines():")
    print("          print(repr(line))")
    print("stream 的方法和完整 URL 必填；timeout、trust_env 是本例显式设置的可选参数。")
    print(
        "stream 产生给 with 使用的管理对象；进入 with 后，as response 拿到 Response。"
    )
    print("此时可看响应头和状态码，正文仍由你随后逐步读取；退出 with 会关闭这次响应。")
    print("iter_lines() 不用传参数，返回逐行字符串的迭代器；for 每次取得一行。")
    print("它会去掉行末换行符，SSE 的结束空行因此表现为空字符串。")
    print("repr(line) 显示字符串的表示形式，空字符串会清楚显示成 ''。")
    print("一条 SSE 事件可以有多行；取得一行不等于取得完整事件。")
    print('startswith("data: ")：检查字符串是否以这一段开头，返回 True 或 False。')
    print(
        'removeprefix("data: ")：匹配时去掉开头这一段，返回新字符串；不匹配则内容不变。'
    )
    print("这两个方法都属于字符串，不用另行导入；引号中 data: 后的空格也参与匹配。")
    print("本例先筛选 data 行，再去掉字段前缀，把剩下的 JSON 文本交给 json.loads。")
    print("\n三、运行完整读取：服务端每次等约 0.25 秒，依次产生 1、2、3")
    print("时间是本机实测值，每轮会变化；同一事件的几行通常紧接着到达。")
    full_lines = []
    full_numbers = []
    early_lines = []
    early_numbers = []
    # 外层管服务器：另起本文件 --serve --port N，main 调用 serve；退出时停服务器。
    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        # stream(方法, 完整 URL, ...)：进入内层 with 取得流式 Response，退出关闭响应。
        with httpx.stream(
            "GET", base_url + "/ticks", timeout=3, trust_env=False
        ) as response:
            response.raise_for_status()
            # perf_counter()：高精度计时，当前值减开始值就是经过的秒数。
            started = time.perf_counter()
            # iter_lines()：边接收边取文本行；不会替你把多行拼成 SSE 事件。
            for line in response.iter_lines():
                elapsed = time.perf_counter() - started
                full_lines.append({"elapsed_s": elapsed, "line": line})
                print(f"  +{elapsed:.3f}s 收到行：{line!r}")
                # startswith(前缀)：判断 line 是否以指定文本开头，返回 bool。
                if line.startswith("data: "):
                    # removeprefix(前缀)：匹配时去掉开头这一段，返回 str；不修改 line。
                    json_text = line.removeprefix("data: ")
                    # loads(JSON 文本)：解析为 Python 对象；本例得到带 number 键的字典。
                    data_dict = json.loads(json_text)
                    full_numbers.append(data_dict["number"])
                    # 这里只读本例固定的 data 行；不是完整的通用 SSE 解析器。
        # is_closed：Response 的布尔属性，表示当前响应是否已经关闭。
        full_closed = response.is_closed
        print("完整读取到的计数：", full_numbers, "；本次响应已关闭：", full_closed)
        print("\n四、再发一次独立请求：到第一条事件的结束空行就 break")
        with httpx.stream(
            "GET", base_url + "/ticks", timeout=3, trust_env=False
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                early_lines.append(line)
                print("  收到行：", repr(line))
                # 同上：先判断这是不是 data 行，再把前缀与 JSON 内容分开。
                if line.startswith("data: "):
                    json_text = line.removeprefix("data: ")
                    data_dict = json.loads(json_text)
                    early_numbers.append(data_dict["number"])
                if line == "":
                    print("  到达本例第一条事件的结束空行，执行 break。")
                    break
            print("已经退出 for 循环；接下来离开内层 with，关闭本次响应。")
        early_closed = response.is_closed
        print(
            "提前停止前读到的计数：", early_numbers, "；本次响应已关闭：", early_closed
        )
        # 关闭一次响应后，整份服务仍在；这里用已学的普通 get 实际确认。
        health_status = httpx.get(
            base_url + "/health", timeout=3, trust_env=False
        ).status_code
        print("服务器仍能处理另一条 /health 请求，实际状态码：", health_status)
        print(
            "break 退出当前循环；离开 stream 的 with 关闭本次响应；它们没有关闭服务器。"
        )
        print(
            "客户端停止读也不证明服务端业务立即取消；本例只核对客户端读到哪里和响应关闭。"
        )
    print("离开外层 running_server 的 with 后，本轮服务器才由运行环境停止。")
    print("\n五、注意什么")
    print("timeout=3 是 HTTPX 的网络操作等待上限配置，不是整个流只能持续三秒。")
    print("本例收到 1、2、3 后自然读到正文结束；它们是人工计数，不是模型 token。")
    print("下一步要另外约定业务完成事件，不能只因读到 EOF 就认定回答完整。")
    assert full_numbers == [1, 2, 3]
    assert early_numbers == [1]
    assert full_closed and early_closed and health_status == 200
    result = {
        "full": {
            "numbers": full_numbers,
            "lines": full_lines,
            "response_closed": full_closed,
        },
        "early": {
            "numbers": early_numbers,
            "lines": early_lines,
            "response_closed": early_closed,
        },
        "health_after_response_close": health_status,
    }
    # dumps：记录实际到达时刻、原始行及关闭状态，不填学员的原因分析。
    (run_dir / "httpx_stream_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def serve(port: int) -> None:
    """已有运行背景：在另一份程序中监听本机端口。"""
    uvicorn.run(
        make_app(), host="127.0.0.1", port=port, access_log=False, log_level="warning"
    )


def main() -> None:
    """默认运行演示并留证；--serve 是辅助环境启动服务的分支。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="内部服务入口")
    parser.add_argument("--port", type=int, default=8000, help="内部服务端口")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        run_logged(
            "httpx_stream_demo",
            demonstrate,
            {"model_calls": 0, "transport": "real_loopback_http"},
            Path(__file__),
            Path(__file__).parent / "outputs",
            origin_env="DAY52_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
