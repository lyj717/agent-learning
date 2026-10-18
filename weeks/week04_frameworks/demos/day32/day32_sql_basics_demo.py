"""Day 32 概念 1：SQL 是语句，SQLite 是运行它的数据库。

阅读顺序：main → show_sql_basics。这个文件不导入 LangGraph。
小表只在内存里练 SQL，不创建或修改任何 .sqlite 文件。
"""

import sqlite3


def main() -> None:
    """从零展示表、行、SQL 语句和 Python 的 sqlite3 调用。"""
    print("=== 1. 这是什么 ===")
    print("数据库可以想成存多张表的地方；表有列名，每行是一条记录。")
    print("SQL 是给数据库的语句，例如建表、插入一行、查询几行。")
    print("SQLite 是运行 SQL 的数据库；它既能用内存，也能用一个 .sqlite 文件。")
    print(
        "CREATE / INSERT / SELECT 是 SQL；connect / execute / commit / fetchone 是 Python 调用。"
    )

    print("\n=== 2. 为什么需要它 ===")
    print("看到 .sqlite 文件时，不要当成文本打开；用数据库连接和查询才能读其中的表。")

    print("\n=== 3. 场景 ===")
    print("客服有两张工单；我们想找到其中一张工单最近一次记录。")

    print("\n=== 4. 亲手建表、写入、查询 ===")
    show_sql_basics()

    print("\n=== 5. 注意什么 ===")
    print("本演示的表只在内存中，关闭连接后就消失；它不是 LangGraph 的内部表。")
    print("先看懂连接、表、行与查询即可；下一份演示再讲 LangGraph 的 config。")


def show_sql_basics() -> None:
    """用一张临时小表演示建表、插入和按会话查询。"""
    print("① sqlite3.connect(位置)：打开数据库连接，返回 Connection 对象。")
    print("   这里的位置是 :memory:，只在内存建教学表，不会改动 LangGraph 的文件。")
    # sqlite3.connect(位置)：打开 SQLite 连接；":memory:" 表示临时放在内存里，
    # 不会创建或改动任何 .sqlite 文件。关闭连接后，这张教学表就消失。
    connection = sqlite3.connect(":memory:")

    create_sql = "CREATE TABLE visits (ticket_id TEXT, turn INTEGER, request TEXT)"
    print(f"② SQL 建表：{create_sql}")
    print("visits 是表名；TEXT 存文字，INTEGER 存整数；每行是一条记录。")
    print("   connection.execute(SQL) 把这条 SQL 交给 SQLite 执行；建表语句没有参数。")
    # execute(SQL, 参数元组)：执行一条 SQL；这条建表语句没有 ?，所以无需参数。
    connection.execute(create_sql)

    insert_sql = "INSERT INTO visits (ticket_id, turn, request) VALUES (?, ?, ?)"
    print(f"③ SQL 插入：{insert_sql}")
    print("每执行一次 INSERT，就新增一行。")
    print("   ? 是值的位置；execute 的第二个参数是三个实际值组成的元组。")
    print("   例如 ('ticket-a', 1, '查询订单') 对应三个 ?，不拼接 SQL 字符串。")
    connection.execute(insert_sql, ("ticket-a", 1, "查询订单"))
    connection.execute(insert_sql, ("ticket-a", 2, "补充收货地址"))
    connection.execute(insert_sql, ("ticket-b", 1, "申请发票"))
    # commit()：确认本连接的写入。写磁盘数据库时，这一步关系到重新打开后能否读到。
    connection.commit()
    print("④ connection.commit() 确认写入。先把三行全部查出来，看看表里有什么。")

    all_sql = "SELECT ticket_id, turn, request FROM visits ORDER BY ticket_id, turn"
    print(f"   SQL：{all_sql}")
    # 查询的 execute 返回 Cursor；fetchall() 读完结果，返回由行元组组成的列表。
    all_rows = connection.execute(all_sql).fetchall()
    print(
        f"   fetchall() 返回 {type(all_rows).__name__}，里面有 {len(all_rows)} 个行元组："
    )
    for row in all_rows:
        print(f"   {row}")
    print("   ORDER BY 在这里指定展示顺序；不写它时不能假定查询结果的先后。")

    select_sql = (
        "SELECT turn, request FROM visits WHERE ticket_id = ? "
        "ORDER BY turn DESC LIMIT 1"
    )
    print(f"⑤ 现在只找 ticket-a 最近一轮。SQL：{select_sql}")
    print("SELECT 指定要取的列；WHERE 选 ticket-a；ORDER BY 倒序，LIMIT 1 只取第一行。")
    # SELECT 的 execute 返回 Cursor（结果读取器）；第二个参数给唯一的 ? 填值。
    cursor = connection.execute(select_sql, ("ticket-a",))
    print(f"   execute 返回 {type(cursor).__name__}，它负责从查询结果中取行。")
    # fetchone() 从 Cursor 取一行，得到 (turn, request) 元组；查不到时得到 None。
    latest = cursor.fetchone()
    print(f"⑥ cursor.fetchone() 取一行，结果 (turn, request) = {latest}")
    print("   第一项 2 是轮次，第二项『补充收货地址』是请求；ticket-b 被 WHERE 排除。")
    missing = connection.execute(select_sql, ("ticket-missing",)).fetchone()
    print(f"⑦ 同样查不存在的 ticket-missing，fetchone() 返回 {missing}。")
    print("⑧ connection.close() 关闭连接；:memory: 中的教学表随后消失。")
    connection.close()


if __name__ == "__main__":
    main()
