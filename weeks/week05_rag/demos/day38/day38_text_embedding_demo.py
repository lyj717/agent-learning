"""Day 38：为 RAG 片段与问题认识真实 embedding API 的输入、输出及边界。

只演示短字符串，不提供加载、切分与来源配对的完整实现；这些由学员练习组合。
默认只读模型缓存。首次准备可传 --download，允许从公开来源下载模型文件。
首次接触 NumPy 时先运行同目录 day38_numpy_array_demo.py，认识数组和 .tolist()。
"""

import argparse

from day38_embedding_support import MODEL_CACHE, MODEL_NAME, VECTOR_SIZE
from fastembed import TextEmbedding


def main() -> None:
    """用真实本地模型演示批量文本与单个问题的向量输出。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="允许下载公开模型文件")
    args = parser.parse_args()

    print("Day 38｜文字送进去，为什么拿回来的是一组数字？")
    print("\n这份演示在本周目标中的作用")
    print("本周做带出处的 RAG 问答。Day 36/37 已有带来源的正文片段。")
    print("本演示负责向量化：把片段和问题变成能用于比较的数字表示。")
    print("学完应能调用真实模型、区分批量与单条输出，并核对输入和向量的对应。")
    print("练习会把这个 API 接到你自己的片段上；Day 39 再接向量库和检索。")
    print("首次接触 NumPy：先读同目录 day38_numpy_array_demo.py，再回来看本演示。")

    print("\n1. 这是什么")
    print("TextEmbedding 是 FastEmbed 提供的模型接口，不是对话模型。")
    print("导入：from fastembed import TextEmbedding。输入文字，输出向量，不生成回答。")
    print("本课固定中文模型 BAAI/bge-small-zh-v1.5，每条输出 512 个数字。")
    print("这是本机 CPU 上真实运行的模型，和前一份人工二维数字演示分开。")

    print("\n2. 为什么需要它")
    print("问题和资料不一定使用同样的词，不能只凭字符串完全相同寻找相关资料。")
    print("向量提供一种可计算的表示；能否找到支持答案的原文，还要后续检验。")

    print("\n3. 场景")
    print("以下两句话是 AI 教学文本；我们分别编码资料和一个问题，暂不排序或回答。")
    passages = [
        "打印机卡纸时，先关闭电源再取出纸张。",
        "新员工应在报到当天领取门禁卡。",
    ]
    question = "打印机夹住纸了该怎样处理？"
    print(f"资料：{passages}")
    print(f"问题：{question}")

    print("\n4. 代码与实际结果")
    print("构造：TextEmbedding(model_name=模型名, cache_dir=缓存路径, ...)")
    print("模型名在库里有英文默认值，本课必须显式指定上面的中文模型。")
    print("cache_dir 可选：本课指定到当天 outputs，避免把大文件放进系统临时目录。")
    print("threads=2、cuda=False 可选：限制 CPU 线程数、明确不用显卡。")
    print("local_files_only 可选：True 只读缓存；本文件 --download 时才设 False。")
    print(f"模型：{MODEL_NAME}；本课预期维度：{VECTOR_SIZE}")
    print(f"缓存：{MODEL_CACHE}")
    print("模型加载中；首次下载需要网络，下载完成后可使用默认的本地模式。", flush=True)
    # TextEmbedding(...) 返回模型对象；本课展示完整初始化，练习环境会复用同样配置。
    model = TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE),
        threads=2,
        cuda=False,
        local_files_only=not args.download,
    )
    print("调用：model.embed(documents=字符串列表, batch_size=256, ...) -> 生成器")
    print("documents 必填，传正文字符串列表；batch_size 可选，控制一批处理多少条。")
    print("不传 model 参数：模型已经在构造对象时选定。这里用 batch_size=2。")
    # embed(字符串列表, batch_size=批大小)：按输入顺序逐条产生 NumPy 数组。
    pending = model.embed(passages, batch_size=2)
    print(f"embed 返回类型：{type(pending).__name__}；还不是 list。")
    vectors = list(pending)
    print(f"list 消费生成器后：输入 {len(passages)} 条，得到 {len(vectors)} 条向量。")
    for index, vector in enumerate(vectors):
        # ndarray.tolist()：把 NumPy 数组转换成普通 Python 列表，不改变数字顺序。
        numbers = vector.tolist()
        print(f"输入[{index}]={passages[index]}")
        print(f"  向量类型={type(vector).__name__}，维度={len(numbers)}")
        print(f"  转列表后元素类型={type(numbers[0]).__name__}，前 5 项={numbers[:5]}")
    print(f"同一个生成器再取一次：{list(pending)}；已经消费过，不能重用。")

    question_batch = list(model.embed([question]))
    print(f"一个问题也传列表 [question]：得到 {len(question_batch)} 条向量。")
    question_vector = question_batch[0].tolist()
    print(
        f"取第 0 条后才是问题向量：维度={len(question_vector)}，前 5 项={question_vector[:5]}"
    )

    print("\n5. 注意什么")
    print("条数是有几段输入；维度是每段有几个数字。两条输入不是一个二维向量。")
    print("传 page_content 正文；id、source、行号另外保留，不能从数字反推出准确出处。")
    print("重复正文仍有各自的记录，不能因为向量相同就丢掉其中一个来源。")
    print("本课按 BGE v1.5 支持的无指令方式：资料和问题都不额外加前缀。")
    print("后续沿用同一模型与生成方式；换模型即使维度相同，也需要重新生成资料向量。")
    print("该模型输入上限为 512 tokens，过长文本会截断；行数限制不能保证不超限。")
    print("今日短教学文本不会触及上限；处理自有资料时仍需检查片段长度。")
    print("真实浮点数会受运行环境影响，不照抄前 5 项作为验收答案。")
    print("缓存文件不是学员交付物；今天没有调用 DeepSeek、保存向量库或生成回答。")


if __name__ == "__main__":
    main()
