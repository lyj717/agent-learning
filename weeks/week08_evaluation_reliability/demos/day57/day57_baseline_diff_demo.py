"""Day57 演示二：基线对比——回归是「和上一版比」，不是「这次看着还行」。

Week08 要能回答「改了提示词或换了模型，系统有没有变差」。
本演示讲冻结基线、四类变化，以及为什么总通过数会骗人。
学完应能解释 baseline 为什么要单独保存、CI 通常只拦哪一类；
练习 B 会把这个比较写成 compare_baseline。
全部是内联教学数据（设备借用场景），不读练习文件，不调用模型或网络。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、场景、代码、骗人的总数、边界的顺序讲一次基线回归。"""
    say("Week08 的交付物要能接进 CI：每次改完，自动告诉你有没有变差。")
    say("本演示负责其中的判定口径：拿这一版逐题结果，和冻结的上一版比较。")
    say("学完应能解释 baseline 为什么要单独保存、四类变化怎么分、CI 该拦哪一类；")
    say("练习 B 会把比较逻辑写成函数，练习的 regression 入口用它跑两版真实回答。")

    say("\n一、这是什么")
    say("baseline（基线）是一份冻结的逐题结果：上一版对同一批题，每题通过还是失败、")
    say("失败项是什么。它随代码一起保存，不随后一次运行自动改写。")
    say("回归对比就是把新一版的逐题结果和这份基线对齐，分成四类：")
    say("  regressed：上次通过、这次失败——真正要拦的回归。")
    say("  fixed：上次失败、这次通过——修好了，要记下来。")
    say("  still_failing：两次都失败——已知欠账，单独列，不藏起来。")
    say("  unchanged_pass：两次都通过。")

    say("\n二、为什么需要它")
    say("没有基线，只能靠「这次跑起来没报错」「感觉还行」判断，改坏的地方没人发现。")
    say("只报一个总通过率也不够：一题修好、另一题改坏，总数可以完全不变。")
    say("把逐题结果冻结下来，比较才有对象；失败项名字还能指出是哪一项检查变坏了。")

    say("\n三、具体场景：8 道设备借用问答，两版回答")
    rows = [
        ("c01", True, True),
        ("c02", True, True),
        ("c03", True, False),
        ("c04", False, True),
        ("c05", True, True),
        ("c06", True, True),
        ("c07", False, False),
        ("c08", True, True),
    ]
    say("题号｜上一版｜这一版")
    for case_id, before, after in rows:
        say(f"{case_id}｜{'通过' if before else '失败'}｜{'通过' if after else '失败'}")

    passed_before = sum(1 for _, before, _ in rows if before)
    passed_after = sum(1 for _, _, after in rows if after)
    regressed = [case_id for case_id, before, after in rows if before and not after]
    fixed = [case_id for case_id, before, after in rows if not before and after]
    still_failing = [
        case_id for case_id, before, after in rows if not before and not after
    ]
    unchanged_pass = [case_id for case_id, before, after in rows if before and after]

    say(f"\n总数：上一版 {passed_before}/8；这一版 {passed_after}/8")
    say(f"regressed={regressed}")
    say(f"fixed={fixed}")
    say(f"still_failing={still_failing}")
    say(f"unchanged_pass={unchanged_pass}")
    say("两版都是 6/8，但 c04 修好、c03 改坏了。只看总数会得出「没有变化」。")

    say("\n四、把它放进 CI 时，谁该让流水线失败")
    say("regressed 非空 → 失败，这是回归。")
    say("still_failing 非空 → 不因此失败，但要出现在报告里（已知欠账）。")
    say("fixed 非空 → 通过，提醒更新基线，否则下次还会被当成 fixed。")
    say("基线不能每次运行后自动覆盖：那样每次都是「和刚跑完的自己比」，永远没有回归。")

    say("\n五、注意什么")
    say("1. 题号集合变了（新增或删除题），要建新的基线版本，不能悄悄合并两边。")
    say("2. 规则本身改了（比如新加一条禁词），也要重建基线；")
    say("   否则分不清变化是回答变了，还是判分口径变了。")
    say("3. 已知失败要留在基线里单独列；靠跳过失败题让数字好看，等于把问题藏起来。")
    say("4. 基线不是「正确答案表」：它记录的是上一版的判定结果，")
    say("   规则层放过的语义错误，也会原样留在通过项里。")
    say("5. 一次只比同一批题、同一套规则；跨版本比较要先说清两版差在哪。")

    say("\n下一步：实现练习 B 的 compare_baseline；")
    say("再用 --part regression 比较 day57_baseline.json 与两版真实回答。")


if __name__ == "__main__":
    main()
