"""Day52 前置：HTTPX 怎样通过真实端口调用已完成的 Day51 应用。

独立启动自己的服务进程和旧业务环境；不依赖先跑 Uvicorn 演示。
"""

import argparse
import json
import sys
from pathlib import Path

import httpx
import uvicorn

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_app import make_app
from weeks.week07_production.demos.day52.day52_runtime import running_server


def serve(port: int) -> None:
    """运行环境：用已知业务创建应用，再启动本例自己的服务进程。"""
    app = make_app()
    print("服务端：旧会话应用已创建，等待 HTTP 请求。", flush=True)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        access_log=False,
        log_level="warning",
        lifespan="off",
    )


def show_response(
    records: list[dict],
    label: str,
    response: httpx.Response,
    expected_status: int,
) -> None:
    """只负责显示并记录实际响应；HTTP 调用仍直接写在主演示中。"""
    row = {
        "case": label,
        "method": response.request.method,
        "url": str(response.url),
        "status": response.status_code,
        "body": response.json(),
    }
    records.append(row)
    print("\n", label, "：", row["method"], row["url"])
    print("实际/期望状态码：", row["status"], "/", expected_status)
    print("实际正文：", row["body"])
    assert response.status_code == expected_status


def demonstrate(run_dir: Path) -> None:
    """用 Client、get、post、json 和 raise_for_status 核对旧服务的实际响应。"""
    print("本阶段要让已有问答应用通过真实 HTTP 提供普通响应与后续 SSE。")
    print("本例只认识客户端：谁发送请求、怎样传 JSON、怎样查看响应和状态。")
    print("学完应能读懂后续流式客户端的起点，不需要重写 Day51 的问答或历史。")
    print("\n一、是什么：HTTPX 是发送 HTTP 请求并接收响应的客户端库。")
    print("为什么：服务监听端口后，还需要一个调用者把请求真正发送过去。")
    print("场景：你已写的 Day51 common_post 在服务进程内，另一个进程提交 /ask。")
    print("\n二、导入和接口：先创建客户端，再发送请求")
    print(
        "import httpx；with httpx.Client(base_url=地址, timeout=3, trust_env=False) as client:"
    )
    print(
        "Client 的参数都可选；本例 base_url 是前缀，timeout 限制等待，trust_env=False 避开环境代理。"
    )
    print(
        'client.get("/health")：GET，不带请求体；client.post("/ask", json=字典)：POST JSON。'
    )
    print("get/post 的路径必填；json 是可选请求体参数，本例 /ask 的模型要求提供它。")
    print(
        "返回 Response，不是直接返回 dict；status_code 是数字，json() 才把 JSON 正文解析成对象。"
    )
    print(
        "raise_for_status() 在 2xx 时返回响应自身，非 2xx 抛 HTTPStatusError；本例比较 200/400。"
    )
    print("\n三、实际调用：客户端 → 端口/Uvicorn → FastAPI 路由 → 你已写的处理函数")
    records: list[dict] = []
    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        # Client(...) 返回客户端；with 结束关闭客户端连接，不等于重建服务端应用。
        with httpx.Client(base_url=base_url, timeout=3, trust_env=False) as client:
            response = client.get("/health")
            show_response(records, "健康检查", response, 200)
            response = client.post(
                "/ask", json={"session_id": " reader-a ", "question": " 地点 "}
            )
            response.raise_for_status()
            show_response(records, "提交旧问答", response, 200)
            assert response.json()["session_id"] == "reader-a"
            assert response.json()["checked"]["answer"] == "请到二楼取书。"
            response = client.get("/sessions/reader-a/history")
            show_response(records, "读取本次历史", response, 200)
            assert len(response.json()["turns"]) == 1
            response = client.post(
                "/ask", json={"session_id": "reader-a", "question": "  "}
            )
            show_response(records, "业务拒绝空白问题", response, 400)
            try:
                # raise_for_status()：把失败 HTTP 状态变成可捕获的客户端异常。
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                print(
                    "客户端捕获：",
                    type(error).__name__,
                    "；响应状态仍是",
                    error.response.status_code,
                )
                records[-1]["client_exception"] = type(error).__name__
            else:
                raise AssertionError("400 应被 raise_for_status 转为 HTTPStatusError")
        with httpx.Client(
            base_url=base_url, timeout=3, trust_env=False
        ) as another_client:
            response = another_client.get("/sessions/reader-a/history")
            show_response(records, "换客户端，仍访问同一应用", response, 200)
            assert len(response.json()["turns"]) == 1
        (run_dir / "http_responses.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("\n四、注意什么")
    print("400 响应已经收到；只有调用 raise_for_status 才在客户端抛上述异常。")
    print("连接不上或等待超时属于 HTTPX 的传输异常，与收到 400/500 响应不同。")
    print(
        "本例沿用 Day51 的严格模型、历史和旧问答，三个业务回调都是人工替身，模型调用为 0。"
    )
    print("本例尚未读取 SSE；stream() 与 iter_lines() 留到前置核对后的独立演示。")


def main() -> None:
    """独立运行本例并留证；内部服务分支由公共启动环境调用。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="内部服务进程入口")
    parser.add_argument("--port", type=int, default=8000, help="服务进程监听端口")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        run_logged(
            "httpx_demo",
            demonstrate,
            {"transport": "real_loopback_http", "model_calls": 0},
            Path(__file__),
            Path(__file__).parent / "outputs",
            origin_env="DAY52_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
