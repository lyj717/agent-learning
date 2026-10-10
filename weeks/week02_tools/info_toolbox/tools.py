"""项目本地工具：从 Day 17–18 已完成的计算器、天气和订单工具迁入。"""

import ast
import operator
import sqlite3

from database import DB_PATH

WEATHER_DATA = {
    "杭州": {"temperature_c": 22, "condition": "多云"},
    "上海": {"temperature_c": 25, "condition": "晴"},
    "北京": {"temperature_c": 18, "condition": "小雨"},
}

# operator.add(a, b) 就是 a + b 的「函数版」。
# 为什么需要它：语法树里存的是「这是加法」这个**类型**（ast.Add），
# 而你要的是「能调用的函数」。这张表就是两者的对照。
_BINARY_OPS = {
    ast.Add: operator.add,  # +
    ast.Sub: operator.sub,  # -
    ast.Mult: operator.mul,  # *
    ast.Div: operator.truediv,  # /
}
_UNARY_OPS = {
    ast.USub: operator.neg,  # 负号，例如 -5
}


def _eval_node(node):
    """递归地把语法树的节点算成数字。只认识数字、括号和四则运算。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        return _BINARY_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"算式里出现了我不认识的东西：{ast.dump(node)}")


def calculator(expression: str) -> float:
    """算一个只含 + - * / 和括号的算式，返回数字。"""
    # ast.parse(表达式, mode="eval")：把一段 Python 表达式解析成**语法树**（AST）。
    # 这里用它来「只放行数字、运算符和括号」——函数调用、变量名、属性访问都会
    # 掉进 _eval_node 最后那个 raise，所以不像 eval() 那样能被注入代码。
    # （eval() 也能算这个，但它会把字符串当代码执行；模型给的参数不能直接喂给它。）
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def get_weather(city: str) -> dict:
    """返回城市的模拟天气快照；不支持的城市抛出 ValueError。"""
    if city in WEATHER_DATA:
        return {
            "city": city,
            "temperature_c": WEATHER_DATA[city]["temperature_c"],
            "condition": WEATHER_DATA[city]["condition"],
        }
    else:
        raise ValueError(f"不支持城市名{city}")


def query_orders(city: str) -> dict:
    """查询城市的已支付订单笔数与总金额。"""
    connection = sqlite3.connect(DB_PATH)
    filter_sql = (
        "SELECT id, city, amount FROM orders WHERE city = ? AND status = 'paid'"
    )
    cursor = connection.execute(filter_sql, (city,))
    matched_rows = cursor.fetchall()
    count = len(matched_rows)
    cost = 0
    for row in matched_rows:
        cost += row[2]
    connection.close()
    return {"city": city, "paid_count": count, "paid_total": cost}
