"""Python 的 for 循环：它和 C 的 for 根本不是同一个东西。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_for_loop_demo.py
"""

import time


def section(title: str) -> None:
    print(f"\n{'=' * 52}\n{title}\n{'=' * 52}")


# ============================================================
section("1. 最核心的区别：C 数下标，Python 取元素")
# ============================================================

# C 的写法是这样的（这里只是注释，不是可运行代码）：
#   int arr[] = {10, 20, 30};
#   for (int i = 0; i < 3; i++) {
#       printf("%d\n", arr[i]);
#   }
#
# 注意三个部分：初始化 i、判断条件、循环后自增。
# Python 里没有这三段式，写法变成这样：

numbers = [10, 20, 30]

for number in numbers:
    print(f"  拿到元素：{number}")

print("\n读法：『对 numbers 里的每一个 number，做下面这件事』。")
print("整个过程里没有计数器，你拿到的是元素本身，不是下标。")


# ============================================================
section("2. 想要计数器？用 range()")
# ============================================================

# range 才是 C 里那个三段式的对应物
print("range(3)        ->", list(range(3)))
print("range(1, 4)     ->", list(range(1, 4)))
print("range(0, 10, 3) ->", list(range(0, 10, 3)))
print("range(5, 0, -1) ->", list(range(5, 0, -1)))

print("\n对应关系：")
print("  C:      for (int i = 0; i < 3; i++)   ← 上界是 3，循环里 i 取到 2")
print("  Python: for i in range(3):            ← 上界写 3，i 同样取到 2")
print("  两者一致：上界都不包含在内（左闭右开）")

print("\n用 range 加下标访问的写法（能用，但不 Python 化）：")
for i in range(len(numbers)):
    print(f"  下标 {i} 的值是 {numbers[i]}")


# ============================================================
section("3. 能遍历的东西远不止列表")
# ============================================================

print("字符串（逐个字符）：")
for char in "agent":
    print(f"  {char}")

print("\n元组：")
for item in (1, 2, 3):
    print(f"  {item}")

print("\n集合（顺序不保证）：")
# 这里故意用集合：想让你看到集合的遍历顺序和书写顺序不一致
for item in {3, 1, 2}:  # noqa: PLC0208
    print(f"  {item}")

print("\n生成器（边算边给，不占内存）：")
for value in (x * x for x in range(4)):
    print(f"  平方：{value}")

# 真实场景是 for line in open("data.txt", encoding="utf-8"):，
# 逐行读不占内存。这里用带换行符的列表示意：
print("\n模拟文件逐行读取（真实写法是 for line in open(...)）：")
for line in ["第一行\n", "第二行\n"]:
    print(f"  {line.strip()}", end="  ← strip() 去掉末尾换行符\n")

print("\n只要次数，不关心值，用下划线当变量名：")
for _ in range(3):
    print("  重复一次")


# ============================================================
section("4. 需要下标时：enumerate")
# ============================================================

fruits = ["苹果", "香蕉", "橘子"]

print("笨办法（像 C 一样自己数）：")
for i in range(len(fruits)):
    print(f"  {i}: {fruits[i]}")

print("\nPython 的做法，一次拿到下标和元素：")
for index, fruit in enumerate(fruits):
    print(f"  {index}: {fruit}")

print("\n想从 1 开始数（给人看的序号）：")
for index, fruit in enumerate(fruits, start=1):
    print(f"  第 {index} 个是 {fruit}")

print("\n结论：只要需要下标，就用 enumerate，不要自己维护计数器。")


# ============================================================
section("5. 同时遍历两个序列：zip")
# ============================================================

names = ["小明", "小红", "小刚"]
scores = [95, 88, 72]

print("并排遍历，像拉链一样把两边咬合：")
for name, score in zip(names, scores):
    print(f"  {name}: {score}")

print("\n长度不一样时，以短的为准，多余的直接忽略：")
for name, score in zip(["甲", "乙", "丙"], [1, 2]):
    print(f"  {name}: {score}")


# ============================================================
section("6. 遍历字典的三种方式")
# ============================================================

user = {"name": "小明", "age": 28, "city": "北京"}

print("只要键（等价于遍历字典本身）：")
for key in user:
    print(f"  {key}")

print("\n只要值：")
for value in user.values():
    print(f"  {value}")

print("\n键和值都要（最常用）：")
for key, value in user.items():
    print(f"  {key} = {value}")

print("\n想按顺序输出，先排序：")
for key in sorted(user):
    print(f"  {key}: {user[key]}")


# ============================================================
section("7. break、continue，还有 C 里没有的 for-else")
# ============================================================

print("break：找到就停，别继续找")
for number in [3, 7, 12, 15, 20]:
    if number % 2 == 0:
        print(f"  第一个偶数：{number}")
        break

print("\ncontinue：这个跳过，继续下一个")
for number in range(6):
    if number % 2 == 0:
        continue
    print(f"  奇数：{number}")

print("\nfor-else：循环正常跑完才执行 else，被 break 中断就不执行。")
print("这个特性 C 里没有，用来表达『找了一圈没找到』特别自然：")

for number in [3, 7, 11]:
    if number % 2 == 0:
        print(f"  找到偶数 {number}")
        break
else:
    print("  全部是奇数，一个偶数都没有")


# ============================================================
section("8. 坑一：循环里不要修改正在遍历的容器")
# ============================================================

numbers = [2, 4, 6, 8]
print(f"目标：把 {numbers} 里的偶数全部删掉（预期结果应该是空列表）\n")

print("错误写法——边遍历边删：")
broken = numbers.copy()
for number in broken:
    print(f"  当前处理 {number}，列表现在是 {broken}")
    if number % 2 == 0:
        broken.remove(number)
