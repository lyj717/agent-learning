"""Day 32 概念 2：config 是会话选择信息，不是图状态。

本文件只用普通 Python 字典拆开 config 的形状；下一份演示才运行 LangGraph。
阅读顺序：main。这里的 saved_by_thread 是教学类比，不是框架内部实现。
"""


def main() -> None:
    """看同一份输入与两个不同会话编号分别是什么。"""
    print("=== 1. 这是什么 ===")
    print("state 是节点要处理的内容，例如请求和处理次数。")
    print("config 是本次运行的附加配置；LangGraph 从中读 thread_id 来选会话。")
    print("它们是两份不同的字典，不要把 thread_id 塞进 state 的 turns 字段里。")

    print("\n=== 2. 为什么需要它 ===")
    print("同一个数据库文件可以存多段会话；同一文件不等于同一会话。")
    print("thread_id 就像工单编号：选对编号，后面才能找对旧记录。")

    print("\n=== 3. 场景 ===")
    state = {"request": "查询订单", "turns": 0}
    config_a = {"configurable": {"thread_id": "ticket-a"}}
    config_b = {"configurable": {"thread_id": "ticket-b"}}
    print(f"给节点的 state：{state}")
    print(f"工单 A 的 config：{config_a}")
    print(f"工单 B 的 config：{config_b}")

    print("\n=== 4. 拆开字典看 ===")
    print("最外层键 configurable 是 LangGraph 约定的运行配置位置。")
    print("里面的 thread_id 是键，ticket-a / ticket-b 是我们自己选的两个编号。")
    print(f"先取内层字典 config_a['configurable']：{config_a['configurable']}")
    print(
        "再取会话编号 config_a['configurable']['thread_id']："
        f"{config_a['configurable']['thread_id']}"
    )
    print(f"同样取工单 B 的编号：{config_b['configurable']['thread_id']}")

    # 下面只是普通 Python 字典，用来显示编号如何选到不同的记录。
    # 它不是 LangGraph 的数据库表，也不是 SqliteSaver 的内部代码。
    saved_by_thread = {"ticket-a": "A 的旧记录", "ticket-b": "B 的旧记录"}
    print("只用普通 Python 做一次类比：")
    print(
        f"  用 A 的编号选到：{saved_by_thread[config_a['configurable']['thread_id']]}"
    )
    print(
        f"  用 B 的编号选到：{saved_by_thread[config_b['configurable']['thread_id']]}"
    )

    print("\n=== 5. 注意什么 ===")
    print("现在只看懂 config 的形状；还没有运行图或真的保存检查点。")
    print("下一份演示会把负责存取旧状态的对象接进图，再看这个编号怎样起作用。")
    print("之后调用图时，invoke(本轮 state 输入, config) 分别把两份字典传进去。")
    print("换 thread_id 会选另一段会话；消息自身的 ID 和工具点单 ID 是别的标识。")


if __name__ == "__main__":
    main()
