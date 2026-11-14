"""AI 维护的 Day58 人工对照：裁判 prompt 的必需内容与解析函数的边界。

只提供输入与期望，不实现 build_judge_messages / parse_judge_verdict。
prompt 检查只核对「必需信息有没有交给模型」，不评价措辞好坏。
全部离线，不调用模型。
"""

import json
from collections.abc import Callable
from copy import deepcopy

CASE = {
    "id": "demo01",
    "question": "借用投影仪时，在哪里登记、要带什么？",
    "must_include": ["前台", "工牌"],
    "must_not_include": ["押金"],
    "retrieved_ids": ["demo/equipment.md#L1-L2"],
    "evidence": [
        {
            "id": "demo/equipment.md#L1-L2",
            "text": "借用前到前台登记，并带上工牌；归还时交回遥控器与电源线。",
        }
    ],
}

ANSWER = {
    "status": "answered",
    "answer": "先到前台登记，并带上工牌。",
    "cited_ids": ["demo/equipment.md#L1-L2"],
}

NO_CITATION_CASE = {
    **CASE,
    "id": "demo02",
    "retrieved_ids": ["demo/equipment.md#L1-L2"],
}

NO_CITATION_ANSWER = {
    "status": "answered",
    "answer": "先到前台登记，并带上工牌。",
    "cited_ids": [],
}


def _combined(messages: object) -> str:
    """把两条消息的 content 拼成一段，便于查关键词。"""
    if not isinstance(messages, list):
        return ""
    parts = []
    for message in messages:
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            parts.append(message["content"])
    return "\n".join(parts)


def _shape_ok(messages: object) -> bool:
    """核对两条消息、角色与内容类型。"""
    if not isinstance(messages, list) or len(messages) != 2:
        return False
    roles = [
        message.get("role") if isinstance(message, dict) else None
        for message in messages
    ]
    if roles != ["system", "user"]:
        return False
    return all(
        isinstance(message, dict)
        and isinstance(message.get("content"), str)
        and message["content"].strip()
        for message in messages
    )


def run_a(build_fn: Callable[..., list[dict]]) -> None:
    """检查 prompt 的必需内容，共 10 组。"""
    messages = build_fn(CASE, ANSWER)
    text = _combined(messages)
    lower = text.lower()
    user_text = ""
    if isinstance(messages, list) and len(messages) == 2:
        user_text = str(messages[1].get("content", ""))

    checks = [
        (
            "返回 system + user 两条消息，内容非空",
            _shape_ok(messages),
            "两条消息、角色与内容",
        ),
        ("包含 answer_ok 字段名", "answer_ok" in text, "answer_ok"),
        ("包含 citation_ok 字段名", "citation_ok" in text, "citation_ok"),
        ("说明没有引用时 citation_ok 用 null", "null" in lower, "null"),
        ("要求只输出 JSON", "json" in lower, "json"),
        ("用户消息包含问题原文", CASE["question"] in user_text, CASE["question"]),
        ("用户消息包含回答原文", ANSWER["answer"] in user_text, ANSWER["answer"]),
        (
            "用户消息包含证据编号与原文",
            all(
                item in user_text
                for item in [CASE["evidence"][0]["id"], CASE["evidence"][0]["text"]]
            ),
            "证据 id 与正文",
        ),
        (
            "不把 must_include / must_not_include 交给模型",
            "must_include" not in text and "must_not_include" not in text,
            "没有预期要点泄漏",
        ),
    ]

    no_citation = build_fn(NO_CITATION_CASE, NO_CITATION_ANSWER)
    checks.append(("没有引用时也能生成两条消息", _shape_ok(no_citation), "两条消息"))

    print("来源：AI 人工检查样本；没有模型或网络请求。")
    failures = 0
    for number, (name, ok, expected) in enumerate(checks, start=1):
        print(f"\n对照 {number}｜{name}")
        print(f"实际={ok}；期望=True；一致={ok}")
        print(f"核对项={expected}")
        failures += int(not ok)
    print(f"\n汇总：结果一致 {len(checks) - failures}/{len(checks)}")
    if failures:
        raise AssertionError("prompt 缺少必需内容，详见上方对照")


def _same_verdict(actual: object, expected: dict) -> bool:
    """核对三个键、布尔/None 类型与 reason 原文。"""
    if not isinstance(actual, dict) or set(actual) != {
        "answer_ok",
        "citation_ok",
        "reason",
    }:
        return False
    return (
        type(actual["answer_ok"]) is bool
        and actual["answer_ok"] is expected["answer_ok"]
        and actual["citation_ok"] is expected["citation_ok"]
        and isinstance(actual["reason"], str)
        and actual["reason"].strip() == expected["reason"]
    )


def run_b(parse_fn: Callable[[str], dict]) -> None:
    """检查解析与校验，共 10 组。"""
    valid = {"answer_ok": True, "citation_ok": None, "reason": "回答与原文一致。"}
    raw_valid = json.dumps(valid, ensure_ascii=False)
    raw_fenced = f"```json\n{raw_valid}\n```"

    cases: list[tuple[str, object, dict | type]] = [
        ("纯 JSON", raw_valid, valid),
        ("Markdown 代码块", raw_fenced, valid),
        (
            "JSON 前后带解释文字",
            f"判断如下：{raw_valid}",
            ValueError,
        ),
        ("缺少 reason", '{"answer_ok": true, "citation_ok": null}', ValueError),
        (
            "多出额外键",
            '{"answer_ok": true, "citation_ok": null, "reason": "一致", "confidence": 0.9}',
            ValueError,
        ),
        (
            "answer_ok 写成字符串",
            '{"answer_ok": "true", "citation_ok": null, "reason": "一致"}',
            ValueError,
        ),
        (
            "reason 不是字符串",
            '{"answer_ok": true, "citation_ok": null, "reason": 1}',
            ValueError,
        ),
        (
            "citation_ok 为 false 也合法",
            '{"answer_ok": true, "citation_ok": false, "reason": "引用不支持。"}',
            {"answer_ok": True, "citation_ok": False, "reason": "引用不支持。"},
        ),
        ("输入不是字符串", None, TypeError),
        ("空字符串", "   ", ValueError),
    ]

    print("来源：AI 人工检查样本；没有模型或网络请求。")
    failures = 0
    for number, (name, raw, expected) in enumerate(cases, start=1):
        before = deepcopy(raw)
        print(f"\n对照 {number}｜{name}")
        print(f"输入={raw!r}")
        try:
            actual = parse_fn(raw)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
            consistent = isinstance(expected, type) and isinstance(error, expected)
            print(f"实际异常={type(error).__name__}: {error}")
        else:
            consistent = isinstance(expected, dict) and _same_verdict(actual, expected)
            print(f"实际={actual}")
        expected_text = expected.__name__ if isinstance(expected, type) else expected
        print(f"期望={expected_text}；结果一致={consistent}")
        unchanged = raw == before
        print(f"输入未改动={unchanged}")
        failures += int(not consistent) + int(not unchanged)
    total = len(cases)
    print(f"\n汇总：结果一致 {total - failures}/{total}")
    if failures:
        raise AssertionError("解析结果与期望不一致，详见上方对照")
