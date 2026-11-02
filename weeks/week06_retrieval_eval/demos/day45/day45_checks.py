"""AI 人工对照：分别验证关键词排名和 RRF，不给学员函数实现。"""

from collections.abc import Callable
from copy import deepcopy

from langchain_core.documents import Document


def show_case(
    name: str,
    fn: Callable[..., list[str]],
    args: tuple,
    expected: list[str] | type[ValueError],
) -> int:
    """运行一组对照、打印实际与期望，返回结果和输入检查的不一致数。"""
    before = deepcopy(args)
    try:
        actual = fn(*args)
    except NotImplementedError:
        raise
    except Exception as error:  # noqa: BLE001 - 汇总全部失败，最后统一报错。
        actual = type(error)
        print(f"异常={type(error).__name__}: {error}")
    if expected is ValueError:
        consistent = actual is ValueError
    else:
        consistent = isinstance(actual, list) and actual == expected
    unchanged = args == before
    print(f"对照={name}；实际={actual}；期望={expected}；结果一致={consistent}")
    print(f"输入未改动={unchanged}；期望=True")
    return int(not consistent) + int(not unchanged)


def run_keyword_checks(fn: Callable[..., list[str]]) -> None:
    """用独立人工词库检查 A，包含同分、空词库与参数先校验。"""

    def doc(name: str, text: str) -> Document:
        """构造单行人工文档，编号与来源独立于真实笔记。"""
        return Document(
            id=f"{name}.md#L1-L1",
            page_content=text,
            metadata={"source": f"{name}.md", "line_start": 1, "line_end": 1},
        )

    chunks = [
        doc("z-reset", "reset device reboot"),
        doc("billing", "invoice refund payment"),
        doc("weather", "weather forecast rain"),
        doc("dictionary", "python dictionary key"),
        doc("a-reset", "reset device reboot"),
        doc("library", "book borrow return"),
    ]
    a, z = "a-reset.md#L1-L1", "z-reset.md#L1-L1"
    billing, weather = "billing.md#L1-L1", "weather.md#L1-L1"
    zh_chunks = [
        doc("zh-device", "设备复位"),
        doc("zh-billing", "发票退款"),
        doc("zh-weather", "天气预报"),
        doc("zh-dictionary", "字典键值"),
    ]
    same_prefix_chunks = [
        doc("a-z-reset", "reset device reboot"),
        doc("a-a-reset", "reset device reboot"),
        *chunks[1:4],
        chunks[5],
    ]
    cases = [
        ("同分按编号，不按原输入先后", "reset", chunks, 3, [a, z]),
        ("问题大小写和标点按固定规则处理", "RESET!", chunks, 3, [a, z]),
        (
            "只匹配 reset 不保证包含 password 的依据",
            "reset password",
            chunks,
            3,
            [a, z],
        ),
        ("分数下标对应原文档", "invoice", chunks, 3, [billing]),
        (
            "中文问题与资料用同一词项规则",
            "怎么复位",
            zh_chunks,
            3,
            ["zh-device.md#L1-L1"],
        ),
        ("中文问题中的标点不作词项", "天气？", zh_chunks, 3, ["zh-weather.md#L1-L1"]),
        ("没有正分", "missingterm", chunks, 3, []),
        ("最后只取一条", "reset", chunks, 1, [a]),
        ("多词项且分数不同", "invoice reset", chunks, 3, [billing, a, z]),
        ("原片段逆序仍按规则排序", "reset", chunks[::-1], 3, [a, z]),
        (
            "同分且首字符相同，仍比较完整编号",
            "reset",
            same_prefix_chunks,
            3,
            ["a-a-reset.md#L1-L1", "a-z-reset.md#L1-L1"],
        ),
        ("空片段", "reset", [], 3, []),
        ("全部片段无词项", "reset", [doc("punctuation", "!!!")], 3, []),
        ("问题只有标点", "!!!", chunks, 3, []),
        ("有空正文也不丢下标关系", "reset", [doc("empty", ""), *chunks], 3, [a, z]),
        ("另一组同分", "invoice weather", chunks, 3, [billing, weather]),
        ("limit 大于正分数量", "reset", chunks, 20, [a, z]),
        ("limit=0 即使片段为空也拒绝", "reset", [], 0, ValueError),
        ("负 limit 即使片段为空也拒绝", "reset", [], -1, ValueError),
        ("limit 不接受 bool", "reset", chunks, True, ValueError),
        ("limit 不接受小数", "reset", chunks, 1.5, ValueError),
        ("空白问题即使片段为空也拒绝", "  ", [], 3, ValueError),
        ("空字符串问题拒绝", "", chunks, 3, ValueError),
    ]
    failures = 0
    print("A：AI 人工词库；不是实际笔记的实验。正分过滤是本课规则，不是答案判断。")
    for chunk in [*chunks, *zh_chunks, *same_prefix_chunks[:2]]:
        print(f"人工资料={chunk.id}；正文={chunk.page_content!r}")
    for name, query, current, limit, expected in cases:
        print(
            f"\n问题={query!r}；limit={limit}；输入编号={[doc.id for doc in current]}"
        )
        failures += show_case(name, fn, (query, current, limit), expected)
    print(f"\nA 汇总：{len(cases)} 组结果 + {len(cases)} 组输入检查；不一致={failures}")
    if failures:
        raise AssertionError(f"A 有 {failures} 项不一致，详见全部对照")


