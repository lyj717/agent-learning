"""Day 36：加载文本资料并核对原始行位置。

从仓库根运行：
    .venv\\Scripts\\python.exe -B weeks/week05_rag/exercises/day36_sources_exercises.py --part a
    .venv\\Scripts\\python.exe -B weeks/week05_rag/exercises/day36_sources_exercises.py --part b

不带 --part 默认运行 A；B 使用独立内存资料。--help 查看命令用法。
下面所有预设输入和期望都是 AI 教学数据，不作为学员实验记录。
"""

import argparse
from pathlib import Path

from langchain_core.documents import Document

DAY_DIR = Path(__file__).resolve().parents[1] / "demos" / "day36"
MATERIALS = DAY_DIR / "materials"


def load_sources(root: Path, relative_paths: list[str]) -> list[Document]:
    """按清单读取非空 UTF-8 文本，保留全文、相对来源与行数。"""
    l_doc = []
    for r_path in relative_paths:
        path = root / r_path
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if text.strip():
            l_doc.append(
                Document(
                    page_content=text,
                    metadata={"source": r_path, "line_count": len(lines)},
                    id=r_path,
                )
            )
    return l_doc


def locate_quote(document: Document, quote: str) -> list[int]:
    """返回非空白引用与正文整行完全匹配的全部原始行号。"""
    l_line = []
    if not quote.strip():
        return l_line
    text = document.page_content
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        if line == quote:
            l_line.append(number)
    return l_line


def show_a() -> None:
    """打印 A 的实际记录、边界结果和固定期望，供学员自行核对。"""
    names = ["policies/guide.txt", "blank.txt", "archive/guide.txt"]
    original_names = names.copy()
    print("A｜教学资料目录：", MATERIALS)
    documents = load_sources(MATERIALS, names)
    print(f"实际条数：{len(documents)}；期望：2")
    print("期望顺序 / id / source：policies/guide.txt、archive/guide.txt")
    print("期望行数：6、3；正文应与原文件一致；blank.txt 不应出现。")
    for document in documents:
        print(f"\n实际类型：{type(document).__name__}；期望：Document")
        print(f"实际 id：{document.id!r}；source：{document.metadata.get('source')!r}")
        print(
            f"实际 metadata 键：{sorted(document.metadata)}；期望：line_count、source"
        )
        print(f"实际行数：{document.metadata.get('line_count')!r}")
        print(f"实际全文：{document.page_content!r}")
        source = document.metadata.get("source")
        if source in names:
            original_text = (MATERIALS / source).read_text(encoding="utf-8")
            print(
                f"与原文完全一致：{document.page_content == original_text}；期望：True"
            )
    print(f"\n输入清单未修改：{names == original_names}；期望：True")
    print(f"空清单实际：{load_sources(MATERIALS, [])!r}；期望：[]")
    try:
        load_sources(MATERIALS, ["不存在.txt"])
    except FileNotFoundError:
        print("缺失文件实际：FileNotFoundError；期望：FileNotFoundError")
    else:
        print("缺失文件实际：没有抛异常；期望：FileNotFoundError")


def show_b() -> None:
    """用独立内存输入打印 B 的多组实际与期望，不代写定位逻辑。"""
    # 以下是检查输入，不是加载器实现。编号与来源都是 AI 明确指定的假数据。
    document = Document(
        page_content=(
            "报价说明（AI 教学假数据）\n"
            "复核后才能报价。\n\n"
            "紧急报价需单独确认。\n"
            "复核后才能报价。\n"
            "  保留这行的空格。  \n"
        ),
        metadata={"source": "quote_rules.txt", "line_count": 6},
        id="quote_rules.txt",
    )
    # model_dump()：把 Pydantic 对象转成普通 Python 数据，此处仅用于核对输入未被修改。
    original = document.model_dump()
    print("B｜检查用的原始正文（\\n 表示换行）：", repr(document.page_content))
    cases = [
        ("重复整行", "复核后才能报价。", [2, 5]),
        ("空行后的位置", "紧急报价需单独确认。", [4]),
        ("原样保留空格", "  保留这行的空格。  ", [6]),
        ("删掉空格后不相等", "保留这行的空格。", []),
        ("半句不是整行", "复核后", []),
        ("没有此原文", "可以先报价再复核。", []),
        ("空引用", "", []),
        ("空白引用", "   ", []),
    ]
    for label, quote, expected in cases:
        actual = locate_quote(document, quote)
        print(f"{label}｜原文={quote!r}｜实际={actual!r}｜期望={expected!r}")
    empty = Document(page_content="")
    print(f"空正文｜实际={locate_quote(empty, '任意原文')!r}｜期望=[]")
    print(f"原 Document 未修改：{document.model_dump() == original}；期望：True")


def main() -> None:
    """选择 A 或 B，打印实际结果与期望供核对。"""
    parser = argparse.ArgumentParser(description="Day 36：加载原文并保留可核对的出处")
    parser.add_argument(
        "--part", choices=("a", "b"), default="a", help="选 a 或 b 单独运行"
    )
    args = parser.parse_args()
    print("本入口使用 AI 教学假数据。实际输出由你运行，观察只写在文件末尾。")
    if args.part == "a":
        show_a()
    else:
        show_b()


if __name__ == "__main__":
    main()


# ===== 现象与原因：学员亲跑后填写，保留原稿；不需要另建记录 md =====
# 开工短复习（约 10 分钟，不看旧答案；AI 看实际缺口再决定是否补课）：
# 1. 同一检查点文件中的 thread_id、一次消息的 id、工具点单的 tool_call_id，
#    各用于区分什么？新会话能否自动防止同一报价业务重复保存？
#    我的回答：
#   thread_id标识一次对话，一次消息的id标识message自身，tool_call_id用来配对assistant点单与tool观察
#   新对话不能自动防止，要设置单独的业务防重机制
# 2. 节点分别只返回新增的一条 messages 和新增的一条普通 trace 时，
#    在已学图的更新规则下，旧列表分别会怎样？
#    我的回答：
#   message会通过add_messages自动追加到旧列表上，trace则会覆盖旧列表
# 今天的观察（依据 A/B 实际输出与材料原文件，用自己的话简短说明）：
# 1. A 的两个 guide.txt 有何不同？只保存文件名会丢失哪一项来源信息？
#    我的观察与原因：
#   正文，行数都不同，只保存文件名会丢失目录信息，导致无法区分具体来源
# 2. B 中重复整行、空行后的整行各返回什么？先过滤空行再编号会造成什么错？
#    我的观察与原因：
#   重复整行返回：[2, 5] 空行后的整行：[4]
#   先过滤空行再编号会导致行号与实际不一致
# 3. B 的原样空格、删掉空格、半句对照说明了什么？返回 [] 能否直接说明
#    “整份资料没有支持答案的信息”？结合今天实际使用的匹配方式解释。
#    我的观察与原因：
#   B 的原样空格、删掉空格、半句对照说明必须和整行一模一样才能计数
#   返回[]并不能直接说明整份资料没有支持答案的信息，因为读取是整行读取的，如果答案分布在两行或者不到一行也识别不到
