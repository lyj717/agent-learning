"""Day 33 可选知识点：response_schema 什么时候只是说明，什么时候会校验。

这份只比较两种 schema 写法对 resume 回答的影响，不涉及审批流程。
先读 AnswerShape 与 main；show_case 中的单节点图只为提供真实的暂停环境。
"""

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import ValidationError
from typing_extensions import TypedDict


class AnswerShape(TypedDict):
    """期望收到的回答字典：包含一个布尔字段 approved。"""

    # 这个类型定义传给 response_schema 时，框架会用它校验回答。
    approved: bool


class DemoState(TypedDict):
    """教具状态：用 answer 观察校验通过后实际收到的值。"""

    answer: object


def main() -> None:
    """对照普通格式字典、类型定义以及正确和错误回答。"""
    print("=== 1. 这是什么 ===")
    print("response_schema 是 interrupt 的可选参数；不同传法的校验行为不同。")
    print("普通 JSON Schema 字典：框架公开格式说明，但不据此校验回答。")
    print("带类型的定义：框架会检查回答能否按这个定义解析。")

    print("\n=== 2. 为什么需要分清 ===")
    print("写了格式说明，不一定就阻止错误回答；要确认自己启用了哪种行为。")

    print("\n=== 3. 本例用到的名字 ===")
    print("from typing_extensions import TypedDict：作用与已学的字典类型说明相似。")
    print("AnswerShape 定义 approved: bool；传入 response_schema 时才用于回答校验。")
    print("from pydantic import ValidationError：回答未通过校验时抛出的异常类型。")
    print("本例在外层调用 graph.invoke 时捕获它，节点里的 interrupt 不包 try/except。")

    print("\n=== 4. 三组真实对照 ===")
    show_case("4.1 普通格式字典", {"type": "boolean"}, "随便写的文字")
    show_case("4.2 类型定义 + 错误回答", AnswerShape, {"approved": "随便写的文字"})
    show_case("4.3 类型定义 + 正确回答", AnswerShape, {"approved": True})

    print("\n=== 5. 注意什么 ===")
    print("Command(resume=...) 创建命令时不会完成这项校验；图恢复时才检查。")
    print("通过校验才会把回答交给节点后续代码；部分值可能按类型规则自动转换。")
    print("本课基础练习没有设置 response_schema，先完成原练习即可。")


def show_case(title: str, schema: dict | type, response: object) -> None:
    """为一组 schema 与回答创建独立环境，并打印接受或校验失败。"""

    def receive_answer(_state: DemoState) -> dict:
        """在同一处配置回答格式，并接收恢复时送回的值。"""
        answer = interrupt("请提供回答", response_schema=schema)
        return {"answer": answer}

    # 已学过的支持环境：每组一个新内存数据库、单节点图和会话。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        builder = StateGraph(DemoState)
        builder.add_node("receive", receive_answer)
        builder.add_edge(START, "receive")
        builder.add_edge("receive", END)
        graph = builder.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": "schema-example"}}
        graph.invoke({"answer": None}, config)

        print(f"{title}：resume={response}")
        try:
            final = graph.invoke(Command(resume=response), config)
        except ValidationError:
            print("    结果：ValidationError，未把错误回答交给后续代码。")
        else:
            print(f"    结果：接受，节点实际收到 {final['answer']}")


if __name__ == "__main__":
    main()
