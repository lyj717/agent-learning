"""Day 18 练习数据准备脚本，不是数据库文件。

seed_db() 会在同目录生成 day18_orders.sqlite，删除并重建 orders 表，
插入六条固定的假订单。演示和练习会自动调用它；重复运行会覆盖表中旧数据。
生成的 .sqlite 文件被 .gitignore 忽略，不是交付物。
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("day18_orders.sqlite")

ORDERS = [
    (1, "杭州", 120.0, "paid"),
    (2, "杭州", 80.0, "paid"),
    (3, "杭州", 50.0, "cancelled"),
    (4, "上海", 200.0, "paid"),
    (5, "上海", 30.0, "paid"),
    (6, "北京", 90.0, "paid"),
]


def seed_db() -> Path:
    """重建练习库；每次运行都得到相同的六条订单。"""
    # sqlite3.connect(路径)：连接数据库文件；不存在时创建。
    connection = sqlite3.connect(DB_PATH)
    # 这段只是每次把练习数据恢复到同一个起点，不是今天的查询练习。
    connection.execute("DROP TABLE IF EXISTS orders")
    connection.execute(
        "CREATE TABLE orders ("
        "id INTEGER PRIMARY KEY, city TEXT NOT NULL, "
        "amount REAL NOT NULL, status TEXT NOT NULL)"
    )
    for order in ORDERS:
        connection.execute(
            "INSERT INTO orders (id, city, amount, status) VALUES (?, ?, ?, ?)",
            order,
        )
    # commit()：把插入写进文件；close()：关闭文件连接。
    connection.commit()
    connection.close()
    return DB_PATH


if __name__ == "__main__":
    print(f"已建立练习库：{seed_db()}")
    print("注意：每次运行本脚本或 Day 18 演示、练习，都会重建 orders 表。")
    print(
        "orders 表：6 条订单；paid：杭州 2 单 / 200 元，上海 2 单 / 230 元，北京 1 单 / 90 元"
    )
