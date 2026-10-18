"""Day 25：让代码工具只做获准的数值计算，并看清权限边界。

先读 main 的四节输出；再看 run_limited_code 怎样启动子进程；
最后按需要读 day25_code_worker.py 中的语法检查与计算。
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

# resolve() 得到绝对路径；工作目录换了也能找到可信的 worker 脚本。
HERE = Path(__file__).resolve().parent
WORKER = HERE / "day25_code_worker.py"
MAX_CODE_CHARS = 240
TIMEOUT_SECONDS = 3


def section(title: str) -> None:
    """打印分节标题。"""
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


def main() -> None:
    """按允许、拒绝、隔离范围的顺序讲解受限代码工具。"""
    section("1. 为什么需要代码工具")
    print("这是什么：把一小段多行数值代码交给工具计算，最后一行给出结果。")
    print("为什么需要：Day 24 的计算器只收一个算式；多步计算有时要保存中间变量。")
    print("场景：青禾笔记本单价来自检索原文，数量来自用户问题。")
    code = "unit_price = 18\nquantity = 7\nunit_price * quantity"
    print(f"代码：\n{code}")
    print("注意：这里的 18 是演示已查到的教学价格；代码不会自己去读商品文件。")

    section("2. 允许的程序怎样得到结果")
    print("这是什么：只接受数字、单变量赋值、负号和四则运算。")
    print("为什么需要：模型提供的是输入，工具要先决定它有权做什么。")
    print("场景：上面三行中，前两行存变量，最后一行计算商品金额。")
    outcome = run_limited_code(code)
    print("代码：run_limited_code(上面的三行代码)")
    print(f"工具是否成功：{outcome['ok']}；计算结果：{outcome.get('value')}")
    print("注意：受限执行器自己解释语法树，没有把输入交给 exec 或 eval。")

    section("3. 语法树只需要懂到哪一步")
    print("这是什么：语法树是 Python 把代码拆开后得到的结构，像把算式拆成数字和加号。")
    print("为什么需要：检查结构，才能判断代码里有没有函数调用、导入等不允许的动作。")
    print("场景：18 + 7 会拆出数字、加号等节点；这里只看结构，不计算结果。")
    print("代码：18 + 7")
    # ast.parse(代码, mode="exec") 把代码文本变成语法树，不执行代码。
    small_tree = ast.parse("18 + 7", mode="exec")
    node_explanations = {
        ast.Module: "整段代码",
        ast.Expr: "一行表达式",
        ast.BinOp: "双边运算",
        ast.Constant: "一个常量",
        ast.Add: "加号",
    }
    # ast.walk(语法树) 依次取出节点；type(node).__name__ 是节点的名称。
    for node in ast.walk(small_tree):
        print(f"  {type(node).__name__}：{node_explanations[type(node)]}")
    print("做练习 A 只需会：解析代码、逐个看节点、判断节点是否在允许名单里。")
    print("注意：不必背节点全集；Constant 可能装数字，也可能装字符串，还要检查值。")

    section("4. 不允许的程序在执行前被拒绝")
    print("这是什么：检查整棵语法树，碰到不在白名单里的节点就拒绝。")
    print("为什么需要：模型不能因为写了 open 或 import 就获得文件、网络权限。")
    print("场景：尝试读取文件；这里只检查输入，不会真的打开文件。")
    blocked = 'open("private.txt").read()'
    print(f"代码：{blocked}")
    # 与上一节相同：只分析结构，不执行 open。
    tree = ast.parse(blocked, mode="exec")
    print("语法树先经过这些节点：")
    for node in ast.walk(tree):
        print(f"  {type(node).__name__}")
        if isinstance(node, ast.Call):
            # Call 是第一个不在白名单内的节点，示意到这里就够了。
            break
    blocked_outcome = run_limited_code(blocked)
    print(
        f"工具是否成功：{blocked_outcome['ok']}；原因：{blocked_outcome.get('error')}"
    )
    print("注意：不能只查有没有单词 open；权限规则看的是语法节点。")

    section("5. 子进程隔离了什么，又没有隔离什么")
    print("这是什么：每次调用启动一个新进程，变量不会从上一次传过来。")
    print("为什么需要：一次工具调用的中间状态不应悄悄影响下一次。")
    print("场景：只写 unit_price，看看能否偷用第 2 节的变量。")
    isolated_outcome = run_limited_code("unit_price")
    print("代码：unit_price")
    print(
        f"工具是否成功：{isolated_outcome['ok']}；原因：{isolated_outcome.get('error')}"
    )
    print("注意：子进程和 Python -I 不是操作系统安全沙箱；它仍有当前账号的权限。")
    print("本教具的边界是：外部代码只进入语法白名单解释器，不执行通用 Python。")

    section("接下来动手")
    print("第一步：写 day25_syntax_exercises.py，找出第一个不被允许的语法节点。")
    print("第二步：写 day25_permission_exercises.py，由应用决定能否调用代码工具。")
    print("周末整合时再把这个受限工具接进你写的 Agent 主循环。")


def run_limited_code(code: str) -> dict:
    """把短代码交给可信的子进程，返回成功值或拒绝原因。"""
    if not isinstance(code, str) or not code.strip():
        # 先拒绝错误类型与空内容，不启动子进程。
        return {"ok": False, "error": "ValueError: code 必须是非空字符串"}
    if len(code) > MAX_CODE_CHARS:
        # 限制输入规模；worker 还会独立检查一次。
        return {"ok": False, "error": f"ValueError: code 超过 {MAX_CODE_CHARS} 个字符"}
    try:
        # subprocess.run(命令列表, input=..., timeout=...) 启动可信 worker，
        # 传入文本并等待最多三秒；-I 只隔离 Python 导入/环境设置，不限制系统权限。
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(WORKER)],
            input=code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SECONDS,
            check=False,
            env={},
        )
    except subprocess.TimeoutExpired:
        # 超时只代表没等到结果，不把它当作计算成功。
        return {"ok": False, "error": "TimeoutError: 代码工具超过三秒"}
    if completed.returncode != 0:
        # worker 异常退出时不把内部堆栈交给模型。
        return {"ok": False, "error": "RuntimeError: 受限执行器异常退出"}
    try:
        # json.loads(JSON 文本) 把子进程的一行输出恢复成 Python 字典。
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        # 非 JSON 输出不能当作可信工具观察。
        return {"ok": False, "error": "RuntimeError: 执行器返回了无效 JSON"}
    if not isinstance(result, dict) or type(result.get("ok")) is not bool:
        # 即使输出能解析，也要确认最基本的结果形状。
        return {"ok": False, "error": "RuntimeError: 执行器返回格式错误"}
    return result


if __name__ == "__main__":
    main()
