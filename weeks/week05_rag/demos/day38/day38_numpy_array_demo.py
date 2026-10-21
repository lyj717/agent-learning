"""Day 38 的 NumPy 前置：认识模型返回的数组、形状和 .tolist()。

只使用手工数字，不运行模型、不训练、不联网；为读取真实 embedding 返回值做准备。
"""

import numpy as np


def main() -> None:
    """从普通列表出发，区分数组、批量外层列表与普通数值列表。"""
    print("Day 38｜NumPy 是什么，为什么向量模型返回 ndarray？")
    print("\n这份演示在本周目标中的作用")
    print("本周要做带出处的 RAG 问答，今天需要取得资料与问题的向量。")
    print("真实模型每次产生的向量是 NumPy 数组；先认识这个返回类型，再去调用模型。")
    print("学完应能读懂数组的类型、形状，知道怎样转成练习要求的普通 Python 列表。")
    print("后续 A/B 会用到这些转换；本文件不提供片段配对或问题编码的完整实现。")

    print("\n1. 这是什么")
    print("NumPy 是 Python 的数值计算库，提供适合存放、处理成组数字的数组。")
    print("数组类型叫 ndarray，名字来自 N-dimensional array，即多维数组。")
    print("导入写 import numpy as np；np 只是常见别名，后面用 np. 访问库里的名字。")
    print("NumPy 本身不是 embedding 模型，不负责把文字理解成语义向量。")
    print("它已经随 FastEmbed 安装，本课也在 requirements.txt 中显式声明，无需重装。")

    print("\n2. 为什么需要它")
    print("普通 list 能存数字；数值计算库还需要高效地对大量同类型数字进行运算。")
    print("NumPy 为这种需求提供数组和计算工具，所以模型库经常用数组交回计算结果。")
    print("本课先学怎样读和转换返回值，不要求掌握整套数值计算。")

    print("\n3. 场景")
    print("以下数字由 AI 手工指定，只是类型和形状教具，不是真实文本向量。")
    print("用三个数代替真实模型的 512 个数，以便一眼看完整。")

    print("\n4. 代码与实际结果")
    numbers = [0.25, 0.5, -0.125]
    # np.array(数据, dtype=可选类型)：从列表等数据创建 ndarray，返回数组对象。
    # np.float32：32 位浮点数类型；dtype 省略时由输入数据推断，这里显式指定以便对照。
    vector = np.array(numbers, dtype=np.float32)
    print("创建：np.array(数字列表, dtype=np.float32) -> ndarray")
    print(f"普通列表：{numbers}；类型={type(numbers).__name__}")
    print(f"NumPy 数组：{vector}；类型={type(vector).__name__}")
    print(
        f"两者都能 len 和按下标取值：len(vector)={len(vector)}，vector[0]={vector[0]}"
    )
    print(f"vector.dtype={vector.dtype}，表示数组中数字的存储类型。")
    print(f"普通列表乘 2（重复内容）：{numbers * 2}")
    print(f"数组乘 2（每个数乘 2）：{vector * 2}")

    print("\n形状：有几条向量，每条有几个数？")
    print("shape、ndim 是数组属性，直接读取，不加调用括号。")
    print(f"一条向量：shape={vector.shape}，ndim={vector.ndim}，len={len(vector)}")
    print("(3,) 是只有一个元素的元组：这条数组沿唯一一条轴存了三个数。")
    print("在 embedding 中叫三维向量，因为每条有三个数；ndim=1 则表示数组有一条轴。")
    print("同理，一条 512 维 embedding 的 shape 是 (512,)，ndim 仍是 1。")
    rows = [numbers, [0.5, -0.25, 0.125]]
    batch = np.array(rows, dtype=np.float32)
    print(f"手工拼成两行：\n{batch}")
    print(f"批数组：shape={batch.shape}，ndim={batch.ndim}，len={len(batch)}")
    print("(2, 3) 表示两条、每条三个数；len(batch)=2 是条数，不是每条向量的维度。")
    print("这是手工创建的二维数组示意，FastEmbed 的 embed 实际返回生成器。")

    print("\n转换：list(vector) 和 vector.tolist() 有什么区别？")
    shallow = list(vector)
    # ndarray.tolist()：无参数；本例把一维数组转为含 Python float 的普通列表。
    plain = vector.tolist()
    print(
        f"list(vector) 外层类型={type(shallow).__name__}，首项类型={type(shallow[0]).__name__}"
    )
    print(
        f"vector.tolist()={plain}，外层类型={type(plain).__name__}，首项类型={type(plain[0]).__name__}"
    )
    print(
        "前者逐项收集，里面保留 NumPy 数值；后者也把数值转换为兼容的 Python 内置类型。"
    )
    print("本例是一维浮点数组，所以 .tolist() 返回 list[float]；不会修改原数组。")
    print(f"转换后原 vector 的类型仍为 {type(vector).__name__}。")

    print("\n接回模型接口：收集外层，不等于转换每条向量。")
    # 生成器表达式：逐条创建手工数组，只模仿 embed 逐条产生数组的返回结构。
    pending = (np.array(row, dtype=np.float32) for row in rows)
    print(f"人工生成器类型={type(pending).__name__}，这里没有模型调用。")
    vectors = list(pending)
    print(f"list(pending) 后：外层={type(vectors).__name__}，条数={len(vectors)}")
    print(f"里面第 0 条仍是 {type(vectors[0]).__name__}，shape={vectors[0].shape}")
    first = vectors[0].tolist()
    print(f"对第 0 条调用 .tolist() 后：{first}，首项类型={type(first[0]).__name__}")

    print("\n5. 注意什么")
    print("vector.tolist() 的前提是 vector 为数组；普通 Python list 没有这个方法。")
    print("本课必须分清：生成器 -> 收集为 list；其中每条 ndarray -> 转为普通数值列表。")
    print("二维数组调用 .tolist() 会得到嵌套列表；一维数组才对应本课的一条向量列表。")
    print(
        "从模型拿到数组对象后可以直接调用它的方法；只为调用 .tolist() 无需另写 import numpy。"
    )
    print("本文件直接创建数组，所以需要 import numpy as np。")
    print("向量的语义来自已经训练好的模型；NumPy 负责这里的数值表示和操作。")
    print("看懂这些后再回到真实 embedding 演示，不新增练习或观察题。")


if __name__ == "__main__":
    main()