print(f"  结果 {broken}  ← 错了！4 和 8 被跳过了")
print("  原因：删掉 2 之后，后面的元素整体前移一位，")
print("        而遍历位置已经往后走了，于是 4 被跳过。\n")

print("正确做法一：遍历副本，改原列表")
fixed_one = numbers.copy()
for number in numbers.copy():
    if number % 2 == 0:
        fixed_one.remove(number)
print(f"  结果 {fixed_one}")

print("\n正确做法二（推荐）：用推导式生成新列表")
fixed_two = [n for n in numbers if n % 2 != 0]
print(f"  结果 {fixed_two}")

print("\n正确做法三：从后往前删（不会错位，可读性差，一般不用）")
fixed_three = numbers.copy()
for i in range(len(fixed_three) - 1, -1, -1):
    if fixed_three[i] % 2 == 0:
        del fixed_three[i]
print(f"  结果 {fixed_three}")


# ============================================================
section("9. 坑二：循环变量出了循环还在（没有块级作用域）")
# ============================================================

for i in range(3):
    pass

print(f"循环结束后 i 还在：i = {i}")
print("C 里循环一结束 i 就没了（C99 之前），Python 没有块级作用域。")
print("所以别到处用 i、j、k 这种短名字，容易和外面的变量撞上。")


# ============================================================
section("10. 坑三：改循环变量不会改到容器里的值")
# ============================================================

numbers = [1, 2, 3]

print("这样写以为能把每个元素乘 2，其实没用：")
for number in numbers:
    number = number * 2
print(f"  {numbers}  ← 列表没变，因为 number 只是每次拿到的一个副本")

print("\n正确做法一：按下标改")
for i in range(len(numbers)):
    numbers[i] = numbers[i] * 2
print(f"  {numbers}  ← 这次真的改了原列表")

print("\n正确做法二（推荐）：生成新列表")
# 为了看清楚，这里用原始数据而不是上面已经被改过的列表
doubled = [n * 2 for n in [1, 2, 3]]
print(f"  {doubled}")


# ============================================================
section("11. 推导式：把循环压成一行")
# ============================================================

numbers = [1, 2, 3, 4, 5, 6]

print("[n * 2 for n in numbers]            ->", [n * 2 for n in numbers])
print("[n for n in numbers if n % 2 == 0]  ->", [n for n in numbers if n % 2 == 0])
print("{n: n * n for n in range(4)}         ->", {n: n * n for n in range(4)})

print("\n什么时候不用推导式：")
print("  1. 循环体里做的事超过两行")
print("  2. 需要 break 或 continue（推导式里不支持）")
print("  3. 嵌套超过两层")
print("这些情况老老实实写普通 for 循环，可读性更重要。")


# ============================================================
section("12. 嵌套循环与如何跳出外层")
# ============================================================

print("嵌套循环（找第一个满足条件的组合）：")
found = False
for i in range(3):
    for j in range(3):
        if i * j == 4:
            print(f"  找到 i={i}, j={j}")
            found = True
            break
    if found:
        break

print("\nPython 没有 goto，也没有给循环贴标签。")
print("要跳出多层，最清楚的做法是写成一个函数，直接 return：")


def find_pair() -> tuple[int, int] | None:
    for i in range(3):
        for j in range(3):
            if i * j == 4:
                return i, j
    return None


print(f"  函数版的结果：{find_pair()}")
print("提示：当你需要『跳出两层循环』时，往往说明这段逻辑该抽成函数了。")


# ============================================================
section("13. 为什么 Python 的 for 能遍历这么多东西")
# ============================================================

print("因为 for 不关心对象是什么，只要求它能被『迭代』。")
print("只要对象实现了迭代协议，for 就能遍历它：文件、数据库游标、")
print("网络响应流、生成器……这就是它比 C 的 for 表达力强的原因。\n")


class Countdown:
    """一个可以倒数的自定义对象。"""

    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            # 抛这个异常，for 就知道该停了
            raise StopIteration
        self.current -= 1
        return self.current + 1


for value in Countdown(3):
    print(f"  倒数：{value}")

print("\nfor 底层做的事：先调用 __iter__ 拿到迭代器，")
print("然后不断调用 __next__ 取值，直到它抛出 StopIteration 为止。")
print("你不需要手写这些，但知道这层机制，看报错时会清楚很多。")


# ============================================================
section("14. 性能：不同写法差多少")
# ============================================================

SIZE = 1_000_000

# perf_counter()：高精度计时器，专门用来量「这段代码跑了多久」
start = time.perf_counter()
total = 0
for i in range(SIZE):
    total += i
loop_time = time.perf_counter() - start

start = time.perf_counter()
total_builtin = sum(range(SIZE))
builtin_time = time.perf_counter() - start

print(f"普通 for 循环：{loop_time * 1000:.1f} 毫秒")
print(f"内置函数 sum：{builtin_time * 1000:.1f} 毫秒")
print(f"内置函数快 {loop_time / builtin_time:.1f} 倍，结果都是 {total_builtin}")

print("\n结论：能直接用内置函数（sum、max、any、min）就别自己写循环。")
print("但注意顺序：先把逻辑写对，再考虑性能。过早优化是浪费时间。")


section("总结：从 C 切换到 Python 要改的四个习惯")
print("1. 别写 for (i=0; i<n; i++)，直接遍历元素")
print("2. 需要序号就用 enumerate，需要配对就用 zip")
print("3. 循环变量出了循环还在，别用短名字到处飞")
print("4. 别在循环里改正在遍历的容器，用推导式生成新列表")
