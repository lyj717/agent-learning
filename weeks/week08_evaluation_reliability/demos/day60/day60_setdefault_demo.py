"""Day60 补充演示：setdefault 到底做了什么——有就取，没有就放，再返回它。

按题号把多行收进同一个列表时，`by_id.setdefault(row["id"], []).append(row)`
看起来很绕。本演示用三条记录一步步展示它和 `[]`、`.get()` 的区别。
学完应能判断什么时候用哪一种。全部离线，不调用模型。
"""


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def main() -> None:
    """按用途、逐步演示、对比、坑与替代写法的顺序讲一次 setdefault。"""
    say("Day60 要把同一个题号的多轮结果收进一个列表，常见写法是：")
    say('    by_id.setdefault(row["id"], []).append(row)')
    say("本演示拆开看每一步，以及它和 []、get 的区别。")

    say("\n一、这是什么")
    say("dict.setdefault(键, 默认值) 的规则只有三条：")
    say("1. 键已经在字典里：返回它原来的值，不改动；")
    say("2. 键不在：把「默认值」放进去，再返回这个默认值；")
    say("3. 不管哪种情况，返回的都是「这个键对应的值」。")
    say("所以它常用于「分组」：先拿到该组的列表，再往列表里追加。")

    say("\n二、逐步演示：三条记录，按题号分组")
    rows = [
        {"id": "q01", "ttft_ms": 100},
        {"id": "q02", "ttft_ms": 200},
        {"id": "q01", "ttft_ms": 120},
    ]
    groups = {}
    say(f"初始 groups={groups}")

    say("\n第 1 条：id=q01，字典里还没有 q01")
    got = groups.setdefault("q01", [])
    say(f"setdefault 后 groups={groups}；返回={got}")
    got.append(rows[0])
    say(f"append 后 groups={groups}")

    say("\n第 2 条：id=q02，也没有")
    got = groups.setdefault("q02", [])
    got.append(rows[1])
    say(f"groups={groups}")

    say("\n第 3 条：id=q01，已经有了")
    got = groups.setdefault("q01", [])
    say(f"返回的是原来的列表吗？{got is groups['q01']}")
    got.append(rows[2])
    say(f"groups={groups}")
    say("q01 的列表没有被替换，第三个元素是追加进去的。")

    say("\n三、和 [] 直接取的区别")
    say('groups["q03"] 会直接报 KeyError：')
    try:
        groups["q03"]
    except KeyError as error:
        say(f"  实际异常={type(error).__name__}: {error}")

    say("\n四、和 .get() 的区别")
    default = []
    value = groups.get("q03", default)
    say(f'groups.get("q03", []) 返回={value}')
    say(f"但字典里有没有 q03？{'q03' in groups}（get 不会插入）")

    say("\n五、setdefault 的默认值会被创建，但不会覆盖已有值")
    before = groups["q01"]
    again = groups.setdefault("q01", ["这个新列表不会被使用"])
    say(f"已经有 q01 时再 setdefault，返回的是原列表吗？{again is before}")
    say(f"q01 现状={groups['q01']}")

    say("\n六、更短的替代：defaultdict(list)")
    from collections import defaultdict

    by_id = defaultdict(list)
    for row in rows:
        by_id[row["id"]].append(row)
    say(f"defaultdict 分组结果={dict(by_id)}")
    say("区别：defaultdict 在缺键时自动建列表，不需要写 setdefault；")
    say("但访问一个不存在的键也会悄悄建空列表，排查时要记得这一点。")

    say("\n七、注意什么")
    say("1. 默认值写 []，不要写同一个列表变量，否则各组会共用同一个列表。")
    say("2. setdefault 不会把已有值改成默认值；要覆盖得直接赋值。")
    say("3. 计数不要用 setdefault，用 counts[w] = counts.get(w, 0) + 1 更直接。")
    say("4. 键必须是可哈希的；题号字符串没问题。")

    say("\n下一步：用这个分组方式把 baseline / optimized 各自按 id 收好，")
    say("再对每组取中位数。")


if __name__ == "__main__":
    main()
