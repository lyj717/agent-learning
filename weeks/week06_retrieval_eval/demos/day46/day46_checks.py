"""AI 人工对照：检查批量整合、留出隔离、参数传递和失败路径，不实现练习。"""

from collections.abc import Callable
from copy import deepcopy

from langchain_core.documents import Document

from weeks.week06_retrieval_eval.demos.shared.evaluation_functions import score_query


def ids(names: str) -> list[str]:
    """把人工字母编号展开成演示片段编号，不表示仓库文件。"""
    return [f"{name}.md#L1-L1" for name in names]


def sample(case_id: str, question: str, relevant: str, split: str = "dev") -> dict:
    """构造格式已经确认的人工题，相关依据只取一行。"""
    return {
        "id": case_id,
        "split": split,
        "question": question,
        "answerable": bool(relevant),
        "evidence": [
            {"source": f"{name}.md", "line_start": 1, "line_end": 1}
            for name in relevant
        ],
    }


def summary(total: int, answerable: int, hit: float | None, candidates: int) -> dict:
    """为固定人工题给出完整期望汇总；这些题命中时均只有一块相关项，k=3。"""
    return {
        "total": total,
        "answerable_count": answerable,
        "no_answer_count": total - answerable,
        "mean_hit": hit,
        "mean_recall": hit,
        "mean_precision": None if hit is None else hit / 3,
        "no_answer_with_candidates": candidates,
    }


def make_search(
    name: str, corpus: list[Document], rank_map: dict, calls: list
) -> Callable[[str, int], list[str]]:
    """为一组人工对照绑定独立参数，返回记录调用的向量替身。"""

    def search(question: str, limit: int) -> list[str]:
        """只返回预写榜单；错误类型分支故意违反返回类型以验证拒绝行为。"""
        calls.append((question, limit))
        if question == "DO NOT SEARCH":
            raise AssertionError("不允许检索留出题")
        if name.endswith("duplicate"):
            return ids("aa")
        if name.endswith("unknown"):
            return ids("x")
        if name.endswith("too_many"):
            return ids("abcd")
        if name.endswith("wrong_type"):
            return tuple(ids("a"))
        if name.endswith("runtime"):
            raise RuntimeError("人工检索失败")
        return rank_map[question][:limit] if corpus else []

    return search


