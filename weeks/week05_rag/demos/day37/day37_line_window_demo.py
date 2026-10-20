"""Day 37：为 RAG 的资料切分理解固定行窗口与重叠。

只用独立的行列表讲窗口怎样移动；多文件切分与片段 Document 留给练习。
"""


def main() -> None:
    """用已知行列表展示窗口大小、步长与文末停止。"""
    print("Day 37｜固定行窗口：每次取几行，下次从哪里继续？")
    print("\n这份演示在本周目标中的作用")
    print("本周做带出处的 RAG 问答，需要从资料中取出相关片段，再交给模型回答。")
    print("这份演示对应资料切分：先把全文分成可以单独检索的小段，英文叫 chunk。")
    print("学完应能解释窗口大小、重叠行数、步长，以及文末为什么停止。")
    print("后续练习会把这些窗口变成有来源的 Document，再用于向量化与检索。")

    print("\n1. 这是什么")
    print("固定行窗口：每段最多取固定行数；相邻窗口可共享若干行，这叫重叠。")
    print("chunk_lines 是每段最多几行；overlap_lines 是相邻两段重复几行。")
    print("步长 step = chunk_lines - overlap_lines，表示下次起点前进几行。")
    print("\n2. 为什么需要它")
    print("把很长的全文作为一个检索单元，命中后可能带入很多与问题无关的文字。")
    print("切成片段能缩小检索单元；重叠可保留边界附近的一些上下文，也会增加重复文字。")
    print("\n3. 场景")
    print("把五行设备登记事项分段。下面是 AI 教学行列表，不是学员资料或真实检索结果。")

    print("\n4. 代码与实际结果")
    lines = ["第1行：登记", "第2行：核对", "第3行：签收", "第4行：归还", "第5行：销记"]
    chunk_lines = 3
    overlap_lines = 1
    step = chunk_lines - overlap_lines
    print(f"原行列表：{lines}")
    print(f"窗口={chunk_lines} 行，重叠={overlap_lines} 行，步长={step} 行")
    print("列表切片 lines[start:stop] 包含 start，不包含 stop；下标从 0 开始。")
    print("因此切片 [0:3] 对应原文第 1～3 行，原文行范围的两端都包含。")
    # range(起点, 不含的终点, 步长)：生成起点序列，本例候选起点是 0、2、4。
    for start in range(0, len(lines), step):
        stop = min(start + chunk_lines, len(lines))
        window = lines[start:stop]
        print(f"切片 [{start}:{stop}] -> 原行 {start + 1}～{stop} -> {window}")
        if stop == len(lines):
            print("已经到达文末，立即停止；不再生成完全被上一段包含的第 5～5 行。")
            break

    print("\n对照：这五行不重叠时，可取第 1～3、4～5 行；重叠一行时是 1～3、3～5 行。")
    print("原行第 3 行被两段共享；行的原始编号没有因为重叠改变。")
    print("\n5. 注意什么")
    print("本课要求 chunk_lines >= 1，且 0 <= overlap_lines < chunk_lines。")
    print("不满足时抛内置 ValueError（无需 import）；重叠等于窗口会让步长变成 0。")
    print("最后一段可以不足窗口大小；内部空行也占一行，不能删行后重新编号。")
    print("按行限制不能保证字符或 token 上限：一行很长，片段仍可能很大。")
    print(
        "重叠也不保证问题所需的信息一定完整或一定命中；效果需要后续用自己的样本核对。"
    )


if __name__ == "__main__":
    main()
