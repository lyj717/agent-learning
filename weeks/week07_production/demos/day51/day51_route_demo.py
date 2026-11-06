"""Day51A：把普通函数登记为 HTTP 接口，看清服务端和客户端各写什么。

核心是 GET /notice 如何交给 read_notice()；TestClient 提供本例独立运行环境。
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_route(run_dir: Path) -> None:
    """显示双方的实际调用代码，按发送、函数执行、收到响应的顺序观察。"""
    print("Week07 要把问答函数接成接口，让其他程序提交请求、取得回答。")
    print("本例先用一条人工通知代替问答，只弄清：请求怎样找到你写的函数。")
    print("学完应能写出登记接口、发送请求的代码；练习 B 再换成你自己的接口。")
    print("\n一、先认清名字和双方的工作")
    print("HTTP：请请求方法，/求与响应的通信规则；GET 是notice 是请求路径。")
    print("FastAPI：写服务端的 Python 框架，负责找到并调用处理请求的函数。")
    print("TestClient：本课用的测试客户端，向指定 app 提交请求，取得响应。")
    print("httpx：上份演示导入的 Python 库；httpx.Request(...) 当时只构造请求对象。")
    print("为什么需要路由：客户端只报方法和路径，框架要知道该调用哪个函数。")
    print("路由就是这条对应规则：GET /notice -> read_notice。")
    print("你负责写函数、登记规则；FastAPI 按规则调用；客户端负责提出请求。")
    print("本文件同时放双方代码，是为了能独立运行并看到全过程。")

    print("\n二、服务端写什么：创建应用、定义函数、登记对应规则")
    print("[1] app = FastAPI()")
    print("FastAPI 从 fastapi 导入；本例不传参数，得到应用对象 app。")
    # FastAPI()：创建应用对象；后面的登记和测试客户端都使用同一个 app。
    app = FastAPI()
    calls: list[str] = []

    print("[2] def read_notice() -> dict[str, str]:")
    print('        return {"notice": "周六阅览室闭馆。"}')
    print("这是你写的普通函数，没有入参，返回字典；定义函数后函数体尚未执行。")

    def read_notice() -> dict[str, str]:
        """本例唯一业务动作，返回人工通知字典。"""
        # calls 和下面的 print 只是执行标记，帮助观察是谁在什么时候调用函数。
        calls.append("read_notice")
        print("  ② 服务端：【read_notice() 函数体现在执行】，返回通知字典。")
        return {"notice": "周六阅览室闭馆。"}

    print('[3] app.add_api_route("/notice", endpoint=read_notice, methods=["GET"])')
    print("/notice 是你约定的路径；endpoint 接收负责处理的函数；methods 是允许的方法。")
    print("这三个值都由你决定；客户端之后要按这个约定请求。")
    # add_api_route(路径, endpoint=已定义函数, methods=方法列表)：登记，尚不调用 endpoint。
    app.add_api_route("/notice", endpoint=read_notice, methods=["GET"])
    print("add_api_route 返回 None；规则保存在 app 中，所以不需要写 result = ...。")
    print("实际登记内容：GET /notice -> read_notice；函数执行次数：", len(calls))
    print("期望次数是 0：登记规则这个动作没有调用 read_notice()。")

    print("\n三、客户端怎么用：发送一次请求，查看一次响应")
    print("from fastapi.testclient import TestClient")
    print("with TestClient(app) as client:")
    print('    response = client.get("/notice")')
    print("    print(response.status_code)")
    print("    print(response.json())")
    print("TestClient(app) 的 app 必填：它指定把请求交给上面哪一个应用。")
    print("client 是客户端对象；with 在结束后关闭客户端资源。")
    print("client.get(路径) 提交 GET 请求并等待响应；本例的路径必填，不需要请求体。")
    print("本地客户端已接到 app，故这里只写 /notice；将来走网络还需要服务地址。")
    print("TestClient 在进程内交给框架处理，本例不启动网络端口。")
    print("现在实际执行刚才展示的客户端代码，注意 ①②③ 的先后：")
    # TestClient(app)：在进程内向指定 FastAPI 应用发送请求；此处不启动 TCP 服务。
    with TestClient(app) as client:
        print("  ① 客户端：执行 client.get('/notice')，向 app 提交 GET /notice。")
        # client.get(path)：提交请求并等待框架处理，返回 httpx.Response 响应对象。
        response = client.get("/notice")
        print("  ③ 客户端：get 调用结束，response 接到响应对象。")
        print(
            "本次请求方法和路径：", response.request.method, response.request.url.path
        )
        print("response 类型：", type(response).__name__)
        print("response.status_code：", response.status_code, "；期望 200。")
        print("response.text（JSON 文本）：", response.text)
        # response.json()：将已经收到的 JSON 正文解析为 Python 对象，不再提交请求。
        body = response.json()
        print("response.json()（解析后的字典）：", body)
        print("read_notice 累计执行次数：", len(calls), "；期望 1。")
        print(
            "中间由 FastAPI 完成：匹配 GET /notice -> 调用 read_notice() -> 形成 JSON 响应。"
        )
        print("函数返回字典；客户端 get 返回响应对象，状态码与正文从该对象读取。")

        print("\n四、再换两个请求，确认方法和路径确实决定是否调用函数")
        print('[对照 1] client.get("/unknown")：路径没有登记。')
        before = len(calls)
        missing = client.get("/unknown")
        print("状态码：", missing.status_code, "；期望 404。")
        print("本次 read_notice 执行次数：", len(calls) - before, "；期望 0。")
        print('[对照 2] client.post("/notice", json={})：路径相同，方法换成 POST。')
        print(
            "post(路径, json=字典) 提交 POST；json 是要提交的 JSON 数据，本例为空字典。"
        )
        before = len(calls)
        # client.post(path, json=数据)：发送 POST；本路径没有登记 POST，所以不调用业务函数。
        wrong_method = client.post("/notice", json={})
        print("状态码：", wrong_method.status_code, "；期望 405。")
        print("本次 read_notice 执行次数：", len(calls) - before, "；期望 0。")
        print("三次请求后业务函数累计执行次数：", len(calls), "；仍应是 1。")

    print("\n五、注意什么")
    print(
        "app.add_api_route(...) 写在服务端，建立对应规则；client.get(...) 写在客户端，使用接口。"
    )
    print(
        "/notice 是你自己起的路径；read_notice 是你自己起的函数名，两者通过登记这一行关联。"
    )
    print(
        "endpoint=read_notice 是传函数；写 read_notice() 会先执行并把字典当 endpoint。"
    )
    print("只定义函数或登记规则，都不会执行函数体；匹配的请求到来时由 FastAPI 调用。")
    print(
        "源码末尾的 main/run_logged 只负责启动演示和保存日志，理解接口时先看上面五段。"
    )
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存路由登记与请求处理的实际输出。"""
    run_logged(
        "route_demo",
        demonstrate_route,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
