"""Day57 补充演示：按编号配对，为什么双层循环是 n×n，字典查找只要 n 次。

Day57 的 compare_baseline 要把两版结果按题号配对。本演示用两份成绩单说明
「逐个扫描」和「按键直接取」的差别，对应把 O(n²) 改成 O(n)。
学完应能解释比较次数从哪来，并在自己的函数里去掉内层循环。
全部离线，不读练习文件，不调用模型或网络。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def pair_by_scan(
    before: dict[str, int], after: dict[str, int]
) -> tuple[list[tuple[str, int, int]], int]:
    """双层循环逐个找同号，返回配对结果与比较次数。"""
    pairs = []
    comparisons = 0
    for before_id, before_score in before.items():
        for after_id, after_score in after.items():
            comparisons += 1
            if before_id == after_id:
                pairs.append((before_id, before_score, after_score))
    return pairs, comparisons


def pair_by_lookup(
    before: dict[str, int], after: dict[str, int]
) -> tuple[list[tuple[str, int, int]], int]:
    """按学号直接取另一份成绩，返回配对结果与查找次数。"""
    pairs = []
    lookups = 0
    for before_id, before_score in before.items():
        lookups += 1
        pairs.append((before_id, before_score, after[before_id]))
    return pairs, lookups


def main() -> None:
    """按场景、两种写法、计数、边界的顺序讲一次按键查找。"""
    say("Day57 练习里把两版逐题结果配对：题号相同的一对，才能分出")
    say("regressed / fixed / still_failing / unchanged_pass。")
    say("本演示用 4 个学号的两份成绩单，比较「双层循环」和「字典直接取」的差别。")
    say("学完应能说清比较次数从哪来，并把内层循环改成一次按键访问。")

    say("\n一、这是什么")
    say("配对，就是给第一份里的每个编号，找到第二份里同一个编号的那条记录。")
    say("第一份有 n 条、第二份也有 n 条，且两边编号集合相同。")

    say("\n二、具体场景：两份成绩单，编号顺序不同")
    before = {"S03": 88, "S01": 92, "S02": 75, "S04": 60}
    after = {"S02": 78, "S04": 60, "S01": 92, "S03": 88}
    say(f"第一次成绩：{before}")
    say(f"第二次成绩：{after}")

    say("\n三、写法一：对每个学号，把第二份从头看一遍")
    scanned, comparisons = pair_by_scan(before, after)
    say(f"配对结果={sorted(scanned)}")
    say(f"比较次数={comparisons}（4 个学号 × 4 条记录）")
    say("第一份每条都要把第二份 4 条看一遍，n 条就是 n×n 次；")
    say("8 条就是 64 次，100 条就是 1 万次。这就是 O(n²) 的来源。")

    say("\n四、写法二：按学号直接取第二份里的记录")
    looked_up, lookups = pair_by_lookup(before, after)
    say(f"配对结果={sorted(looked_up)}")
    say(f"查找次数={lookups}（每个学号只查一次）")
    say("字典按 key 查值，平均是 O(1)：不需要从头看，直接定位到那条记录。")
    say("n 个学号就查 n 次，这就是 O(n)。")

    say("\n五、两边结果一样，差在次数")
    say(f"两种写法配对结果相同={sorted(scanned) == sorted(looked_up)}")

    say("\n六、注意什么")
    say("1. 前提是两边编号集合相同；如果缺号，after[before_id] 会抛 KeyError。")
    say("   你的函数已经在前面校验过题号集合，所以可直接按键取。")
    say("2. 不能确定键一定在时，用 after.get(before_id) 并处理 None，")
    say("   或先校验；不要用 try/except KeyError 掩盖数据问题。")
    say("3. O(1) 是平均情况：字典是哈希表，极端冲突时仍可能变慢；")
    say("   这里说的是常规工程口径，不是严格证明。")
    say("4. 输出要排序时，对结果列表 sorted()，不要依赖字典本身的插入顺序。")

    say("\n下一步：把 compare_baseline 内层的 for 第二份循环去掉，")
    say("改成 current[base_case_id]；四个列表返回前已经 sorted() 就保持。")


if __name__ == "__main__":
    main()
