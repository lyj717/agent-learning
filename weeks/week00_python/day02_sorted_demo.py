"""sorted 的 key 和 lambda：一步步拆开看。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_sorted_demo.py
"""


def section(title: str) -> None:
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


# ============================================================
section("1. sorted 最基本的用法：给一串东西排队")
# ============================================================

print("数字：", sorted([3, 1, 4, 1, 5]))
print("字符串：", sorted(["banana", "apple", "cherry"]))
print("它返回一个新列表，原来的不动：")

original = [3, 1, 4]
result = sorted(original)
print(f"  原列表：{original}")
print(f"  排序结果：{result}")


# ============================================================
section("2. 麻烦来了：如果排的不是简单值呢")
# ============================================================

# 购物车：每项是「商品名 + 销量」，用元组表示
sales = [("键盘", 320), ("鼠标", 880), ("显示器", 150)]

print(f"原始数据：{sales}\n")
print("直接 sorted 会按什么排？")
print(f"  sorted(sales) → {sorted(sales)}")
print("  它是先比第一个元素（商品名），名字一样才比销量。")
print("  但我们想按销量排——这时候就需要 key。\n")

print("如果元素是字典，连排都排不了：")

records = [{"name": "键盘", "sold": 320}, {"name": "鼠标", "sold": 880}]
try:
    sorted(records)
except TypeError as error:
    print(f"  报错：{error}")
print("  因为 Python 不知道两个字典该怎么比大小。")


# ============================================================
section("3. key 的作用：给每个元素算一个「排序依据」")
# ============================================================

print("把上面的报错例子配上 key 就能排了：\n")

by_sales = sorted(records, key=lambda item: item["sold"])
for item in by_sales:
    print(f"  {item}")

print("\nkey 参数做的事，用大白话说就是：")
print("  「别拿整个元素去比，先按我说的规则算出一个数，用这个数比。」")
print()
print("所以 sorted 内部大概是这个流程：")

for item in records:
    print(f"    {item}  算出的依据是 {item['sold']}")

print()
print("  然后按依据从小到大排队 → 键盘(320) 在前，鼠标(880) 在后")

print("\n比喻：给每个学生发一个号码牌，然后按号码牌排队。")
print("学生本人没变，变的只是「按什么排」。")


# ============================================================
section("4. lambda 是什么：一个没有名字的小函数")
# ============================================================

print("先看普通函数怎么写：\n")


def get_sold(item) -> int:
    """取出一条记录的销量。"""
    return item["sold"]


print("  def get_sold(item):")
print("      return item['sold']")
print()
print("用 lambda 写，就是同一件事挤成一行：\n")

# 演示用：把 lambda 赋给变量（正式代码里更推荐直接写 def 函数）
get_sold_lambda = lambda item: item["sold"]

print("  lambda item: item['sold']")
print()
print("对照着看：")
print(f"  {'普通函数':<24}{'lambda':<24}")
print("  " + "-" * 48)
print(f"  {'def 函数名(参数):':<24}{'lambda 参数:':<24}")
print(f"  {'    return 表达式':<24}{'表达式':<24}")

print("\n两个函数效果完全一样：")
print(f"  get_sold(records[0])        → {get_sold(records[0])}")
print(f"  get_sold_lambda(records[0]) → {get_sold_lambda(records[0])}")

print("\nlambda 的特点：")
print("  1. 没有名字（所以叫「匿名函数」）")
print("  2. 只能写一个表达式，不能写多行")
print("  3. 没有 return，冒号后面的表达式结果就是返回值")


# ============================================================
section("5. 现在把 key 和 lambda 拼起来读")
# ============================================================

code = 'sorted(records, key=lambda item: item["sold"])'
print(code)
print()
print("  从左往右拆：")
print("  sorted(...)              要排序")
print("  records                  排的是这串东西")
print("  key=                     按某个依据排")
print("  lambda item:             对每个元素，把它叫做 item")
print('  item["sold"]             取出它的 sold 字段，当排序依据')
print()
print("整句读作：「把 records 排序，依据是每个元素的 sold 字段，从小到大」。")

print("\nlambda 后面的参数名随便起，叫什么都一样：")
by_sold = sorted(records, key=lambda item: item["sold"])
print(f"  三种写法排出来的结果完全一样：{by_sold}")
print("  key=lambda item: item['sold']")
print("  key=lambda x: x['sold']")
print("  key=lambda 记录: 记录['sold']")


# ============================================================
section("6. 回到你的场景：按词频排序")
# ============================================================

counts = {"the": 3, "and": 2, "cat": 1, "dog": 1}

print(f"统计结果是字典：{counts}\n")
print("字典不能直接排序，先转成「键值对」的列表：")

