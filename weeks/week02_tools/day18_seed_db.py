"""Day 18 练习数据准备脚本，不是数据库文件。

seed_db() 会在同目录生成 day18_orders.sqlite，删除并重建 orders 表，
插入六条固定的假订单。演示和练习会自动调用它；重复运行会覆盖表中旧数据。
生成的 .sqlite 文件被 .gitignore 忽略，不是交付物。
"""

import sqlite3
from contextlib import closing
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
    # closing(连接)：离开 with 时关闭连接；sqlite3 自己的 with 只管提交/回滚。
    with closing(sqlite3.connect(DB_PATH)) as connection:
        # executescript(SQL)：一次执行多条固定的建表语句；这里只用于本地数据准备。
        connection.executescript(
            """
            DROP TABLE IF EXISTS orders;
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                city TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL
            );
            """
        )
        # executemany(SQL, 参数行)：把每行参数分别绑定到 ?，批量插入练习数据。
        connection.executemany(
            "INSERT INTO orders (id, city, amount, status) VALUES (?, ?, ?, ?)",
            ORDERS,
        )
        # commit()：把插入真正写进文件；closing 只负责关闭，不会替你提交。
        connection.commit()
    return DB_PATH


if __name__ == "__main__":
    print(f"已建立练习库：{seed_db()}")
    print("注意：每次运行本脚本或 Day 18 演示、练习，都会重建 orders 表。")
    print(
        "orders 表：6 条订单；paid：杭州 2 单 / 200 元，上海 2 单 / 230 元，北京 1 单 / 90 元"
    )
