"""Day 23 小练习 B：字典已经解析完，分别校验答复和行动的形状。"""


def read_final(data: dict) -> str:
    """从合法的 final 决定中取出 answer；不合法时抛 ValueError。"""
    if set(data) != {"kind", "answer"}:
        raise ValueError("字段不符！")
    if data["kind"] != "final":
        raise ValueError("字段值不符！")
    if not isinstance(data["answer"], str):
        # 协议约定形状错误抛 ValueError，而不是 TypeError。
        raise ValueError("答复必须是字符串！")  # noqa: TRY004
    if not data["answer"].strip():
        raise ValueError("答复为空！")
    return data["answer"]


def read_action(data: dict, allowed_tools: set[str]) -> tuple[str, dict]:
    """从合法的 action 决定中取出工具名和参数字典；否则抛 ValueError。"""
    if set(data) != {"kind", "tool", "arguments"}:
        raise ValueError("字段不符！")
    tool = data["tool"]
    arguments = data["arguments"]
    if data["kind"] != "action":
        raise ValueError("字段值不符！")
    if not isinstance(tool, str):
        # 先拒绝列表等非字符串，避免白名单检查时出现意外的 TypeError。
        raise ValueError("工具名必须是字符串！")  # noqa: TRY004
    if tool not in allowed_tools:
        raise ValueError("没有该工具！")
    if not isinstance(data["arguments"], dict):
        # 协议约定形状错误抛 ValueError，而不是 TypeError。
        raise ValueError("参数必须是字典！")  # noqa: TRY004
    return tool, arguments


def main() -> None:
    """分别打印 final 和 action 的对照组，不把它们拼成完整循环。"""
    final_cases = [
        ("正常答复", {"kind": "final", "answer": "共 12 件"}, "共 12 件"),
        ("空答复", {"kind": "final", "answer": "  "}, "ValueError"),
        (
            "多余字段",
            {"kind": "final", "answer": "12", "tool": "multiply"},
            "ValueError",
        ),
    ]
    for label, data, expected in final_cases:
        print(f"\nfinal：{label}；期望：{expected}")
        try:
            answer = read_final(data)
        except ValueError as error:
            print(f"实际：ValueError: {error}")
        else:
            print(f"实际：{answer!r}")

    action_cases = [
        (
            "正常行动",
            {
                "kind": "action",
                "tool": "multiply",
                "arguments": {"left": 3, "right": 4},
            },
            "('multiply', {'left': 3, 'right': 4})",
        ),
        (
            "未知工具",
            {"kind": "action", "tool": "erase_all", "arguments": {}},
            "ValueError",
        ),
        (
            "参数还是字符串",
            {"kind": "action", "tool": "multiply", "arguments": "{}"},
            "ValueError",
        ),
        ("缺参数", {"kind": "action", "tool": "multiply"}, "ValueError"),
    ]
    for label, data, expected in action_cases:
        print(f"\naction：{label}；期望：{expected}")
        try:
            decision = read_action(data, {"multiply"})
        except ValueError as error:
            print(f"实际：ValueError: {error}")
        else:
            print(f"实际：{decision!r}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行后填写）
# 1. 为什么 read_action 要检查工具名是否在 allowed_tools 中？
# 答：工具名不在支持的工具中的话到时候模型运行时找不到工具依然要报错而且更难纠错
# 2. --live 的真实正文里，kind、工具名和 arguments 各是什么？它能通过哪条规则？
#    先运行 day23_protocol_demo.py --live，再把看到的值填进来。
# 答：kind:action，工具名:multiply，arguments:"left":3,"right":4
#   能通过decode_json_reply以及read_action的所有规则
