"""Day45：第一次认识 BM25，用独立词库理解评分器的输入、输出与边界。

用途：为关键词通道准备。先读 main 中的两次关键调用，再看下方的独立评分对照。
资料和问题均为 AI 手写教具，没有对应的仓库资料文件，不是学员实验结果。
从仓库根目录运行本文件即可；只使用本机已安装的 rank-bm25==0.2.2。

接口参考：https://github.com/dorianbrown/rank_bm25#usage
评分实现：https://github.com/dorianbrown/rank_bm25/blob/master/rank_bm25.py
"""

from math import log

# rank-bm25 是安装包名；Python 中从 rank_bm25 模块导入 BM25Okapi 评分器类。
from rank_bm25 import BM25Okapi


def main() -> None:
    """先直接调用评分 API，再通过独立对照解释分数的来源与使用边界。"""
    print("Week6 要根据标注比较检索改动。Day45 给原向量检索增加关键词通道。")
    print("本演示负责其中的评分：学完能准备词项输入、创建评分器、读懂逐片段分数。")
    print("练习 A 再把这些分数与 Document 的编号对应，组成关键词排名。")
    print("下面都是 AI 手写的小资料；英文只是为了看清每个参与匹配的词项。")

    print("\n一、BM25 是什么，为什么要用它？")
    print("BM25 是一种按词项统计给资料打分的方法。一个问题对应每份资料的一个分数。")
    print("例如用户搜索 reset（复位），希望先找到写有这个词项的设备说明。")
    print("如果只判断‘有没有 reset’，所有含它的片段就都一样，无法进一步比较。")
    print("BM25 还考虑：它在一块里出现几次、全库有多少块含它、这一块有多长。")
    print("同一问题、同一个评分器下，分数越高，表示按这套词项规则越值得优先查看。")

    print("\n二、输入形状：corpus 是资料集合，query 是一个问题")
    print("先把文字处理成词项。一个词项是参与匹配的单位，例如 'reset' 或一个中文字。")
    print("corpus：list[list[str]]。外层每项是一块资料，内层每项是这块的一个词项。")
    print("query：list[str]。它只代表一个问题，所以没有 corpus 那层外部列表。")
    print("本例已手工写好词项；真实练习用同一个 tokenize_text 处理问题和所有片段。")
    corpus = [
        ["reset", "device", "button"],
        ["reset", "reset", "button"],
        ["invoice", "refund", "payment"],
        ["weather", "rain", "forecast"],
        ["python", "dictionary", "key"],
        ["service", "timeout", "retry"],
    ]
    labels = ["A 复位说明", "B 复位提示", "C 账单", "D 天气", "E 字典", "F 服务重试"]
    query = ["reset"]
    for index, tokens in enumerate(corpus):
        print(f"  corpus[{index}]：{labels[index]}，词项={tokens}")
    print(f"  query={query}")
    print("注意：内层是列表，不是集合。B 的 reset 出现两次，重复次数会用于评分。")
    print(
        "直接传 'reset device' 这种字符串不会替你分词，还可能被逐字符处理，输入就变了。"
    )

    print("\n三、第一次关键调用：用全部资料创建评分器")
    print("导入：from rank_bm25 import BM25Okapi")
    print("签名：BM25Okapi(corpus, tokenizer=None, k1=1.5, b=0.75, epsilon=0.25)")
    print("corpus 必填；本例传上面六块的词项列表，不是只传预计会命中的 A、B。")
    print("创建对象时统计全库：每块的词项次数、长度，以及每个词出现在多少块里。")
    print("返回 BM25Okapi 对象，保存这些统计，后续可反复拿它给不同问题评分。")
    # BM25Okapi(词项列表的列表)：创建本地评分器；这里所有可选参数使用默认值。
    bm25 = BM25Okapi(corpus)
    print("  已执行 bm25 = BM25Okapi(corpus)，得到可调用 get_scores 的评分器对象。")
    print("可选参数先认识用途，本次练习保留默认值：")
    print("  tokenizer=None：输入已是词项，不再让构造器调用分词函数。")
    print(
        "    若传函数，其接口为 tokenizer(一份原始文本) -> list[str]；它只处理建库资料。"
    )
    print("    get_scores 的问题词项仍需调用方准备，本课统一用外部 tokenize_text。")
    print("  k1=1.5：控制一个词反复出现时，加分如何逐渐趋于饱和。第五节会对照。")
    print("  b=0.75：控制按资料长度调整分数的程度；b=0 表示不做长度调整。")
    print("  IDF 是根据词项在全库的分布算出的区分权重，第五节会用两个词来比较。")
    print("  epsilon=0.25：参与负 IDF 的替换。它不是最低正分，第七节看具体例子。")

    print("\n四、第二次关键调用：用一个问题给全部资料评分")
    print("签名：bm25.get_scores(query)；query 必填，是已处理好的问题词项 list[str]。")
    # get_scores(问题词项列表)：返回一维 NumPy 数组，第 i 项对应 corpus 的第 i 块。
    scores = bm25.get_scores(query)
    print(f"  已执行 scores = bm25.get_scores({query})")
    print(f"  实际返回={scores}")
    print("这是 NumPy 的一维数组，可以先当成按下标读取的数字序列，不需要先学 NumPy。")
    print(
        f"  len(scores)={len(scores)}，与六块资料一一对应；scores[0] 对应 corpus[0]。"
    )
    for index in range(len(corpus)):
        # float(数组中的数值)：转成普通 Python float，便于打印和后续比较。
        score = float(scores[index])
        print(
            f"  下标={index}，{labels[index]}，正文词项={corpus[index]}，分数={score:.6f}"
        )
    print("留意：B 的分数高于 A，但返回的第一项仍是 A 的分数。get_scores 没有排序。")
    print("它也没有替你选前 3 条或返回片段 id。使用分数时必须保留原来的下标对应关系。")
    print("如果先把 scores 单独排序，再按新下标去取原片段，就可能把高分配给另一块。")

    print("\n五、分数怎么来的：把三个影响因素分开看")
    print("5.1 词频 TF：一个词在同一块资料里出现几次。不是全库总共出现几次。")
    print("主例 A、B 都长 3 个词项，reset 分别出现 1 次、2 次，所以 B 得分更高。")
    show_term_frequency()

    print("\n5.2 词项权重 IDF：看全库有多少块包含这个词，衡量它的区分能力。")
    print("主例 reset 出现在 A、B 两块里，device 只出现在 A 一块里。")
    print(
        "固定看 A：这两个词在 A 都出现 1 次，资料长度也相同，可以观察稀有程度的影响。"
    )
    device_scores = bm25.get_scores(["device"])
    print(f"  A 对 reset 的分数={float(scores[0]):.6f}")
    print(f"  A 对 device 的分数={float(device_scores[0]):.6f}")
    print("这里更少资料包含的 device 权重更高。这也是建评分器时需要统计全库的原因。")
    print("这只是隔离因素的对照；不同问题的分数不能当成统一的置信度来比较。")
    show_document_length()

    print("\n六、匹配规则和分数的含义")
    print("get_scores 按传入的词项逐个匹配，库本身不会统一大小写或自动识别同义词。")
    upper_scores = bm25.get_scores(["RESET"])
    print(f"  同一个评分器，问题改为 ['RESET']，实际分数={upper_scores}")
    print("因为资料只有小写 reset。问题和资料都先用同一规则处理，才能避免这类漏匹配。")
    print("多词问题会把各问题词项的贡献相加；缺一个问题词不意味着整块一定是零分。")
    partial_scores = bm25.get_scores(["reset", "warranty"])
    print(f"  问题改为 ['reset', 'warranty']，实际分数={partial_scores}")
    print("warranty（保修）在六块里都没出现，它没有贡献；reset 仍让 A、B 得分。")
    print("因此有匹配、有分数，只能支持词项排名，不能证明片段包含所问的全部答案。")
    print("device 的例子还得到大于 1 的分数：BM25 没有‘0 到 1 的正确概率’这个含义。")

    show_score_boundaries()

    print("\n八、回到练习 A：你要自己接起来的部分")
    print("本演示讲清了两次 API 调用：用全库词项创建评分器，再用问题词项取得逐块分数。")
    print(
        "A 需要把 Document.page_content 处理成词项，并保留分数与原 Document.id 的对应。"
    )
    print("再按题目要求筛选正分、排列次序、返回最多 limit 个编号；这些组合由你完成。")
    print(
        "调用前处理：空资料列表、全部资料无词项、问题处理后无词项，避免空词库建评分器。"
    )
    print(
        "空白问题在 A 中按题意报 ValueError；这属于调用方的参数规则，不是库替你检查。"
    )
    print("资料内容、词项或顺序改变后，应重新创建评分器，避免沿用旧统计或错配分数。")


