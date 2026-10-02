"""join 的用法：它和你直觉里以为的顺序是反的。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_join_demo.py
"""

import time


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


# ============================================================
section("1. 基本用法：分隔符在前，列表在后")
# ============================================================

words = ["苹果", "香蕉", "橘子"]

print(f"列表是：{words}\n")
print('  "\\n".join(words)  →  ' + repr("\n".join(words)))
print()
print("上面那行的真实输出是：")
print("\n".join(words))

print("\n换个分隔符试试：")
print('  "-".join(words)   →  ' + "-".join(words))
print('  ", ".join(words)  →  ' + ", ".join(words))
print('  "".join(words)    →  ' + "".join(words))

print("\n注意这个反直觉的地方：")
print('  正确："\\n".join(列表)      ← 分隔符在前面，点号后面接列表')
print('  错误：列表.join("\\n")      ← 列表没有 join 这个方法')

print("\n为什么会这样？因为 join 是「字符串的方法」。")
print("意思是：拿这个字符串当分隔符，把后面那串东西连起来。")
print("读作：「用换行把 words 连起来」。")


# ============================================================
section("2. 边界情况：空列表和单个元素")
# ============================================================

print('  "\\n".join([])          →  ' + repr("\n".join([])))
# 这两行就是要演示 join 在单元素和多元素时的行为，故意用 join 而不是写死字符串
print('  "\\n".join(["唯一"])    →  ' + repr("\n".join(["唯一"])))  # noqa: FLY002
print('  "\\n".join(["甲", "乙"]) →  ' + repr("\n".join(["甲", "乙"])))  # noqa: FLY002

print("\n规律：分隔符只出现在相邻两个元素「之间」。")
print("所以空列表得到空字符串，单个元素不会多出分隔符——")
print("这也意味着你不需要写「是不是最后一个」那种判断。")


# ============================================================
section("3. 最容易踩的坑：元素必须是字符串")
# ============================================================

print("如果列表里混了数字，会直接报错：\n")

try:
    ",".join(["第 1 名", 2, "第 3 名"])  # noqa: FLY002
except TypeError as error:
    print(f"  报错：{error}")

print("\n两种修法：")

numbers = [1, 2, 3]

# 修法一：先把每个元素转成字符串（推导式）
converted = [str(n) for n in numbers]
print('  用推导式：",".join([str(n) for n in numbers])  →  ' + ",".join(converted))

# 修法二：用 map，把转换函数套到每个元素上
print(
    '  用 map：  ",".join(map(str, numbers))          →  ' + ",".join(map(str, numbers))
)

print("\n两种都行。map 更短，推导式更好读——团队里两种都常见。")


# ============================================================
section("4. join 和 split 是一对反向操作")
# ============================================================

line = "小明,小红,小刚"

split_result = line.split(",")
join_result = ",".join(split_result)

print(f"  原始字符串：{line!r}")
print(f'  split(",") 之后：{split_result}')
print(f"  join 回去：      {join_result!r}")
print(f"  是不是等于原串：{join_result == line}")

print("\n这两个方法你在数据处理里会反复来回用：")
print("  读文件 → split 拆成一行行、一段段")
print("  写文件 → join 拼回字符串")


# ============================================================
section("5. 为什么不推荐用 += 拼字符串")
# ============================================================

pieces = [str(i) for i in range(20000)]

# 写法一：循环里 +=
# perf_counter()：高精度计时器，专门用来量「这段代码跑了多久」
start = time.perf_counter()
result_a = ""
for piece in pieces:
    result_a += piece
time_a = time.perf_counter() - start

# 写法二：join
start = time.perf_counter()
result_b = "".join(pieces)
time_b = time.perf_counter() - start

print(f"  循环里 += ：{time_a * 1000:8.2f} 毫秒")
print(f"  用 join   ：{time_b * 1000:8.2f} 毫秒")
print(f"  join 快 {time_a / time_b:.0f} 倍左右，结果相同：{result_a == result_b}")

print("\n原因：字符串在 Python 里是不可变的，")
print("每次 += 都要造一个全新的字符串并把旧内容复制过去。")
print("循环 2 万次，就复制了 2 万次。而 join 一次算好总长度，只造一个。")

print("\n实用建议：几行文字的拼接用 += 完全没问题（可读性优先），")
print("但一旦是在循环里、或者数量不确定，就用 join。")


# ============================================================
section("6. 你会在哪些地方用到它")
# ============================================================

print("1. 把多条消息拼成一段文本（就是你现在这道题）")
print('     "\\n".join(内容列表)')
print()
print("2. 生成 CSV 的一行")
print('     ",".join(["张三", "28", "北京"])')
print()
print("3. 打日志时把几个值接起来")
print('     " | ".join(["步骤 3", "耗时 1.2s", "成功"])')
print()
print("4. 生成提示词模板时拼接多段说明")
print('     "\\n\\n".join([角色说明, 工具说明, 输出要求])')


section("一句话总结")
print("分隔符.join(一串字符串)  →  用分隔符把这串东西连成一个字符串")
print()
print("记住三件事就够用了：")
print("  1. 分隔符写前面")
print("  2. 列表里必须全是字符串（有数字就先 str() 转）")
print("  3. 循环里拼字符串优先用 join，别用 +=")
