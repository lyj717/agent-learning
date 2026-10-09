"""Day 18 加餐：从零看懂 SQLite 的建表、增删改查。

运行：.venv\\Scripts\\python.exe weeks\\week02_tools\\day18_sqlite_basics_demo.py

全程使用 :memory: 内存数据库。关掉程序后数据消失，不碰 day18_orders.sqlite。
先跑一遍看屏幕解释，再对照源码找每一步的 SQL。第 1～5 节是 Day 18 必需；
第 6 节的修改、删除是认识常见 SQL 操作，今天的订单工具用不到。
"""

import sqlite3


def section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


section("1. 文件、表、行、列分别是什么")
print(
    """这是什么：可以先把数据库想成一个表格文件；一张表有列和多行。
为什么：Day 18 的订单不是模型知道的常识，而是我们自己保存的数据。
场景：orders 表每行是一笔订单，有 id、city、amount、status 四列。

  id  city  amount  status
   1  杭州   120.0   paid
   2  杭州    80.0   paid

今天用 :memory: 建一个只活在程序运行期间的小数据库；没有生成文件。
Day 18 练习用 day18_orders.sqlite，那是同样的表，只是保存到磁盘。"""
)
# sqlite3.connect(位置)：打开数据库连接。":memory:" 表示仅放在内存中。
connection = sqlite3.connect(":memory:")
print("运行代码：sqlite3.connect(':memory:') → 已打开一个空数据库")
print("注意：connection 是 Python 操作数据库的入口；结束时要 close()。")


section("2. CREATE TABLE：造一张空表")
print(
    """这是什么：CREATE TABLE 建表，括号里写列名和每列的大致类型。
为什么：插入订单之前，要先说清每行有哪些格子。
场景：id 是整数编号，city 和 status 是文字，amount 是数字。"""
)
create_sql = """
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    city TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL
)
"""
print("运行的 SQL：", create_sql)
# execute(SQL)：让数据库执行一条 SQL；这条会造表，不返回订单行。
connection.execute(create_sql)
print("运行结果：orders 表已存在，但目前还是 0 行。")
print("注意：PRIMARY KEY 保证 id 不重复；NOT NULL 表示这一列不能留空。")


section("3. INSERT：把订单放进表里")
print(
    """这是什么：INSERT INTO 表名 (列名...) VALUES (值...) 插入一行。
为什么：空表没东西可查。我们先放四笔假订单。
场景：杭州两笔已支付、一笔已取消；上海一笔已支付。"""
)
orders = [
    (1, "杭州", 120.0, "paid"),
    (2, "杭州", 80.0, "paid"),
    (3, "杭州", 50.0, "cancelled"),
    (4, "上海", 200.0, "paid"),
]
insert_sql = "INSERT INTO orders (id, city, amount, status) VALUES (?, ?, ?, ?)"
print("运行的 SQL：", insert_sql)
for order in orders:
    # execute(SQL, 值元组)：四个 ? 依次取 order 里的四个值。
    connection.execute(insert_sql, order)
    print(f"  插入：{order}")
# commit()：确认写入。真实文件数据库要调用它，别只 close()。
connection.commit()
print("运行结果：插入 4 行并提交。")
print("注意：? 是数据的位置，不是让 Python 拼 SQL 字符串。")


section("4. SELECT：先看全部，再看指定列")
print(
    """这是什么：SELECT 选要看的列，FROM 指定表。
为什么：想知道数据库里到底有哪些订单，先完整看一遍。
场景：SELECT id, city, amount, status FROM orders 按这个顺序取四列。
ORDER BY id 表示按编号排序，这样每次打印顺序都一样。"""
)
select_sql = "SELECT id, city, amount, status FROM orders ORDER BY id"
print("运行的 SQL：", select_sql)
# execute 返回 cursor（游标），可以把它理解成「这次查询的结果入口」。
cursor = connection.execute(select_sql)
# fetchall()：把查询结果的所有行取成一个列表；每行是一个 tuple。
rows = cursor.fetchall()
print(f"fetchall() 得到 {len(rows)} 行：")
for row in rows:
    print(f"  {row}")
print("注意：row[0] 是 id、row[1] 是 city；顺序由 SELECT 后面的列决定。")


section("5. WHERE：只留符合条件的行")
print(
    """这是什么：WHERE 在所有行里筛选；AND 表示两个条件都要满足。
为什么：杭州有已取消订单，不能把它算进已支付金额。
场景：city 是杭州，而且 status 是 paid；从四行筛出两行。"""
)
city = "杭州"
status = "paid"
filter_sql = "SELECT id, city, amount FROM orders WHERE city = ? AND status = ?"
print("运行的 SQL：", filter_sql)
print(f"传给两个 ? 的值：{(city, status)}")
cursor = connection.execute(filter_sql, (city, status))
matched_rows = cursor.fetchall()
for row in matched_rows:
    print(f"  筛中：{row}")
count = len(matched_rows)
total = 0
for row in matched_rows:
    total += row[2]  # 这次 SELECT 的第 3 列是 amount，所以用索引 2。
print(f"Python 统计：{count} 单，共 {total:g} 元")
print(
    "注意：把 city 当第二个参数传入，而不是拼进 SQL。没查到时 fetchall() 是空列表，笔数和金额都是 0。"
)


section("6. UPDATE 和 DELETE：改一行、删一行（认识即可）")
print(
    """这是什么：UPDATE 改已有行，DELETE 删已有行。
为什么：真实订单的状态会变化，也可能要删测试数据。
场景：先把 id=3 的订单改为已支付，再删掉 id=4 的上海订单。
以下只改内存里的演示表，不会改 Day 18 的订单文件。"""
)
update_sql = "UPDATE orders SET status = ? WHERE id = ?"
print("运行的 SQL：", update_sql, "参数：", ("paid", 3))
connection.execute(update_sql, ("paid", 3))
cursor = connection.execute("SELECT id, status FROM orders WHERE id = ?", (3,))
# fetchone()：只取一行；查不到时返回 None。
print("修改后：", cursor.fetchone())

delete_sql = "DELETE FROM orders WHERE id = ?"
print("运行的 SQL：", delete_sql, "参数：", (4,))
connection.execute(delete_sql, (4,))
connection.commit()
cursor = connection.execute("SELECT id FROM orders ORDER BY id")
print("删除后还在的 id：", [row[0] for row in cursor.fetchall()])
print("注意：UPDATE 和 DELETE 一定要想清 WHERE；漏写可能影响整张表。")


section("7. 回到 Day 18 的订单工具")
print(
    """今天写 query_orders(city) 时，只需要刚才的四步：
  ① sqlite3.connect(DB_PATH) 打开练习库
  ② SELECT ... FROM orders WHERE city = ? AND status = ?
  ③ fetchall() 拿到行，用 len() 和 for 统计
  ④ close() 关闭连接

day18_seed_db.py 会先准备好六条假订单；你的函数负责查询，不负责建表。
这份演示的四行数据只在内存中。两份数据分开，互不影响。"""
)
# close()：关闭连接。内存数据库随之消失。
connection.close()
print("演示结束：内存数据库已关闭。")
