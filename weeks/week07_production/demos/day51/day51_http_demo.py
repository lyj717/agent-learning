"""Day51A：先认识 HTTP 请求与响应的结构，为后续服务入口准备。

这里只构造人工报文，不发送网络请求；报文中的通知和响应均为 AI 教具。
"""

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_http(run_dir: Path) -> None:
    """逐项查看人工请求和响应，不把构造报文冒充服务已经处理请求。"""
    print("Week07 最终要把问答做成服务；先看服务收到什么、客户端拿回什么。")
    print("本演示只负责 HTTP 报文结构；后续路由演示才让 FastAPI 处理请求。")
    print("\n一、是什么：HTTP 是客户端与服务端交换请求和响应的一套约定。")
    print("HTTP 是通信规则的名字；Python 代码通过具体的客户端库来构造或发送请求。")
    print("本文件用的 httpx 是一个 Python 库，所以写 import httpx。")
    print("httpx.Request(...) 构造请求对象；httpx.get(完整地址) 才会发起 GET 请求。")
    print(
        "本例只做前一种；下一份演示用 TestClient(app).get(路径) 在本地提交给 FastAPI。"
    )
    print("你以前请求模型 API 时是客户端；这周还要写服务端，接收别人发来的请求。")
    print(
        "为什么：另一个进程不能直接拿到你的 Python 函数，需要约定访问地址和数据格式。"
    )
    print("场景：客户端提交读者名字，服务返回一条通知。下面全是人工构造的报文。")
    print("\n二、请求包括：方法、地址、请求头、可选的请求体。")
    print("方法 GET 通常用于读取，POST 用于提交数据；具体行为由服务的接口约定。")
    # Request(method, url, json=字典)：构造请求对象；这一行不会发送请求。
    request = httpx.Request(
        "POST",
        "http://example.invalid/notices",
        json={"reader": "小林"},
    )
    print("方法 request.method：", request.method)
    print("完整地址 request.url：", request.url)
    print("路径 request.url.path：", request.url.path)
    print("内容类型请求头：", request.headers["content-type"])
    print("请求体原始字节：", request.content)
    print("按 UTF-8 解码后的请求体：", request.content.decode("utf-8"))
    print("reader 是 JSON 字段；POST 是 HTTP 方法；/notices 是路径，它们各有用途。")
    print("\n三、响应包括：状态码、响应头、可选的响应体。")
    # Response(status_code, json=字典, request=请求)：构造人工响应，并关联它对应的请求。
    response = httpx.Response(
        200, json={"notice": "小林，请在闭馆前归还图书。"}, request=request
    )
    print("状态码 response.status_code：", response.status_code)
    print("响应内容类型：", response.headers["content-type"])
    print("响应体文本 response.text：", response.text)
    # response.json()：把 JSON 响应体解析成 Python 对象；这里返回 dict，不会再发请求。
    body = response.json()
    print("解析后类型：", type(body).__name__)
    print("解析后 notice 字段：", body["notice"])
    print("\n四、注意什么")
    print("200 表示 HTTP 请求成功；404 是路径/资源未找到；405 是该路径不接受这种方法。")
    print("422 在本课表示 FastAPI 输入校验未通过；业务主动拒绝时会另用 400。")
    print(
        "状态码是响应外层信息；JSON 是响应体，JSON 中出现 detail 并不自动变成错误状态码。"
    )
    print("本演示没有服务器，也没有真正发送请求；example.invalid 只是示意地址。")
    print("下一份用 TestClient 在进程内把请求交给 FastAPI；真实端口启动留到 Day51B。")
    print("本轮说明和报文已保存在：", run_dir)


def main() -> None:
    """使用既有留证工具保存本次教学输出。"""
    run_logged(
        "http_demo",
        demonstrate_http,
        {"transport": "constructed_messages", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
