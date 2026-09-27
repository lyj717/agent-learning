"""拆解这句代码：key = stripped.partition("=")[0].strip()

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_partition_demo.py
"""


def section(title: str) -> None:
    print(f"\n{'=' * 54}\n{title}\n{'=' * 54}")


# ============================================================
section("1. partition 到底返回什么")
# ============================================================

line = "LLM_MODEL=deepseek-v4-flash"

result = line.partition("=")
print(f"原始字符串：{line!r}")
print(f"partition 的结果：{result}")
print(f"它的类型：{type(result).__name__}")
print(f"它的长度：{len(result)}")

print("\n看懂结构：partition 按第一个等号切成三块，装进一个元组")
print(f"  [0] 等号左边：{result[0]!r}")
print(f"  [1] 等号本身：{result[1]!r}")
print(f"  [2] 等号右边：{result[2]!r}")


# ============================================================
section("2. 逐步拆解那句代码")
# ============================================================

# 原始的一行，末尾故意带空格和换行，模拟真实文件里的内容
raw_line = "  LLM_MODEL = deepseek-v4-flash  \n"
print(f"文件里原始的一行：{raw_line!r}\n")

# 第一步：去掉首尾空白
stripped = raw_line.strip()
print(f"第 1 步  strip()      结果：{stripped!r}")

# 第二步：按第一个等号切三块
parts = stripped.partition("=")
print(f"第 2 步  partition()  结果：{parts}")

# 第三步：取第 0 块，也就是等号左边
before_equal = parts[0]
print(f"第 3 步  [0]          结果：{before_equal!r}")

# 第四步：把等号左边的空格也去掉
key = before_equal.strip()
print(f"第 4 步  strip()      结果：{key!r}")

print("\n四步合起来，就是那一行代码：")
print('  key = stripped.partition("=")[0].strip()')
print(f"  最终 key = {key!r}")


# ============================================================
section("3. 链式调用的读法：从左往右，一层套一层")
# ============================================================

code = 'stripped.partition("=")[0].strip()'
print(code)
print()
print("  stripped              ← 起点：一个字符串")
print('  .partition("=")       ← 调用方法，得到一个三元组')
print("  [0]                   ← 从三元组里取第 0 个，得到一个字符串")
print("  .strip()              ← 又变成字符串了，可以继续调用字符串方法")
print()
print("链式调用的关键：每一步的结果是什么类型，决定了下一步能用什么方法。")
print("这里 partition 返回元组，所以能用 [0]；")
print("[0] 拿到的是字符串，所以能接着用 .strip()。")


# ============================================================
section('4. 为什么不用 split("=")')
# ============================================================

tricky = "JWT_SECRET=abc=def=ghi"

print(f"假设配置值里本身含等号：{tricky!r}\n")

print("partition 只切第一个等号（更安全）：")
print(f"  {tricky.partition('=')}")

print("\nsplit('=') 会把所有等号都切开（值被切碎了）：")
print(f"  {tricky.split('=')}")

print("\n如果只想要键，两种都行。但如果要取值，")
print("split 会把一个完整的值切成好几段，容易出错。")


# ============================================================
section("5. 没有等号时会怎样")
# ============================================================

no_equal = "# 这是一行注释"

print(f"字符串：{no_equal!r}\n")
print(f"partition 的结果：{no_equal.partition('=')}")
print("\n注意：找不到分隔符时，partition 不会报错，")
print("而是把整串放在第 0 位，另外两个是空字符串。")
print("所以 [0] 拿到的是整行内容。")

print("\n正因如此，check_env.py 里在调用前先挡住了这种情况：")
print('  if not stripped or stripped.startswith("#") or "=" not in stripped:')
print("      continue")


# ============================================================
section("6. 同一件事的两种写法")
# ============================================================

stripped = "LLM_API_KEY=sk-abc123"

print(f"字符串：{stripped!r}\n")

# 写法一：解包（check_env.py 第 106 行用的）
key_a, _, value_a = stripped.partition("=")
print("写法一：一次拿到三块，用下划线表示『中间那个我不要』")
print(f"  key_a   = {key_a!r}")
print(f"  value_a = {value_a!r}")

# 写法二：只取第 0 块（check_env.py 第 127 行用的）
key_b = stripped.partition("=")[0].strip()
print("\n写法二：只要第一块，直接取下标")
print(f"  key_b   = {key_b!r}")

print("\n同一件事，两种写法都对。怎么选：")
print("  只要其中一块     → 用 [0] 这种取下标的方式")
print("  两块以上都要     → 用解包，可读性更好")


# ============================================================
section("7. 真实场景：手动解析 .env 文件")
# ============================================================

content = """
# 模型配置
LLM_API_KEY=sk-abc123
LLM_BASE_URL=https://api.deepseek.com

# 带空格的写法也能正确处理
LLM_MODEL = deepseek-v4-flash
DEBUG=true
"""

print("原始内容：")
print(content)

print("逐行解析的结果：")
config = {}

for line in content.splitlines():
    stripped = line.strip()

    # 跳过空行和注释行
    if not stripped or stripped.startswith("#"):
        continue

    # 没有等号的直接跳过
    if "=" not in stripped:
        continue

    # 左边是键，右边是值，两边都去掉多余空格
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()

    config[key] = value
    print(f"  {key:<16} = {value}")

print(f"\n解析出的配置项数量：{len(config)}")

print("\n这就是读取 .env 文件的原理。")
print("真实的 python-dotenv 库做的事情跟上面差不多，")
print("只是多了引号处理、变量替换、多行值等更复杂的规则。")


section("总结")
print('stripped.partition("=")     按第一个等号切成三块')
print("            [0]               取第一块（等号左边）")
print("            .strip()          去掉多余空格")
print()
print("整句读作：「把这行按第一个等号切开，取左边那块，去掉空格，作为键名」")