pairs = list(counts.items())
print(f"  counts.items() → {list(counts.items())}")
print(f"  list(...)      → {pairs}")

print("\n现在每个元素是一个元组：")
print(f"  {pairs[0]}   ← 第 0 个位置是词，第 1 个位置是次数")

print("\n要按次数排，所以取第 1 个位置：")
print("  sorted(pairs, key=lambda x: x[1])")
print(f"  → {sorted(pairs, key=lambda x: x[1])}")

print("\n要按词频从高到低，加 reverse=True：")
print("  sorted(pairs, key=lambda x: x[1], reverse=True)")
print(f"  → {sorted(pairs, key=lambda x: x[1], reverse=True)}")

print("\n只要前两个，最后加个切片：")
print("  sorted(pairs, key=lambda x: x[1], reverse=True)[:2]")
print(f"  → {sorted(pairs, key=lambda x: x[1], reverse=True)[:2]}")


# ============================================================
section("7. 重要：key 不一定非要 lambda")
# ============================================================

words = ["banana", "apple", "cherry", "fig"]

print("key 要的是一个「函数」。既然 len 本身就是函数，就可以直接传：\n")
print("  按长度排：sorted(words, key=len)")
print(f"  → {sorted(words, key=len)}")

print("\n  忽略大小写：sorted(['b', 'A', 'c'], key=str.lower)")
print(f"  → {sorted(['b', 'A', 'c'], key=str.lower)}     ← 大写 A 排在了 b 前面")

print("\n什么时候用现成函数、什么时候用 lambda：")
print("  能直接找到现成函数（len、str.lower）→ 直接传，更简洁")
print("  需要自己算一个值（取某个字段）  → 用 lambda")


# ============================================================
section("8. reverse=True：从大到小")
# ============================================================

print(f"  sorted([3, 1, 4])                  → {sorted([3, 1, 4])}")
print(f"  sorted([3, 1, 4], reverse=True)    → {sorted([3, 1, 4], reverse=True)}")

print("\nreverse 和 key 是两件独立的事：")
print("  key      决定「按什么排」")
print("  reverse  决定「正着排还是倒着排」")


# ============================================================
section("9. 进阶：按多个条件排（依据写成元组）")
# ============================================================

students = [
    ("小明", 90, 15),
    ("小红", 90, 12),
    ("小刚", 85, 14),
]

print(f"数据：{students}")
print("格式是（姓名, 分数, 年龄）\n")
print("先按分数从高到低，分数相同再按年龄从小到大：\n")

print("  sorted(students, key=lambda s: (-s[1], s[2]))")

ranked = sorted(students, key=lambda s: (-s[1], s[2]))
for name, score, age in ranked:
    print(f"  {name}  分数 {score}  年龄 {age}")

print("\n技巧在于：把依据写成一个元组 (-分数, 年龄)。")
print("元组比大小时先比第一项，相同时再比第二项。")
print("分数前加负号 = 分数越大排越前（因为负数越小）。")


# ============================================================
section("10. 三个最常见的错误")
# ============================================================

print("错误一：写成 key=x[1]（忘了 lambda）\n")
try:
    # pairs[0][1] 是一个整数（比如 3），不是函数
    sorted(pairs, key=pairs[0][1])
except TypeError as error:
    print(f"  报错：{error}")

print("\n  原因：key 要的是「一个函数」，不是「一个值」。")
print("  pairs[0][1] 会先被算成一个数字（比如 3），Python 拿到的是数字，")
print("  接着它想调用这个数字（3(...)），自然就报「不是可调用的对象」。")
print("  正确：key=lambda x: x[1]  ← 给它一个「怎么算」的说明书")

print("\n错误二：lambda 忘了写参数\n")
try:
    # 故意写一个没有参数的 lambda，用来看报错长什么样
    sorted(pairs, key=lambda: 1)
except TypeError as error:
    print(f"  报错：{error}")

print("\n  原因：sorted 会拿每个元素去调用这个函数，所以它必须能接收一个参数。")

print("\n错误三：依据的类型不一致")
mixed = [{"v": "abc"}, {"v": 123}]
try:
    sorted(mixed, key=lambda item: item["v"])
except TypeError as error:
    print(f"  报错：{error}")
print("  原因：字符串和数字不能比大小。排序依据的类型必须统一。")


section("一句话总结")
print("sorted(一串东西, key=排序依据函数, reverse=是否倒序)")
print()
print("关于 key 和 lambda 记住三句话：")
print("  1. key 要的是一个「函数」——说明「怎么算排序依据」")
print("  2. lambda x: x[1] 就是「给我 x，我返回它的第 1 个位置」")
print("  3. 能传现成函数（len、str.lower）就不用写 lambda")
