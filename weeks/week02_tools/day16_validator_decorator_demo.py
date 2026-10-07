"""Day 16 加餐：`@field_validator(...)` 加 `@classmethod` 到底是干嘛的。

这两行是整个 Pydantic 里最容易「照抄但不懂」的地方，所以单独做个实验给你：
每一节都改一个地方、跑一次、看结果怎么变。

跑法（完全离线，不花钱）：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_validator_decorator_demo.py
"""

import warnings

from pydantic import BaseModel, ValidationError, field_validator


def section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# ============================================================
section("实验 1：不加装饰器会怎样")
# ============================================================


class NoDecorator(BaseModel):
    name: str | None = None

    def blank_to_none(cls, value):  # pylint: disable=no-self-argument
        """一个普普通通的函数，Pydantic 根本不知道它的存在。"""
        print("      （这行永远不会被打印——没人调用它）")
        return None if value == "" else value


print("  传空串进去：")
print(f"    结果：{NoDecorator(name='').model_dump()}")
print("  空串原样留在字段里了。函数写在那儿，但没人叫它——")
print("  装饰器就是「登记」：告诉 Pydantic「这个函数请在校验时调用」。")


# ============================================================
section("实验 2：只加 @field_validator，忘了 @classmethod")
# ============================================================

# catch_warnings(record=True)：把这段里产生的警告**抓下来**，
# 不然它只会往屏幕上一闪，你还得自己猜到底有没有。
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")  # 同类警告不合并，有几条记几条

    class OnlyValidator(BaseModel):
        name: str | None = None

        @field_validator("name", mode="before")
        def blank_to_none(cls, value):
            return None if value == "" else value

    result = OnlyValidator(name="").model_dump()

print(f"  能跑起来，结果也对：{result}")
print(f"  警告条数：{len(caught)}")
for item in caught:
    print(f"    {item.category.__name__}: {item.message}")
print(
    "\n  （真实的实验结论：当前这个 Pydantic 版本**不警告**，不写也能跑。）"
    "\n  那为什么还要写？上面这段的 catch_warnings 就是答案的一半："
    "\n  「能跑」和「写法稳定」是两件事——不同版本的行为不一定一样，"
    "\n  而 @classmethod 是所有示例里的标准写法，写上零代价，还把意图说清楚了。"
)

print("\n  另一半答案是「cls 到底是什么」，让它自己说：")


class ShowCls(BaseModel):
    name: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def peek(cls, value):
        print(f"      cls = {cls}")
        print(f"      它是个类吗：{isinstance(cls, type)}")
        print(f"      它和 ShowCls 是同一个东西吗：{cls is ShowCls}")
        return value


ShowCls(name="刘小明")
print(
    "  看出来了吧：校验发生在**实例还没造出来**的时候，"
    "\n  所以第一个参数只能是类，不可能是 self。这就是 @classmethod 的原因。"
)


# ============================================================
section("实验 3：mode='before' 和默认 mode 的差别")
# ============================================================


def make_model(mode: str, calls: list):
    """造两个只差一个 mode 的模型；calls 用来记录校验器被调用了几次。"""

    class BlankToNone(BaseModel):
        name: str | None = None

        @field_validator("name", mode=mode)
        @classmethod
        def blank_to_none(cls, value):
            calls.append(value)
            return None if isinstance(value, str) and value.strip() == "" else value

    return BlankToNone


for mode in ("before", "after"):
    print(f"\n  ── mode='{mode}' ──")
    calls: list = []
    model = make_model(mode, calls)
    for label, value in [("'  '", "  "), ("''", ""), ("数字 123", 123)]:
        try:
            print(f"    传 {label:<10} -> 通过 {model(name=value).model_dump()}")
        except ValidationError as error:
            print(f"    传 {label:<10} -> 失败：{error.errors()[0]['msg']}")
    print(f"    校验器一共被调用了 {len(calls)} 次，收到过：{calls}")

print(
    """
  差别在第三行：
    · before 模式下，数字 123 也会先送进你的函数（调用 3 次），
      你可以决定「把它修好」还是「直接报错」；
    · after 模式下，123 在类型检查那一关就被打回了，你的函数轮不到执行（调用 2 次）。
  所以要「先修再查」的东西，必须写在 before 里。"""
)


# ============================================================
section("实验 4：装饰器是倒着套上去的（理解 @ 的正确姿势）")
# ============================================================

print(
    "  你写的是这两行：\n"
    "\n"
    "      @field_validator('phone')\n"
    "      @classmethod\n"
    "      def phone_must_be_11_digits(cls, value): ...\n"
    "\n"
    "  它等价于下面这三行（装饰器**从下往上**生效）：\n"
    "\n"
    "      def phone_must_be_11_digits(cls, value): ...\n"
    "      phone_must_be_11_digits = classmethod(phone_must_be_11_digits)  # 先：包成类方法\n"
    "      phone_must_be_11_digits = field_validator('phone')(phone_must_be_11_digits)  # 后：登记字段\n"
    "\n"
    "  所以顺序不能反：field_validator 要求手里拿到的已经是个类方法。\n"
    "  （装饰器是从函数「离得最近的那个」开始套，这个规律对所有装饰器都成立。）\n"
    "  顺序反了会怎样？实验 6 真跑给你看——不报错，但校验器静默失效。",
)


