"""Day 32 概念 4：get_state 返回什么，怎样判断有没有旧状态。

先运行 day32_sqlite_saver_demo.py；这里复用它的单节点图，只学读检查点。
阅读顺序：main。每次运行都用全新内存数据库，因此输出可重复。
"""

from day32_sqlite_saver_demo import CONFIG, build_graph
from langgraph.checkpoint.sqlite import SqliteSaver


def main() -> None:
    """在同一个会话写入前后分别读取状态快照。"""
    print("=== 1. 这是什么 ===")
    print("检查点是图保存的某一时刻的状态；StateSnapshot 是读取结果的包装对象。")
    print("snapshot.values 才是状态字典，例如 request 和 turns；不要把两者当成一样。")

    print("\n=== 2. 为什么需要它 ===")
    print("新工单没有旧状态，旧工单已有消息和次数；本轮输入要区别处理。")
    print("先读 .values，才能根据真实保存的内容判断，而不是猜文件是否存在。")

    print("\n=== 3. 场景 ===")
    print(f"观察的会话 ID：{CONFIG['configurable']['thread_id']}")
    print("本例用新的内存数据库，先读空会话，再运行一轮，再读同一会话。")

    print("\n=== 4. 代码与真实输出 ===")
    # from_conn_string(":memory:") 为本脚本建立临时 SQLite 保存器。
    # with 中的 saver 是 SqliteSaver 实例，离开 with 后连接会关闭。
    with SqliteSaver.from_conn_string(":memory:") as saver:
        # build_graph(保存器) 来自上一份演示，返回编译好的单节点图。
        graph = build_graph(saver)

        # get_state(config) 按 thread_id 读取最新快照，返回 StateSnapshot；
        # 它只读取，不会执行 record 节点。第一次还没有保存任何状态。
        before = graph.get_state(CONFIG)
        print(f"4.1 写入前：get_state 返回 {type(before).__name__} 对象。")
        print(f"    before.values = {before.values}")
        print(f"    before is None？{before is None}")
        print(f"    bool(before.values) = {bool(before.values)}")
        print("    本例的必填状态字段还没写入：这个 thread_id 没有旧状态。")

        # invoke(本轮输入状态, config) 执行节点并让保存器写入检查点。
        print("4.2 现在调用 invoke；下面的 record 输出会来自这一步。")
        graph.invoke({"request": "查询订单", "turns": 0}, CONFIG)

        after = graph.get_state(CONFIG)
        print("4.3 再读同一 thread_id：")
        print(f"    after.values['request'] = {after.values['request']}")
        print(f"    after.values['turns'] = {after.values['turns']}")
        print(f"    bool(after.values) = {bool(after.values)}")
        print("    非空字典表示已经有旧状态；以后可以只传本轮更新。")

        again = graph.get_state(CONFIG)
        print(
            f"4.4 再读一次，turns 仍是 {again.values['turns']}，因为 get_state 不执行节点。"
        )

        other_config = {"configurable": {"thread_id": "another-session"}}
        other = graph.get_state(other_config)
        print(f"4.5 同一数据库换一个 thread_id，.values = {other.values}")

    print("\n=== 5. 注意什么 ===")
    print(
        "在本例及练习 B 的必填字段下，看 .values 是否为空；不要用 snapshot is None 判断。"
    )
    print("get_state 只读，invoke 才执行节点并写出新检查点。")
    print("练习 B 换成工单消息后也用这个判断；代码和观察仍需要你自己完成。")


if __name__ == "__main__":
    main()
