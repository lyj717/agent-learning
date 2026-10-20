"""Day 37：固定行窗口切分与片段原文核对。

从仓库根目录运行本文件，分别传 --part a、--part b；默认 a，--help 只看用法。
后半部是 AI 提供的检查环境，输入和期望均为教学数据。
B 使用独立输入，可以单独运行；学员观察保留在文件末尾。
"""

import argparse
import sys
from pathlib import Path

from langchain_core.documents import Document

# 直接运行时先定位仓库根目录，再导入已经由学员完成的 Day 36 加载器。
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week05_rag.exercises.day36_sources_exercises import (
    load_sources,
)

MATERIALS = Path(__file__).resolve().parents[1] / "demos" / "day37" / "materials"


def chunk_documents(
    documents: list[Document], chunk_lines: int = 3, overlap_lines: int = 1
) -> list[Document]:
    """按固定行窗口与重叠切分全文，保留片段编号、来源和原始行范围。"""
    chunks = []
    step = chunk_lines - overlap_lines
    if chunk_lines < 1 or overlap_lines >= chunk_lines or overlap_lines < 0:
        raise ValueError
    for document in documents:
        text = document.page_content
        lines = text.splitlines()
        source = document.metadata["source"]
        if text.strip():
            for start in range(1, len(lines) + 1, step):
                stop = min(start - 1 + chunk_lines, len(lines))
                if len(lines) == 1:
                    window = lines[0]
                    chunk_text = window
                else:
                    window = lines[start - 1 : stop]
                    chunk_text = "\n".join(window)
                chunk = Document(
                    page_content=chunk_text,
                    metadata={"source": source, "line_start": start, "line_end": stop},
                    id=f"{source}#L{start}-L{stop}",
                )
                chunks.append(chunk)
                if stop == len(lines):
                    break
    return chunks


def matches_source(original: Document, chunk: Document) -> bool:
    """核对片段的来源、行范围和正文是否与给定全文一致。"""
    source_ok = False
    len_ok = False
    content_ok = False
    lines_text = []
    lines = original.page_content.splitlines()
    line_start = chunk.metadata["line_start"]
    line_end = chunk.metadata["line_end"]
    if original.metadata["source"] == chunk.metadata["source"]:
        source_ok = True
    if 1 <= line_start <= line_end <= len(lines):
        len_ok = True
    for number, line in enumerate(lines, start=1):
        if line_start <= number <= line_end:
            lines_text.append(line)
    content = "\n".join(lines_text)
    # print(f"{content=}")
    # print(f"{chunk.page_content=}")
    if content == chunk.page_content:
        content_ok = True
    # print(f"{source_ok=}, {len_ok=}, {content_ok=}")
    return source_ok and len_ok and content_ok


# ===== 以下是 AI 提供的检查环境，学员只需实现上面两个函数 =====
def show_ranges(documents: list[Document]) -> list[tuple[str, int, int]]:
    """把实际来源和范围提取出来打印，不实现切分或原文核对。"""
    return [
        (
            document.metadata.get("source"),
            document.metadata.get("line_start"),
            document.metadata.get("line_end"),
        )
        for document in documents
    ]


