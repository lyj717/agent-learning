"""Day 36 答疑：资料根目录与相对路径怎样合成完整文件路径。

为 RAG 的资料加载确认“去哪里读、读哪些文件”；本演示只拼路径，不读取文件。
"""

from pathlib import Path


def main() -> None:
    """用实际资料目录演示完整地址、相对地址和路径拼接。"""
    print("Day 36｜root 和 relative_paths 分别传什么？")
    print("\n这份演示在本周目标中的作用")
    print("本周做带出处的 RAG 文档问答，加载资料前要先确定文件在哪里。")
    print("学完应能区分资料文件夹的完整地址与文件在其中的相对地址。")
    print("后续加载器会用两者找到文件，并用相对地址记录资料来源。")

    print("\n1. 这是什么")
    print("root 是资料文件夹的完整地址，类型是 Path。")
    print("relative_paths 是 list[str]：每个字符串说明从 root 出发，怎样找到一个文件。")
    print("UTF-8 描述文件正文采用的编码；路径清单只保存文件位置。")
    print("\n2. 为什么需要它")
    print("把共同的资料文件夹单独传入，清单里的每个文件就不用重复写前面那一长段地址。")
    print("\n3. 场景")
    print("资料文件夹里有 policies 和 archive 两个子目录，各有一个 guide.txt。")

    print("\n4. 代码与实际结果")
    print("导入：from pathlib import Path；Path(地址字符串) 创建一个路径对象。")
    # resolve() 得到脚本的完整路径；parent 取所在文件夹。
    root = Path(__file__).resolve().parent / "materials"
    relative_paths = ["policies/guide.txt", "archive/guide.txt"]
    print(f"root（资料文件夹的完整地址）：{root}")
    print(f"relative_paths（字符串清单）：{relative_paths!r}")
    print(
        f"root 的类型：{type(root).__name__}；列表第一项类型：{type(relative_paths[0]).__name__}"
    )

    relative_path = relative_paths[0]
    # Path 对象 / 子路径：拼接路径；返回新 Path，不会读取或创建文件。
    file_path = root / relative_path
    print(f"\nrelative_path（单个相对地址）：{relative_path!r}")
    print(f"root / relative_path（完整文件地址）：{file_path}")
    # is_absolute() 无参数，返回 bool，判断该路径是否为完整的绝对路径。
    print(f"root 是绝对路径：{root.is_absolute()}")
    print(f"relative_path 是绝对路径：{Path(relative_path).is_absolute()}")

    print("\n5. 注意什么")
    print(
        "relative_paths 是整个列表；relative_path 是其中一个字符串，名字末尾的 s 表示复数。"
    )
    print("Path 对象上的 / 表示拼路径；这里没有做除法，也没有读取正文。")
    print("这两个输入由调用方传给你的函数；练习里不必写死本机的整段绝对地址。")


if __name__ == "__main__":
    main()
