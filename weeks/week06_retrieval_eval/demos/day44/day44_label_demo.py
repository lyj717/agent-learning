"""Day44：认识真实问题的标注字段，为评测提供独立于检索结果的标准。"""

import json


def main() -> None:
    """用完整内存资料说明问题、期望、依据行与相关片段标签。"""
    print("Week6 要比较检索改动；Day43 的评分器需要正确的 relevant_ids 才有意义。")
    print("本演示负责这些标签从哪里来：先读固定原文，人工标依据，再映射到片段。")
    print("学完能填写 day44_labels.json；练习 A 再实现行范围到片段编号的投影。")
    print("\n一、这是什么")
    print("标注就是提前写清：这道题资料能否回答，应该答哪些点，依据在原文哪里。")
    print("它是评测标准，不能根据检索实际找到了什么来反推。")
    print("\n二、为什么需要")
    print("只把返回的片段标成相关，就看不到没被返回的依据，Recall 的分母也会算错。")
    print("\n三、场景：以下是 guide.md 的完整内存资料，不是学员真实笔记")
    lines = [
        "借用设备前请在前台登记。",
        "登记时请出示借用单。",
        "归还时交回遥控器。",
        "同时交回电源线。",
    ]
    for number, line in enumerate(lines, start=1):
        print(f"  {number}: {line}")
    print("\n四、字段和最小数据示例")
    print("下面这条 example 是 AI 手工写的教学样本，所用原文也完整显示在上面。")
    print("真实样本也要对照固定全文标注；本次新增二十题已按你的要求由 AI 协助准备。")
    example = {
        "id": "example01",
        "split": "dev",
        "question": "借用设备在哪里登记？",
        "answerable": True,
        "expected": "在前台登记。",
        "evidence": [{"source": "guide.md", "line_start": 1, "line_end": 1}],
    }
    print(f"id={example['id']}：这道题的编号。")
    print(f"split={example['split']}：这道题属于哪一组；这里和文本怎样切块没有关系。")
    print("  dev：开发题，后续调检索方案时可以反复看它的结果。")
    print("  holdout：留出题，先标好，等方案固定后再看效果，不据其结果调方案。")
    print("  真实文件 q01～q24 已分到 dev，q25～q30 已分到 holdout，保留这些值即可。")
    print(f"问题={example['question']}")
    print(f"answerable={example['answerable']}：读完全文后，确认能回答。")
    print(f"expected={example['expected']}：将来核对模型回答需要的要点。")
    print(f"evidence={example['evidence']}：记原文位置，行号包含两端。")
    print("在 JSON 文件里，True 写成 true，False 写成 false，None 写成 null。")
    print("若问题问押金多少钱，这份全文没写：answerable=false，evidence=[]，")
    print("expected 写‘原文没有提供押金金额’，不填写猜出的金额。")
    print("若还没读完或没标完，answerable=null；它不能作为无答案题参加评分。")

    print("\n五、原文依据怎样对应到片段")
    print("先看切分结果。编号里的行号都指原文，不是进入某个片段后重新从1计数。")
    for name, start, end in [("甲", 1, 3), ("乙", 3, 4)]:
        print(f"\n片段{name}：guide.md#L{start}-L{end}")
        for number in range(start, end + 1):
            print(f"  原文第{number}行：{lines[number - 1]}")

    print("\n情形1：同一处原文依据被两个片段重复覆盖")
    print("换一个小问题：归还时要交回遥控器吗？")
    print("原文第3行已经能回答。甲含第3行，乙也含第3行，但原文中仍是同一处依据。")
    print("你在 evidence 中只写这一处原文位置：")
    remote_evidence = [{"source": "guide.md", "line_start": 3, "line_end": 3}]
    show_evidence(remote_evidence)
    print("随后程序检查全部片段，相关编号应有两个：guide.md#L1-L3、guide.md#L3-L4。")
    print("不需要因为有两个相关片段，就在 evidence 里把第3行写两遍。")
    print("也不要把甲乙的整个范围写成依据：那会把与本问题无关的登记信息也标进去。")

    print("\n情形2：回答需要原文中不同位置的信息")
    print("问题：在哪里登记，归还时要交回什么？")
    print("登记地点在第1行；归还物品在第3～4行。这次有两处不同依据。")
    print("evidence 分别记录这两处原文位置：")
    combined_evidence = [
        {"source": "guide.md", "line_start": 1, "line_end": 1},
        {"source": "guide.md", "line_start": 3, "line_end": 4},
    ]
    show_evidence(combined_evidence)
    print("这里有两项，是因为有两处需要标的原文位置，不是因为恰好切出了两个片段。")
    print("如果有效依据分散在不同文件，也分别填写各自的完整 source 和原文行号。")
    print("如果同一事实在原文多个不同位置确实重复出现，逐处核对后也可分别标记。")
    print("来源 archive/guide.md 即使也有第3行，也不能自动当作 guide.md 的同一处依据。")
    print("练习的规则：同一 source，两个范围至少共享一行，包含端点；不要求整段包含。")
    print("行范围到片段集合的循环与去重，由你在练习 A 实现。")

    print("\n六、注意边界")
    print("相关只表示片段带有标注依据的一部分，不保证所有必要事实已经找齐。")
    print("两块可能重复同一事实；完整回答仍应对照 expected、原文和模型实际回答。")
    print("原文版本要固定；切分改变时，保留原文依据，重新生成该版本的相关片段标签。")
    print("不同切分的片段分母可能改变，不能只靠片段 Recall 宣称切分一定更好。")
    print(
        "真实文件：day44_labels.json 中旧十题复用既有记录，新增二十题由 AI 按本次授权补齐。"
    )


def show_evidence(evidence: list[dict]) -> None:
    """把人工教学标注显示为可读的 JSON，不计算相关片段或填写真实数据。"""
    # json.dumps(对象, ensure_ascii=False, indent=2)：转成保留中文、缩进两格的 JSON 文本。
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