def show_a() -> None:
    """复用 Day 36 加载器，并用固定情境打印 A 的实际与期望。"""
    originals = load_sources(MATERIALS, ["policies/guide.txt", "archive/guide.txt"])
    # model_dump()：导出普通 Python 数据，供检查输入在调用后有没有被改动。
    before = [document.model_dump() for document in originals]
    actual = chunk_documents(originals)
    expected = [
        ("policies/guide.txt", 1, 3),
        ("policies/guide.txt", 3, 5),
        ("policies/guide.txt", 5, 7),
        ("archive/guide.txt", 1, 2),
    ]
    print("A｜复用你 Day 36 的加载器；资料目录：", MATERIALS)
    print(f"完整来源与行范围｜实际={show_ranges(actual)!r}｜期望={expected!r}")
    print(f"实际片段数={len(actual)}｜期望=4")
    for document in actual:
        print(f"\n实际 id：{document.id!r}；期望格式：来源#L起行-L末行")
        print(
            f"实际 metadata：{document.metadata!r}；期望键：source、line_start、line_end"
        )
        print(f"实际片段正文：{document.page_content!r}")
        # str.count(子串)：统计子串出现次数；此处只帮助检查真实换行符是否被保留。
        newline_count = document.page_content.count("\n")
        expected_newlines = (
            document.metadata["line_end"] - document.metadata["line_start"]
        )
        print(f"实际换行字符数：{newline_count}；按声明行范围期望：{expected_newlines}")
    print(
        f"原全文记录未修改：{before == [doc.model_dump() for doc in originals]}｜期望=True"
    )

    # 这些是固定检查输入和期望行范围，不是切分实现。
    cases = [
        ("刚到文末", "甲\n乙\n丙\n丁\n戊", 3, 1, [(1, 3), (3, 5)]),
        ("末尾不足窗口", "甲\n乙\n丙\n丁\n戊\n己", 3, 1, [(1, 3), (3, 5), (5, 6)]),
        ("没有重叠", "甲\n乙\n丙\n丁\n戊", 3, 0, [(1, 3), (4, 5)]),
        ("最大合法重叠", "甲\n乙\n丙\n丁", 3, 2, [(1, 3), (2, 4)]),
        ("重复正文不同位置", "重复\n甲\n重复\n甲\n重复", 3, 1, [(1, 3), (3, 5)]),
        ("长单行", "长" * 1200, 3, 1, [(1, 1)]),
    ]
    for label, text, size, overlap, ranges in cases:
        original = Document(
            page_content=text, metadata={"source": "memory.txt"}, id="memory.txt"
        )
        snapshot = original.model_dump()
        result = chunk_documents([original], chunk_lines=size, overlap_lines=overlap)
        expected_ranges = [("memory.txt", start, end) for start, end in ranges]
        print(f"\n{label}｜实际={show_ranges(result)!r}｜期望={expected_ranges!r}")
        print(f"原输入未修改：{snapshot == original.model_dump()}｜期望=True")
        if label == "重复正文不同位置":
            print("实际片段编号：", [document.id for document in result])
            print("实际正文：", [document.page_content for document in result])
            print("期望：正文相同，id 分别以 #L1-L3 和 #L3-L5 结尾。")
        if label == "长单行":
            print(
                "实际各片段字符数：",
                [len(document.page_content) for document in result],
            )
            print("期望：一个片段、1200 字符；窗口 3 行没有限制字符数。")

    blanks = [
        Document(page_content="", metadata={"source": "empty.txt"}),
        Document(page_content=" \t\n\n", metadata={"source": "blank.txt"}),
    ]
    print(f"\n空输入｜实际={chunk_documents([])!r}｜期望=[]")
    print(f"空白全文｜实际={chunk_documents(blanks)!r}｜期望=[]")
    for size, overlap in [(0, 0), (3, -1), (3, 3)]:
        try:
            chunk_documents([], chunk_lines=size, overlap_lines=overlap)
        except ValueError:
            print(f"无效参数 {size=}, {overlap=}｜实际=ValueError｜期望=ValueError")
        else:
            print(f"无效参数 {size=}, {overlap=}｜实际=未抛异常｜期望=ValueError")


