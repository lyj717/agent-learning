"""Day 23 小练习 A：只处理模型正文到 Python 字典的第一关。"""

import json


def decode_json_reply(raw: str, finish_reason: str) -> dict:
    """把完整的 JSON 正文解析成字典；失败时抛 ValueError。"""
    if finish_reason == "length":
        raise ValueError("解析失败！模型输出被截断")
    elif finish_reason != "stop":
        raise ValueError(f"解析失败！结束原因：{finish_reason}")
    if not raw.strip():
        raise ValueError("解析失败！正文为空")
    try:
        reply = json.loads(raw)
        if not isinstance(reply, dict):
            # 协议约定形状错误也抛 ValueError，而不是 TypeError。
            raise ValueError("解析失败！最外层不是字典")  # noqa: TRY004
        return reply
    except json.JSONDecodeError:
        raise ValueError("解析错误！JSON语法错误")


def main() -> None:
    """打印每种输入的结果，让学员自己核对是否符合预期。"""
    cases = [
        (
            "正常行动",
            '{"kind":"action","tool":"multiply","arguments":{"left":3,"right":4}}',
            "stop",
            "返回 dict",
        ),
        ("输出截断", '{"kind":"final","answer":"12"}', "length", "ValueError"),
        ("空正文", "  ", "stop", "ValueError"),
        ("合法 JSON 列表", '["action"]', "stop", "ValueError"),
        ("坏 JSON", '{"kind":', "stop", "ValueError"),
        ("异常结束原因", "{}", "content_filter", "ValueError"),
    ]
    for label, raw, finish_reason, expected in cases:
        print(f"\n{label}；期望：{expected}")
        try:
            result = decode_json_reply(raw, finish_reason)
        except ValueError as error:
            print(f"实际：ValueError: {error}")
        else:
            print(f"实际：{type(result).__name__}: {result}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行后填写）
# 1. “输出截断”这一组的正文看起来是合法 JSON，为什么仍要拒绝？
# 答：因为停止原因是length，表示输出可能被截断，不能认定为完整决定
# 2. “合法 JSON 列表”能被 json.loads 解析，为什么仍不能交给下一关？
# 答：被json.loads解析只能说明符合json格式，并不能说明这段文本符合要求，本函数就要求最外层必须是字典
