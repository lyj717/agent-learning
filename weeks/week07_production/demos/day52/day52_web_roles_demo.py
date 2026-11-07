"""Day52 角色前置：用同一条图书馆通知比较普通调用、程序内测试与本机 HTTP。

先读 read_notice、make_app 和 demonstrate；serve/main 是已搭好的运行入口。
本例独立创建最小应用，只复用端口/进程/日志背景，不导入其他演示的业务。
HTTPS 只解释含义；实际请求使用本机 HTTP，不调用模型。
"""

import argparse
import json
import sys
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged
from weeks.week07_production.demos.day52.day52_runtime import running_server


def read_notice() -> dict[str, str]:
    """本例业务：直接给出固定的取书地点；不查数据库、不请求模型。"""
    print("  read_notice 真正执行：返回固定的取书地点。", flush=True)
    return {"place": "二楼服务台"}


def make_app() -> FastAPI:
    """用 FastAPI 登记 GET /notice 交给哪个函数；创建对象尚未监听端口。"""
    app = FastAPI()
    # add_api_route(路径, 处理函数, methods=[方法])：登记匹配规则，不当场执行业务。
    # 传 read_notice 函数本身；收到 GET /notice 时，FastAPI 才调用 read_notice()。
    app.add_api_route("/notice", read_notice, methods=["GET"])

    def health() -> dict[str, str]:
        """供运行环境等待服务就绪，不属于取书业务。"""
        return {"status": "ok"}

    app.add_api_route("/health", health, methods=["GET"])
    return app


