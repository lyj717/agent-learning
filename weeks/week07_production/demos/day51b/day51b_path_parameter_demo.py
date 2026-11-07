"""Day51B：独立认识 URL 中的一段文字怎样成为处理函数的参数。

本例只回显图书编号，给练习中的“按会话编号读取历史”准备路径参数知识。
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_path(run_dir: Path) -> None:
    """对照两条带编号的请求与没有编号的请求，显示框架交给函数的值。"""
    print("Week07 要让问答服务按会话编号读取各自的历史。")
    print("本例先只认识路径参数：客户端把编号放进 URL，FastAPI 把它交给函数。")
    print("练习 B 会把本例的 book_id 换成 session_id；本例不保存历史、不调用模型。")
    print("\n一、是什么：路径参数是 URL 路径里可以变化的一段内容。")
    print("为什么：要访问不同图书，不必为每个编号分别登记一个函数。")
    print("场景：GET /books/B-12 和 GET /books/C-9，都由同一个函数处理。")
    print("\n二、服务端怎样登记、函数接到什么")
    print('app.add_api_route("/books/{book_id}", endpoint=read_book, methods=["GET"])')
    print("这里的 {book_id} 表示占位位置，book_id 是占位名称，不是固定文字。")
    print("def read_book(book_id: str) -> dict[str, str]: ...")
    print("占位名称和函数参数名相同；FastAPI 从路径取出字符串，作为 book_id 传入。")
    # FastAPI()：创建本例应用，不需要先运行其他演示。
    app = FastAPI()

    def read_book(book_id: str) -> dict[str, str]:
        """接收框架从路径解析的编号，原样回显。"""
        print("  【函数体执行】book_id =", repr(book_id))
        return {"book_id": book_id}

    # add_api_route：path 里的 {book_id} 对应处理函数的同名参数。
    app.add_api_route("/books/{book_id}", endpoint=read_book, methods=["GET"])
    print("\n三、客户端具体怎么请求")
    print('response = client.get("/books/B-12")；客户端写实际编号，不写占位模板。')
    # TestClient(app)：沿用 Day51A 的本地发送器，在进程内交给这个应用处理。
    with TestClient(app) as client:
        for path in ["/books/B-12", "/books/C-9", "/books"]:
            print("\n发送 GET", path)
            response = client.get(path)
            print("状态码：", response.status_code)
            # json()：把已收到的响应正文解析成字典，不再次发送请求。
            print("响应正文：", response.json())
    print("\n四、注意什么")
    print("前两次应为 200，分别接到 B-12、C-9；/books 缺少编号这一段，应为 404。")
    print("参数来自路径；本例没有请求体，也不用额外提交一个 book_id JSON 字段。")
    print("路径匹配只说明拿到了编号；本例是回显教具，没有查询图书是否真的存在。")
    print("规则通过 add_api_route 登记；普通函数仍由 FastAPI 在匹配请求后调用。")
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存人工路径参数实验的输出。"""
    run_logged(
        "path_demo",
        demonstrate_path,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51B_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
