"""Day 36：为 RAG 中正文与来源一起传递，认识 Document 的字段。

学完应能用 Document 表示一条文本记录，并区分正文、来源信息和记录编号。
后续切分、检索和展示引用时，需要继续保留并传递这些来源信息。
"""

from langchain_core.documents import Document


def main() -> None:
    """用内存中的教学片段说明 Document 的接口和边界。"""
    print("Day 36｜Document：把文字和出处放在同一条记录里")
    print("\n这份演示在本周目标中的作用")
    print("本周要完成 RAG 文档问答，回答里的出处必须能回到实际提供的资料。")
    print("这份演示讲资料怎样表示：由我们填写来源信息，与正文放在同一条记录里传递。")
    print("学完应能创建并读取 Document，分清正文、来源信息和记录编号。")
    print("后续切分和检索片段时要继续保留来源，最终用来展示和核对答案的引用。")
    print("\n1. 这是什么")
    print("Document 是 LangChain 提供的文本记录类。page_content 放正文，")
    print("metadata 放来源等附加信息；id 是可选的记录编号。metadata 叫元数据。")
    print("page_content 里的 page 只是字段名，不要求资料一定来自 PDF。")
    print("\n2. 为什么需要它")
    print("只留下正文，后面就很难解释这句话来自哪个文件、哪个位置。")
    print("\n3. 场景")
    print("设备说明和培训摘要可能有同一句话，但它们是两份不同资料。")
    print("下面的正文、来源名和行号都是 AI 教学示意，不是从文件读取的实验结果。")

    print("\n4. 代码与实际结果")
    print("导入：from langchain_core.documents import Document")
    print("本课常用参数：Document(page_content, *, metadata=..., id=None)")
    print(
        "page_content 必填，传 str；metadata 可选，传 dict；id 可选，传 str 或 None。"
    )
    print(
        "省略 metadata 时会创建新的空字典；星号后的参数按名字传，例如 metadata={...}。"
    )
    print("调用返回一个 Document 对象；用 .page_content / .metadata / .id 读取字段。")
    # Document(page_content=正文, metadata=附加信息, id=可选编号)：创建文本记录。
    manual = Document(
        page_content="归还设备前先检查配件。",
        metadata={"source": "设备说明.txt", "line_start": 7, "line_end": 7},
        id="equipment-rule",
    )
    summary = Document(
        page_content="归还设备前先检查配件。",
        metadata={"source": "培训摘要.txt", "line_start": 2, "line_end": 2},
        id="training-note",
    )
    for document in (manual, summary):
        print(f"\n编号：{document.id}")
        print(f"正文：{document.page_content}")
        print(f"来源：{document.metadata['source']}")
        print(
            f"行范围：{document.metadata['line_start']}"
            f"～{document.metadata['line_end']}"
        )
    print(f"\n正文相同：{manual.page_content == summary.page_content}")
    print(f"来源相同：{manual.metadata['source'] == summary.metadata['source']}")
    without_source = Document(page_content="单独的一句话。")
    print(
        f"省略可选参数时：id={without_source.id!r}，metadata={without_source.metadata}"
    )

    print("\n5. 注意什么")
    print("source、line_start、line_end 都是我们自定义的 metadata 键，不会自动生成。")
    print("Document 不会读文件、核对行号、切分、计算向量或证明正文真实。")
    print("一个 Document 可装全文，也可装片段；不是创建它就已经完成 RAG。")
    print("id 不会自动检查全局唯一；来源位置也可能因文件修改而失效。")
    print("本示例只说明怎样表示出处，实际引用仍要回到当时读取的原文核对。")


if __name__ == "__main__":
    main()
