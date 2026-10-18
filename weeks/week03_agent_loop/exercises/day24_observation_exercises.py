"""Day 24 小练习 B：复用已完成的检索，把多种工具结果回填成一条 tool 消息。"""

import sys as _sys
from pathlib import Path as _Path

# 直接运行脚本时补入仓库根目录，跨目录模块仍用完整包路径导入。
_REPO_ROOT = _Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))


import json

from weeks.week03_agent_loop.demos.day24.day24_retrieval_demo import (
    calculator,
    make_call,
)
from weeks.week03_agent_loop.exercises.day24_search_exercises import search_notes


def build_tool_message(call: dict, tool_table: dict) -> dict:
    """执行原生工具点单，返回带原调用 ID 的 tool 消息。"""
    try:
        if "id" not in set(call) or "function" not in set(call):
            raise ValueError
        function = call["function"]
        name = function["name"]
        arguments = json.loads(function["arguments"])
        if not isinstance(name, str):
            raise ValueError("工具名必须是字符串")  # noqa: TRY004
        if name not in tool_table:
            raise ValueError(f"没有这个工具：{name}")
        if not isinstance(arguments, dict):
            raise ValueError("arguments 最外层必须是字典")  # noqa: TRY004
        result = tool_table[name](**arguments)
        content = json.dumps(result, ensure_ascii=False)
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OSError) as error:
        content = f"工具执行失败：{type(error).__name__}: {error}"
    return {"role": "tool", "tool_call_id": call["id"], "content": content}


def main() -> None:
    """展示列表、数字、无命中与错误回填，检查 content 的类型与原调用 ID。"""
    tool_table = {"search_notes": search_notes, "calculator": calculator}
    cases = [
        (
            "检索",
            "search_notes",
            '{"keyword":"青禾笔记本"}',
            "成功；content 解回 list，两条命中",
        ),
        ("计算", "calculator", '{"expression":"18 * 7"}', "成功；content 解回数字 126"),
        (
            "无命中",
            "search_notes",
            '{"keyword":"不存在的商品"}',
            "成功；content 为 [] 的 JSON 文本",
        ),
        ("未知工具", "delete_notes", "{}", "错误文字：ValueError"),
        ("坏 JSON", "calculator", '{"expression":', "错误文字：JSONDecodeError"),
        ("参数是列表", "calculator", "[]", "错误文字：ValueError"),
        (
            "不支持的算式",
            "calculator",
            '{"expression":"2 ** 3"}',
            "错误文字：ValueError",
        ),
    ]
    # enumerate(..., start=1) 为每一组生成不同 ID，便于核对是否用了原 ID。
    for index, (label, name, arguments, expected) in enumerate(cases, start=1):
        call = make_call(name, arguments, f"call_practice_{index}")
        print(f"\n{label}；期望：{expected}")
        print(f"原点单：{call}")
        message = build_tool_message(call, tool_table)
        print(f"实际 tool 消息：{message}")
        content = message["content"]
        print(f"content 的类型：{type(content).__name__}")
        if isinstance(content, str) and content.startswith("工具执行失败："):
            # 错误文字用于回填，不能当作成功结果再解析。
            continue
        # json.loads(JSON 文本) 用于核对成功 content 能否恢复原来的数据类型。
        restored = json.loads(content)
        print(f"解析 content 后：{type(restored).__name__}，{restored}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行后填写）
# 1. 检索返回的是列表，为什么 tool 消息的 content 却是 str？
#    对照“无命中”和“未知工具”两组，它们的区别是什么？
# 答：用json.dumps变成json文本了
#   无命中是content为"[]"，表示正确走完了流程，但是找不到相应的文本
#   未知工具是工具名不在支持的工具中，会将错误文字作为 tool 消息回填
# 2. 用 PyCharm 给 day24_retrieval_demo.py 的 Parameters 填 --live 并运行。
#    记录真实检索的关键词与出处、随后计算器的 expression、最终答复引用的出处。
#    算式里的两个数字分别来自哪里？若模型没有按这个顺序走，也如实记录。
# 我的运行：assistant 点单：search_notes({"keyword": "青禾笔记本"})
#   content：[{"source": "products.txt", "line": 2, "text": "青禾笔记本：单价 18 元/本，规格 A5。"}]
#   assistant 点单：calculator({"expression": "18*7"})
#   content：126
#   计算过程：单价 18 元/本 × 7 本 = 126 元（仅商品金额，不含其他费用）。
# 单价出处：products.txt 第 2 行 ——「青禾笔记本：单价 18 元/本，规格 A5。」
# 注意：以实际返回为准，核对计算器的数字是否来自问题与检索原文。
# 我的解释：18来自products.txt里的青禾笔记本：单价 18 元/本
#   7来自问题里的青禾笔记本买7本,模型就是按着这个顺序走的
