# Python 学习笔记

用途：记下「和我会的语言的差异」「踩过的坑」「报错原文与原因」。
每周重读一次。

---

## 我要干什么 → 用什么

这张表按**需求**查，不按术语查。

用法：卡住的时候先在纸上（或在心里）说一句「我现在要干什么」，比如「把几条消息拼成一段文字」，
再来这里找。找不到，说明这个需求还没挂上标签，解决之后回来补一条。

左边一栏要写**你当时的原话**，不要写官方术语——写「字符串拼接」没用，因为卡住的时候你
脑子里想的是「怎么换行拼起来」。

### 字符串与输出

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 把一堆东西一行一行拼成一段文字 | 先 `append` 攒进列表，最后 `"\n".join(列表)`；不要边循环边 `+=` | Day 2 第 1 题、Day 4 综合题第 4 步 |
| 自己指定分隔符（逗号、顿号） | `"，".join(列表)` | `day02_join_demo.py` |
| 空列表会不会多出个分隔符 | 不会，`"\n".join([])` 就是空字符串 | `day02_join_demo.py` 第 2 节 |
| 往字符串里插变量 | `f"{name} 有 {count} 条"` | `day01_fstring_demo.py` |
| 想知道字符串里有没有看不见的字符 | `print(repr(s))` 或 `f"{s!r}"` | `notes/卡住了怎么办.md` 第 3 招 |
| 数字保留两位小数 | `f"{price:.2f}"` | Day 1 |

### 列表 / 字典 / 排序

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 从一堆东西里挑出符合条件的 | `[x for x in xs if 条件]` | Day 2 |
| 对每个元素做点变化，得到新列表 | `[x * 2 for x in xs]` | Day 2 |
| 数每个词出现几次 | `counts[w] = counts.get(w, 0) + 1` | `day02_counter_demo.py` |
| 取字典的值，但不确定键在不在 | `d.get("k", 默认值)` | `notes/卡住了怎么办.md` 自查第 2 条 |
| 键一定在，缺了就该当场报错 | `d["k"]` | 同上 |
| 按某个字段从大到小排 | `sorted(xs, key=lambda x: x["score"], reverse=True)` | `day02_sorted_demo.py` |
| 排完序只要前 N 个 | `sorted(...)[:N]` | Day 2 第 2 题 |
| 排序依据的字段名是参数传进来的 | `key=lambda x: x[field]` | Day 3 第 3 题 |
| 只要前几个 / 跳过前几个 | `xs[:3]` / `xs[3:]` | Day 2 |

### 函数

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 参数可以省略，用默认值 | `def f(a, b=5)`；调用时写 `f(a, b=10)` 更清楚 | Day 3 |
| 默认值想用列表/字典 | 默认写 `None`，函数里 `if x is None: x = []` 再建 | Day 3 第 4 题、`FAILURES.md` |
| 给参数和返回值写说明书 | `def f(query: str, top_k: int = 5) -> list[str]:` | Day 3 第 2 题 |
| 把「怎么排序、怎么取数」交给调用者 | 用 `key=` 收一个函数，函数里用传进来的参数 | Day 3 第 3 题 |
| 不确定参数有几个 | `*args` / `**kwargs` | 清单里列过，只在 `day04_class_demo.py` 的 `AlertCheck` 露过一次 |

### 类

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 把一组数据和对它的操作绑在一起 | `class X:` + `__init__(self, ...)` + 方法 | `day04_class_demo.py` |
| print 出来是给人看的格式 | `__str__`（记得 `return` 字符串，别在里面 print） | Day 4 第 1 题 |
| 调试、放进列表里显示得清楚 | `__repr__`，写成 `X(a=1, b=2)` 的样子 | Day 4 第 1 题 |
| 让 `len(我的对象)` 能用 | `__len__` | `day04_more_demo.py` 第 2 节 |
| 有个值是由别的数据算出来的 | `@property` | `day04_more_demo.py` 第 4 节 |
| 两个类有一半代码重复 | 继承 `class B(A):` + `super().__init__(...)` | `day04_more_demo.py` 第 1 节 |
| 不同的类提供同名方法，被统一循环处理 | 各自实现 `run()`，外层一个循环调用 | `day04_class_demo.py` 第 4 节 |

### 数据校验与结构（Pydantic）

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 外部来的数据（模型返回、接口、文件）先校验 | `class X(BaseModel):` + 类型注解 | Day 4 第 2 题 |
| 某个字段可以不传 | `= Field(default_factory=list)` | Day 4 第 3 题 |
| 转成字典 / 转成 JSON 字符串 | `.model_dump()` / `.model_dump_json()` | `day04_pydantic_demo.py` 第 7 节 |
| 转出来的值要发给接口 | `.model_dump(mode="json")`，否则枚举还是枚举对象 | Day 4 综合题第 5 步 |
| 从 JSON 字符串直接变对象 | `.model_validate_json(raw)` | Day 4 第 3 题 |
| 一个字段只能取固定几个值 | `class X(StrEnum)` | `day04_more_demo.py` 第 3 节 |
| 报错里想知道是哪一类问题 | 看 `type=`：`missing` / `string_type` / `enum` … | Day 4 第 4 题 |
| 看看这个结构交给模型长什么样 | `.model_json_schema()` | `day04_pydantic_demo.py` 第 8 节 |

### 文件与运行

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 这个文件既能被导入，又能单独跑 | `if __name__ == "__main__":` | `day04_more_demo.py` 第 5 节 |
| 用另一个文件里的东西 | `import day04_helpers` / `from day04_helpers import format_tool` | 同上 |

### 查东西（不记得某个函数/对象怎么用）

| 我要干什么（大白话） | 写法 | 见过的地方 |
|---|---|---|
| 不知道某个函数有什么参数、还能怎么用 | `print(f.__doc__)` 或 `help(f)` | Day 4 查 `model_dump` 的 `mode` 参数 |
| 不知道一个对象身上有哪些方法 | `[n for n in dir(x) if not n.startswith("_")]` | Day 4 用这招找到 `model_validate_json` |
| 想知道某个东西到底是什么类型 | `print(type(x))`、`print(x.__name__)` | 排错常用 |

补表的方法：每次卡住、最后解决之后回到这里加一行，左边写你当时的原话，右边贴最小的代码形状。
这张表越来越长是好事——它就是你的「已掌握清单」。

---

## 语法差异（Day 1 起累积）

| 我会的语言 | Python | 注意 |
|---|---|---|
|  | 缩进即语法，没有大括号 |  |
|  | `None` |  |
|  | f-string |  |
|  | `and / or / not` |  |

---

## 踩过的坑

### 1. 可变默认参数

```python
# 错误写法

# 正确写法

# 为什么：
```

### 2. 

---

## 报错速查

| 报错信息 | 原因 | 怎么修 |
|---|---|---|
|  |  |  |

---

## 还不懂、留着以后搞清楚的

- 
