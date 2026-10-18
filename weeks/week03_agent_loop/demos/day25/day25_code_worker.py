"""Day 25 的受限执行器：只解释数字赋值与四则运算，不执行任意 Python。

此文件由可信的教学程序作为子进程启动。代码字符串来自外部时，先检查语法树，
再由下面的函数逐个计算允许的节点；这里没有调用 exec 或 eval。
"""

import ast
import json
import math
import operator
import sys

MAX_CODE_CHARS = 240
MAX_STATEMENTS = 4
MAX_ABS_VALUE = 1_000_000_000

# ast.walk 会经过这些节点；不在名单里的 Call、Import、Attribute、循环等一律拒绝。
ALLOWED_NODES = (
    ast.Module,
    ast.Assign,
    ast.Expr,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.USub,
)

# operator.add(a, b) 等是四则运算的函数形式，沿用前几天的计算器思路。
BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def checked_number(value: object) -> int | float:
    """只接受有限且绝对值不过大的数字，排除 bool 与字符串。"""
    if type(value) not in (int, float):
        # bool 虽是 int 的子类，这里也不允许。
        raise ValueError("只允许数字常量")
    # math.isfinite(数字) 检查 inf、nan；绝对值上限还限制计算结果的大小。
    if abs(value) > MAX_ABS_VALUE or not math.isfinite(value):
        # 避免一个小程序造出过大的中间结果。
        raise ValueError("数字超过允许范围")
    return value


def check_tree(code: str) -> ast.Module:
    """在计算前检查长度、行数、语句形状和所有语法节点。"""
    if not code.strip() or len(code) > MAX_CODE_CHARS:
        # 空代码与过长代码都不进入解析器。
        raise ValueError(f"代码须非空且不超过 {MAX_CODE_CHARS} 个字符")
    # ast.parse(代码, mode='exec') 只生成语法树；不会执行代码。
    tree = ast.parse(code, mode="exec")
    if not 1 <= len(tree.body) <= MAX_STATEMENTS:
        # 最多三条赋值加一条结果表达式。
        raise ValueError(f"最多 {MAX_STATEMENTS} 条语句")
    # ast.walk(语法树) 逐个访问所有节点；只查字符串关键词会漏掉别的危险写法。
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            # 例如 open(...) 是 Call，import os 是 Import，均在运行前拒绝。
            raise ValueError(f"不允许的语法：{type(node).__name__}")
        if isinstance(node, ast.Constant):
            # Constant 也可能是字符串或 bool，不能只看节点名称。
            checked_number(node.value)
    for statement in tree.body[:-1]:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
        ):
            # 前面的语句只准写单个变量赋值，例如 price = 18。
            raise ValueError("前面的语句只能是单变量赋值")
    if not isinstance(tree.body[-1], ast.Expr):
        # 最后一行必须提供要返回的计算结果。
        raise ValueError("最后一行必须是结果表达式")  # noqa: TRY004
    return tree


def eval_number(node: ast.AST, variables: dict[str, int | float]) -> int | float:
    """只计算已获准的数字、变量、负号和四则运算节点。"""
    if isinstance(node, ast.Constant):
        # 常量已在 check_tree 中查过，此处继续限制返回值。
        return checked_number(node.value)
    if isinstance(node, ast.Name):
        # 变量只能从本次程序自己的字典里取，不能读取 Python 全局变量。
        if node.id not in variables:
            # 每次执行都使用新字典，上次的变量不会留下。
            raise ValueError(f"未定义变量：{node.id}")
        return variables[node.id]
    if isinstance(node, ast.BinOp):
        # 左右两边先各自计算，再调用允许的四则运算函数。
        left = eval_number(node.left, variables)
        right = eval_number(node.right, variables)
        result = BINARY_OPS[type(node.op)](left, right)
        return checked_number(result)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # 允许负号，例如 -price。
        return checked_number(-eval_number(node.operand, variables))
    raise ValueError(f"不允许的表达式：{type(node).__name__}")


def run_program(code: str) -> int | float:
    """执行受限的多行数值程序，返回最后一行表达式的值。"""
    tree = check_tree(code)
    variables: dict[str, int | float] = {}
    for statement in tree.body[:-1]:
        variables[statement.targets[0].id] = eval_number(statement.value, variables)
    return eval_number(tree.body[-1].value, variables)


def main() -> None:
    """从标准输入读代码，只向标准输出写一条 JSON 结果。"""
    try:
        # stdin.buffer.read(字节数) 限制外部输入；decode 明确按 UTF-8 解码。
        raw = sys.stdin.buffer.read(1025)
        if len(raw) > 1024:
            # 直接运行 worker 时也不接受无限长输入。
            raise ValueError("输入字节数过多")
        result = {"ok": True, "value": run_program(raw.decode("utf-8"))}
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as error:
        # 拒绝与计算错误都返回明确文字，不把异常堆栈交给模型。
        result = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    # json.dumps(对象) 生成一行 JSON；默认转义中文，避免 Windows 输出编码干扰。
    print(json.dumps(result))


if __name__ == "__main__":
    main()
