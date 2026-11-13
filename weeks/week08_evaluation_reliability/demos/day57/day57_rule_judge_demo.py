"""Day57 演示一：规则匹配判分——先看清楚它判得了什么、判不了什么。

Week08 的目标是给已有问答链路加自动评测与 CI 回归；本演示只负责最便宜的一层：
用事先写好的字面条件检查一份回答，输出「哪几项没有通过」。
学完应能解释一条规则为什么通过或失败，并说清它看不见哪些错误。
练习 A 会把这个判断写成 judge_answer；本演示用独立的设备借用场景，
没有同名函数，也不读练习数据。全部离线，不调用模型、向量库或网络。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、场景、代码、盲区、边界的顺序讲一次规则判分。"""
    say("Week08 要给项目加自动评测和回归检查：改提示词、换模型、动检索之后，")
    say("要能在一两分钟内知道「哪些题从通过变成了失败」。")
    say("本演示负责其中最便宜的一层：规则匹配判分。")
    say("学完应能判断一条规则为什么通过/失败，并说出它判不了什么；")
    say("练习 A 会把这里的判断写成一个可复用的函数。")

    say("\n一、这是什么")
    say("规则匹配判分，是把「一份回答该满足什么条件」写成可执行的字面检查：")
    say("必须出现哪些词、不能出现哪些词、引用的片段编号是否真在本次检索结果里。")
    say("它输出的是「哪几项没通过」，不是一个笼统的对错。")
    say("它不知道答案的意思，只比较文字和集合。")

    say("\n二、为什么需要它")
    say("人工判分最准，但每次改代码都找人重看几十条，既慢又不可重复；")
    say("模型裁判能看语义，但要花钱、有波动，还要自己的评测器先被评测。")
    say("规则层零成本、结果确定，适合每次提交都跑；它守的是结构、格式和硬约束。")
    say("所以常见做法是三层：规则先拦，模型裁判再看语义，人工只抽样。")

    say("\n三、具体场景：设备借用问答")
    say("问题：借用投影仪时，在哪里登记、要带什么？")
    say("标注时定下的预期：回答必须出现「前台」和「工牌」，不能出现「押金」；")
    say("回答必须至少引用一个本次检索到的片段编号。")
    say("检索结果有两个编号：equipment.md#L1-L2、equipment.md#L3-L4。")

    say("\n四、代码：逐项检查，失败项留名字")
    must_include = ["前台", "工牌"]
    must_not_include = ["押金"]
    retrieved_ids = {"equipment.md#L1-L2", "equipment.md#L3-L4"}
    answer_text = "先到前台登记，并带上工牌。"
    cited_ids = ["equipment.md#L1-L2"]

    missing = [point for point in must_include if point not in answer_text]
    forbidden = [point for point in must_not_include if point in answer_text]
    no_citation = not cited_ids
    outside = [item for item in cited_ids if item not in retrieved_ids]
    failed = []
    if missing:
        failed.append("missing_points")
    if forbidden:
        failed.append("forbidden_text")
    if no_citation:
        failed.append("no_citation")
    if outside:
        failed.append("citation_not_retrieved")

    say(f"回答={answer_text}")
    say(f"缺失要点={missing}；出现禁词={forbidden}")
    say(f"引用={cited_ids}；不在检索结果={outside}")
    say(f"结果：passed={not failed}；failed={failed}")

    say("\n换一份回答，看失败项怎样把原因分开：")
    bad_text = "先到前台登记，但要交押金。"
    missing_bad = [point for point in must_include if point not in bad_text]
    forbidden_bad = [point for point in must_not_include if point in bad_text]
    failed_bad = []
    if missing_bad:
        failed_bad.append("missing_points")
    if forbidden_bad:
        failed_bad.append("forbidden_text")
    say(f"回答={bad_text}")
    say(f"结果：passed=False；failed={failed_bad}")
    say("只报一个 False，看不出是缺要点还是踩了禁词；")
    say("失败项列表能让回归报告直接指出变坏的检查名字。")

    say("\n五、它的盲区：全部命中，也可能说反了")
    blind_text = "不用去前台登记，也不用带工牌。"
    blind_missing = [point for point in must_include if point not in blind_text]
    say(f"回答={blind_text}")
    say(f"规则检查：缺失要点={blind_missing} → 通过={not blind_missing}")
    say("但这句话把做法说反了：原文要求先到前台登记并带工牌。")
    say("规则只做字面包含：它看见了「前台」「工牌」，没看见前面的「不用」。")
    say("同义改写、否定句、结论和原文相反，都可能这样溜过去。")

    say("\n六、注意什么")
    say("1. must_include 是必要条件，不是充分条件：全命中只说明这些词出现过。")
    say("2. 子串匹配很脆：改写、空格、大小写都会影响结果；正则更灵活也更难维护。")
    say("3. 引用编号在检索结果里，只证明「没有编造编号」，不证明片段支持结论。")
    say("4. 失败项要有固定名字和固定顺序，回归对比才能稳定地分辨改坏了哪一项。")
    say("5. 规则判「通过」的题也要留人工抽查；否则错误会被基线冻结成永远通过。")
    say("6. 规则来自人写的预期要点，要点本身标错了，再确定的规则也只是稳定地错。")

    say("\n下一步：读演示二，理解「回归 = 和冻结的上一版比」；")
    say("然后实现练习 A 的 judge_answer，再实现 B 的 compare_baseline。")


if __name__ == "__main__":
    main()
