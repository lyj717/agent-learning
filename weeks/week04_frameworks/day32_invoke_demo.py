"""Day 32 前置概念：graph.invoke 的两个主要参数和返回值。

先运行 day32_config_demo.py，再运行本文件，之后才看 SqliteSaver 演示。
阅读顺序：main → CountState → count_request → build_graph。
本文件不装检查点保存器，不连接数据库，也不调用模型。
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


def main() -> None:
    """比较不传 config 与传同一 config 时的三次调用。"""
    print("=== 1. 这是什么 ===")
    print("invoke 是已编译图对象的方法：graph.invoke(...) 让图运行一次。")
    print("第一个参数 input 是这一次交给图的内容；本例是包含 request、turns 的字典。")
    print("第二个参数 config 是这次运行的附加配置，可省略；它不是节点处理的内容。")
    print("本例按默认方式运行到 END，返回最终状态字典。")

    print("\n=== 2. 为什么需要它 ===")
    print("build_graph 只是把节点和路线搭好；真正运行节点要调用 graph.invoke。")
    print("调用一次就是一次图运行，不是直接调用 count_request 函数。")

    print("\n=== 3. 场景 ===")
    print("客服每处理一条请求，节点把 turns 加 1。先不安装任何保存器。")

    print("\n=== 4. 代码与真实输出 ===")
    graph = build_graph()
    print(f"4.1 build_graph() 返回 {type(graph).__name__}；上面还没有节点输出。")

    first_input = {"request": "查询订单", "turns": 0}
    print(f"4.2 第一次：graph.invoke(input)，input={first_input}")
    # invoke(input, config=None) 执行这一次图；这里省略可选的 config。
    # 默认返回最终状态字典；节点在调用时才真正运行。
    first_result = graph.invoke(first_input)
    print(f"    返回值：{first_result}")
    print("    节点只返回 turns 更新；图的返回值仍包含 request 和 turns。")

    config = {"configurable": {"thread_id": "ticket-a"}}
    second_input = {"request": "补充收货地址", "turns": 0}
    print(f"4.3 第二次：graph.invoke(input, config)，input={second_input}")
    print(f"    config={config}")
    # 第一个实参是本轮状态输入；第二个实参是本轮运行配置。
    second_result = graph.invoke(second_input, config)
    print(f"    返回值：{second_result}")

    third_input = {"request": "再问发票", "turns": 0}
    print(f"4.4 第三次：沿用同一 config，但输入仍传 turns=0：{third_input}")
    third_result = graph.invoke(third_input, config)
    print(f"    返回值：{third_result}")

    print("\n=== 5. 注意什么 ===")
    print("三次节点进入时都是 turns=0，返回都是 1，因为本文件没装保存器。")
    print("只传相同 thread_id 不会自动产生记忆；下一份演示再装 SqliteSaver 做对照。")
    print("这里讲的是图的 invoke；以后看到 model.invoke，要看调用者是模型还是图。")


class CountState(TypedDict):
    """图状态的两个字段：请求文字与处理次数。"""

    request: str
    turns: int


def count_request(state: CountState) -> dict[str, int]:
    """打印节点收到的次数，再只返回更新后的 turns。"""
    print(f"    count 节点运行：收到 turns={state['turns']}")
    return {"turns": state["turns"] + 1}


def build_graph() -> CompiledStateGraph:
    """沿用 Day 29 的固定路线，搭好一个未安装保存器的图。"""
    # StateGraph(状态类型) 创建建图器；类型只描述状态字段。
    builder = StateGraph(CountState)
    # add_node(名字, 函数) 登记节点；add_edge(起点, 终点) 连接路线。
    builder.add_node("count", count_request)
    builder.add_edge(START, "count")
    builder.add_edge("count", END)
    # compile() 返回可执行图，但这里尚未执行节点。
    return builder.compile()


if __name__ == "__main__":
    main()
