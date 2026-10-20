"""Day 36：为 RAG 的资料加载与出处核对，复习文本读取和原始行号。

学完应能读出完整正文，保留空行和空格，并把一行文字对应回原文件的位置。
后续切分资料和核对引用时，会用到这里保留的原文与位置。
"""

from pathlib import Path


def main() -> None:
    """读取一份教学文本，逐行核对读取结果。"""
    print("Day 36｜读取资料：字符串里的文字怎样对应回原文件？")
    print("\n这份演示在本周目标中的作用")
    print("本周要完成 RAG 文档问答：先从自己的资料找证据，再让模型回答并给出出处。")
    print("这份演示对应最前面的资料加载，以及后续引用所需的原文位置核对。")
    print("学完应能按 UTF-8 读出完整正文，保留空行与空格，并核对原始行号。")
    print("后续切分资料、保存片段来源和检查引用时，会用到这里读出的原文与位置。")
    print("\n1. 这是什么")
    print("Path 表示文件路径；read_text 把文件按指定编码读成一个 str。")
    print("str.splitlines 把字符串按换行拆成 list[str]，默认去掉换行符。")
    print("这些是 Python 文件处理的复习，不是向量检索。")

    print("\n2. 为什么需要它")
    print("以后回答要标出处。若先删掉空行再编号，得到的行号就对不上原文件。")
    print("\n3. 场景")
    print("读取一份设备登记说明。以下是 AI 编写的教学假数据，不是学员实验。")

    print("\n4. 代码与实际结果")
    # resolve() 得到脚本的绝对路径；parent 取所在目录，不依赖终端工作目录。
    path = Path(__file__).resolve().parent / "demo_notes.txt"
    print("导入：from pathlib import Path")
    print("签名：path.read_text(encoding=None, errors=None, newline=None) -> str")
    print("path 是要读的文件。三个参数都可选；本课显式传 encoding='utf-8'。")
    print("errors 默认严格解码，失败会报错；newline 默认把常见文件换行统一成 \\n。")
    # read_text(encoding=...)：读取整个文本文件并返回 str，读完自动关闭文件。
    text = path.read_text(encoding="utf-8")
    print(f"文件：{path.name}")
    print(f"完整字符串（repr 显示换行与空格）：{text!r}")

    print("\n签名：text.splitlines(keepends=False) -> list[str]，无必填参数。")
    print("keepends=True 时保留各行末尾的换行符；今天使用默认 False。")
    # splitlines()：按换行拆分，保留中间的空行，不保留默认的行末换行符。
    lines = text.splitlines()
    # enumerate(序列, start=1)：逐项同时给出从 1 开始的编号，和编辑器行号对应。
    for number, line in enumerate(lines, start=1):
        print(f"原始第 {number} 行：{line!r}")
    print("空字符串拆行：", "".splitlines())
    print("末尾一个换行不会额外多出一行：", "登记完成\n".splitlines())
    print("\n对照：读错编码时，默认不会悄悄丢掉无法解释的字节。")
    try:
        path.read_text(encoding="ascii")
    except UnicodeDecodeError:
        print("捕获到预设的 UnicodeDecodeError：中文教学文本不能按 ASCII 解码。")

    print("\n5. 注意什么")
    print("splitlines 之后先按原顺序编号，再决定是否跳过空行；别把新序号当原行号。")
    print(
        "strip() 可用于判断是否全是空白，但会改两侧空格，不要拿它替换需要核对的原文。"
    )
    print("文件不存在会抛内置 FileNotFoundError；解码失败抛内置 UnicodeDecodeError。")
    print("这两个异常类不需要 import；不要捕获后把错误伪装成空资料。")
    print("今天只读取 UTF-8 文本，不把 PDF 的二进制字节当文本解码。")


if __name__ == "__main__":
    main()
