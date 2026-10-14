"""Day 27 的离线假模型：只提供可控点单，不实现学员的 Agent 循环。

运行入口在 day27_integrated_exercises.py；这里的回复不是联网模型输出。
"""

import json
import re


def _call(name: str, arguments: dict, call_id: str) -> dict:
    """制作一条原生工具调用。"""
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            # json.dumps(对象, ensure_ascii=False) 把参数变为原生接口需要的 JSON 文本。
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def _tool_result(messages: list[dict], call_id: str) -> str:
    """确认最后一条消息确实是指定调用的工具观察。"""
    last = messages[-1]
    if last.get("role") != "tool" or last.get("tool_call_id") != call_id:
        raise AssertionError(f"假模型等不到 {call_id} 对应的 tool 回填")
    return last["content"]


def _price_from_search(messages: list[dict]) -> tuple[int, str]:
    """从上一条检索观察读价格和出处，供假模型下一步点单。"""
    raw = _tool_result(messages, "call_search")
    hits = json.loads(raw)
    if not isinstance(hits, list) or not hits:
        raise AssertionError("假模型没有收到非空检索结果")
    hit = hits[0]
    match = re.search(r"单价 (\d+) 元", hit["text"])
    if match is None:
        raise AssertionError("检索原文没有可读的单价")
    return int(match.group(1)), f"{hit['source']}:{hit['line']}"


def fake_chat(messages: list[dict], *, scenario: str, timeout_seconds: float) -> dict:
    """按消息历史给一条假响应，包含 message、finish_reason 和 usage。"""
    if scenario == "slow_model" and timeout_seconds < 0.2:
        # 教学用的确定性超时：没有真的等待 0.2 秒。
        raise TimeoutError("假模型请求超过单次上限")

    step = sum(message.get("role") == "assistant" for message in messages) + 1
    question = messages[0]["content"]
    # re.search(模式, 文本) 找题目里的件数；这段只属于假模型的固定情境。
    quantity_match = re.search(r"(\d+)", question)
    quantity = int(quantity_match.group(1)) if quantity_match else 5
    usage = {"prompt_tokens": 18 + step, "completion_tokens": 7}
    if scenario == "usage_unknown":
        usage = None
    elif scenario == "token_budget":
        usage = {"prompt_tokens": 80, "completion_tokens": 20}

    call = None
    answer = None
    if scenario in {"normal", "code", "usage_unknown", "token_budget"}:
        if step == 1:
            call = _call(
                "search_notes", {"keyword": "蓝湾便签", "limit": 2}, "call_search"
            )
        elif step == 2:
            price, _ = _price_from_search(messages)
            if scenario == "code":
                program = f"unit_price = {price}\nquantity = {quantity}\nunit_price * quantity"
                call = _call("run_code", {"code": program}, "call_code")
            else:
                call = _call(
                    "calculator", {"expression": f"{price} * {quantity}"}, "call_calc"
                )
        elif step == 3:
            call_id = "call_code" if scenario == "code" else "call_calc"
            result = _tool_result(messages, call_id)
            if result.startswith("工具执行失败："):
                answer = f"无法计算：{result}"
            else:
                value = json.loads(result)
                if isinstance(value, dict):
                    if value.get("ok"):
                        value = value["value"]
                    else:
                        answer = f"受限数值工具拒绝：{value.get('error')}"
                if answer is None:
                    _, source = _price_from_search(messages[:-2])
                    answer = f"蓝湾便签 {quantity} 本共 {value} 元；单价出处 {source}。"
    elif scenario == "no_hit":
        if step <= 2:
            if step == 2 and _tool_result(messages, "call_missing_1") != "[]":
                raise AssertionError("无命中应回填 []")
            call = _call(
                "search_notes",
                {"keyword": "不存在的商品", "limit": 2},
                f"call_missing_{step}",
            )
        else:
            answer = "没有查到单价，无法计算。"
    elif scenario == "bad_args":
        if step == 1:
            call = _call("calculator", {"expression": ["11", "5"]}, "call_bad")
        else:
            answer = f"参数错误，无法计算：{_tool_result(messages, 'call_bad')}"
    elif scenario == "continuous_error":
        if step <= 2:
            if step == 2 and "工具执行失败：" not in _tool_result(
                messages, "call_error_1"
            ):
                raise AssertionError("错误观察没有回填")
            call = _call("calculator", {"expression": "11 ** 5"}, f"call_error_{step}")
        else:
            answer = "反复失败，无法计算。"
    elif scenario == "slow_model":
        answer = "这个分支仅用于单次超时对照。"
    else:
        raise ValueError(f"未知假模型情境：{scenario}")

    if call is None and answer is None:
        raise AssertionError(f"假模型在第 {step} 次请求后仍未结束")
    message = {
        "role": "assistant",
        "content": answer,
        "tool_calls": [call] if call is not None else [],
    }
    return {
        "message": message,
        "finish_reason": "tool_calls" if call is not None else "stop",
        "usage": usage,
    }


def main() -> None:
    """只展示假模型的第一次点单，不替学员运行工具或写循环。"""
    messages = [{"role": "user", "content": "蓝湾便签买 5 本多少钱？"}]
    response = fake_chat(messages, scenario="normal", timeout_seconds=1.0)
    call = response["message"]["tool_calls"][0]
    print("这是什么：离线假模型按已收到的消息，给一条固定情境的 assistant 回复。")
    print("为什么需要：写 Agent 循环时，可以稳定检查点单和回填，不必每次联网。")
    print("场景：用户问蓝湾便签总价，模型第一步决定先检索单价。")
    print(f"工具名：{call['function']['name']}")
    print(f"参数 JSON：{call['function']['arguments']}")
    print(f"调用 ID：{call['id']}")
    print(f"结束原因：{response['finish_reason']}；教学假 usage：{response['usage']}")
    print("注意：这一步只有 assistant 点单；尚未执行检索，也没有 tool 观察或最终答复。")


if __name__ == "__main__":
    main()
