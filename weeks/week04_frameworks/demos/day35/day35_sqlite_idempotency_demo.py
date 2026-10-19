"""Day 35 知识点：用 SQLite 的唯一业务编号防止重复写入。

阅读顺序：main → insert_quote_once。只需要 Python 标准库 sqlite3。
每次运行新建内存数据库，不创建文件，也不调用模型或 LangGraph。
"""

import sqlite3


def main() -> None:
    """对照同一业务编号重试与另一笔新操作，认识数据库唯一约束。"""
    print("=== 1. 这是什么 ===")
    print("幂等：同一笔操作重复提交，实际效果仍与只提交一次相同。")
    print("今天只看本地报价记录：数据库用 quote_id 识别同一笔报价。")
    print(
        "quote 是『报价』；quote_id 是我们今天自定义的报价操作编号，不是 LangGraph 参数。"
    )
    print(
        "它就是一个字符串，例如 'quote-41'；同一次操作重试继续用原编号，新操作用新编号。"
    )
    print("PRIMARY KEY 是主键约束；同一个非空编号在这张表里只能出现一次。")

    print("\n=== 2. 为什么需要它 ===")
    print("节点恢复重跑或请求重试，都可能让同一笔报价再次执行写入。")
    print("只在 Python 里先查询再插入，两个并发请求可能都查到『还没有』。")
    print("把唯一性交给数据库约束，重复编号就无法变成第二条记录。")

    print("\n=== 3. 场景与接口 ===")
    print("报价 quote-41 第一次提交、原样重试，再提交新报价 quote-42。")
    print("两笔报价可以金额相同；是否是同一操作由稳定的业务编号决定。")
    print("insert_quote_once(connection, quote_id, amount_yuan) -> bool")
    print("connection：已建好 quotes 表的数据库连接；quote_id：非空字符串编号。")
    print("amount_yuan：本例的整数金额；True 表示新增，False 表示本次未新增。")
    print("SQL 基础是 Day32 的复习；今天的新重点是让唯一约束阻止重复写入。")

    print("\n=== 4. SQL、参数与真实输出 ===")
    # connect(位置) 返回 Connection；":memory:" 新建只属于本连接的内存数据库。
    connection = sqlite3.connect(":memory:")
    try:
        create_sql = (
            "CREATE TABLE quotes ("
            "quote_id TEXT PRIMARY KEY NOT NULL, amount_yuan INTEGER NOT NULL)"
        )
        print(f"① 建表语句：{create_sql}")
        print("TEXT 存文字，INTEGER 存整数，NOT NULL 不允许缺失值。")
        # execute(SQL, 参数) 执行一条语句并返回 Cursor；没有占位符时可省略参数。
        connection.execute(create_sql)

        print("\n② 插入语句：")
        print("INSERT OR IGNORE INTO quotes (quote_id, amount_yuan) VALUES (?, ?)")
        print("INSERT 新增一行；OR IGNORE 在这里让主键重复的行跳过，不报重复错误。")
        print("两个 ? 是两个值的位置；execute 的第二个参数传 (quote_id, amount_yuan)。")
        print("参数按位置对应，不用 f 字符串把数据拼成 SQL。")
        print("execute 返回 Cursor；本例读它的 rowcount 属性了解插入了几行。")
        print("rowcount=1 表示本次新增；=0 表示跳过。它不是整个表的总行数。")
        print("commit() 提交当前写入，返回 None；磁盘数据库提交后才能可靠保留写入。")

        requests = [("quote-41", 280), ("quote-41", 280), ("quote-42", 280)]
        expected_counts = [1, 1, 2]
        for (quote_id, amount_yuan), expected in zip(requests, expected_counts):
            added = insert_quote_once(connection, quote_id, amount_yuan)
            select_sql = "SELECT quote_id, amount_yuan FROM quotes ORDER BY quote_id"
            # fetchall() 不需要参数：取完查询结果，返回行元组组成的列表；没记录返回 []。
            rows = connection.execute(select_sql).fetchall()
            print(f"\n提交 {quote_id}，金额 {amount_yuan} 元：本次新增={added}")
            print(f"  表中记录数：实际 {len(rows)}；期望 {expected}")
            print(f"  按编号查询的 (quote_id, amount_yuan)：{rows}")

        print("\n③ 复习只按一个编号查询：")
        find_sql = "SELECT amount_yuan FROM quotes WHERE quote_id = ?"
        print(f"SQL：{find_sql}")
        print("execute(find_sql, ('quote-41',))：只有一个值时，元组的逗号仍要保留。")
        print("('quote-41') 只是字符串；('quote-41',) 才是一个元素的元组。")
        found = connection.execute(find_sql, ("quote-41",)).fetchall()
        print(f"fetchall() 返回：{found}；其中 (280,) 是只有一列的行元组。")
    finally:
        # close() 不接收参数、返回 None；关闭内存连接后，整张教学表随之消失。
        connection.close()

    print("\n=== 5. 注意什么 ===")
    print("同一操作重试必须继续使用原 quote_id；每次换编号就无法防重。")
    print("thread_id 编会话，message.id 编消息，tool_call_id 配对点单与观察。")
    print("它们各有用途；这里防重所需的是报价这个业务操作的稳定编号。")
    print("同编号但金额不同也会跳过，不会更新旧金额；真实接口还应核对内容是否冲突。")
    print("OR IGNORE 也能跳过某些其他约束错误，因此 rowcount=0 本身不能证明是重复。")
    print("本例固定输入有效，才把未新增解释为主键重复；不把它当作通用参数校验。")
    print("唯一约束只防止这张表重复入库，不保证转账、发货等外部动作恰好执行一次。")
    print("外部动作还需要服务端用业务编号防重，并处理动作结果与记录之间的失败。")
    print("本例数据库在内存里；跨进程保存记录时要使用磁盘数据库并正确提交。")


def insert_quote_once(
    connection: sqlite3.Connection, quote_id: str, amount_yuan: int
) -> bool:
    """尝试写入一条有效报价；返回这一次是否新增了一行。"""
    cursor = connection.execute(
        "INSERT OR IGNORE INTO quotes (quote_id, amount_yuan) VALUES (?, ?)",
        (quote_id, amount_yuan),
    )
    # rowcount 是属性，不写括号；本例一条 INSERT 的值为 1（新增）或 0（跳过）。
    added = cursor.rowcount == 1
    connection.commit()
    return added


if __name__ == "__main__":
    main()
