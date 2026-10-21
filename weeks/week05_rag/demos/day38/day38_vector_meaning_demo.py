"""Day 38：用人工数字理解向量、维度和余弦，不调用真实 embedding。"""

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """AI 提供的数学教具：计算两个同维、非零向量的余弦相似度。"""
    if not left or len(left) != len(right):
        raise ValueError("两个向量必须非空，且维度相同。")
    # math.sqrt(非负数)：求平方根；平方和再开方得到向量的长度。
    left_length = math.sqrt(sum(value * value for value in left))
    right_length = math.sqrt(sum(value * value for value in right))
    if left_length == 0 or right_length == 0:
        raise ValueError("零向量没有方向，不能计算余弦相似度。")
    # zip(两份列表)：逐项配对；乘积之和叫点积，这里用于计算方向的夹角。
    dot_product = sum(a * b for a, b in zip(left, right))
    return dot_product / (left_length * right_length)


def main() -> None:
    """比较三组人工方向，说明真实文本向量的使用边界。"""
    print("Day 38｜一串数字为什么可以用来比较文字？")
    print("\n这份演示在本周目标中的作用")
    print("本周目标：做带出处的 RAG 问答，先找资料，再让模型依据资料回答。")
    print("本演示对应向量化：先认识模型将返回什么形状，以及后面怎样比较它们。")
    print("学完应能分清向量、维度、相似度分数，不把分数当成答案或出处。")
    print("后续会用真实模型生成片段与问题向量；今天这份只提供数学直觉。")

    print("\n1. 这是什么")
    print("向量可以先看成有固定顺序的一组数字，例如 [2.0, 0.0]。")
    print("有几个数字就有几维：这组有两个数字，所以是二维向量。")
    print("embedding 模型把文字转换成向量；文字与向量是不同的表示。")
    print("下面的数字由 AI 手工指定，没有模型、训练数据或真实文本含义。")

    print("\n2. 为什么需要它")
    print("不同写法可能谈同一件事。文本向量让程序能计算一种数值上的接近程度。")
    print("余弦相似度比较向量方向：同向、垂直、反向分别对应 1、0、-1。")
    print("这提供一个比较办法，但真实模型能否找到有用资料，仍要用实际样本检查。")

    print("\n3. 场景")
    print("以后会比较一个问题和一条资料片段的向量。现在先用二维数字观察方向。")
    print("这里的两维只是画方向用的坐标，不给真实向量的每一维指定语义名称。")

    print("\n4. 代码与实际结果")
    reference = [2.0, 0.0]
    examples = [
        ("同方向、长度不同", [6.0, 0.0], 1.0),
        ("方向垂直", [0.0, 3.0], 0.0),
        ("方向相反", [-4.0, 0.0], -1.0),
    ]
    print(f"参照向量：{reference}；维度：{len(reference)}")
    print("cosine_similarity(左向量, 右向量) -> float：本文件提供的数学教具。")
    print("计算方式：对应项乘积之和，除以两个向量长度的乘积。")
    for label, vector, expected in examples:
        actual = cosine_similarity(reference, vector)
        print(f"{label}｜向量={vector}｜实际={actual:.1f}｜期望={expected:.1f}")
    print("同方向的数字虽不相同，余弦仍为 1，因为这里比较的是方向。")

    print("\n5. 注意什么")
    print("真实比较要使用同一模型的兼容生成方式，维度也必须相同。")
    print("仅有维度相同还不够，不要混用不同模型或不兼容版本生成的向量。")
    print("余弦数学范围为 -1～1；分数不是事实正确率、概率，也不是引用支持度。")
    print("分数较高只说明按这个模型和比较方式更接近，不证明资料能支持某个结论。")
    print("向量本身没有 source、line_start 等字段，片段编号与出处仍需另外一起保留。")
    print("零向量不能算余弦；不同维度也不能直接这样比较。")
    print("余弦函数由 AI 作为教具提供，今天不要求你独立手写这段数学算法。")
    print("本文件没有真实 embedding 请求，也没有完成检索或带引用回答。")


if __name__ == "__main__":
    main()
