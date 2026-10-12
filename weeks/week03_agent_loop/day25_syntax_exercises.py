"""Day 25 小练习 A：从语法树找出代码工具不允许的第一个节点。"""

import ast

from day25_code_worker import ALLOWED_NODES


def first_disallowed_node(code: str) -> str | None:
    """返回第一个不被允许的语法节点名；全部允许时返回 None。"""
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            return type(node).__name__
        if isinstance(node, ast.Constant):  # noqa: SIM102
            # 先确认节点是 Constant，才读取只有它拥有的 value。
            if type(node.value) not in {float, int}:
                return "Constant"
    return None


def main() -> None:
    """打印允许语法、被拒语法和坏语法的对照结果。"""
    cases = [
        ("允许的数值程序", "price = 18\nquantity = 7\nprice * quantity", "None"),
        ("函数调用", 'open("private.txt")', "Call"),
        ("导入模块", "import os\n1", "Import"),
        ("循环", "while True:\n    pass\n1", "While"),
        ("字符串不是数字", '"18"', "Constant"),
        ("语法不完整", "price =", "SyntaxError"),
    ]
    for label, code, expected in cases:
        print(f"\n{label}；期望：{expected}")
        try:
            result = first_disallowed_node(code)
        except SyntaxError as error:
            print(f"实际：SyntaxError: {error.msg}")
        else:
            print(f"实际：{result}")


if __name__ == "__main__":
    main()


# 现象与原因
# 1. 允许的程序与 open("private.txt") 分别输出什么？为什么不能只在代码文本中找单词 open？
# 答：分别输出None和Call，权限规则看的是语法节点，而不是单纯在代码里找open
# 2. 字符串 "18" 的节点也是 Constant，为什么它仍应被拒绝？
# 答："18"是字符串，需要的是数字类型的18
