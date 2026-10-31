"""Day 42 的 AI 内存资料与对照环境，不实现学员的引用回查函数。

分数和数据库编号只为检查接口而手工设定，不是实际向量检索结果。
"""

from collections.abc import Callable
from copy import deepcopy

from langchain_core.documents import Document

CURRENT = "current/guide.md"
ARCHIVE = "archive/guide.md"
ORIGINAL_TEXTS = {
    CURRENT: (
        "光学工作坊领取说明\n借用观测镜需要出示绿色预约单。\n"
        "观测镜在一楼器材台领取。\n归还前请取下个人标签。\n开放日为每周六。"
    ),
    ARCHIVE: (
        "旧版领取说明\n登记\n核验\n借用观测镜需要出示绿色预约单。\n"
        "观测镜在一楼器材台领取。\n归还前请取下个人标签。"
    ),
}


def make_inputs() -> tuple[dict[str, Document], list[tuple[Document, float]]]:
    """每次新建 source→全文与三条候选；无磁盘文件、模型或数据库依赖。"""
    originals = {
        source: Document(
            id=source,
            page_content=text,
            metadata={"source": source, "line_count": len(text.splitlines())},
        )
        for source, text in ORIGINAL_TEXTS.items()
    }
    candidates = []
    for source, start, end, score in [
        (CURRENT, 2, 3, 0.81),
        (ARCHIVE, 4, 5, 0.81),
        (CURRENT, 4, 4, 0.43),
    ]:
        candidates.append(
            (
                Document(
                    id=f"{source}#L{start}-L{end}",
                    page_content="\n".join(
                        originals[source].page_content.splitlines()[start - 1 : end]
                    ),
                    metadata={"source": source, "line_start": start, "line_end": end},
                ),
                score,
            )
        )
    return originals, candidates


def show_originals() -> None:
    """显示内存全文、候选编号和手工分数，供学员独立核对。"""
    print("Day 42｜引用回查变式：资料、分数均为 AI 教具，不调用模型。")
    print("下面的来源名是内存标识，不声称存在同名磁盘文件。")
    originals, candidates = make_inputs()
    for source, original in originals.items():
        print(f"\n来源={source}")
        for number, line in enumerate(original.page_content.splitlines(), start=1):
            print(f"  {number}: {line}")
    print("\n本批候选（手工排定，分数不参与今天的函数）：")
    for chunk, score in candidates:
        print(f"  id={chunk.id}；分数={score}；正文={chunk.page_content!r}")
    print("假设数据库 point id 曾为 71/19/88；本批 Document.id 已恢复为原片段编号。")


def run_checks(learner_fn: Callable[..., list[Document]]) -> None:
    """打印十二组引用回查对照及输入不变检查；不提供回查实现或语义判分。"""
    show_originals()
    names = [
        "单条引用",
        "引用顺序与候选顺序相反，同正文两个来源均保留",
        "空引用",
        "本批不存在的原片段编号",
        "把数据库编号 71 当成引用",
        "被引用片段找不到全文",
        "正文存在但声明的行范围越过文末",
        "正文与位置正确，但片段 id 中的行号错误",
        "两条引用中第一条正常，第二条正文被改动",
        "未被引用的另一条候选损坏，只回查本次引用",
        "空引用、空候选与空全文字典",
        "第一条引用有全文，第二条引用缺少全文",
    ]
    for case_number, name in enumerate(names, start=1):
        originals, candidates = make_inputs()
        current, archive = candidates[0][0], candidates[1][0]
        cited_ids = [current.id]
        expected = [current]
        expect_error = False
        if case_number == 2:
            cited_ids = [archive.id, current.id]
            expected = [archive, current]
        elif case_number == 3:
            cited_ids = []
            expected = []
        elif case_number == 4:
            cited_ids = [f"{CURRENT}#L99-L99"]
            expect_error = True
        elif case_number == 5:
            cited_ids = ["71"]
            expect_error = True
        elif case_number == 6:
            cited_ids = [archive.id]
            del originals[ARCHIVE]
            expect_error = True
        elif case_number == 7:
            current.metadata.update(line_start=8, line_end=9)
            current.id = f"{CURRENT}#L8-L9"
            cited_ids = [current.id]
            expect_error = True
        elif case_number == 8:
            current.id = f"{CURRENT}#L1-L2"
            cited_ids = [current.id]
            expect_error = True
        elif case_number == 9:
            archive.page_content = "观测镜在地下室领取。"
            cited_ids = [current.id, archive.id]
            expect_error = True
        elif case_number == 10:
            archive.page_content = "观测镜在地下室领取。"
        elif case_number == 11:
            cited_ids = []
            candidates = []
            originals = {}
            expected = []
        elif case_number == 12:
            cited_ids = [current.id, archive.id]
            del originals[ARCHIVE]
            expect_error = True

        # deepcopy(对象)：独立复制检查输入，比较学员函数调用前后的内容。
        before = deepcopy((cited_ids, candidates, originals))
        print(f"\n对照 {case_number}｜{name}")
        print(f"引用输入={cited_ids}")
        for chunk, score in candidates:
            print(f"  候选={chunk.id}；metadata={chunk.metadata}；分数={score}")
            print(f"    正文={chunk.page_content!r}")
        print(f"全文来源键={list(originals)}")
        expected_display = (
            "ValueError" if expect_error else [doc.id for doc in expected]
        )
        try:
            actual = learner_fn(cited_ids, candidates, originals)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001 - 检查环境打印错误后继续下一组。
            consistent = expect_error and isinstance(error, ValueError)
            print(
                f"实际异常={type(error).__name__}: {error}；"
                f"期望={expected_display}；一致={consistent}"
            )
        else:
            valid_list = isinstance(actual, list) and all(
                isinstance(doc, Document) for doc in actual
            )
            display = [doc.id for doc in actual] if valid_list else repr(actual)
            consistent = not expect_error and valid_list and actual == expected
            print(f"实际={display}；期望={expected_display}；一致={consistent}")
        unchanged = (cited_ids, candidates, originals) == before
        print(f"输入未改动实际={unchanged}；期望=True；一致={unchanged}")
    print("\ncompleted 只表示十二组已运行；请核对全部一致项。观察写在 Day 42 验收 md。")
