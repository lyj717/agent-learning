"""Day 37：独立认识片段编号、来源路径和原文行范围。"""

from langchain_core.documents import Document


def main() -> None:
    """手工表示一条片段，说明它怎样对应回一份全文。"""
    print("Day 37｜一条片段怎样说明自己是谁、来自哪里？")
    print("本周目标：做带出处的文档问答，让回答可以回到资料中核对。")
    print("本演示作用：在切分这一环，认识片段编号与原文位置分别记录什么。")
    print("学完能做：读懂一条片段的 id、source 和行范围，手工对应回全文。")
    print("后续用途：检索会返回片段；这些字段将帮助我们显示出处、回查引用。")

    print("\n1. 这是什么")
    print("片段是从一份全文里取出的一部分文字，仍用已学的 Document 表示。")
    print("id 区分这一条片段；source 记录来自哪份资料；行范围记录在原文哪里。")
    print("这三个问题不同，不能只留下片段正文，也不能拿片段编号代替来源。")

    print("\n2. 为什么需要它")
    print("同一文件会切出多条片段：它们的来源相同，片段编号却应不同。")
    print("只知道片段来自某个文件，仍不知道该回到原文哪几行核对。")

    print("\n3. 场景")
    print("设备说明有四行，现在手工取第 2～3 行，作为一条待检索的片段。")
    print("正文与文件名都是 AI 教学假数据；本演示不读文件，也不执行批量切分。")

    print("\n4. 代码与实际结果")
    # Document(page_content=正文, metadata=附加信息, id=记录编号)：表示一条文本记录。
    original = Document(
        page_content=(
            "设备借用说明（AI 教学假数据）\n"
            "归还前检查充电器。\n"
            "归还前核对设备编号。\n"
            "遗失配件需联系管理员。\n"
        ),
        metadata={"source": "equipment.txt"},
        id="equipment.txt",
    )
    # splitlines()：按换行得到原始行列表，默认移除各行末尾的换行符。
    lines = original.page_content.splitlines()
    # enumerate(行列表, start=1)：依原顺序给出从 1 开始的原文行号。
    for line_number, line in enumerate(lines, start=1):
        print(f"原文第 {line_number} 行：{line!r}")

    print("\n原文行号的 2～3 是从 1 开始、包含两端的范围。")
    print("Python 切片 [1:3] 从下标 1 取到下标 3 之前，取到的恰是原文第 2、3 行。")
    print("本例对应：切片左端 = line_start - 1，切片右端 = line_end。")
    # '\n'.join(行列表)：用一个换行连接各行，得到一段新的正文字符串。
    chunk_text = "\n".join(original.page_content.splitlines()[1:3])
    chunk = Document(
        page_content=chunk_text,
        metadata={"source": "equipment.txt", "line_start": 2, "line_end": 3},
        id="equipment.txt#L2-L3",
    )

    print(f"\n全文 id：{original.id!r}")
    print(f"片段 id：{chunk.id!r}")
    print(f"片段正文：{chunk.page_content!r}")
    print(f"片段来源：{chunk.metadata['source']!r}")
    print(f"片段起始行：{chunk.metadata['line_start']}")
    print(f"片段结束行：{chunk.metadata['line_end']}")
    print(f"片段 metadata 的全部键：{sorted(chunk.metadata)}")
    print(f"来源保持相同：{original.metadata['source'] == chunk.metadata['source']}")
    print(f"记录编号已经改变：{original.id != chunk.id}")
    print("这里的 #L2-L3 是我们给编号约定的写法，库不会自动解析它或生成行号。")

    print("\n5. 注意什么")
    print("source、line_start、line_end 都是自定义 metadata 键，不是自动核验的事实。")
    print("Document 不会检查片段正文是否真在这个来源的这些行中，回查仍要由程序完成。")
    print("原文里若有重复文字，光看正文无法判断引用的是哪一次出现，仍需保留位置。")
    print("splitlines 再用换行连接会重新组织正文；不承诺字节原样或保留末尾换行。")
    print("行号只对应当时读取的资料；文件增删行后，旧位置与片段编号都可能失效。")
    print("今天先学怎样表示位置，后面的练习再由你完成切分与原文回查。")


if __name__ == "__main__":
    main()
