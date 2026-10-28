"""Day 40 答疑：Document 先取出普通字段，才能变成 JSON 文本。

用单条片段的两个字段说明类型转换，帮助理解证据消息的输入；
练习 A 的五字段、批量整理与完整消息仍由学员实现。
"""

import json

from langchain_core.documents import Document


def main() -> None:
    """对照直接转换 Document 报错与转换普通字段字典成功。"""
    print("本周目标是带出处的 RAG 问答；模型请求中的 content 需要字符串。")
    print("本演示解释：怎样从 Document 取出普通数据，让 json.dumps 能处理。")
    print("学完回到练习 A，自己按题目要求整理多条证据的五个字段。")

    print("\n1. 这是什么")
    print("序列化在这里就是把 Python 数据转成 JSON 字符串。")
    print("json.dumps 能处理字典、列表、字符串、数字、布尔值和 None，")
    print("但这些容器内部的每个值也要能转换；它不会自动理解 Document 对象。")

    print("\n2. 为什么需要先取字段")
    print("Document 保存了正文、编号和元数据；我们要明确挑出本次发送哪些字段。")
    print("写进 system 的要求会在请求发出后交给模型，不能替 Python 完成类型转换。")

    print("\n3. 场景：一条 AI 手写的教学片段，无同名磁盘文件")
    # Document(page_content=正文, id=编号, metadata=元数据)：保存片段，不是 JSON 字符串。
    chunk = Document(
        id="teaching/bicycle.md#L2-L2",
        page_content="借用自行车需登记联系方式。",
        metadata={"source": "teaching/bicycle.md", "line_start": 2, "line_end": 2},
    )
    print(f"对象类型={type(chunk).__name__}；正文={chunk.page_content!r}")

    print("\n4. 代码与实际结果")
    print("尝试 json.dumps({'evidence': [chunk]})：")
    try:
        # json.dumps(对象, ensure_ascii=False)：转成 JSON 字符串，保留可读中文。
        json.dumps({"evidence": [chunk]}, ensure_ascii=False)
    except TypeError as error:
        print(f"实际报错：{type(error).__name__}: {error}")

    print("\n先取两个字段，组成普通字典；这里只演示类型转换，不是 A 的完整五字段：")
    row = {"id": chunk.id, "text": chunk.page_content}
    print("row = {'id': chunk.id, 'text': chunk.page_content}")
    print(f"字典实际={row}")
    payload = {"evidence": [row]}
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(f"转换后类型={type(json_text).__name__}，实际内容：")
    print(json_text)

    print("\n5. 注意什么")
    print("外层是字典或列表还不够：里面仍有 Document，一样会报错。")
    print("练习 A 要自己逐条取 id、source、line_start、line_end、text，组成字典列表。")
    print("取字段和组装消息由 Python 完成；system 负责告诉模型怎样依据收到的资料回答。")


if __name__ == "__main__":
    main()
