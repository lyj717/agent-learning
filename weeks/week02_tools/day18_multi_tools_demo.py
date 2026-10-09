"""Day 18 演示：每节先讲概念，再运行一段看得见结果的代码（完全离线）。"""

import sqlite3
from contextlib import closing

from day18_seed_db import DB_PATH, seed_db


def section(title: str) -> None:
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


section("1. 三个工具放在同一份列表里")
print(
    """这是什么：给模型看的工具说明是一份列表，一项说明一个能力。
为什么：同一句问题可能需要计算、天气快照或本地订单，不能只带计算器。
场景：「杭州有几笔已支付订单？」需要订单能力。先看三个工具的名字、用途和入参。"""
)
# 这里只列出说明的关键字段；练习第 2 题再把它们写成完整 JSON Schema。
tool_cards = [
    {"name": "calculator", "use_for": "算术", "argument": "expression"},
    {"name": "get_weather", "use_for": "模拟天气快照", "argument": "city"},
    {"name": "query_orders", "use_for": "已支付订单统计", "argument": "city"},
]
print("运行代码：逐个读工具卡片")
for card in tool_cards:
    print(f"  {card['name']}：{card['use_for']}；必填参数 {card['argument']}")
print("注意：这是给人看的缩略卡片；真正发请求时要写完整的 parameters JSON Schema。")


section("2. 工具粒度：一个工具只做一件明确的事")
print(
    """这是什么：粒度指一个工具管多宽的任务。
为什么：「处理所有业务问题」没有清楚的输入边界，模型也难判断何时用。
场景：物流系统只允许按运单号查状态，就给它一个明确的查询函数。"""
)
shipment_status = {"YT001": "运输中", "YT002": "已签收"}


def lookup_shipment(tracking_id: str) -> str:
    """演示专用：按运单号查固定快照。"""
    return shipment_status.get(tracking_id, "未找到运单")


print("运行代码：同一个函数收到不同运单号")
for tracking_id in ["YT001", "YT999"]:
    print(f"  lookup_shipment({tracking_id!r}) -> {lookup_shipment(tracking_id)}")
print(
    "注意：这个工具只收 tracking_id，不能代查天气或执行任意 SQL；Day 18 的订单工具同理，只统计指定城市的已支付订单。"
)


section("3. SQLite：用占位符查询本地订单")
print(
    """这是什么：day18_orders.sqlite 是本地数据库文件，orders 表就保存在里面。
day18_seed_db.py 是准备练习数据的 Python 脚本，不是数据库；它负责建表、插入六条假订单。
为什么：本地订单不是模型训练知识，必须由代码查；练习还需要每次都从同一份数据开始。
场景：查六条演示订单中，杭州已支付订单的笔数和金额。"""
)
print("运行代码：调用 seed_db() 准备数据库，再查询")
# seed_db()：删除并重建 orders 表，插入六条固定的假订单；没有入参，返回文件路径。
# 演示和练习都会自动调用它，不需要提前手动运行；重跑会覆盖表里原有的订单。
db_path = seed_db()
print(f"  已重建数据库文件：{db_path.name}（重跑演示或练习都会重置六条订单）")
print("运行代码：连接数据库，执行固定查询，再读取一行结果")
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
print(f"  杭州已支付订单：{count} 单，共 {total:g} 元")
print("注意：('杭州',) 是单元素元组，逗号不能漏；? 绑定的是值，不是 SQL 代码。")


section("4. tool_choice：这一轮允许模型怎样选择")
print(
    """这是什么：tool_choice 控制这一轮能否点工具；auto 允许模型选择或直接回答。
为什么：问「你好」时不需要强迫它查订单。
场景：同一份三工具列表，只改 tool_choice，观察请求配置的区别。"""
)
choices = [
    "auto",
    "none",
    {"type": "function", "function": {"name": "query_orders"}},
]
print("运行代码：构造三份离线示意配置（不向模型发送请求）")
for choice in choices:
    tool_names = [card["name"] for card in tool_cards]
    print(f"  可见工具={tool_names}；tool_choice={choice!r}")
print(
    "注意：这里只展示取值，未构造完整 API 请求。真实选择要看 --live 的第一轮 tool_calls；思考模式可能拒绝指定工具。"
)


section("5. 选错时先比较预期与实际")
print(
    """这是什么：选错包括点了不合适的工具，也包括该点工具却直接回答。
为什么：不记录第一轮实际点单，就只能凭最终答案猜发生了什么。
场景：下面是人为造的三条轨迹，演示怎么比较；它们不是模型实测。"""
)


def compare_choice(expected: str, actual_calls: list[str]) -> str:
    """演示专用：比较预期工具名与第一轮实际点单。"""
    if expected in actual_calls:
        return "选中了预期工具"
    if not actual_calls:
        return "未调用工具"
    return "选了别的工具"


sample_traces = [
    ("杭州有几笔已支付订单？", "query_orders", ["query_orders"]),
    ("杭州有几笔已支付订单？", "query_orders", ["get_weather"]),
    ("杭州有几笔已支付订单？", "query_orders", []),
]
print("运行代码：逐条检查示意轨迹")
for question, expected, actual in sample_traces:
    print(
        f"  {question} 预期={expected}，实际={actual} → {compare_choice(expected, actual)}"
    )
print(
    "注意：这些轨迹只是教你读输出；你的三条案例要从自己跑的 --live 记录。没观察到选错，就如实写尝试与结果。"
)
