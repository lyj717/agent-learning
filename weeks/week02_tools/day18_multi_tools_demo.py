"""Day 18 讲解：多工具选择、工具粒度、SQLite 参数化查询（完全离线）。"""

import sqlite3
from contextlib import closing

from day18_seed_db import DB_PATH, seed_db


def section(title: str) -> None:
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


section("1. 三个工具是什么")
print(
    """这是什么：同一轮请求把 calculator、get_weather、query_orders 的说明一起给模型。
为什么：问题有三种来源——算式、模拟天气、本地订单，模型要先决定找谁。
场景：「杭州有多少笔已支付订单？」该查本地订单，不该问天气或算术。
代码：请求的 tools 是三份说明的列表；模型返回 tool_calls，代码按名字查表执行。
注意：工具名、description、参数名都要说同一件事；模型看不到 Python 函数体。"""
)

section("2. 工具该做多大一件事")
print(
    """这是什么：粒度是一个工具负责的事情有多宽。
为什么：「处理所有业务请求」太宽，模型难选，也难限制数据库能读什么。
场景：本课只问某城市已支付订单的数量与金额；query_orders(city) 就够。
代码：参数只有 city；SQL 只读 orders 表、只统计 status='paid'。
注意：别把任意 SQL 字符串交给模型执行。要查别的报表，再设计明确的新工具。"""
)

section("3. SQLite 是什么，为什么用占位符")
print(
    """这是什么：SQLite 把表存在本地文件里；SQL 是向表提问的语言。
为什么：订单是我们自己的数据，模型训练时不知道，必须由代码查。
场景：下面用 Day 18 的六条演示订单，查杭州已支付订单。
代码：先建练习库，再用 ? 给 city 绑定参数。"""
)
seed_db()
# sqlite3.connect(路径)：打开 SQLite 文件。
# closing(连接)：with 结束时关闭连接；sqlite3 自己的 with 不负责关闭。
with closing(sqlite3.connect(DB_PATH)) as connection:
    # execute(SQL, 参数元组)：把参数绑定到 SQL 里的 ?；不拼接不可信的城市名。
    cursor = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount), 0) "
        "FROM orders WHERE city = ? AND status = 'paid'",
        ("杭州",),
    )
    # fetchone()：取查询结果的第一行；此聚合查询恰好只返回一行。
    count, total = cursor.fetchone()
print(f"杭州已支付订单：{count} 单，共 {total:g} 元")
print("注意：('杭州',) 是单元素元组，逗号不能漏；? 绑定的是值，不是 SQL 代码。")

section("4. auto 与工具选择")
print(
    """这是什么：tool_choice='auto' 表示模型可以点一个或多个工具，也可以直接回答。
为什么：问「你好」时，强迫它查订单只会做无用功。
场景：同一份三工具说明，分别问天气、算式、订单，观察第一轮点单。
代码：Day 18 练习的 --live 会打印问题、实际工具名、参数和最终答案。
注意：模型选哪个不是代码里的 if/else；代码负责提供工具列表并决定是否执行。"""
)

section("5. 选错时怎么排查")
print(
    """这是什么：选错指第一轮实际点单与任务需要的工具不一致，也包括该用工具却没点。
为什么：描述含糊、功能重叠、参数名误导，都会改变模型理解。
场景：「杭州消费多少？」可能指个人消费，也可能指订单金额；先确认问题本身。
代码：记录原问题、预期工具、实际工具与参数，再只改一处描述重跑同题。
注意：不要把一次随机选择写成必然规律；没观察到三次选错，就如实写未观察到。"""
)
