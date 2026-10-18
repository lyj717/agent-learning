"""Day 33 知识点：interrupt 的作用、参数、暂停输出和返回值。

这份只研究 interrupt，不连接审批业务，也不导入其他演示。
先读 main 的接口说明与三组输入，再读 show_pause 中标有「本课关键调用」的一行。
末尾的单节点图只复用 Day 29/32 的接线和内存保存器，供 interrupt 运行。
"""

from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class DemoState(TypedDict):
    """教具的最小状态；answer 仅用于观察暂停后有没有普通返回值。"""

    # object 表示本教具的回答可能是文字、布尔值或字典等类型。
    answer: object


def main() -> None:
    """只改变 interrupt 的参数，对照它向调用方交出的内容。"""
    print("=== 1. 这是什么 ===")
    print("interrupt 是从 langgraph.types 导入的函数，用在图的节点内部。")
    print("作用：暂停本次图运行，并把你传入的信息交给调用图的程序。")

    print("\n=== 2. 为什么需要它 ===")
    print("节点缺少一项由人提供的信息时，可以先提出请求，而不继续执行后面的代码。")

    print("\n=== 3. 用法与参数 ===")
    print("导入：from langgraph.types import interrupt")
    print("签名：interrupt(value, *, response_schema=None)")
    print("value：必填，要交给外部的信息；可以是文字、数字、布尔值、列表或普通字典。")
    print("这些内容要能用 JSON 表达；不要传函数、数据库连接等对象。")
    print("response_schema：可选，默认 None，描述期望回答的格式。")
    print(
        "星号表示 response_schema 只能写成 response_schema=...，不能当第二个位置参数。"
    )
    print(
        "本课练习只需 value；第三组传入普通 JSON Schema 字典，只公开格式，不自动校验回答。"
    )

    print("\n=== 4. 参数改变后，暂停输出怎样变 ===")
    show_pause("4.1 value 是字符串", "请补充订单号")
    show_pause(
        "4.2 value 是字典",
        {"question": "缺少哪项资料？", "choices": ["订单号", "购买日期"]},
    )
    # 这是 JSON Schema 字典：用 {"type": "boolean"} 描述希望收到布尔回答。
    # 框架会公开这份字典；仅传字典不会自动校验回答，本例也不恢复图。
    show_pause(
        "4.3 额外传 response_schema",
        "需要加急吗？",
        response_schema={"type": "boolean"},
    )

    print("\n=== 5. 返回值与使用边界 ===")
    print("首次走到 interrupt：先暂停，不会立刻给 answer 赋一个普通返回值。")
    print("图调用方从 result['__interrupt__'][0].value 读取你给出的 value。")
    print("将来外部补回回答时，那个回答才成为 interrupt(...) 的返回值。")
    print("运行条件：在节点内调用，图已安装 checkpointer，config 中有 thread_id。")
    print("本文件只看暂停接口；不读取 snapshot.next，不执行审批或外部动作。")


def show_pause(
    title: str, value: object, *, response_schema: dict | None = None
) -> None:
    """为一组 interrupt 参数提供运行环境，并打印它的暂停输出。"""

    def pause_node(_state: DemoState) -> dict:
        """只调用一次 interrupt；首次暂停时 return 还不会执行。"""
        # 本课关键调用：value 是给外部的内容，response_schema 是可选格式说明。
        answer = interrupt(value, response_schema=response_schema)
        print("    interrupt 后面的代码已执行。")
        return {"answer": answer}

    # 以下仅为已学过的运行环境：单节点图 + Day 32 的内存 SQLite 保存器。
    # 每组新建数据库和会话，因此本文件重跑时无需清理任何文件。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        builder = StateGraph(DemoState)
        builder.add_node("pause", pause_node)
        builder.add_edge(START, "pause")
        builder.add_edge("pause", END)
        graph = builder.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": "interrupt-parameter-example"}}
        result = graph.invoke({"answer": None}, config)

    pending = result["__interrupt__"][0]
    print(title)
    print(f"    传入的 value = {value}")
    print(f"    暂停输出的 .value = {pending.value}")
    print(f"    暂停输出的 .response_schema = {pending.response_schema}")
    print(f"    状态里的 answer = {result['answer']}，仍未收到回答。")


if __name__ == "__main__":
    main()
