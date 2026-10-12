"""Day 25 小练习 B：由应用权限决定是否执行代码工具并回填观察。"""

import json

from day24_observation_exercises import build_tool_message
from day24_retrieval_demo import make_call
from day25_code_demo import run_limited_code


def build_code_observation(call: dict, allow_code: bool, tool_table: dict) -> dict:
    """按应用给的权限返回 tool 消息，获准时才真正执行工具。"""
    if allow_code is False:
        return {
            "role": "tool",
            "tool_call_id": call["id"],
            "content": "工具执行失败：PermissionError: 本次请求未获代码执行权限",
        }
    return build_tool_message(call, tool_table)


def must_not_run(code: str) -> dict:
    """验证拒绝分支没有偷偷执行代码；若被调用就让主程序响亮失败。"""
    raise AssertionError(f"未获权限却执行了：{code}")


def main() -> None:
    """对照获准、未获准和获准但语法被拒的三种观察。"""
    code = "unit_price = 18\nquantity = 7\nunit_price * quantity"
    allowed_call = make_call("run_code", json.dumps({"code": code}), "call_allowed")
    allowed_table = {"run_code": run_limited_code}
    print("\n应用授权代码工具；期望：ok=true、value=126")
    allowed = build_code_observation(allowed_call, True, allowed_table)
    print(f"实际 tool 消息：{allowed}")
    print(f"解析 content 后：{json.loads(allowed['content'])}")

    denied_call = make_call("run_code", json.dumps({"code": code}), "call_denied")
    print("\n应用未授权；期望：PermissionError 回填，must_not_run 不被调用")
    denied = build_code_observation(denied_call, False, {"run_code": must_not_run})
    print(f"实际 tool 消息：{denied}")

    blocked_call = make_call(
        "run_code", json.dumps({"code": 'open("private.txt")'}), "call_blocked"
    )
    print("\n应用已授权，但代码越过语法白名单；期望：ok=false、Call 被拒")
    blocked = build_code_observation(blocked_call, True, allowed_table)
    print(f"实际 tool 消息：{blocked}")
    print(f"解析 content 后：{json.loads(blocked['content'])}")


if __name__ == "__main__":
    main()


# 现象与原因
# 1. 未授权和已授权但代码被拒，两条 tool 消息的 content 有什么不同？
# 答：未授权：'content': '工具执行失败：PermissionError: 本次请求未获代码执行权限'
#   已授权但代码被拒: 'content': '{"ok": false, "error": "ValueError: 不允许的语法：Call"}'
# 2. 为什么 allow_code 必须来自应用，而不能让模型在 arguments 里写 allow_code=true？
# 答：允许的代码必须由自己的程序来判断而不能交给模型来判断
