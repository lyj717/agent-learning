"""Day 40 的内存教学资料与打印环境，不实现两道练习。"""

from langchain_core.documents import Document

SUPPORTED_QUESTION = "参加木工体验课，签到时要出示什么，材料包在哪里领取？"
INSUFFICIENT_QUESTION = "木工体验课几点结束？"

# 这些是 AI 提供的内存原文；来源名用于练习，不声称磁盘上有同名文件。
ORIGINALS = {
    "workshop/checkin.md": (
        "木工体验课签到说明\n签到时请出示预约码。\n材料包在签到后由前台发放。"
    ),
    "archive/checkin.md": (
        "体验课旧档案\n说明\n登记\n签到流程\n签到时请出示预约码。\n材料包在签到后由前台发放。"
    ),
    "workshop/return.md": "工具归还说明\n结束后请将护目镜放回工具架。",
}


def make_evidence() -> list[Document]:
    """返回本次给定的三条候选；不调用检索器，也不生成练习答案。"""
    return [
        Document(
            id="workshop/checkin.md#L2-L3",
            page_content="签到时请出示预约码。\n材料包在签到后由前台发放。",
            metadata={"source": "workshop/checkin.md", "line_start": 2, "line_end": 3},
        ),
        Document(
            id="archive/checkin.md#L5-L6",
            page_content="签到时请出示预约码。\n材料包在签到后由前台发放。",
            metadata={"source": "archive/checkin.md", "line_start": 5, "line_end": 6},
        ),
        Document(
            id="workshop/return.md#L2-L2",
            page_content="结束后请将护目镜放回工具架。",
            metadata={"source": "workshop/return.md", "line_start": 2, "line_end": 2},
        ),
    ]


def show_evidence(evidence: list[Document]) -> None:
    """打印实际提供给模型的片段，便于人工逐条核对回答。"""
    print("输入类型：AI 内存教学片段；今天已给定候选，尚未接通检索。")
    print(f"本次证据条数：{len(evidence)}")
    for chunk in evidence:
        print(f"  原片段 id={chunk.id}")
        print(
            f"  来源={chunk.metadata['source']}；"
            f"原行={chunk.metadata['line_start']}～{chunk.metadata['line_end']}"
        )
        print(f"  正文={chunk.page_content!r}")


def show_originals() -> None:
    """展示教学全文的真实行号；来源核对仍可复用已学的旧函数。"""
    for source, full_text in ORIGINALS.items():
        print(f"\n内存来源={source}")
        for line_number, line in enumerate(full_text.splitlines(), start=1):
            print(f"  {line_number}: {line}")