# 下方每个函数都有自己的最小资料，只用于隔离观察评分因素，不包含练习 A 的实现。
def show_term_frequency() -> None:
    """临时关闭长度调整，观察正权重词项重复加分但不会按次数成倍增长。"""
    print("  独立对照：让 reset 分别出现 1、2、8 次，其余五块都不含它。")
    print("  为单独观察次数，这里临时设 b=0，关闭长度调整；练习 A 仍用默认 b=0.75。")
    corpus = [
        ["reset"],
        ["reset", "reset"],
        ["reset"] * 8,
        ["invoice"],
        ["weather"],
        ["dictionary"],
        ["timeout"],
        ["refund"],
    ]
    bm25 = BM25Okapi(corpus, b=0)
    scores = bm25.get_scores(["reset"])
    for index in range(3):
        print(
            f"  出现 {len(corpus[index])} 次，分数={float(scores[index]):.6f}，"
            f"是出现 1 次时的 {float(scores[index] / scores[0]):.3f} 倍"
        )
    print("  次数从 1 变 8，分数没有变 8 倍。这就是重复加分逐渐趋于饱和。")


def show_document_length() -> None:
    """在匹配次数相同时，对照默认长度调整与关闭长度调整。"""
    print("\n5.3 资料长度：本库按词项个数计算长度，不按原文字节数计算。")
    print("相同次数的匹配，出现在很长的片段里可能更偶然，所以要结合相对长度调整。")
    corpus = [
        ["reset", "button"],
        ["reset", "button", "device", "manual", "press", "hold", "release", "wait"],
        ["invoice", "refund"],
        ["weather", "rain"],
        ["dictionary", "key"],
        ["timeout", "retry"],
    ]
    print(f"  短块={corpus[0]}")
    print(f"  长块={corpus[1]}")
    print(f"  另外四块={corpus[2:]}；两块中的 reset 都只出现 1 次。")
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(["reset"])
    print(f"  默认 b=0.75：短块={float(scores[0]):.6f}，长块={float(scores[1]):.6f}")
    without_length = BM25Okapi(corpus, b=0)
    equal_scores = without_length.get_scores(["reset"])
    print(
        f"  关闭 b=0：短块={float(equal_scores[0]):.6f}，长块={float(equal_scores[1]):.6f}"
    )
    print("  这个对照里默认设置让短块更高；关闭长度调整后两者相同。")
    print("  不是‘越短一定越高’：实际分数还同时受词项次数和词项权重影响。")


