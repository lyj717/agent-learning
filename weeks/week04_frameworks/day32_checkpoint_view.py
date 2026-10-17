"""Day 32：在 PyCharm 里查看 SQLite 检查点保存的最新状态。

先运行 day32_checkpoint_demo.py；直接运行本文件即可查看，不会执行 record 节点。
"""

from pathlib import Path

from day32_checkpoint_demo import CONFIG, DB_FILE, build_demo_graph
from langgraph.checkpoint.sqlite import SqliteSaver


def main() -> None:
    """只读取固定会话的最新状态，把可理解的字段打印出来。"""
    print(f"SQLite 文件：{DB_FILE}")
    print(f"查看的 thread_id：{CONFIG['configurable']['thread_id']}")

    # Path(路径).is_file() 检查文件是否存在；没有时不打开 SQLite，以免创建空文件。
    if not Path(DB_FILE).is_file():
        print("数据库文件还不存在。先运行一次 day32_checkpoint_demo.py。")
        return

    # from_conn_string(文件路径) 打开本地保存器；with 结束时关闭连接。
    with SqliteSaver.from_conn_string(DB_FILE) as saver:
        graph = build_demo_graph(saver)
        # get_state(config) 读取这个 thread_id 最近保存的快照，不执行节点。
        # .values 是该快照里的状态字典，例如 {'request': ..., 'turns': 2}。
        snapshot = graph.get_state(CONFIG)
        if not snapshot.values:
            print("文件存在，但这个 thread_id 还没有保存的状态。")
            return

        print("数据库中这段会话的最新状态：")
        print(f"  request = {snapshot.values['request']}")
        print(f"  turns   = {snapshot.values['turns']}")
    print("这里只读取保存的值，没有调用 invoke，处理次数不会增加。")


if __name__ == "__main__":
    main()