def show_b() -> None:
    """提供独立全文和片段，打印 B 的来源与位置对照。"""
    original = Document(
        page_content="登记规则（AI 教学假数据）\n先核对。\n\n先核对。\n结束。\n",
        metadata={"source": "policies/guide.txt", "line_count": 5},
        id="policies/guide.txt",
    )
    print("B｜独立原始正文：", repr(original.page_content))
    for number, line in enumerate(original.page_content.splitlines(), start=1):
        print(f"原文第 {number} 行：{line!r}")
    print(f"原文实际总行数：{len(original.page_content.splitlines())}")
    # 各条来源与位置由 AI 明确指定；包含故意错误的待核对数据。
    cases = [
        ("第一处重复原文", "policies/guide.txt", 2, 2, "先核对。", True),
        ("另一处重复原文", "policies/guide.txt", 4, 4, "先核对。", True),
        ("范围含空行", "policies/guide.txt", 3, 4, "\n先核对。", True),
        ("正文不符", "policies/guide.txt", 2, 2, "先检查。", False),
        ("指错原始行", "policies/guide.txt", 3, 3, "先核对。", False),
        ("同名但来源不同", "archive/guide.txt", 2, 2, "先核对。", False),
        ("行号从零开始", "policies/guide.txt", 0, 2, "先核对。", False),
        ("终点超出全文", "policies/guide.txt", 4, 6, "先核对。\n结束。", False),
        ("起点晚于终点", "policies/guide.txt", 4, 3, "", False),
    ]
    original_snapshot = original.model_dump()
    for label, source, start, end, text, expected in cases:
        chunk = Document(
            page_content=text,
            id=f"{source}#L{start}-L{end}",
            metadata={"source": source, "line_start": start, "line_end": end},
        )
        snapshot = chunk.model_dump()
        actual = matches_source(original, chunk)
        print(
            f"{label}｜source={source}｜行={start}～{end}｜实际={actual!r}｜期望={expected}"
        )
        print(f"片段未修改：{snapshot == chunk.model_dump()}｜期望=True")
    print(f"原全文未修改：{original_snapshot == original.model_dump()}｜期望=True")
    empty = Document(page_content="", metadata={"source": "empty.txt"})
    probe = Document(
        page_content="任意文字",
        metadata={"source": "empty.txt", "line_start": 1, "line_end": 1},
        id="empty.txt#L1-L1",
    )
    print(f"空全文｜实际={matches_source(empty, probe)!r}｜期望=False")


def main() -> None:
    """选择 A 或 B，打印实际结果与期望供核对。"""
    parser = argparse.ArgumentParser(description="Day 37：固定行窗口与片段来源核对")
    parser.add_argument(
        "--part", choices=("a", "b"), default="a", help="选择 A 或 B 单独运行"
    )
    args = parser.parse_args()
    print("本入口只用 AI 教学数据；函数与观察由学员完成，不联网、不写输出文件。")
    if args.part == "a":
        show_a()
    else:
        show_b()


if __name__ == "__main__":
    main()


# ===== 现象与原因：学员实现并亲跑后填写，不另外建观察 md =====
# 1. A 的“重复正文不同位置”中，两个片段的正文、source、id 分别有何异同？
#    为什么不能直接把全文 id 原样用作每一片段的 id？
#    我的观察与原因：
#   正文：['重复\\n甲\\n重复', '重复\\n甲\\n重复'] source：memory.txt id：['memory.txt#L1-L3', 'memory.txt#L3-L5']
#   正文和source都相同，只有id不同
#   因为source相同的不同片段可能正文相同，直接把全文 id 原样用作每一片段的 id就无法判断具体出自哪个片段了
# 2. 五行全文在重叠 0 行与 1 行时，窗口范围怎样变化？为什么默认参数不再补 5～5 行？
#    我的观察与原因：
#   重叠从 0 行改为 1 行后，第二段的起点从第 4 行提前到了第 3 行，两段共享第 3 行。
#   默认参数不再补第 5～5 行，是因为第二段的第 3～5 行已经到达文末，全文的五行都已覆盖。 再补一段第 5～5 行，只会重复已经包含的第 5 行，没有新增内容，所以在窗口第一次到达文末时就停止。
# 3. B 中指向第 4 行的重复原文为什么能通过，而指向第 3 行或越过文末的不能？
#    原文中“存在这句话”和“这条片段的出处准确”有什么区别？
#    我的观察与原因：
#   第4行符合要求，来源文件一致，4～4 是合法范围，而且第 4 行的原文与片段正文“先核对。”完全相同
#   第三行和越过文末违反了要求,3～3 的范围合法，但第 3 行实际是空行，与片段正文“先核对。”不相同，属于正文与声明的位置不符。
#   指向第 4～6 行不能通过：全文只有 5 行，第 6 行不存在，属于声明的范围越界。即使已有部分的文字能对上，这个出处范围仍然不合法。
#    “原文中存在这句话”是在检查某处有没有这句话；“出处准确”还要检查记录填写的文件和具体位置是否对得上
# 4. “长单行”产生多少片段、每段多少字符？按行窗口能否保证模型的 token 上限？
#    我的观察与原因：
#   产生一个片段，1200个字符
#   不能，因为一行理论上可以无限长