def show_score_boundaries() -> None:
    """逐步代入 IDF 计算，区分没有匹配与匹配后零分、负分。"""
    print("\n七、重要边界：零分和负分分别可能怎么来？")
    print("以下针对当前 rank-bm25==0.2.2 的 BM25Okapi，其他实现的权重公式可能不同。")
    print("先把问题里的 reset 想成一次加分机会：它的贡献还要乘上自己的 IDF 权重。")
    print("匹配到了词，说明有这个加分机会；乘上的权重是多少，还要根据全库统计计算。")

    corpus_missing = [["invoice", "refund"], ["weather", "rain"]]
    bm25_missing = BM25Okapi(corpus_missing)
    missing_scores = bm25_missing.get_scores(["reset"])
    print(f"  情况 1：词库={corpus_missing}，问题=['reset']，分数={missing_scores}")
    print("    根本没有 reset，所以它对每块都没有贡献。")

    print("\n  看情况 2、3 前，先认识这版实现的初始 IDF 计算：")
    print("    初始 IDF = log((N - df + 0.5) / (df + 0.5))")
    print("    N 是全部片段的个数；df 是含这个词的片段个数，不是这个词出现的总次数。")
    print(
        "    log 是自然对数。本节只用三个性质：比值大于 1 得正数，等于 1 得 0，小于 1 得负数。"
    )
    # log(正数)：求自然对数。这里分别演示输入大于、等于、小于 1 的结果，不必手算对数。
    print(
        f"    可运行核对：log(3)={log(3):.6f}，log(1)={log(1):.6f}，log(1/3)={log(1 / 3):.6f}"
    )
    print("    情况 2、3 中，含 reset 的块都只含它 1 次，且块长等于平均块长。")
    print(
        "    此时次数和长度部分算出的系数恰好为 1，所以该块得分就是 reset 的最终 IDF。"
    )

    corpus_half = [["reset"], ["invoice"]]
    bm25_half = BM25Okapi(corpus_half)
    half_scores = bm25_half.get_scores(["reset"])
    initial_half_idf = log((2 - 1 + 0.5) / (1 + 0.5))
    print(f"\n  情况 2：词库={corpus_half}，问题=['reset']，分数={half_scores}")
    print("    第一步：一共 2 块，只有第一块含 reset，所以 N=2、df=1。")
    print(
        f"    第二步：初始 IDF=log((2-1+0.5)/(1+0.5))=log(1.5/1.5)=log(1)={initial_half_idf:.6f}"
    )
    print("    第三步：库只替换负 IDF；0 不小于 0，所以这里保留 0。")
    # idf：评分器保存的“词项 -> 最终权重”字典；此处读出来与手工计算对照。
    print(f"    评分器里的实际权重 bm25_half.idf['reset']={bm25_half.idf['reset']:.6f}")
    print(f"    第一块：有 reset，但贡献=1×0=0，实际分数={float(half_scores[0]):.6f}。")
    print(
        f"    第二块：没有 reset，所以没有贡献，实际分数={float(half_scores[1]):.6f}。"
    )
    print("    两块都是零分，原因却不同；只看零分不能反推‘这一块没有匹配的词’。")

    corpus_tiny = [["reset", "button"]]
    bm25_tiny = BM25Okapi(corpus_tiny)
    tiny_scores = bm25_tiny.get_scores(["reset"])
    initial_tiny_idf = log((1 - 1 + 0.5) / (1 + 0.5))
    print(f"\n  情况 3：词库={corpus_tiny}，问题=['reset']，分数={tiny_scores}")
    print("    第一步：一共 1 块，这块含 reset，所以 N=1、df=1。")
    print(
        f"    第二步：初始 IDF=log((1-1+0.5)/(1+0.5))=log(1/3)={initial_tiny_idf:.6f}"
    )
    print(
        "    reset 和 button 都只出现在这一块里，两个不同词的初始 IDF 都是 -1.098612。"
    )
    # average_idf：全词库各个不同词项的初始 IDF 的算术平均值，用于负权重替换。
    print(
        f"    第三步：平均初始 IDF=(-1.098612-1.098612)/2={bm25_tiny.average_idf:.6f}"
    )
    print(
        "    第四步：库发现 reset 的初始 IDF 为负，就将它替换为 epsilon×平均初始 IDF。"
    )
    print(
        f"    epsilon=0.25；替换后=0.25×({bm25_tiny.average_idf:.6f})={bm25_tiny.idf['reset']:.6f}"
    )
    print(
        f"    最后：该块得分=1×({bm25_tiny.idf['reset']:.6f})={float(tiny_scores[0]):.6f}。"
    )
    print("    关键在于：平均值也是负的，正数 0.25 乘上负数，结果仍然为负。")
    print("    这段处理没有把负数截成 0，也没有把权重设成 0.25；它做的是乘法替换。")
    print("    因此它不能保证最终得分非负；负分也不是在判定原文内容错误。")
    show_zero_weight_limit()
    print("这三组说明：有匹配仍可能零分或负分，不能把‘有词’与‘正分’画等号。")
    print("练习 A 只返回严格大于 0 分的块，是本课固定规则，不是 BM25 的普遍定理。")
    print("按这条规则返回 []，也不能据此宣布原文没有答案；正分规则可能过滤了含词片段。")
    print(
        "如果被过滤的正是标注相关片段，评测必须记录漏检；不能用‘分数为零’解释成标注无关。"
    )


