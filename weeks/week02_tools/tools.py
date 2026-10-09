"""Week 02 的「工具箱」：放着**真能执行**的函数，模型可以点名调用它们。

注意这里只有函数本身，没有「工具说明」——说明（JSON Schema）要写在练习里，
因为「怎么描述一个工具」正是 Day 17、Day 18 要学的东西。

Day 17 的计算器已完成；Day 18 的天气和 SQLite 查询留给学员实现。
"""

import ast
import operator

# Day 18 的查询要用 sqlite3；写 query_orders 时取消下一行的注释。
# import sqlite3

# Day 18 的数据库路径由 day18_seed_db.py 提供；写 query_orders 时取消下一行。
# from day18_seed_db import DB_PATH

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
    """查模拟天气。

    要做的：从 WEATHER_DATA 读 city，返回带 city、temperature_c、condition
    的 dict。城市不在表里时，抛带城市名的 ValueError，留给 Day 19 处理。
    期望结果：get_weather("杭州") 给出 22°C、多云。
    提示：这是固定的练习快照，不是真实天气；不要写成“当前天气”。
    """
    raise NotImplementedError("Day 18 天气工具还没写")


def query_orders(city: str) -> dict:
    """查 SQLite 中某城市的已支付订单。

    要做的：连接 DB_PATH，查 orders 表中 city 等于入参且 status='paid'
    的 COUNT(*) 与 COALESCE(SUM(amount), 0)，返回带 city、paid_count、
    paid_total 的 dict；没有记录时返回 0 和 0，不要报错。
    期望结果：query_orders("杭州") 给出 2 单、200 元。
    提示：sqlite3 与 DB_PATH 的导入已在文件顶部注释，写时取消注释；
    DB_PATH 来自 day18_seed_db。先运行 seed_db() 建表。SQL 用 ? 绑定 city，
    不要把模型给的城市拼进 SQL 字符串。可参照 day18_multi_tools_demo.py 第 3 节。
    """
    raise NotImplementedError("Day 18 订单工具还没写")
