"""Day 35 答疑留档：TypedDict 子类型为什么也有父类型的字段。

只用普通 Python 字典，不运行 LangGraph，不创建数据库，也不实现练习函数。
当前 support 为了便于查阅，已改成直接列出全部字段；此演示仍可用于认识继承写法。
"""

from typing import TypedDict


class AgentState(TypedDict):
    """缩小的旧状态：声明停止原因与草稿两个字段。"""

    stop_reason: str | None
    answer: str | None


class QuoteState(AgentState):
    """沿用 AgentState 的字段，再新增 approved。"""

    approved: bool


def main() -> None:
    """用完整的普通字典证明子类型包含旧字段，并说明声明与赋值的区别。"""
    print("=== 1. 这是什么 ===")
    print("class QuoteState(AgentState) 中的括号表示继承：")
    print("QuoteState 保留 AgentState 的字段定义，再增加自己写出的字段。")
    print("TypedDict 用来描述字典的字段和类型；运行时数据仍是普通 dict。")

    print("\n=== 2. 为什么需要 ===")
    print("扩展旧状态时，可以保留旧字段，不必把所有字段重新写一遍。")
    print("所以只看 QuoteState 类里面新写的几行，不是它的完整字段列表。")

    print("\n=== 3. 本例的完整字段 ===")
    print("AgentState 提供 stop_reason、answer；QuoteState 新增 approved。")
    print("因此 QuoteState 描述的字典同时包含这三个字段。")

    print("\n=== 4. 读取继承字段 ===")
    # 类型标注描述这份字典；右侧的字典才真正提供字段值。
    state: QuoteState = {
        "stop_reason": "final_answer",
        "answer": "报价草稿：88 元。",
        "approved": False,
    }
    print(f"state['stop_reason'] = {state['stop_reason']!r}；期望 'final_answer'")
    print(f"state['answer'] = {state['answer']!r}；来自父类型声明的字段")
    print(f"state['approved'] = {state['approved']}；来自子类型新增的字段")

    print("\n=== 5. 注意什么 ===")
    print("继承保留字段定义，不会自动给字段填值；值仍由初始输入或后续更新提供。")
    print("继承是一种复用字段的写法；当前 support 为了方便查阅，已直接列出全部字段。")
    print("模型交回部分更新，图应用更新后，路由收到的 state 才包含更新后的值。")


if __name__ == "__main__":
    main()
