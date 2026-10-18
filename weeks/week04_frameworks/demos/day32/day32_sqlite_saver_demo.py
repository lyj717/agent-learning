"""Day 32 概念 3：SqliteSaver 是图的检查点保存器。

先运行 day32_config_demo.py 和 day32_invoke_demo.py；
本文件对照未安装和已安装保存器时的两轮调用。
阅读顺序：main → RequestState → record_request → build_graph。
这里的 SQLite 数据库在内存中；跨进程文件保存留到最后的整合演示。
"""

from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

# 上一份 config 演示讲过：thread_id 从同一数据库中选一段会话。
CONFIG = {"configurable": {"thread_id": "saver-demo"}}


def main() -> None:
    """对照没装与装了保存器时同一会话的两轮。"""
    print("=== 1. 这是什么 ===")
    print("检查点是图在运行中保存的一份状态快照，例如 request 和 turns。")
    print("checkpointer 是负责保存、取回快照的对象；SqliteSaver 是它的 SQLite 版本。")
    print("SQLite 是数据库；SqliteSaver 是用它保存、读取检查点的 Python 对象。")
    print("数据库的数据可只放在内存，也可存进一个 .sqlite 文件。")

    print("\n=== 2. 为什么需要它 ===")
    print("不装保存器，两次独立的图调用不能靠 thread_id 找回上一轮的 turns。")
    print("先看同一 Python 进程里的两次调用；跨进程文件保存留到最后的演示。")

    print("\n=== 3. 场景 ===")
    print("客服收到第一条请求，随后收到同一会话的一条补充请求。")
    print(f"两次都使用这份 config：{CONFIG}")

    print("\n=== 4. 代码与真实输出 ===")
    print("4.1 先不装保存器：compile(checkpointer=None)。")
    print("    第二次仍要自己传 turns=0；同一 config 不会自动接上第一次的 1。")
    no_saver_graph = build_graph(None)
    no_saver_first = no_saver_graph.invoke({"request": "查询订单", "turns": 0}, CONFIG)
    no_saver_second = no_saver_graph.invoke(
        {"request": "补充收货地址", "turns": 0}, CONFIG
    )
    print(
        f"    两次返回的 turns：{no_saver_first['turns']}、{no_saver_second['turns']}"
    )

    print("4.2 from_conn_string(':memory:') 用临时 SQLite 数据库准备保存器。")
    print("    进入 with 后，as saver 得到 SqliteSaver 对象；离开 with 会关闭连接。")
    # from_conn_string(连接位置) 是上下文管理器；:memory: 表示内存数据库。
    # with 中的 saver 才是 SqliteSaver 实例，不是文件路径字符串。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        print(f"    saver 的实际类型：{type(saver).__name__}")
        # build_graph(保存器对象) 返回编译好的图；这里还没执行 record_request。
        graph = build_graph(saver)
        print("4.3 build_graph 内调用 compile(checkpointer=saver)。")
        print("    checkpointer 是参数名；saver 是刚得到的 SqliteSaver 对象。")
        print(f"    返回 {type(graph).__name__}；节点尚未执行。")

        first_input = {"request": "查询订单", "turns": 0}
        print(f"4.4 第一次 invoke(输入, config)：输入={first_input}")
        # invoke(本轮状态输入, 运行配置) 执行图，返回本轮最终状态字典。
        first = graph.invoke(first_input, CONFIG)
        print(f"    返回：request={first['request']}，turns={first['turns']}")

        second_input = {"request": "补充收货地址"}
        print(f"4.5 第二次 invoke(输入, 同一 config)：输入={second_input}")
        print("    没有再传 turns；图从这段会话刚保存的检查点保留旧 turns。")
        second = graph.invoke(second_input, CONFIG)
        print(f"    返回：request={second['request']}，turns={second['turns']}")

    print("\n=== 5. 注意什么 ===")
    print("compile(checkpointer=...) 只把保存器装进图；节点在 invoke 时才执行。")
    print("这里用 :memory:，退出程序就丢；给 from_conn_string 文件路径才可跨进程保存。")
    print("此例没有调用 get_state；下一份演示单独看怎样读取检查点。")


class RequestState(TypedDict):
    """状态字段说明；运行时状态仍是普通的 Python 字典。"""

    request: str
    turns: int


def record_request(state: RequestState) -> dict[str, int]:
    """读当前次数，只返回需要改动的 turns。"""
    print(f"    record 节点真的执行了：进入时 turns={state['turns']}")
    return {"turns": state["turns"] + 1}


def build_graph(checkpointer: SqliteSaver | None) -> CompiledStateGraph:
    """把 Day 29 的单节点路线编译成图，可选择是否装保存器。"""
    # StateGraph(状态类型) 创建建图器；TypedDict 只说明字段类型。
    builder = StateGraph(RequestState)
    # add_node(节点名, 函数) 登记节点；add_edge(起点, 终点) 连接路线。
    builder.add_node("record", record_request)
    builder.add_edge(START, "record")
    builder.add_edge("record", END)
    # compile(checkpointer=保存器实例或 None) 返回可执行图，不在这里执行节点。
    # 左边的 checkpointer= 是库规定的参数名，右边是本函数收到的对象。
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    main()