def run_fusion_checks(fn: Callable[..., list[str]]) -> None:
    """用人工两路排名检查 B，不把 RRF 分数当作相关标签。"""
    a, b, c, d, e = [f"{name}.md#L1-L1" for name in "abcde"]
    cases = [
        ("跨路同编号累加", [a, b], [c, b], 3, 60, [b, a, c]),
        ("关键词路为空", [b, a], [], 3, 60, [b, a]),
        ("向量路为空", [], [b, a], 3, 60, [b, a]),
        ("两路都空", [], [], 3, 60, []),
        ("两路完全一致只留唯一编号", [a, b], [a, b], 3, 60, [a, b]),
        ("同分按编号", [b, a], [a, b], 3, 60, [a, b]),
        ("完全不重合也能融合", [c, a], [b, d], 4, 60, [b, c, a, d]),
        ("融合之后再截取", [a, b], [c, b], 1, 60, [b]),
        ("默认平滑常量", [a, b, c], [d, e, c], 3, 60, [c, a, d]),
        ("非默认常量且名次从1开始", [a, b, c], [d, e, c], 3, 1, [a, c, d]),
        ("向量路截取范围外重复也拒绝", [a, b, a], [], 1, 60, ValueError),
        ("关键词路截取范围外重复也拒绝", [], [a, b, a], 1, 60, ValueError),
        ("limit=0 先于空排名校验", [], [], 0, 60, ValueError),
        ("负 limit 先于空排名校验", [], [], -1, 60, ValueError),
        ("limit 不接受 bool", [a], [], True, 60, ValueError),
        ("limit 不接受小数", [a], [], 1.5, 60, ValueError),
        ("常量为0拒绝", [a], [], 3, 0, ValueError),
        ("常量不接受 bool", [a], [], 3, True, ValueError),
        ("常量不接受小数", [a], [], 3, 1.5, ValueError),
        ("负常量先于空排名校验", [], [], 3, -1, ValueError),
    ]
    failures = 0
    print("B：AI 人工榜单；同一通道去重校验和跨通道合并是两件事。")
    for name, vector, keyword, limit, rank_constant, expected in cases:
        print(
            f"\n向量={vector}；关键词={keyword}；limit={limit}；rank_constant={rank_constant}"
        )
        failures += show_case(
            name, fn, (vector, keyword, limit, rank_constant), expected
        )
    print(f"\nB 汇总：{len(cases)} 组结果 + {len(cases)} 组输入检查；不一致={failures}")
    if failures:
        raise AssertionError(f"B 有 {failures} 项不一致，详见全部对照")
