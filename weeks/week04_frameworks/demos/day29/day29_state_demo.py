"""Day 29：一个节点怎样读取状态、交回更新，再由图合并。

阅读顺序：main → KeywordState → trim_keyword → build_keyword_graph。
直接运行即可；完全离线，关键词和轨迹均为 AI 编写的教学数据。
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


def main() -> None:
    """先讲问题，再运行一个节点，最后对照更新前后的字段。"""
    print("=== 1. 这是什么 ===")
    print("状态是本次任务共用的一份数据；今天仍用普通字典装它。")
    print("节点是处理这份数据的函数；边规定处理完以后去哪里。")
    print("LangGraph 按我们画好的连接调用函数，并把函数返回的更新合入状态。")

    print("\n=== 2. 为什么需要它 ===")
    print("Day 27 用循环里的变量保存 messages、trace，用 if/return 决定继续或结束。")
    print("流程变多以后，可以把共享数据放入状态，把每段处理放进节点。")
    print("今天先拆出最小的一步；这个小任务用普通函数同样能完成。")

    print("\n=== 3. 场景与输入 ===")
    print("检索前，去掉关键词两端的空格；任务问题要保留。")
    print("图的路线：START → trim → END。今天没有模型、工具点单或真实检索。")
    initial: KeywordState = {
        "question": "查找青禾笔记本的资料",
        "keyword": "  青禾笔记本  ",
        "trace": ["收到问题"],
    }
    print(f"问题：{initial['question']}")
    print(f"关键词：{initial['keyword']!r}")
    print(f"原轨迹：{initial['trace']}")

    print("\n=== 4. 对照源码运行 ===")
    print("KeywordState 用 TypedDict 列出键名与值类型；运行时 state 仍是 dict。")
    print("类型注解不代替输入校验。本例只传入上面准备好的合法字典。")
    print("先注册函数、连接边，再 compile；此时还没有执行 trim_keyword。")
    graph = build_keyword_graph()
    print("图已编译。现在 invoke(initial)，从 START 开始执行：")
    # invoke(初始状态)：执行编译后的图，本例返回到达 END 时的状态字典。
    result = graph.invoke(initial)
    print(f"最终问题：{result['question']}（节点未返回这个键，原值仍保留）")
    print(f"最终关键词：{result['keyword']!r}")
    print(f"最终轨迹：{result['trace']}")
    print(f"调用者原来的关键词仍是：{initial['keyword']!r}")

    print("\n=== 5. 注意什么 ===")
    print("本例没有指定合并函数：返回哪个键，就用新值替换那个键；没返回的保留。")
    print("因此 trace 只剩『整理关键词』。列表也会替换，不会自动追加。")
    print("若要保留旧轨迹，本日练习由节点返回包含旧项与新项的完整列表。")
    print("请返回更新字典；不要用原地改 state 或 append 的副作用传递结果。")
    print("这里原输入未变，是因为节点创建了新值；不要理解成框架会深拷贝一切。")
    print("节点里没有模型请求，框架也不会自动替你调用模型。")
    print("下一课才接条件边；消息专用合并规则另学，不能一概当作列表相加。")


# TypedDict（从 typing 导入）：声明这份字典有哪些键、各键的值是什么类型。
# 这里三个键都由 main 提供；它不会自动补默认值，也不会运行时验证值类型。
class KeywordState(TypedDict):
    question: str
    keyword: str
    trace: list[str]


def trim_keyword(state: KeywordState) -> dict:
    """读取关键词，返回要替换的两个字段，不改动传入的字典。"""
    print(f"  trim 节点读到关键词：{state['keyword']!r}")
    update = {
        "keyword": state["keyword"].strip(),
        "trace": ["整理关键词"],
    }
    print(f"  节点返回更新：关键词 {update['keyword']!r}，轨迹 {update['trace']}")
    return update


def build_keyword_graph() -> CompiledStateGraph:
    """定义一条固定路线，返回可以 invoke 的已编译图。"""
    # StateGraph(状态类型)：创建图的构建器；KeywordState 是类型，不是输入数据。
    builder = StateGraph(KeywordState)
    # add_node(节点名, 函数)：注册函数本身；trim_keyword 后面不加调用括号。
    builder.add_node("trim", trim_keyword)
    # add_edge(起点, 终点)：连接执行顺序；START、END 是库提供的入口、终点标记。
    builder.add_edge(START, "trim")
    builder.add_edge("trim", END)
    # compile()：检查图的连接并生成执行对象；CompiledStateGraph 是其返回类型。
    return builder.compile()


if __name__ == "__main__":
    main()
