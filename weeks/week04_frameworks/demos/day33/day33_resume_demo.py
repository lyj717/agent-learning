"""Day 33 知识点：Command 的 resume 参数怎样把回答送回暂停处。

这份自带最小暂停环境，不导入 interrupt 演示，也不延续它的案例。
先读 main 中的三种 Command，再读 deliver_answer 中标有「本课关键调用」的代码。
这里不讲节点重跑、动作执行或跨进程操作。
"""

from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class AnswerState(TypedDict):
    """教具状态：保存暂停处收到的回答，方便核对值与类型。"""

    # object 表示这里允许观察文字、布尔值、字典等不同类型的回答。
    answer: object


def main() -> None:
    """分别把文字、布尔值和字典作为回答送回暂停处。"""
    print("=== 1. 这是什么 ===")
    print("resume 是 Command 的一个参数，写法是 Command(resume=回答)。")
    print("导入：from langgraph.types import Command")
    print("Command(...) 创建一个命令对象；此时还没有运行图。")

    print("\n=== 2. 为什么需要它 ===")
    print("外部程序已经得到人的回答，需要明确把它送回原会话里等待的 interrupt。")

    print("\n=== 3. 用法、参数与结果 ===")
    print("第一步：command = Command(resume=回答)")
    print("第二步：final = graph.invoke(command, config)")
    print("resume=... 必须写参数名；单个等待点可以接收文字、布尔值、普通字典等。")
    print("config 沿用暂停时的 thread_id；保存器也要能读到原来那份检查点。")
    print("resume 里的值成为节点内 interrupt(...) 的返回值。")
    print("本例没有配置回答校验，下面对照传入值与实际收到的类型。")
    print("若暂停处传了带类型的 response_schema，回答就需要通过它的校验。")

    print("\n=== 4. 三种回答，各自从全新环境开始 ===")
    text_command = Command(resume="王小林")
    print(
        f"4.1 命令对象类型={type(text_command).__name__}，resume={text_command.resume}"
    )
    deliver_answer("姓名文字", text_command)

    bool_command = Command(resume=False)
    print(f"4.2 命令保存的 resume={bool_command.resume}；False 也是有效回答。")
    deliver_answer("布尔回答", bool_command)

    dict_command = Command(resume={"name": "林青", "contact": "站内消息"})
    print(f"4.3 命令保存的 resume={dict_command.resume}")
    deliver_answer("多字段回答", dict_command)

    print("\n=== 5. 注意什么 ===")
    print(
        "本例用 Command 的 resume 参数装回答，再由 graph.invoke(command, config) 交给图。"
    )
    print("回答不必叫 allow，也不必是 True；它的含义由你的节点代码决定。")
    print("恢复完成后，invoke 仍按平时的规则返回图状态；本例用 answer 字段观察回答。")


def deliver_answer(title: str, command: Command) -> None:
    """预备一个暂停点，只观察 resume 送回的回答。"""

    def receive_answer(_state: AnswerState) -> dict:
        """提供测试用的等待点，收到什么就原样存进 answer。"""
        answer = interrupt("请提供这组例子的回答")
        return {"answer": answer}

    # 下方是已学过的单节点图和内存保存器，仅用来预备一个等待回答的位置。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        builder = StateGraph(AnswerState)
        builder.add_node("receive", receive_answer)
        builder.add_edge(START, "receive")
        builder.add_edge("receive", END)
        graph = builder.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": "resume-value-example"}}
        graph.invoke({"answer": None}, config)

        # 本课关键调用：第一项是装有回答的 Command，第二项选择原会话。
        final = graph.invoke(command, config)

    print(
        f"    {title}：节点实际收到 {final['answer']}，"
        f"类型={type(final['answer']).__name__}"
    )


if __name__ == "__main__":
    main()
