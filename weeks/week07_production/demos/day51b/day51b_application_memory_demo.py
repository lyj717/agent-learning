"""Day51B：独立认识应用创建一次后，多次请求怎样访问同一份内存。

用单个计数器比较同应用换客户端、重新创建应用；不预先实现会话问答练习。
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def make_counter_app() -> FastAPI:
    """新建带独立计数器的应用；请求函数访问创建它时的同一份外层字典。"""
    app = FastAPI()
    totals = {"value": 0}
    print("  【创建应用】这次新建 totals，初值 0。")

    def add_one() -> dict[str, int]:
        """修改本应用的计数器，返回修改后的值。"""
        totals["value"] += 1
        print("  【处理请求】修改原有 totals，value =", totals["value"])
        return {"value": totals["value"]}

    app.add_api_route("/count", endpoint=add_one, methods=["POST"])
    return app


def demonstrate_memory(run_dir: Path) -> None:
    """用同一应用的两个客户端和另一份新应用核对数据归属。"""
    print("问答服务需要在多次请求之间保存历史，并按会话分开。")
    print("本例只解决前一半：数据放在哪，才能跨请求保留、又不串到另一份应用。")
    print("练习 B 再由你把计数器换成各会话的历史，并接旧问答函数。")
    print("\n一、是什么：服务端内存是应用运行期间保留的 Python 对象。")
    print("为什么：如果每次处理请求都新建记录，下一次请求就看不到上一次的记录。")
    print("场景：客户端每提交一次 POST /count，计数加一。下面全是人工教具。")
    print("\n二、先看创建和使用分别在哪发生")
    print(
        "make_counter_app()：创建 app，创建 totals 字典，登记 add_one，然后返回 app。"
    )
    print('totals = {"value": 0} 写在创建应用的函数中，每次新建应用时执行一次。')
    print('add_one() 中执行 totals["value"] += 1；没有重新创建 totals。')
    print("处理函数仍能访问创建它时的外层字典，和 Day50 的 emit 访问外层目录同类。")
    print("修改字典内容不用写 global 或 nonlocal。")
    print("返回类型 make_counter_app() -> FastAPI；add_one() -> dict[str, int]。")
    print("\n三、实际对照：注意【创建应用】和【处理请求】各出现在哪里")
    app_a = make_counter_app()
    # TestClient(app)：绑定既有应用；创建客户端这个动作没有调用 make_counter_app。
    with TestClient(app_a) as client:
        for expected in [1, 2]:
            # post(path)：提交没有请求体的 POST，本例返回 {"value": 修改后的整数}。
            response = client.post("/count")
            print(
                "同一客户端、同一 app；实际：",
                response.json(),
                "；期望 value =",
                expected,
            )
    with TestClient(app_a) as another_client:
        response = another_client.post("/count")
        print("换客户端、仍用 app_a；实际：", response.json(), "；期望 value = 3。")
    app_b = make_counter_app()
    with TestClient(app_b) as client:
        response = client.post("/count")
        print("新建 app_b；实际：", response.json(), "；期望 value = 1。")
    print("\n四、注意什么")
    print("服务端数据属于应用中的对象，换一个客户端不会自动清空它。")
    print("把字典放在每次请求的函数体内，会反复重建；放模块全局又可能被多份应用共用。")
    print("练习中要每份应用各有自己的字典，再用 session_id 区分其中的历史。")
    print("内存不会自动保存到磁盘；本例只验证顺序请求，并发与进程重启另行处理。")
    print("这里没有完整问答实现，HTTP、日志和历史的整合留给练习。")
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存本例各请求实际使用的计数状态。"""
    run_logged(
        "memory_demo",
        demonstrate_memory,
        {"transport": "testclient_in_process", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51B_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
