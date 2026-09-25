"""具名元组演示：为什么 version.major 和 version[0] 是同一件事。

直接运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day01_namedtuple_demo.py
"""

import sys
from collections import namedtuple

print("=" * 50)
print("1. sys.version_info 长什么样")
print("=" * 50)

version = sys.version_info
print(f"直接打印：{version}")
print(f"它的类型：{type(version)}")
print(f"它是不是元组：{isinstance(version, tuple)}")

print("\n" + "=" * 50)
print("2. 两种访问方式，结果是同一个值")
print("=" * 50)

print(f"version[0]     = {version[0]}")
print(f"version.major  = {version.major}")
print(f"两者相等吗：{version[0] == version.major}")
print(f"version[1]     = {version[1]}")
print(f"version.minor  = {version.minor}")
print(f"两者相等吗：{version[1] == version.minor}")

print("\n" + "=" * 50)
print("3. 它一共有哪些「名字」可以用")
print("=" * 50)

# 注意：sys.version_info 没有 namedtuple 的 _fields 属性
print(f"它有 namedtuple 的 _fields 属性吗：{hasattr(version, '_fields')}")
print(f"它有 n_fields 属性吗：{hasattr(version, 'n_fields')}，值是 {version.n_fields}")
print("\n为什么？因为它是 CPython 内置的另一种结构，叫 structseq。")
print("它的定位和具名元组一样：每个位置有名字，也能按下标取值。")
print("但它不是 collections.namedtuple 造出来的，所以属性名不一样。\n")

FIELD_NAMES = ["major", "minor", "micro", "releaselevel", "serial"]
for index, name in enumerate(FIELD_NAMES):
    print(f"  第 {index} 个字段叫 {name:12} 值是 {getattr(version, name)}")

print("\n  同类还有 os.stat 的返回值，也是 structseq。")

print("\n" + "=" * 50)
print("4. 既然是元组，就能做元组能做的事")
print("=" * 50)

# 解包
major, minor, micro, releaselevel, serial = version
print(f"解包得到：major={major}, minor={minor}, micro={micro}")

# 按长度取值
print(f"长度：{len(version)}")

# 按位比较：先比第 0 个，相等再比第 1 个
print(f"version >= (3, 11) 的结果：{version >= (3, 11)}")
print(f"version >= (3, 14) 的结果：{version >= (3, 14)}")

print("\n" + "=" * 50)
print("5. 自己造一个具名元组")
print("=" * 50)

# 普通元组：只能靠下标，读代码时得数位置
plain = ("张三", 28, "北京")
print(f"普通元组：[0]={plain[0]}, [1]={plain[1]}, [2]={plain[2]}")
print("       问题：三个月后你还记得 [1] 是年龄还是工号吗？")

# 具名元组：每个位置有名字
Person = namedtuple("Person", ["name", "age", "city"])
person = Person(name="张三", age=28, city="北京")
print(f"\n具名元组：.name={person.name}, .age={person.age}, .city={person.city}")
print(f"照样能用下标：person[0]={person[0]}")
# 解包要单独写一行。注意 f-string 的花括号里只能放表达式，
# 不能放 `a, b = x` 这种赋值语句——写进去只会原样输出文本。
name, age, city = person
print(f"还能解包：{name}, {age}, {city}")
print(f"依然是元组：{isinstance(person, tuple)}")

print("\n" + "=" * 50)
print("6. 一句话总结")
print("=" * 50)
print("具名元组 = 元组 + 给每个位置起个名字")
print("不变的特性：有序、不可修改、可解包、可比较")
print("新增的能力：可以用点号按名字取值，代码更好读")
print()
print("补充：version_info 属于「类具名元组」的内置结构（structseq），")
print("行为上和具名元组一致，只是内部实现和属性名不同。")
