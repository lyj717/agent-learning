"""Day 32 整合：关闭 Python 再启动，检查点还能接上处理次数。

先顺序运行 SQL、config、invoke、SqliteSaver、StateSnapshot 五份小演示。
本文件只验证一件事：同一 SQLite 文件与 thread_id 能跨进程接续。
阅读顺序：main → VisitState → record_request → build_demo_graph。
客服请求是固定教学文字，不调用模型或真实客服系统。
"""

import sys
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

# __file__ 是脚本地址；resolve() 取绝对路径；with_name(文件名) 放到脚本旁。
# 从 PyCharm 或仓库根目录运行，都会连到同一个数据库文件。
DB_FILE = str(Path(__file__).resolve().with_name("day32_checkpoint_demo.sqlite"))
# configurable.thread_id 选这个文件中的一段会话，不是图状态字段。
CONFIG = {"configurable": {"thread_id": "day32-demo"}}


def main(continue_previous: bool) -> None:
    """第一次从零计数，或在另一个 Python 进程里接续上一轮。"""
    print("=== 1. 这是什么 ===")
    print("前面的小演示没有文件数据库；这里改用脚本旁的 .sqlite 文件。")
    print("文件在 Python 退出后仍在，因此第二次启动能找到上次保存的状态。")

    print("\n=== 2. 为什么需要它 ===")
    print("只用内存数据库，程序结束后保存的次数会消失。")
    print("文件路径选数据库；同一文件里的 thread_id 再选具体会话。")

    print("\n=== 3. 场景 ===")
    print("客服先记录订单请求；关掉程序后，仍能接着记录补充请求。")
    print(f"文件路径：{DB_FILE}")
    print(f"会话编号：{CONFIG['configurable']['thread_id']}")

    print("\n=== 4. 代码与真实输出 ===")
    # from_conn_string(文件路径) 准备 SQLite 保存器；with 中的 saver 是
    # SqliteSaver 对象。离开 with 时会关闭这次打开的数据库连接。
    with SqliteSaver.from_conn_string(DB_FILE) as saver:
        # build_demo_graph(保存器) 返回装好 checkpointer 的图，不执行节点。
        graph = build_demo_graph(saver)
        # get_state(config) 读取指定会话的最新 StateSnapshot，不执行节点。
        before = graph.get_state(CONFIG)
        if before.values:
            print(f"4.1 本次启动前保存的 turns：{before.values['turns']}")
        else:
            print("4.1 本次启动前没有旧状态：.values 是空字典。")

        if continue_previous:
            if not before.values:
                print("没有可接续的旧状态；先运行一次不带 --continue 的演示。")
                return
            new_input = {"request": "补充收货地址变更"}
            print("4.2 接续模式：只传新的 request，不重传旧 turns。")
        else:
            new_input = {"request": "查询青禾笔记本订单", "turns": 0}
            print("4.2 首次模式：显式传 turns=0，从零开始计数。")
        print(f"    invoke 第一个参数，本轮输入：{new_input}")
        print("    invoke 第二个参数是 CONFIG，指向同一个 thread_id。")

        # invoke(本轮输入, config) 执行图，返回最终状态，并由保存器写检查点。
        result = graph.invoke(new_input, CONFIG)
        print(f"4.3 invoke 返回：request={result['request']}，turns={result['turns']}")

        after = graph.get_state(CONFIG)
        print(f"4.4 再读最新检查点：turns={after.values['turns']}")

    print("\n=== 5. 注意什么 ===")
    print("第一次不带参数时会重传 turns=0；再次带 --continue 才接旧次数。")
    print("这只是已结束会话收到新请求；运行中等待人工确认的恢复留到 Day 33。")


class VisitState(TypedDict):
    """状态字典有请求文字和处理次数两个字段。"""

    request: str
    turns: int


def record_request(state: VisitState) -> dict[str, int]:
    """收到当前状态，只交回 turns 的本轮更新。"""
    print(f"    record 节点进入时 turns={state['turns']}")
    return {"turns": state["turns"] + 1}


def build_demo_graph(checkpointer: SqliteSaver) -> CompiledStateGraph:
    """沿用 Day 29 的单节点路线，并装入 SQLite 保存器。"""
    # StateGraph(状态类型) 创建建图器，TypedDict 只说明字段类型。
    builder = StateGraph(VisitState)
    # add_node(节点名, 函数) 注册节点；add_edge(起点, 终点) 连接固定路线。
    builder.add_node("record", record_request)
    builder.add_edge(START, "record")
    builder.add_edge("record", END)
    # compile(checkpointer=保存器对象) 返回可执行图，此时节点还没运行。
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    # sys.argv 是命令行参数列表；带 --continue 时才选择接续模式。
    main(continue_previous="--continue" in sys.argv)
