"""Day52 前置：Uvicorn 怎样让 FastAPI 应用真正接受本机 HTTP 请求。

默认自动启动、请求、停止；--serve 是已搭好的服务进程入口。
本例自带最小应用，不依赖另一份演示的业务。
"""

import argparse
import json
import sys
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_runtime import running_server


def make_app() -> FastAPI:
    """创建本例独立的两个 GET 路径，仅创建应用尚未监听端口。"""
    app = FastAPI()

    def health() -> dict:
        """供运行环境确认本例服务已启动。"""
        return {"status": "ok"}

    def ping() -> dict:
        """收到实际请求后返回一个便于核对的小字典。"""
        return {"message": "本机服务已收到请求"}

    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_route("/ping", ping, methods=["GET"])
    return app


def serve(port: int) -> None:
    """子进程实际执行本课的启动调用；端口由运行环境传入。"""
    app = make_app()
    print("服务端：创建 app 完成；现在执行 uvicorn.run。", flush=True)
    # uvicorn.run(app, host=地址, port=端口)：监听 HTTP，并把请求交给 app。
    # app 必填；host 默认 127.0.0.1、port 默认 8000；本例显式给定并关闭访问日志。
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        access_log=False,
        log_level="warning",
        lifespan="off",
    )


def demonstrate(run_dir: Path) -> None:
    """观察应用对象、真实监听进程和客户端收到的响应。"""
    print("本阶段要把 Day51 应用接到真实 HTTP，再提供 SSE 分段响应。")
    print("本例只解决启动：谁把 Python 应用接到一个能访问的端口。")
    print("学完应能区分创建 app 和启动服务器；后续流式演示复用同一启动环境。")
    print("\n一、是什么：Uvicorn 是接收 HTTP 请求、交给 FastAPI 应用处理的服务器。")
    print("为什么：app = FastAPI() 只创建 Python 对象，本身不会监听端口。")
    print("场景：另一个进程想通过 http://127.0.0.1:某端口/ping 访问本应用。")
    print("\n二、实际服务进程中执行的代码（见本文件 serve）")
    print("  app = make_app()")
    print('  uvicorn.run(app, host="127.0.0.1", port=port, ...)')
    print("从 import uvicorn 得到 run；app 是已有应用，host/port 决定监听地址。")
    print("run 持续运行到服务停止，正常停止时返回 None；不是立即返回一次问答结果。")
    print("127.0.0.1 表示只在本机访问；本例自动选空闲端口，不用手动占用 8000。")
    print("\n三、真实调用：发送 → Uvicorn → FastAPI → ping() → 客户端收到响应")
    # running_server 是从 day52_runtime 导入的 AI 辅助工具，不是 Uvicorn 的 API。
    # Path(__file__).resolve() 是本演示文件的绝对路径；run_dir 是本轮日志目录。
    # 进入 with 时，工具另开 Python 程序运行“本文件 --serve --port 本轮端口”。
    # 另一程序的 main 会进入 if args.serve，执行下面的 serve(args.port)。
    # 服务就绪后，as base_url 得到访问地址；离开 with 时自动停止服务。
    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        print("客户端即将发送 GET", base_url + "/ping")
        # httpx.get(url, timeout=秒, trust_env=False)：真实 GET，返回 Response 对象。
        response = httpx.get(base_url + "/ping", timeout=3, trust_env=False)
        result = {
            "url": str(response.url),
            "status": response.status_code,
            "body": response.json(),
        }
        print("实际状态码：", response.status_code, "；期望：200")
        print("实际正文：", response.json())
        assert response.status_code == 200
        assert response.json() == {"message": "本机服务已收到请求"}
        (run_dir / "uvicorn_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("\n四、注意什么")
    print("1. 进程先理解为一份正在运行的 Python 程序；两个进程也可以在同一台电脑上。")
    print("Day51：同一个 Python 程序内，TestClient 把请求直接交给指定的 app 处理。")
    print(
        "  TestClient → FastAPI → 处理函数 → 响应；这条路径没有启动监听端口的服务器。"
    )
    print("今天：运行环境另启动一份 Python 程序，专门执行 serve 中的 uvicorn.run。")
    print(
        "  当前程序的 HTTPX → 本机端口 → 另一程序的 Uvicorn → FastAPI → ping() → 响应。"
    )
    print("2. Uvicorn 负责监听和接收连接；FastAPI 按 GET /ping 找到并调用 ping 函数。")
    print("3. server.log 保存另一份服务端程序的打印和报错，排查服务启动问题时看它。")
    print(
        "server_info.json 保存本轮地址、端口、PID（进程号）和 stopped（是否已停止）。"
    )
    print("本例请求结束后自动停止服务，所以最后 stopped 为 true；这不表示从未启动。")
    print("4. TestClient 和真实 HTTP 都能得到 200；200 只告诉你这次响应成功。")
    print("判断是否监听端口，还要看有没有启动 Uvicorn、客户端是否通过网络地址访问。")


def main() -> None:
    """默认留证演示；内部 --serve 分支由启动环境在子进程中调用。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="内部服务进程入口")
    parser.add_argument("--port", type=int, default=8000, help="服务进程监听端口")
    args = parser.parse_args()
    if args.serve:
        # running_server 启动的另一份程序带 --serve，会在这里实际调用 serve。
        serve(args.port)
    else:
        run_logged(
            "uvicorn_demo",
            demonstrate,
            {"transport": "real_loopback_http", "model_calls": 0},
            Path(__file__),
            Path(__file__).parent / "outputs",
            origin_env="DAY52_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
