"""为什么一个函数里会有两个 return？

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_return_demo.py
"""


def section(title: str) -> None:
    print(f"\n{'=' * 52}\n{title}\n{'=' * 52}")


# ============================================================
section("1. 带执行过程的版本：看它在哪一行停下")
# ============================================================


def find_pair_verbose(target: int) -> tuple[int, int] | None:
    """找出两个数相乘等于 target 的组合，找不到返回 None。"""
    print(f"  进入函数，要找乘积为 {target} 的组合")

    for i in range(3):
        for j in range(3):
            print(f"    检查 i={i}, j={j}，乘积是 {i * j}")
            if i * j == target:
                print("    ┌── 命中！执行第一个 return，函数立即结束")
                return i, j  # ← 第一个 return：找到了就交出去

    print("  └── 两个循环都跑完了，一次都没命中，走到最后一行")
    return None  # ← 第二个 return：没找到，明确交回「没有」


print("情况一：找得到目标")
result_one = find_pair_verbose(4)
print(f"  函数返回：{result_one}\n")

print("情况二：找不到目标")
result_two = find_pair_verbose(7)
print(f"  函数返回：{result_two}")

print("\n关键点：每次调用只会执行其中一个 return。")
print("return 一旦执行，函数立刻结束，后面的代码根本不会跑。")


# ============================================================
section("2. 为什么第一个 return 能跳出两层循环")
# ============================================================

print("如果不用函数、不用 return，你得像上一课那样加标志变量：")
print()
print("  found = False")
print("  for i in range(3):")
print("      for j in range(3):")
print("          if i * j == 4:")
print("              found = True")
print("              break          # 只跳出内层")
print("      if found:")
print("          break              # 还得再写一次才跳出外层")
print()
print("用 return 就不需要标志变量，因为它直接结束整个函数——")
print("两层循环一起退出。这也是为什么它比 break 更干净。")


# ============================================================
section("3. 第二个 return 能不能不写？")
# ============================================================


def without_second_return(target: int):
    for i in range(3):
        for j in range(3):
            if i * j == target:
                return i, j
    # 这里什么都没写


print("把第二个 return 删掉，看会发生什么：")
print(f"  能找到时：{without_second_return(4)}")
print(f"  找不到时：{without_second_return(7)}")

print("\n结论：找不到时它照样返回 None。")
print("因为 Python 的函数如果一路执行到底，就默认返回 None。")

print("\n那为什么还要写出来？")
print("  1. 读代码的人一眼知道「找不到」是预期情况，不是忘了处理")
print("  2. 类型注解里的 | None 就是在说这件事，写出来才和注解对得上")
print("  3. 你以后改成返回别的默认值时，有地方可改")
print("\n一句话：不写也对，写出来是给人看的。")


# ============================================================
section("4. 和 C 的写法对比")
# ============================================================

print("C 里常见做法是返回一个特殊值当「没找到」：")
print()
print("  int find(int target, int *out_i, int *out_j) {")
print("      for (i = 0; i < 3; i++)")
print("          for (j = 0; j < 3; j++)")
print("              if (i * j == target) { *out_i = i; *out_j = j; return 1; }")
print("      return 0;   // 0 表示失败")
print("  }")
print()
print("Py 里返回两个值很省事，不需要指针当输出参数：")
print("  return i, j     ← 直接返回一个元组")
print("  return None     ← 用 None 表示「什么都没有」")


# ============================================================
section("5. 「找不到」是异常情况时，另一种写法")
# ============================================================


def find_pair_strict(target: int) -> tuple[int, int]:
    """找不到就报错，而不是返回 None。"""
    for i in range(3):
        for j in range(3):
            if i * j == target:
                return i, j
    raise ValueError(f"在范围内找不到乘积为 {target} 的组合")


print("能找到时正常返回：")
print(f"  find_pair_strict(4) = {find_pair_strict(4)}")

print("\n找不到时抛异常：")
try:
    find_pair_strict(7)
except ValueError as error:
    print(f"  捕获到异常：{error}")

print("\n两种风格怎么选：")
print("  返回 None —— 「没找到」是正常结果，调用方该自己处理")
print("  抛异常   —— 「没找到」说明前提被破坏了，不该继续往下走")


# ============================================================
section("6. 类型注解和 return 是对应的")
# ============================================================

print("回头看那个注解：")
print("  def find_pair() -> tuple[int, int] | None:")
print()
print("  前半段 tuple[int, int]  ← 对应第一个 return：返回两个整数")
print("  后半段 | None           ← 对应第二个 return：可能返回 None")
print()
print("`|` 读作「或者」，所以整句的意思是：")
print("  「这个函数要么返回两个整数，要么返回 None，不会有第三种结果」")
print()
print("这就是类型注解的价值：调用方不用读函数体，")
print("光看签名就知道要处理两种情况。")


section("总结")
print("1. 一个函数可以有任意多个 return，一次调用只执行其中一个")
print("2. return 一旦执行，函数立即结束，它是唯一能跳出多层循环的干净办法")
print("3. 末尾那个 return None 可以不写，但写出来能说明「找不到」是预期情况")
print("4. 多个 return 和类型注解里的 | None 是一一对应的")
