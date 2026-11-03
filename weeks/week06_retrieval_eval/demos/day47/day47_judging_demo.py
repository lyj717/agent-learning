"""Day47：用相同原文区分回答正确完整、引用支持及结构合法，不实现汇总练习。"""

import json
import sys
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.answer_functions import (
    check_grounded_reply,
)


def main() -> None:
    """展示两个相反方向的反例和拒答，不拿模型状态当人工结论。"""
    print("Week6 要交分层评测。Day46 只保存排名，Day47 才检查实际模型回答。")
    print("本演示讲人工判分：学完能分别填写 answer_ok 与 citation_ok，再用于练习汇总。")
    print("下面原文、回答与判分均为 AI 人工教具，没有真实模型调用。")
    print(
        "\n一、是什么：answer_ok 判断题目是否被正确答全；citation_ok 判断已说出的内容有无引用依据。"
    )
    print("为什么：两个检查对象不同，把它们合并会漏掉缺答或引用缺口。")
    print("场景：问‘课程在哪里签到、要出示什么？’，完整答案必须同时说地点和凭据。")
    evidence = [
        Document(id="class.md#L1-L1", page_content="在前台签到。"),
        Document(id="class.md#L2-L2", page_content="签到时出示预约码。"),
    ]
    for chunk in evidence:
        print(f"原文与候选 {chunk.id}：{chunk.page_content}")
    examples = [
        (
            "只答一半",
            "在前台签到。",
            [evidence[0].id],
            False,
            True,
            "漏了预约码，所以没答全；已说出的地点由实际引用支持。",
        ),
        (
            "答全但引用缺一处",
            "在前台签到，出示预约码。",
            [evidence[0].id],
            True,
            False,
            "内容正确且完整；实际只引用第一行，第二个说法没有被该引用支持。",
        ),
        (
            "引用编号存在但内容相反",
            "在后门签到，出示预约码。",
            [chunk.id for chunk in evidence],
            False,
            False,
            "编号都合法，但前台与后门矛盾，内容和引用两项都不通过。",
        ),
    ]
    print("\n二、代码：先沿用旧 check_grounded_reply(raw_text, evidence) 检查结构。")
    print(
        "raw_text 是 JSON 字符串，evidence 是同一批 Document；两者必填，返回解析后的 dict。"
    )
    print("它只查结构/编号，没有自动判断下面两项语义。")
    for name, answer, citations, answer_ok, citation_ok, reason in examples:
        raw = json.dumps(
            {"status": "answered", "answer": answer, "cited_ids": citations},
            ensure_ascii=False,
        )
        checked = check_grounded_reply(raw, evidence)
        print(f"\n{name}：{checked['answer']}；实际引用={checked['cited_ids']}")
        print(
            f"结构检查通过；人工 answer_ok={answer_ok}，citation_ok={citation_ok}。{reason}"
        )
    print("\n三、无答案场景：完整原文没有课程结束时间，回答‘资料没有提供结束时间’。")
    print(
        "人工 answer_ok=True（正确拒答），citation_ok=None（没有实质答案需要查引用）。"
    )
    print("有答案却纯拒答则 answer_ok=False、citation_ok=None；None 不能算引用通过。")
    print("\n四、注意：expected 与全文用于判回答；实际引用的片段用于判支持。")
    print("未被引用的候选即使含答案，也不能替实际引用补证据。")
    print("这只是最小口径演示。真实 8 份结果由你读完后判，程序只汇总你的标志。")


if __name__ == "__main__":
    main()
