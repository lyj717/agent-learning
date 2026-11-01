"""AI 人工资料的投影对照；不使用学员真实问题，不提供投影实现。"""

from collections.abc import Callable
from copy import deepcopy

from langchain_core.documents import Document


def run_checks(project_fn: Callable[..., set[str]]) -> None:
    """检查同源、闭区间相交、跨多个依据去重与输入不变。"""

    def span(start: int, end: int, source: str = "guide.md") -> dict:
        """构造已校验的人工依据行范围。"""
        return {"source": source, "line_start": start, "line_end": end}

    chunks = [
        Document(id="guide.md#L1-L3", page_content="人工片段甲", metadata=span(1, 3)),
        Document(id="guide.md#L3-L5", page_content="人工片段乙", metadata=span(3, 5)),
        Document(id="guide.md#L6-L7", page_content="人工片段丙", metadata=span(6, 7)),
        Document(
            id="archive/guide.md#L3-L4",
            page_content="人工片段乙",
            metadata=span(3, 4, "archive/guide.md"),
        ),
    ]
    first, second, third, archive = [chunk.id for chunk in chunks]
    cases = [
        ("第一行", [span(1, 1)], chunks, {first}),
        ("重叠边界第3行属于两块", [span(3, 3)], chunks, {first, second}),
        ("第5行属于第二块", [span(5, 5)], chunks, {second}),
        ("依据跨两块且不要求整段被单块包含", [span(4, 6)], chunks, {second, third}),
        ("多处依据分散在两块", [span(1, 1), span(7, 7)], chunks, {first, third}),
        (
            "两处依据落在同一块，只收一个编号",
            [span(4, 4), span(5, 5)],
            chunks,
            {second},
        ),
        ("同名不同来源不能混入", [span(3, 4, "archive/guide.md")], chunks, {archive}),
        ("同正文不能代替来源匹配", [span(4, 4)], chunks, {second}),
        ("无答案空依据", [], chunks, set()),
        ("空片段列表", [span(1, 1)], [], set()),
        ("此批没有所标来源", [span(1, 1, "other.md")], chunks, set()),
        ("此批范围不覆盖依据", [span(8, 8)], chunks, set()),
        ("同时覆盖三块", [span(2, 6)], chunks, {first, second, third}),
        ("片段顺序改变不影响集合", [span(3, 3)], chunks[::-1], {first, second}),
    ]
    failures = 0
    print("AI 人工对照；相关规则为同一 source 且至少共享一个依据行，包含端点。")
    for number, (name, evidence, current, expected) in enumerate(cases, start=1):
        before = deepcopy((evidence, current))
        print(f"\n对照 {number}｜{name}；依据={evidence}")
        print(f"本批片段={[chunk.id for chunk in current]}")
        try:
            actual = project_fn(evidence, current)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总所有失败，最后统一报错。
            actual = f"{type(error).__name__}: {error}"
        consistent = isinstance(actual, set) and actual == expected
        unchanged = (evidence, current) == before
        print(f"实际={actual}；期望={expected}；结果一致={consistent}")
        print(f"输入未改动={unchanged}；期望=True")
        failures += int(not consistent) + int(not unchanged)
    print(f"\n汇总：{len(cases)} 组结果 + {len(cases)} 组输入检查；不一致={failures}")
    if failures:
        raise AssertionError(f"共 {failures} 项不一致，详见全部对照")