def run_comparison_checks(fn: Callable[..., dict]) -> None:
    """逐组核对完整结构、人工期望、输入保持及实际回调清单。"""
    chunks = [
        Document(
            id=ids(name)[0],
            page_content=text,
            metadata={"source": f"{name}.md", "line_start": 1, "line_end": 1},
        )
        for name, text in zip(
            "abcdzfg",
            ["weather", "invoice", "r", "s", "t", "clock", "boat"],
            strict=True,
        )
    ]
    first = sample("dev-r", "r", "c")
    second = sample("dev-t", "t", "z")
    no_answer = sample("dev-none", "missing", "")
    holdout = sample("holdout", "DO NOT SEARCH", "c", "holdout")
    # 每行：题号、问题、相关编号、向量榜、关键词榜、融合榜。全部期望排名手工给出。
    normal_rows = [
        ("dev-r", "r", "c", "abz", "c", "acb"),
        ("dev-t", "t", "z", "zab", "z", "zab"),
        ("dev-none", "missing", "", "a", "", "a"),
    ]
    rank_map = {
        "r": ids("abz"),
        "t": ids("zab"),
        "missing": ids("a"),
        "r s t": ids("abz"),
    }
    empty_summary = summary(0, 0, None, 0)
    specs = [
        (
            "混合批次：逐题、宏平均与留出隔离",
            [first, holdout, second, no_answer],
            chunks,
            3,
            60,
            normal_rows,
            summary(3, 2, 0.5, 1),
            summary(3, 2, 1.0, 1),
            None,
            3,
        ),
        (
            "空批次仍返回完整汇总",
            [],
            chunks,
            3,
            60,
            [],
            empty_summary,
            empty_summary,
            None,
            0,
        ),
        (
            "只有留出题，不调用检索",
            [holdout],
            chunks,
            3,
            60,
            [],
            empty_summary,
            empty_summary,
            None,
            0,
        ),
        (
            "无答案题保留候选计数",
            [no_answer],
            chunks,
            3,
            60,
            [normal_rows[2]],
            summary(1, 0, None, 1),
            summary(1, 0, None, 1),
            None,
            1,
        ),
        (
            "空库无答案题也能完成",
            [no_answer],
            [],
            3,
            60,
            [("dev-none", "missing", "", "", "", "")],
            summary(1, 0, None, 0),
            summary(1, 0, None, 0),
            None,
            1,
        ),
        (
            "非默认 k=1 传到每路与评分",
            [first],
            chunks,
            1,
            60,
            [("dev-r", "r", "c", "a", "c", "a")],
            summary(1, 1, 0.0, 0),
            summary(1, 1, 0.0, 0),
            None,
            1,
        ),
        (
            "rank_constant=1 的名次变化",
            [sample("dev-c", "r s t", "z")],
            chunks,
            3,
            1,
            [("dev-c", "r s t", "z", "abz", "cdz", "acz")],
            summary(1, 1, 1.0, 0),
            summary(1, 1, 1.0, 0),
            None,
            1,
        ),
        (
            "rank_constant=60 的名次变化",
            [sample("dev-c", "r s t", "z")],
            chunks,
            3,
            60,
            [("dev-c", "r s t", "z", "abz", "cdz", "zac")],
            summary(1, 1, 1.0, 0),
            summary(1, 1, 1.0, 0),
            None,
            1,
        ),
        (
            "多处依据仍按题平均，不合并分母",
            [sample("multi", "r", "cz"), second],
            chunks,
            3,
            60,
            [("multi", "r", "cz", "abz", "c", "acb"), normal_rows[1]],
            {**summary(2, 2, 1.0, 0), "mean_recall": 0.75},
            {**summary(2, 2, 1.0, 0), "mean_recall": 0.75},
            None,
            2,
        ),
        (
            "重复 dev 编号在检索前拒绝",
            [first, first],
            chunks,
            3,
            60,
            None,
            None,
            None,
            ValueError,
            0,
        ),
        (
            "后题依据落空也先拒绝整批",
            [first, sample("outside", "outside", "x")],
            chunks,
            3,
            60,
            None,
            None,
            None,
            ValueError,
            0,
        ),
    ]
    for name, value in [("零", 0), ("负数", -1), ("布尔", True), ("小数", 1.5)]:
        specs.append(
            (
                f"k 为{name}，空批次也拒绝",
                [],
                chunks,
                value,
                60,
                None,
                None,
                None,
                ValueError,
                0,
            )
        )
        specs.append(
            (
                f"常量为{name}，空批次也拒绝",
                [],
                chunks,
                3,
                value,
                None,
                None,
                None,
                ValueError,
                0,
            )
        )
    for mode, error in [
        ("duplicate", ValueError),
        ("unknown", ValueError),
        ("too_many", ValueError),
        ("wrong_type", TypeError),
        ("runtime", RuntimeError),
    ]:
        specs.append(
            (f"回调异常：{mode}", [first], chunks, 3, 60, None, None, None, error, 1)
        )

    failures = 0
    for (
        name,
        cases,
        corpus,
        k,
        constant,
        expected_rows,
        before,
        after,
        expected_error,
        expected_calls,
    ) in specs:
        cases, corpus = deepcopy((cases, corpus))
        original = deepcopy((cases, corpus))
        calls = []

        search = make_search(name, corpus, rank_map, calls)
        try:
            actual = fn(cases, corpus, search, k=k, rank_constant=constant)
            if expected_error is not None:
                raise AssertionError(f"应抛 {expected_error.__name__}，实际返回成功")
            assert set(actual) == {"rows", "vector_summary", "fused_summary"}
            assert actual["vector_summary"] == before
            assert actual["fused_summary"] == after
            assert len(actual["rows"]) == len(expected_rows)
            for row, expected in zip(actual["rows"], expected_rows, strict=True):
                case_id, question, relevant, vector, keyword, fused = expected
                expected_fields = {
                    "id": case_id,
                    "question": question,
                    "relevant_ids": ids(relevant),
                    "vector_ids": ids(vector),
                    "keyword_ids": ids(keyword),
                    "fused_ids": ids(fused),
                }
                assert set(row) == set(expected_fields) | {
                    "vector_metrics",
                    "fused_metrics",
                }
                assert {key: row[key] for key in expected_fields} == expected_fields
                assert row["vector_metrics"] == score_query(
                    ids(vector), set(ids(relevant)), k=k
                )
                assert row["fused_metrics"] == score_query(
                    ids(fused), set(ids(relevant)), k=k
                )
            assert calls == [(row[1], k) for row in expected_rows]
            print(
                f"对照={name}；实际题号={[row['id'] for row in actual['rows']]}；结果一致=True"
            )
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 汇总全部人工对照，不遮蔽未实现。
            consistent = expected_error is not None and type(error) is expected_error
            failures += int(not consistent)
            print(
                f"对照={name}；实际={type(error).__name__}: {error}；期望={expected_error}；结果一致={consistent}"
            )
        unchanged = (cases, corpus) == original
        calls_ok = len(calls) == expected_calls
        failures += int(not unchanged) + int(not calls_ok)
        print(
            f"输入未改动={unchanged}；回调次数={len(calls)}；期望={expected_calls}；次数一致={calls_ok}"
        )
    print(f"\nA：{len(specs)} 组结果、输入与回调检查；不一致={failures}")
    if failures:
        raise AssertionError(f"A 有 {failures} 项不一致，请按完整输出订正")
