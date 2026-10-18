"""Day 28 的离线变式点单器；只产生响应，不实现 Agent 循环。"""

import json
import re

QUESTION = "暮云贴纸买 6 包多少钱？请说明单价出处。"


def _call(name: str, arguments: dict, call_id: str) -> dict:
    """制作一条带原生 JSON 参数的工具点单。"""
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def _observation(messages: list[dict], call_id: str) -> str:
    """从消息历史中读取指定调用的工具观察。"""
    for message in reversed(messages):
        if message.get("role") == "tool" and message.get("tool_call_id") == call_id:
            return message["content"]
    raise AssertionError(f"未收到 {call_id} 对应的工具观察")


def _price_and_source(messages: list[dict]) -> tuple[int, str]:
    """从已回填的检索结果取得单价及文件出处。"""
    hits = json.loads(_observation(messages, "day28_search"))
    if not isinstance(hits, list) or not hits:
        raise AssertionError("新商品没有检索命中")
    for hit in hits:
        if "暮云贴纸" in hit["text"] and "单价" in hit["text"]:
            match = re.search(r"单价 (\d+) 元", hit["text"])
            if match is None:
                raise AssertionError("检索原文没有可读的单价")
            return int(match.group(1)), f"{hit['source']}:{hit['line']}"
    raise AssertionError("检索结果中没有新商品的单价")


def _answer_from_observation(messages: list[dict], call_id: str, quantity: int) -> str:
    """根据计算观察生成最终答复，错误观察则生成失败答复。"""
    observation = _observation(messages, call_id)
    if observation.startswith("工具执行失败："):
        return f"无法计算：{observation}"
    result = json.loads(observation)
    if isinstance(result, dict):
        if not result.get("ok"):
            return f"受限数值工具拒绝：{result.get('error')}"
        result = result["value"]
    _, source = _price_and_source(messages)
    return f"暮云贴纸 {quantity} 包共 {result} 元；单价出处 {source}。"


def fake_chat(messages: list[dict], *, scenario: str, timeout_seconds: float) -> dict:
    """按新问题与历史消息返回一条假模型响应。"""
    if timeout_seconds <= 0:
        raise TimeoutError("本次请求没有剩余时间")
    if scenario not in {"normal", "recover", "code"}:
        raise ValueError(f"未知 Day 28 情境：{scenario}")
    if not messages or messages[0].get("content") != QUESTION:
        raise ValueError("Day 28 假模型只处理本日新问题")

    quantity_match = re.search(r"(\d+)", QUESTION)
    if quantity_match is None:
        raise AssertionError("新问题没有购买数量")
    quantity = int(quantity_match.group(1))
    step = sum(message.get("role") == "assistant" for message in messages) + 1
    call = None
    answer = None

    if step == 1:
        call = _call(
            "search_notes", {"keyword": "暮云贴纸", "limit": 2}, "day28_search"
        )
    elif step == 2:
        price, _ = _price_and_source(messages)
        if scenario == "recover":
            call = _call(
                "calculator", {"expression": f"{price} ** {quantity}"}, "day28_bad"
            )
        elif scenario == "code":
            program = (
                f"unit_price = {price}\nquantity = {quantity}\nunit_price * quantity"
            )
            call = _call("run_code", {"code": program}, "day28_code")
        else:
            call = _call(
                "calculator", {"expression": f"{price} * {quantity}"}, "day28_calc"
            )
    elif step == 3 and scenario == "recover":
        if not _observation(messages, "day28_bad").startswith("工具执行失败："):
            raise AssertionError("修正算式前应先收到失败观察")
        price, _ = _price_and_source(messages)
        call = _call(
            "calculator", {"expression": f"{price} * {quantity}"}, "day28_fixed"
        )
    elif step == 3:
        call_id = "day28_code" if scenario == "code" else "day28_calc"
        answer = _answer_from_observation(messages, call_id, quantity)
    elif step == 4 and scenario == "recover":
        answer = _answer_from_observation(messages, "day28_fixed", quantity)
    else:
        raise AssertionError(f"Day 28 假模型在第 {step} 次请求后仍未结束")

    return {
        "message": {
            "role": "assistant",
            "content": answer,
            "tool_calls": [call] if call is not None else [],
        },
        "finish_reason": "tool_calls" if call is not None else "stop",
        "usage": {"prompt_tokens": 30 + step, "completion_tokens": 8},
    }