def demonstrate(run_dir: Path) -> None:
    """围绕一条通知观察各工具的位置；所有关键调用直接写在本函数中。"""
    print("当前阶段要把已有问答提供为 HTTP 服务，后面再认识分段响应。")
    print("本例先弄清谁发请求、谁接请求、谁找函数；先不用组合 RAG 或会话历史。")
    print("学完应能看懂三条调用路径，并说明为什么返回 200 不等于启动了服务器。")
    print("\n一、同一个具体场景：读者想知道图书在哪里取，固定答案是二楼服务台。")
    print("你已会写 Python 函数；read_notice 就是实际给出答案的业务函数。")
    print("为了让浏览器或其他程序也能来问，需要补上接收请求和分配处理函数的工具。")
    print("\n先认识名字，不背整套库：")
    print("HTTP：请求和响应怎样表达的通信规则，例如请求 GET /notice。")
    print("HTTPS：通过加密连接传输 HTTP；不是 Python 库。")
    print("HTTPX：Python 客户端库，负责发请求、收响应；名字以字母 X 结尾。")
    print("Uvicorn：服务器程序，监听地址和端口，把收到的请求交给应用。")
    print("FastAPI：搭建应用的框架，按请求方法和路径找函数，也能校验输入。")
    print("TestClient：测试工具，在当前程序内部向指定应用发请求，不开监听端口。")
    print("\n二、先看你熟悉的普通函数调用")
    print("  result = read_notice()")
    direct = read_notice()
    print("实际返回：", direct)
    print("这里只是 Python 调函数：得到字典，没有 HTTP 状态码，也没有用到服务器。")
    print("\n三、TestClient：先在程序里检查 FastAPI 的分配规则")
    print("  app = make_app()  # 内部登记 GET /notice 对应 read_notice")
    print('  with TestClient(app) as client: response = client.get("/notice")')
    print("路径：TestClient → FastAPI 找到 read_notice → 调用函数 → 响应。")
    print("这次没有执行 uvicorn.run，也没有通过网络端口；仍经过 FastAPI 的路由处理。")
    # TestClient(app)：app 必填；在当前进程内测试应用，不启动 Uvicorn。
    with TestClient(make_app()) as client:
        # client.get(路径)：向上面指定的应用提交 GET，返回 Response。
        response = client.get("/notice")
        in_process = {"status": response.status_code, "body": response.json()}
    print("实际响应：", in_process)
    print("看到了 200，但现在还没有一个由本例启动的 Uvicorn 服务。")
    print("\n四、HTTPX + Uvicorn：另一份程序真的通过端口来访问")
    print("运行环境另开一份 Python 程序，执行下面的启动代码：")
    print('  uvicorn.run(make_app(), host="127.0.0.1", port=本轮端口, ...)')
    print("当前程序用 HTTPX 发请求；另一份程序的 Uvicorn 接收，再交给 FastAPI。")
    # 已搭好的背景：进入 with 启动服务并给出地址；退出时自动停止本轮服务。
    with running_server(Path(__file__).resolve(), run_dir) as base_url:
        print(
            '  response = httpx.get(base_url + "/notice", timeout=3, trust_env=False)'
        )
        # httpx.get(完整 URL, timeout=等待上限秒, trust_env=False)：本机实际 HTTP 请求。
        response = httpx.get(base_url + "/notice", timeout=3, trust_env=False)
        # status_code 是响应状态码；json() 把响应的 JSON 正文解析成 Python 对象。
        over_http = {"status": response.status_code, "body": response.json()}
        print("实际请求地址：", str(response.url))
        print("实际响应：", over_http)
        print("另一份程序执行了业务函数；它的打印会保存到本轮 server.log。")
    print("\n五、服务已经停止：再向刚才的地址发送一次请求")
    try:
        httpx.get(base_url + "/notice", timeout=1, trust_env=False)
    except (httpx.ConnectError, httpx.ConnectTimeout) as error:
        # 两个异常类都从 httpx 取得：连接被拒绝或连接等待超时，均未建立连接。
        # Windows 对停止的端口可能等到超时，不把具体连接异常类型写死。
        stopped_error = type(error).__name__
        print("实际结果：", stopped_error)
        print("连接没有建立，取不到 HTTP 响应，read_notice 也没有被这次请求调用。")
        print("这里不是返回 500：连接失败时根本还没有得到服务器的响应状态码。")
    else:
        raise AssertionError("预期刚停止的本轮服务已经无法连接")
    print("\n六、HTTPS 放在哪里？")
    print("HTTP/HTTPS 描述客户端与服务端怎样通信，不是多加一个回答问题的函数。")
    print("HTTPS 为 HTTP 通信加上加密保护；HTTPX 可以请求 http:// 或 https:// 地址。")
    print(
        "本例实际地址以 http:// 开头；没有配置或演示 HTTPS，单改 URL 前缀不能启用它。"
    )
    print("\n回看结果：普通调用得到字典；TestClient 和本机 HTTP 都能得到 200；")
    print(
        "服务器停止后，本机请求连接失败。请按调用路径认角色，不用背运行环境的辅助代码。"
    )

    assert direct == {"place": "二楼服务台"}
    assert in_process == over_http == {"status": 200, "body": direct}
    # loads/read_text：读取运行环境保存的 JSON 文本，再解析为字典核对服务已停止。
    server = json.loads((run_dir / "server_info.json").read_text(encoding="utf-8"))
    assert server["stopped"] is True
    result = {
        "direct_call": direct,
        "test_client": in_process,
        "real_http": over_http,
        "after_stop": {"error_type": stopped_error, "http_response_received": False},
        "server_stopped": server["stopped"],
    }
    # dumps：把本次客观结果转成 JSON 文本；只保存运行数据，不代写学员观察。
    (run_dir / "roles_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def serve(port: int) -> None:
    """已搭好的服务进程：运行自己的最小应用；只在本机监听。"""
    # uvicorn.run(app, host=监听地址, port=监听端口)：持续运行，直到服务停止。
    uvicorn.run(
        make_app(),
        host="127.0.0.1",
        port=port,
        access_log=False,
        log_level="warning",
        lifespan="off",
    )


def main() -> None:
    """默认运行并留证；--serve 是已搭好的服务子进程入口。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="内部服务入口")
    parser.add_argument("--port", type=int, default=8000, help="内部服务监听端口")
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        run_logged(
            "web_roles_demo",
            demonstrate,
            {"model_calls": 0, "transport": "in_process_and_real_loopback_http"},
            Path(__file__),
            Path(__file__).parent / "outputs",
            origin_env="DAY52_RUN_ORIGIN",
        )


if __name__ == "__main__":
    main()
