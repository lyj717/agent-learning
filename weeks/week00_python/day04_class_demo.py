"""用一个「购物车体检」的例子讲清类：为什么需要它、怎么写、什么时候不该用。

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_class_demo.py
"""


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


# ============================================================
section("1. 先用函数写：能跑，但有个别扭的地方")
# ============================================================

# 购物车就是一个字典：商品名 -> (单价, 数量)
cart = {"键盘": (399.0, 1), "鼠标": (129.0, 2), "显示器": (1299.0, 1)}


def check_budget(c: dict, budget: float) -> bool:
    total = sum(price * count for price, count in c.values())
    ok = total <= budget
    print(f"  [{'v' if ok else 'x'}] 总金额 {total:.2f}，预算 {budget:.2f}")
    return ok


def check_item_count(c: dict, limit: int) -> bool:
    kinds = len(c)
    ok = kinds <= limit
    print(f"  [{'v' if ok else 'x'}] 商品种类 {kinds}，上限 {limit}")
    return ok


print("直接调用：")
check_budget(cart, 2000)
check_item_count(cart, 5)

print("\n问题在哪？")
print("  1. 每加一个检查，main 里就要多写一行调用")
print("  2. 每个函数的参数不一样，没法统一循环处理")
print("  3. 检查项的「名字」和「阈值」这些信息，只能散落在调用处")


# ============================================================
section("2. 写一个最小的类：把数据和动作绑在一起")
# ============================================================


class BudgetCheck:
    """检查总金额有没有超预算。"""

    # 类属性：所有实例共享
    name = "预算检查"

    def __init__(self, budget: float) -> None:
        """创建实例时执行一次，用来记录这个实例自己的数据。"""
        self.budget = budget  # 实例属性：每个实例各有一份

    def run(self, cart: dict) -> bool:
        """实例方法：第一个参数永远是 self。"""
        total = sum(price * count for price, count in cart.values())
        ok = total <= self.budget
        print(f"  [{'v' if ok else 'x'}] 总金额 {total:.2f}，预算 {self.budget:.2f}")
        return ok


print("创建实例，并调用它的方法：")
budget_check = BudgetCheck(budget=2000)
print(f"  实例的名字属性：{budget_check.name}")
print(f"  实例自己的阈值：{budget_check.budget}")
budget_check.run(cart)

print("\n拆解一下发生了什么：")
print("  BudgetCheck(2000)    → 调用 __init__，把 2000 存进 self.budget")
print("  budget_check.run()   → 调用 run，self 自动指向这个实例")
print("  self.budget          → 从这个实例身上取 budget")


# ============================================================
section("3. self 到底是什么：两个实例互不影响")
# ============================================================

loose = BudgetCheck(budget=1000)
wide = BudgetCheck(budget=5000)

print(f"loose.budget = {loose.budget}，wide.budget = {wide.budget}")
print("同一个类造出来的两个实例，各存各的数据：\n")

print("宽松预算：")
wide.run(cart)
print("紧张预算：")
loose.run(cart)

print("\n把类想象成一个「模具」，实例是模具倒出来的一个个零件。")
print("模具只有一个，零件可以有很多个，各自装着不同的数据。")


# ============================================================
section("4. 关键收益：统一接口，一个循环处理所有检查项")
# ============================================================


class ItemCountCheck:
    """检查商品种类有没有超上限。"""

    name = "种类检查"

    def __init__(self, limit: int) -> None:
        self.limit = limit

    def run(self, cart: dict) -> bool:
        kinds = len(cart)
        ok = kinds <= self.limit
        print(f"  [{'v' if ok else 'x'}] 商品种类 {kinds}，上限 {self.limit}")
        return ok


class ExpensiveItemCheck:
    """检查有没有单价过高的商品。"""

    name = "高价商品检查"

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def run(self, cart: dict) -> bool:
        expensive = [
            name for name, (price, _) in cart.items() if price > self.threshold
        ]
        ok = not expensive
        detail = "无" if ok else "、".join(expensive)
        print(
            f"  [{'v' if ok else 'x'}] 单价超过 {self.threshold:.0f} 的商品：{detail}"
        )
        return ok


# 把三个检查项装进一个列表——注意它们类型不同，但都有 name 和 run
checks = [
    BudgetCheck(budget=2000),
    ItemCountCheck(limit=5),
    ExpensiveItemCheck(threshold=1000),
]

print("main 里只需要一个循环，不用关心具体是哪种检查：")
print()

results = {}
for check in checks:
    print(f"{check.name}：")
    results[check.name] = check.run(cart)

print()
print(f"汇总结果：{results}")
print(f"是否全部通过：{all(results.values())}")

print("\n这就是这次改造的全部价值：")
print("  加一个检查项 → 往列表里加一个元素，main 一个字都不用改")
print("  删一个检查项 → 从列表里删掉")
print("  调整顺序     → 改列表顺序")

print("\n这种「不同的类，提供同名方法，被统一循环调用」的做法，")
print("在面向对象里叫「多态」。名字听着玄，做的事情就是这么朴素。")


# ============================================================
section("5. 组合：一个检查项依赖另一个的结果")
# ============================================================


class AlertCheck:
    """根据前面的检查结果决定要不要报警。

    这叫「组合」：把别的检查项对象当作参数传进来，用它提供的接口。
    """

    name = "报警检查"

    def __init__(self, *upstream) -> None:
        self.upstream = upstream  # 记住它依赖的那几个检查项

    def run(self, cart: dict) -> bool:
        failed = [c.name for c in self.upstream if not c.run(cart)]
        ok = not failed
        detail = "全部正常" if ok else f"有问题的项：{'、'.join(failed)}"
        print(f"  [{'v' if ok else 'x'}] {detail}")
        return ok


print("把这个检查项放在最后，它自己会去调用前面几个：\n")
budget = BudgetCheck(budget=2000)
count = ItemCountCheck(limit=2)  # 故意设成一个会失败的阈值
alert = AlertCheck(budget, count)

alert.run(cart)

print("\n注意 AlertCheck 不需要知道 BudgetCheck 内部怎么算的，")
print("只要知道「它有个 run 方法、有个 name 属性」就够了。这叫「面向接口编程」。")


# ============================================================
section("6. 什么时候不该用类")
# ============================================================

print("说实话：如果只有三四个检查项，而且不会经常增删，")
print("用普通函数其实更简单——直接写三行调用就行。")
print()
print("下面这些情况才值得改成类：")
print("  1. 检查项会不断增删，或者由不同的人各自添加")
print("  2. 需要统一循环处理（比如统一计时、统一打印、统一记日志）")
print("  3. 每个检查项需要记住自己的配置（阈值、路径、开关）")
print("  4. 需要让检查项之间互相组合（像上面的报警检查）")
print()
print("反过来说：为了「显得高级」而把简单逻辑拆成一堆类，")
print("是新手常见的一种过度设计。判断标准永远是「它有没有让代码更好读、更好改」。")


section("总结")
print("1. 类 = 模具；实例 = 用模具造出来的零件，各自装着自己的数据")
print("2. __init__ 在创建实例时执行，用来存数据")
print("3. 方法的第一个参数必须是 self，调用时不用手动传")
print("4. 类属性和实例属性：前者共享，后者各有一份")
print("5. 多个类提供同名方法，就能被统一循环调用——这是本次改造的核心")
print("6. 简单场景别硬套类，够用就好")