# ============================================================
section("实验 5：一个校验器管多个字段 / 一个字段挂多个校验器")
# ============================================================


class Multi(BaseModel):
    name: str | None = None
    phone: str | None = None

    # 一个校验器登记在多个字段上：每个字段的值分别送给它一次
    @field_validator("name", "phone", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        return None if value == "" else value

    # 同一个字段可以挂第二个校验器；多个校验器按登记顺序依次执行
    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        # isdigit()：字符串里**每个字符都是数字**时返回 True，否则 False。
        # 注意它对全角数字「１３８…」也返回 True，坑的细节见 day16_regex_demo.py 第 5 节
        if value is not None and not (value.isdigit() and len(value) == 11):
            raise ValueError(f"手机号必须是 11 位数字，收到 {value!r}")
        return value


print(f"  空串 + 空串：{Multi(name='', phone='').model_dump()}")
print(f"  正常值：{Multi(name='刘小明', phone='13800138000').model_dump()}")
try:
    Multi(name="刘小明", phone="138-0013-8000")
except ValidationError as error:
    item = error.errors()[0]
    print(f"  带横线：被第二个校验器拦下 -> {item['loc']}｜{item['msg']}")


# ============================================================
section("实验 6：PyCharm 为什么在这两行上标黄")
# ============================================================

print(
    """  你在 PyCharm 里看到的那句：
    「此装饰器不会收到所预期的可调用对象；内置装饰器返回了特殊对象」

  它在说什么：装饰器本来是「接收下面那个函数、返回一个新东西」的东西。
  PyCharm 看到 @field_validator 上面还压着一个 @classmethod，就去算
  classmethod 的返回值是什么——结果它不是普通函数，而是一个
  **描述符对象（classmethod 类型的对象）**。于是它替你担心：
  「外层这个装饰器指望拿到可调用对象，现在拿到的是个特殊对象，能用吗？」

  而 Pydantic 的答案恰恰是：能用，我就是要这个——它会自己把
  classmethod 拆开，取出里面的函数再调用。所以这是**静态检查的误报**，
  不是运行时错误。下面三种写法都真跑一遍，你自己看结果："""
)


def try_write(label, define) -> None:
    """把「定义一个模型」包起来跑，成功失败都报出来（类体是在定义时就执行的）。"""
    try:
        model = define()
        print(f"  {label}")
        print(f"    -> 能跑：{model(name='').model_dump()}")
    except Exception as error:  # noqa: BLE001
        print(f"  {label}")
        print(f"    -> 报错：{type(error).__name__}: {str(error).splitlines()[0]}")


def documented_order():
    """文档写法：@field_validator 在外，@classmethod 在内。"""

    class Documented(BaseModel):
        name: str | None = None

        @field_validator("name", mode="before")
        @classmethod
        def blank_to_none(cls, value):
            return None if value == "" else value

    return Documented


def reversed_order():
    """顺序反过来：@classmethod 在外，@field_validator 在内。"""

    class Reversed(BaseModel):
        name: str | None = None

        @classmethod
        @field_validator("name", mode="before")
        def blank_to_none(cls, value):
            return None if value == "" else value

    return Reversed


try_write("① 文档写法（@field_validator 在外，@classmethod 在内）", documented_order)
try_write("② 顺序反过来（@classmethod 在外）", reversed_order)

print(
    """\n  ⚠️ 仔细看这两个结果，别被「都不报错」骗了：

    ① 传空串进去 -> {'name': None}   ← 校验器干活了，空串被归一成 None
    ② 传空串进去 -> {'name': ''}     ← 校验器**根本没生效**，空串原样留下

  也就是说：顺序写反**不报错**，它只是把你的校验器悄悄扔了。
  后果比报错严重——模型照常创建、程序照常跑，脏数据一路流进去，
  直到某天你在数据库里发现一堆空串。这类错只能靠**行为**发现，
  不能靠「有没有报错」发现：写完喂一个空串，看它变没变 None。

  所以 PyCharm 那句标黄该怎么看：它标的位置（文档写法）其实是对的，
  提醒本身是误报；但它提醒的道理是真的——classmethod 返回的不是普通函数，
  装饰器顺序一错，行为就完全变了。判据永远是**跑一遍**，不是颜色。"""
)

print(
    """\n  想让 PyCharm 闭嘴的话，在装饰器上一行加它的专用注释：

      # noinspection PyDecorator
      @field_validator("phone")
      @classmethod
      def phone_must_be_11_digits(cls, value): ...

  但先想清楚代价：这句是「别检查我」——把这个检查关掉以后，
  哪天真把装饰器套错了（比如套在 @property 上），它也不会再提醒你了。
  更划算的做法是留着黄，知道它为什么黄。"""
)


# ============================================================
section("一句话总结")
# ============================================================

print(
    "  · @field_validator('字段名', mode=...) 是**登记**：告诉 Pydantic 校验这个字段时叫我"
)
print("  · @classmethod 是**形态**：因为校验发生在实例创建之前，第一个参数是类不是实例")
print("  · mode='before' 抢在类型检查前动手（用来修补），默认 'after' 是查完再动手")
print("  · 两个装饰器从下往上套，顺序不能反")
print("  · 想验证「到底有没有被调用」，在函数里 print 一行是最省事的办法")
print("  · IDE 标黄只是静态推断：判据是跑一遍，不是颜色")
