"""AI 人工判分样例与对照；只检查汇总逻辑，不代判真实回答。"""

from collections.abc import Callable
from copy import deepcopy


def run_checks(fn: Callable[[list[dict]], dict]) -> None:
    """覆盖两种分母、拒答、不适用、空组、查重与待评阅；核对输入不变。"""

    def row(case_id: str, group: str, answer: bool, citation: bool | None) -> dict:
        """建立人工标志，不是模型判断或学员实验结果。"""
        return {
            "id": case_id,
            "group": group,
            "reviewed": True,
            "answer_ok": answer,
            "citation_ok": citation,
        }

    def group(total: int, correct: int, applicable: int, supported: int) -> dict:
        """声明独立对照中的计数与期望比率。"""
        return {
            "total": total,
            "answer_correct": correct,
            "answer_accuracy": correct / total if total else None,
            "citation_applicable": applicable,
            "citation_supported": supported,
            "citation_support_rate": supported / applicable if applicable else None,
        }

    empty = group(0, 0, 0, 0)
    mixed = [
        row("a", "vector", True, True),
        row("b", "vector", False, True),
        row("c", "vector", True, None),
        row("a", "fused", True, False),
        row("b", "fused", True, True),
        row("c", "fused", False, False),
    ]
    specs = [
        (
            "两组不同引用分母，答不全但已有说法受支持",
            mixed,
            {"vector": group(3, 2, 2, 2), "fused": group(3, 2, 3, 1)},
            None,
        ),
        ("空批次仍保留两组", [], {"vector": empty, "fused": empty}, None),
        (
            "正确拒答不进入引用分母",
            [row("x", "vector", True, None)],
            {"vector": group(1, 1, 0, 0), "fused": empty},
            None,
        ),
        (
            "运行失败仍进入回答分母",
            [row("x", "fused", False, None)],
            {"vector": empty, "fused": group(1, 0, 0, 0)},
            None,
        ),
        (
            "引用全错的零分与空组 None 不同",
            [row("x", "fused", False, False)],
            {"vector": empty, "fused": group(1, 0, 1, 0)},
            None,
        ),
        (
            "跨组同题号允许",
            [row("x", "vector", True, True), row("x", "fused", True, True)],
            {"vector": group(1, 1, 1, 1), "fused": group(1, 1, 1, 1)},
            None,
        ),
        ("同组同题号拒绝", [row("x", "vector", True, True)] * 2, None, ValueError),
    ]
    for name, field, value in [
        ("未知组", "group", "holdout"),
        ("空白题号", "id", " "),
        ("数字题号", "id", 1),
        ("尚未评阅", "reviewed", False),
        ("整数冒充已评阅", "reviewed", 1),
        ("正确性仍未填写", "answer_ok", None),
        ("整数冒充回答判分", "answer_ok", 1),
        ("整数冒充引用判分", "citation_ok", 0),
        ("字符串引用判分", "citation_ok", "false"),
    ]:
        bad = row("bad", "vector", True, True)
        bad[field] = value
        specs.append((name, [row("ok", "vector", True, True), bad], None, ValueError))
    failures = 0
    for name, values, expected, error_type in specs:
        values = deepcopy(values)
        before = deepcopy(values)
        try:
            result = fn(values)
            consistent = error_type is None and result == expected
            actual = result
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 逐项展示全部人工对照失败。
            actual = f"{type(error).__name__}: {error}"
            consistent = type(error) is error_type
        unchanged = values == before
        failures += int(not consistent) + int(not unchanged)
        print(f"对照={name}；实际={actual}；结果一致={consistent}")
        print(f"输入未改动={unchanged}")
    print(f"A：{len(specs)} 组结果与输入保持检查；不一致={failures}")
    if failures:
        raise AssertionError(f"A 有 {failures} 项不一致")
