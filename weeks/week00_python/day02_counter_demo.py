"""`counts` 到底是什么：变量名、字典计数套路、以及三个容易混淆的东西。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_counter_demo.py
"""

from collections import Counter


def section(title: str) -> None:
    print(f"\n{'=' * 58}\n{title}\n{'=' * 58}")


# ============================================================
section("1. counts 只是个变量名——换个名字照样工作")
# ============================================================

words = ["猫", "狗", "猫", "鸟", "猫", "狗"]

# 名字叫 counts
counts = {}
for word in words:
    counts[word] = counts.get(word, 0) + 1
print(f"  叫 counts：{counts}")

# 名字叫 计数器 也一样
计数器 = {}
for word in words:
    计数器[word] = 计数器.get(word, 0) + 1
print(f"  叫计数器：{计数器}")

# 名字叫 tally 也一样
tally = {}
for word in words:
    tally[word] = tally.get(word, 0) + 1
print(f"  叫 tally： {tally}")

print("\n三个结果完全相同，因为 counts 不是语言的东西，只是我给变量起的名字。")
print("所以我写 counts.get(...)，你写 counter.get(...) 或者 tally.get(...) 都对。")


# ============================================================
section("2. 真正在用的两样东西：.get() 和 字典[键] = 值")
# ============================================================

words = ["猫", "狗", "猫"]
counter = {}

print("把每一轮的中间状态打出来，就看清套路了：\n")

for index, word in enumerate(words, start=1):
    # 这两行就是全部核心
    previous = counter.get(word, 0)  # ① 取旧值，没有就当 0
    counter[word] = previous + 1  # ② 把「旧值 + 1」写回去

    # 只有第一次见到这个词时，默认值 0 才会起作用
    status = "第一次见到，用上默认值 0" if previous == 0 else "之前见过，返回已有的计数"
    print(f"  第 {index} 轮：词 = {word!r}")
    print(f"      .get({word!r}, 0) → {previous}    （{status}）")
    print(f"      写入之后 → {counter}")

print("\n这个「取出来、加一、写回去」的动作，就是字典计数的全部原理。")


# ============================================================
section("3. 为什么必须写 .get(word, 0)")
# ============================================================

print("如果写成 counter[word] + 1，第一次遇到新词时会怎样？\n")

bad = {}
try:
    bad["猫"] = bad["猫"] + 1
except KeyError as error:
    print(f"  报错：KeyError: {error}")

print("\n原因：字典里还没有这个键，用 [] 直接取就等于「向不存在的抽屉要东西」，")
print("Python 只能报错。而 .get(键, 默认值) 的意思是「没有的话就给我这个默认值」。")

print("\n两种写法的区别：")
print("  counter[word]          键不存在 → 报 KeyError")
print("  counter.get(word, 0)   键不存在 → 安静地返回 0")


# ============================================================
section("4. 你可能找到的 .count() 是另一回事")
# ============================================================

text = "the cat and the dog and the bird"

print("Python 确实有 .count() 这个方法，但它的作用是「数某样东西出现了几次」：\n")

print(f'  "the cat and the dog".count("the")  →  {text.count("the")}')
print(f"  [1, 2, 2, 3].count(2)                →  {[1, 2, 2, 3].count(2)}")
print(f"  [1, 2, 2, 3].count(99)               →  {[1, 2, 2, 3].count(99)}")

print("\n它只能回答「某一样东西有几个」，没法一次告诉你所有东西各有多少个。")
print("想统计全部词频，你可以对每个词都调一次 .count()：")

unique_words = set(text.split())
for word in sorted(unique_words):
    print(f'    text.split().count("{word}") = {text.split().count(word)}')

print("\n结果是对的，但代价很大：每个词都要把整个列表扫一遍。")
print("如果文本里有 1000 个不同的词、10000 个词次，就要扫 1000 次 × 10000 项。")
print("而字典计数只需要扫一遍就能统计出全部词频。")


# ============================================================
section("5. 确实有一个现成工具：collections.Counter")
# ============================================================

words = text.split()

print("Python 标准库里有个专门做这件事的类：\n")

print("  from collections import Counter")
print("  counts = Counter(words)")
print()

counts = Counter(words)
print(f"  Counter(words)          →  {dict(counts)}")
print(f"  counts.most_common(2)   →  {counts.most_common(2)}")
print(f"  counts['the']           →  {counts['the']}")
print(f"  counts['不存在的词']     →  {counts['不存在的词']}   ← 注意：不报错，返回 0")

print("\n它把「建字典 + 遍历 + 计数」三步合成了一步。")
print("你清单里的 Day 2 练习特意写了「Counter 可以用，但先用字典手写一遍」——")
print("因为手写一遍你才知道它内部在干什么，以后出了诡异问题才排查得动。")


# ============================================================
section("6. 三者对照")
# ============================================================

print(f"{'写法':<34}{'能做什么':<24}{'扫几遍':<8}")
print("-" * 70)
print(f"{'.count(某样东西)':<34}{'数一个东西出现几次':<24}{'每个词一遍':<8}")
print(f"{'手写字典计数':<34}{'一次统计全部词频':<24}{'一遍':<8}")
print(f"{'Counter':<34}{'同上，代码更短':<24}{'一遍':<8}")


section("小结")
print("1. counts 是变量名，不是 Python 的方法——查不到是正常的")
print("2. 核心是字典的 .get(键, 默认值) 和 字典[键] = 值 这两样")
print("3. .count() 是「数一个东西几次」，做不了词频统计")
print("4. Counter 是现成的，但先把字典版手写一遍")
print()
print("以后再遇到不认识的名字，先判断它属于哪一类：")
print("  语言/库提供的（能查文档、能 import）")
print("  别人或自己起的变量名、函数名（查不到，要看上下文）")