def show_zero_weight_limit() -> None:
    """用三个独立词库展示这版 IDF 的区分能力与半数含词时的局限。"""
    print("\n  补充对照：匹配与未匹配同分，这个分数在这里还有用吗？")
    print("    就情况 2 而言，确实没有区分力；含词与不含词都得 0，单靠分数选不出来。")
    print("    出现在一半片段的词仍能帮助排除另一半，只是这版公式给它的权重恰好为 0。")
    cases = [
        ("2 块中 1 块含 reset", [["reset"], ["invoice"]]),
        ("3 块中 1 块含 reset", [["reset"], ["invoice"], ["weather"]]),
        ("4 块中 2 块含 reset", [["reset"], ["reset"], ["invoice"], ["weather"]]),
    ]
    print("    下列每行都是独立 AI 教具，问题同为 ['reset']；不属于真实检索优化实验。")
    for label, corpus in cases:
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(["reset"])
        print(f"    {label}：最终 IDF={bm25.idf['reset']:.6f}，各块分数={scores}")
    print("    第二行可以把含词的块排在前面：它得正分，其余两块是 0。")
    print("    第三行说明不是‘词库大一点就没问题’：恰好半数含词时，仍然全部为 0。")
    print("    同分时按 id 排序只能固定次序，无法补回这个词丢掉的区分信息。")
    print(
        "    真实对比仍要固定资料；这里改变词库仅为解释公式，不是靠添加无关资料提升效果。"
    )


if __name__ == "__main__":
    main()
