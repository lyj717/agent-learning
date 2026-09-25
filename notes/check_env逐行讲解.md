# `check_env.py` 逐行讲解

> 这份文件把仓库里 [check_env.py](../agent-learning/check_env.py) 的 270 行代码拆成 8 关来讲。
> 它覆盖了 Python 补齐期 Day 1 到 Day 6 的绝大部分语法点，而且是你自己环境里真实在跑的代码——比任何教程例子都值得读。

---

## 怎么用这份讲解

**不建议从头读到尾。** 按下面的顺序读，每读一关就回到代码里对应位置看一眼。

| 关卡 | 覆盖的代码行 | 对应 Day | 难度 |
|---|---|---|---|
| 第 1 关｜常量与字典 | 16~32 | Day 2 | 入门 |
| 第 2 关｜函数与类型注解 | 35~50 | Day 3 | 入门 |
| 第 3 关｜循环、解包与异常 | 53~72 | Day 2、Day 5 | 入门 |
| 第 4 关｜字符串、切片与推导式 | 75~137 | Day 2 | 中等 |
| 第 5 关｜返回多个值 | 140~168 | Day 3 | 入门 |
| 第 6 关｜读文件与编码 | 171~186 | Day 5 | 中等 |
| 第 7 关｜调用第三方库 | 188~230 | Day 4、Day 5 | 中等 |
| 第 8 关｜命令行参数与入口 | 233~270 | Day 5 | 入门 |

**读法**：先看代码，自己猜意思，再看讲解。猜错的地方才是你真正要学的地方。

---

## 第 1 关｜模块导入与常量（第 16~32 行）

```python
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent

REQUIRED_PACKAGES = {
    "openai": "openai",
    "httpx": "httpx",
}
```

**逐行说明**

`import argparse` —— 导入整个模块。用的时候要写全名：`argparse.ArgumentParser()`。

`from pathlib import Path` —— 只导入模块里的一个东西。用的时候直接写 `Path(...)`。
两种导入方式没有优劣，区别是「写起来短」和「看得出这名字从哪来」。

`ROOT = Path(__file__).parent` —— 这一行有三个知识点：

- `__file__` 是 Python 自动给的变量，值是当前这个文件的路径。注意它前后是两个下划线。
- `Path(...)` 把字符串路径变成路径对象，之后可以用 `/` 拼路径，比用字符串拼更安全。
- `.parent` 取上一级目录。所以 `ROOT` 就是「这个文件所在的文件夹」。

**为什么这样写而不是写死路径**：写死 `C:\Users\dell\...` 的话，换台机器或者换个目录就崩了。用 `__file__` 推导出来的路径，代码放哪都对。这个习惯叫「不要硬编码路径」，面试聊工程素质时会加分。

`REQUIRED_PACKAGES = {...}` —— 字典，用花括号。这里用了一个很实用的技巧：**字典的键是给人看的名字，值是代码里要导入的名字**。因为包名和导入名经常不一样，比如 `python-dotenv` 装的时候叫这个，导入的时候得写 `import dotenv`。

**这一关的坑**

- 变量名全大写（`ROOT`、`REQUIRED_PACKAGES`）是 Python 的约定，表示「这是常量，不要改」。Python 语言层面不禁止你改，是程序员之间的默契。
- 字典末尾那一行 `}` 前面的逗号可以省略，但留着更方便以后加内容。

---

## 第 2 关｜函数与类型注解（第 35~50 行）

```python
def check_python() -> bool:
    """检查 Python 版本。Agent 开发建议 3.11 以上。"""
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"

    if version < (3, 11):
        print(f"  [x] Python {version_text}：版本偏低，建议升级到 3.11 以上")
        return False

    in_venv = sys.prefix != sys.base_prefix
    venv_text = "已启用虚拟环境" if in_venv else "未启用虚拟环境（建议激活 .venv）"

    print(f"  [v] Python {version_text}：{venv_text}")
    print(f"      解释器路径：{sys.executable}")
    return in_venv
```

**逐行说明**

`def check_python() -> bool:` —— 定义一个函数。`-> bool` 是**类型注解**，声明这个函数会返回布尔值。Python 不会因为你返回了别的类型就报错，它只是给人和工具看的说明书。

> 后面写 Agent 时，**工具的入参 schema 就是从这种注解自动生成的**。所以注解写不写、写得对不对，直接决定模型能不能正确调用你的工具。这不是代码风格问题，是功能问题。

`"""检查 Python 版本。..."""` —— 三引号字符串，放在函数第一行就是「文档字符串」。写 `help(check_python)` 时会把这段显示出来。养成写它的习惯，面试官看你仓库时会留意。

`version = sys.version_info` —— 拿到 Python 版本信息。它的类型是一个「具名元组」，所以下面能用 `version.major` 这种点号访问。

`f"{version.major}.{version.minor}.{version.micro}"` —— **f-string**，字符串前面的 `f` 表示里面 `{}` 的内容会被求值后嵌进字符串。这是 Python 里最常用的字符串写法，你后面每天要用几十次。

`if version < (3, 11):` —— 元组比较。Python 会从左往右逐个比较，先比 major，一样再比 minor。所以 `(3, 13, 9) < (3, 11)` 是 False，`(3, 9, 0) < (3, 11)` 是 True。这个写法读起来几乎和自然语言一样。

`return False` —— 立刻结束函数并把 False 交给调用者。**`return` 之后的代码不会执行**，这点和所有语言一样，但新手常在这里搞错缩进。

`in_venv = sys.prefix != sys.base_prefix` —— 判断是否在虚拟环境里。

- `sys.prefix` 是当前生效的 Python 安装目录。
- `sys.base_prefix` 是最底层的 Python 安装目录。
- 两者不同，说明当前用的是虚拟环境。

> 为什么需要这个检查：虚拟环境没启用的最常见后果是「包装了但导不进来」，报错信息是 `ModuleNotFoundError`，新手往往以为是没装包，其实是装到了另一个 Python 里。这个坑你一定会遇到一次。

`venv_text = "已启用虚拟环境" if in_venv else "未启用虚拟环境"` —— 条件表达式，也就是「三元运算符」。格式是 `值A if 条件 else 值B`，等价于一个四行的 if/else。这里用它比写 if 块更清爽。

**这一关的坑**

- 类型注解写错不会报错，所以很多人懒得写。但在 Agent 项目里这个习惯会直接反咬你一口。
- `print` 里的 `[v]` 和 `[x]` 只是自定义的符号，没有特殊含义——用 `[v]` 是因为 `[✓]` 在某些终端会乱码。**在 Windows 上能用 ASCII 就用 ASCII**，这是刚才那次乱码给你的教训。

---

## 第 3 关｜循环、解包与异常（第 53~72 行）

```python
def check_packages() -> bool:
    """逐个尝试导入依赖，报告缺哪个。"""
    missing = []

    for package_name, import_name in REQUIRED_PACKAGES.items():
        try:
            module = __import__(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"  [v] {package_name} {version}")
        except ImportError:
            missing.append(package_name)
            print(f"  [x] {package_name}：未安装")

    if missing:
        print(f"\n  修复：.venv\\Scripts\\python.exe -m pip install {' '.join(missing)}")

    return not missing
```

**逐行说明**

`missing = []` —— 空列表，准备往里装东西。Python 里列表就是可变的数组。

`for package_name, import_name in REQUIRED_PACKAGES.items():` —— 这一行有四个知识点，值得停下来多看两眼：

1. `REQUIRED_PACKAGES.items()` 返回「键值对」的序列，每一项是 `(键, 值)` 的元组。
2. `for a, b in ...` 是**解包**：把每一项的元组直接拆成两个变量。假如写成 `for item in ...`，那就得用 `item[0]` 和 `item[1]` 取值，可读性差很多。
3. 变量名取得好，代码自己会说话：`package_name` 是给人看的名，`import_name` 是给代码用的名。
4. 注意循环体靠缩进界定，没有花括号。

`try: ... except ImportError:` —— 异常处理。`try` 里面的代码一旦抛出 `ImportError`，就跳到 `except` 里继续执行，程序不会崩。

> 为什么这里只捕获 `ImportError` 而不是捕获所有异常？因为**只捕获你预料到的异常**是基本素养。捕获所有异常会把「文件不存在」「变量名打错」这类 bug 一起吞掉，让你在错误的地方排查半天。（不过下面第 7 关你会看到，我在调用模型那里故意反着来了一次，那是另一种场合。）

`module = __import__(import_name)` —— 按字符串动态导入模块。平时你会写 `import openai`，但这里包名放在变量里，所以要用 `__import__`。这是「拿字符串当模块名用」的场景。

`getattr(module, "__version__", "unknown")` —— 取模块的属性，第三个参数是「取不到时的默认值」。有些包（比如 `python-dotenv`）没有 `__version__`，所以自检时会显示 unknown——**这不是错误**，只是那个包没提供版本号。

`missing.append(package_name)` —— 往列表末尾追加一项。注意 `append` 是「就地修改」，它不返回新列表，返回值是 `None`。所以 `missing = missing.append(x)` 这种写法是错的，会把列表变成 None。

`{' '.join(missing)}` —— 把列表拼成字符串，用空格连接。这是 f-string 里嵌表达式的例子：`{}` 里可以放任意表达式，不只是一个变量。

`return not missing` —— 返回「列表是不是空的」。空列表在布尔判断里视为假，所以列表为空时 `not []` 是 True。

**这一关的坑**

- `missing.append()` 返回 None（上面说过，但值得再强调一次，这是高频错误）。
- 空列表、空字典、空字符串、0、None 在条件判断里都算「假」。这个特性叫真值判断，用好了代码很简洁，用错了真会被吓到（比如 `if items:` 和 `if items is not None:` 含义完全不同）。

---

## 第 4 关｜字符串、切片与推导式（第 75~137 行）

这一段是全文最值得读的，因为它是「文本处理」的典型写法。

```python
SUSPICIOUS_PUNCTUATION = "，。；：（）＝“”‘’【】、《》"

def inspect_env_format(env_path: Path) -> bool:
    raw = env_path.read_bytes()
    problems: list[str] = []

    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("文件开头有 BOM 标记，第一个配置项会读不出来")

    text = raw.decode("utf-8-sig", errors="replace")

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            problems.append(f"第 {line_number} 行没有等号，这一行会被忽略")
            continue
        key, _, value = stripped.partition("=")
        ...
```

**逐行说明**

`SUSPICIOUS_PUNCTUATION = "，。；：（）＝“”‘’【】、《》"` —— 字符串就是一串字符。中文标点在 Python 3 里和英文字母一样，一个字符算一个。

`env_path.read_bytes()` —— 按**字节**读文件，返回 `bytes` 类型（前面带 `b` 的那种）。检查文件编码必须在字节层面做，这就是为什么先读 bytes 再解码成文本。

`raw.startswith(b"\xef\xbb\xbf")` —— 检查文件开头有没有 BOM（Windows 记事本存 UTF-8 时可能加上的三个字节）。`\xef` 这种写法叫十六进制转义，表示一个字节。**这个检查就是为你刚才用记事本编辑 `.env` 这个场景写的。**

`problems: list[str] = []` —— 声明变量并加类型注解，含义是「这是一个装字符串的列表」。不加也能跑，加上更清楚。

`raw.decode("utf-8-sig", errors="replace")` —— 把字节解码成文本。

- `utf-8-sig` 的意思是「按 UTF-8 解码，并且如果开头有 BOM 就自动去掉」。
- `errors="replace"` 的意思是「遇到无法解码的字节就替换成一个问号，不要抛异常」。如果不写这个参数，遇到坏字节会直接抛错。

`enumerate(text.splitlines(), start=1)` —— 又是一个高频组合：

- `splitlines()` 把文本按行拆成列表。
- `enumerate(..., start=1)` 在遍历时同时给出序号，从 1 开始（默认是 0）。

所以 `for line_number, line in ...` 同时拿到行号和内容。**需要行号时必须用 enumerate，不要自己写个计数器加 1。**

`stripped = line.strip()` —— 去掉首尾的空白字符（空格、制表符、换行）。中间的空白会保留。

`if not stripped or stripped.startswith("#"):` —— 两个判断用 `or` 连起来：空行，或者以 `#` 开头的注释行。

`continue` —— 跳过本次循环剩下的部分，直接进入下一轮。用它来做「不满足条件就忽略」特别清爽，可以避免把代码写成一层套一层的 if。

`key, _, value = stripped.partition("=")` —— 三个知识点：

- `partition("=")` 把字符串按第一个等号切成三部分：(等号前, 等号本身, 等号后)。
- `key, _, value = ...` 是三变量解包。**下划线 `_` 是约定俗成的「我不关心这个值」**，这里指中间那个等号本身。
- 为什么不用 `split("=")`？因为值里面可能还有等号（比如密钥里有 `=` 的结尾），`split` 会切碎，而 `partition` 只切第一个，更安全。

```python
        found = [char for char in SUSPICIOUS_PUNCTUATION if char in value]
        if found:
            problems.append(f"... {' '.join(found)}")
```

`[char for char in SUSPICIOUS_PUNCTUATION if char in value]` —— **列表推导式**。等价于：

```python
found = []
for char in SUSPICIOUS_PUNCTUATION:
    if char in value:
        found.append(char)
```

推导式把四行压成一行。读法是从左往右：**「我要 char，它的来源是遍历 SUSPICIOUS_PUNCTUATION，条件是它出现在 value 里」**。这是 Python 最标志性的写法，务必练熟——你后面读的所有项目源码里都会出现。

`if found:` —— 利用真值判断：列表为空就是假，非空就是真。等价于 `if len(found) > 0:`，但更 Python 化。

```python
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            problems.append(f"第 {line_number} 行 {key} 的值被引号包着，建议去掉引号")
```

`value[0]` 取第一个字符，`value[-1]` 取**最后一个**字符（负数下标从右往左数，`-1` 是最后一个）。这个写法在 Python 里非常常用，别的语言里通常没有。

`value[0] in "\"'"` —— 判断一个字符是否属于某个集合。这里是判断它是不是单引号或双引号。注意 `\"` 是转义写法，表示双引号本身。

三个条件用 `and` 连起来，全部成立才执行下面的语句。

**这一关的坑**

- `if not stripped or stripped.startswith("#")` 里 `not` 的优先级容易看错，实在不确定就加括号。
- **列表推导式不要嵌套超过两层**。两层以上可读性会崩，不如老老实实写循环。
- 判断「字符在不在字符串里」用 `in`，判断「子串在不在字符串里」也用 `in`——Python 没有单独的 contains 方法。

---

## 第 5 关｜返回多个值（第 140~168 行）

```python
def check_env_file() -> tuple[bool, str]:
    """检查 .env 文件与密钥。返回（是否就绪, 密钥）。"""
    env_path = ROOT / ".env"

    if not env_path.exists():
        print("  [x] 没有找到 .env 文件")
        return False, ""
    ...
    return True, api_key
```

**逐行说明**

`-> tuple[bool, str]` —— 类型注解声明「返回一个元组，里面是一个布尔值和一个字符串」。**Python 的元组就是固定长度的有序容器**，可以用来一次返回多个值。

`ROOT / ".env"` —— 路径拼接。`Path` 对象重载了斜杠运算符，所以这里能用 `/` 拼路径，不管是 Windows 还是 Linux 都能正确工作。用字符串拼 `ROOT + "\\" + ".env"` 在跨平台时容易出问题。

`return False, ""` —— 实际上返回的是一个元组 `(False, "")`。写的时候不用加括号，加了也对。

**调用端怎么接收**（第 247 行）：

```python
env_ok, api_key = check_env_file()
```

直接把返回的元组解包成两个变量。**这是 Python 里返回多个值的标准做法**，不需要像别的语言那样定义一个结构体。

> 什么时候不该这么写：返回值超过三个，或者调用者经常只要其中一个值时，就该改成返回字典或用一个专门的类。现在这样两个值刚好。

**这一关的坑**

- 元组是不可变的，创建后不能改其中的元素。要改就用列表。
- 函数里提前 `return` 可以少写一层缩进，比用一长串 if/else 更好读。

---

## 第 6 关｜读文件与编码（第 171~186 行）

```python
def check_gitignore() -> bool:
    """确认 .env 不会被提交。这个检查比看起来重要。"""
    gitignore = ROOT / ".gitignore"

    if not gitignore.exists():
        print("  [x] 没有 .gitignore，密钥有泄露风险")
        return False

    content = gitignore.read_text(encoding="utf-8")
    if ".env" in content:
        print("  [v] .gitignore 已屏蔽 .env")
        return True

    print("  [x] .gitignore 里没有屏蔽 .env")
    return False
```

**逐行说明**

`gitignore.exists()` —— 判断文件或目录是否存在，返回布尔值。

`gitignore.read_text(encoding="utf-8")` —— 一次性读取整个文本文件。**一定要显式指定编码**：不指定的话 Python 会用系统的默认编码，在中文 Windows 上就是 GBK，读 UTF-8 的文件就会乱码甚至报错。这个坑跨平台协作时最致命。

> 对比一下上一关的 `read_bytes()`：读文本用 `read_text`，检查编码或读二进制用 `read_bytes`。两者都记得 `with` 更好。

**关于 `with`（这个文件里没用，但你一定会见到）**

如果文件很大，或者要写文件，标准写法是：

```python
with open("data.txt", encoding="utf-8") as f:
    content = f.read()
```

`with` 的好处是**离开这个缩进块时自动关闭文件**，即使中途抛异常也会关。不用 `with` 的话，忘记关文件会占用系统资源。这是「上下文管理器」的用法，Day 6 会讲到它的原理。

而 `Path.read_text()` 内部已经帮你处理好了开关文件，所以小文件直接用它更省事。

**这一关的坑**

- 中文 Windows 上 `open()` 不写编码，默认是 GBK，处理 UTF-8 文件必然出问题。
- `"env" in content` 这种判断很粗暴：`.env.example` 也会命中。真实项目里要用更精确的匹配，这里是为了保持简单。

---

## 第 7 关｜调用第三方库（第 188~230 行）

```python
def live_test(api_key: str) -> bool:
    """发一次真实请求，验证密钥和网络都通。"""
    from openai import OpenAI

    base_url = os.environ.get("LLM_BASE_URL") or None
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回答一个字：好"}],
            max_tokens=200,
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        ...
    except Exception as error:  # noqa: BLE001
        print(f"  [x] 调用失败：{type(error).__name__}: {error}")
        return False
```

**逐行说明**

`from openai import OpenAI` —— 注意这里**写在函数内部**，而不是文件开头。原因是：如果没装 openai（正好这个脚本就是用来检查有没有装的），写在文件开头会导致整个脚本连启动都启动不了。写在函数里，只有真调用到这个函数时才需要这个包。这种写法叫「延迟导入」。

`os.environ.get("LLM_BASE_URL") or None` —— 两步：

- `os.environ.get("LLM_BASE_URL")` 读环境变量。用 `get` 而不是 `os.environ["LLM_BASE_URL"]`，因为前者读不到会返回 None，后者会直接抛 KeyError 让程序崩掉。
- 后面的 `or None` 处理「环境变量存在但是空字符串」的情况——空字符串是假值，所以会变成 None。这样 SDK 就会用它自己的默认地址。

`os.environ.get("LLM_MODEL", "gpt-4o-mini")` —— `get` 的第二个参数是默认值：读不到就用它。

`client = OpenAI(api_key=api_key, base_url=base_url)` —— 创建客户端。这里用的是**关键字参数**，明确写出 `api_key=` 和 `base_url=`。这样参数顺序变了也不影响，比按位置传参清楚得多。后面你写 Agent 时几乎全用这种写法。

`messages=[{"role": "user", "content": "回答一个字：好"}]` —— 一个列表，里面装字典。这就是对话历史的格式，Day 10 做多轮对话时你会往这个列表里不断追加。**整个 Agent 开发的核心数据结构就是它。**

`response.choices[0]` —— 从响应里取第一个候选回答。用方括号按下标取值，`0` 是第一个。为什么会有多个？因为模型接口支持一次生成多个候选（`n` 参数），一般只用第一个。

`choice.message.content or ""` —— 又一个真值判断的实用场景：如果 `content` 是 None 或空字符串，就用 `""` 代替。**避免后面的 `.strip()` 报「NoneType 没有 strip 方法」这个错。** 这是写 API 调用时的标准防御动作，因为这行代码刚刚真的救了我们的场（第一次测试时返回的就是空内容）。

`except Exception as error:` —— 这里**故意**捕获所有异常，理由写在上一行的注释里：调用模型可能因为密钥、网络、模型名、限流等十几种原因失败，而这里的目的只是「告诉用户哪种情况会挂」，不需要区分具体异常类型。

注意 `# noqa: BLE001` 这个行尾注释——它是给代码检查工具看的，意思是「我知道你建议不要捕获所有异常，这里是刻意的，别报警」。**这是很有用的一个习惯**：当你要故意违反规范时，把理由写清楚，而不是让工具报一堆错然后你关掉整个检查。

`type(error).__name__` —— 取异常的类名（比如 `APIConnectionError`）。`type()` 拿类型，`.__name__` 拿名字。

`{error}` —— 整个异常对象转成字符串，通常包含错误信息。

**这一关的坑**

- 环境变量读不到时用 `[]` 会崩，用 `.get()` 更稳。
- 捕获所有异常时要写清理由，否则半年后你自己都不知道为什么这么写。
- **接口调用一定要加超时**。这个脚本没加，因为我们希望看它卡多久；真实项目里不加超时，一个卡住的请求会拖死整个服务。

---

## 第 8 关｜命令行参数与程序入口（第 233~270 行）

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="环境自检")
    parser.add_argument("--live", action="store_true", help="额外发一次真实 API 请求")
    args = parser.parse_args()

    print("\n=== 环境自检 ===\n")
    python_ok = check_python()
    ...
    all_ok = python_ok and packages_ok and env_ok and security_ok and live_ok

    if all_ok:
        print("环境就绪，可以开始 Day 1 了。")
    else:
        print("还有项目没通过，按上面的提示修一下再跑一次。")


if __name__ == "__main__":
    main()
```

**逐行说明**

`def main() -> None:` —— `-> None` 表示这个函数不返回任何值。

`argparse.ArgumentParser(description="环境自检")` —— 创建命令行解析器。`description` 会在 `--help` 时显示。

`parser.add_argument("--live", action="store_true", ...)` —— 加一个开关型参数。`action="store_true"` 的意思是「命令行里出现 `--live` 就是 True，不出现就是 False」，不需要跟值。

`args = parser.parse_args()` —— 解析命令行。之后就能用 `args.live` 拿到值。

**关于 `if __name__ == "__main__":` 这一行**

这是 Python 里最需要理解的一行，因为它同时解释了两个问题：

- `__name__` 是 Python 自动设置的变量。**当这个文件被直接运行时，它的值是 `"__main__"`；当这个文件被别的文件导入时，它的值是文件名。**
- 所以这一行的意思是：**「只有直接运行我这个文件时，才执行下面的 main()」**。

为什么要这样写？两个理由：

1. 如果别的代码 `import check_env`，不应该顺带把整个自检流程跑一遍——导入应该只是导入。
2. 你写测试时才能安全地导入里面的函数，单独测试 `check_env_file` 而不触发整个流程。

**`all_ok = python_ok and packages_ok and ...`** —— 五个布尔值用 `and` 串起来：全为真才是真。这比写五个嵌套 if 清楚得多。

**这一关的坑**

- 忘了写 `if __name__ == "__main__":` 的后果是：别人一导入你的文件，你的程序就跑起来了。这个坑在多人协作时很尴尬。
- `and` 是短路求值：前面为假，后面的函数根本不会被调用——这不是 bug，是特性，但要知道。

---

## 读完之后：5 个动手练习

按顺序做，每个都只改几行，但能让你真正读懂这个文件。

**练习 1｜加一项检查（练字典和列表）**
在环境信息里加一行，打印当前工作目录（`Path.cwd()`）。想想该加在哪个函数里。

**练习 2｜让报错更友好（练条件判断）**
现在密钥没填时提示是固定的。改成：如果密钥长度小于 20，提示「密钥看起来太短，确认有没有复制完整」。

**练习 3｜加一个新开关（练命令行参数）**
加一个 `--quiet` 参数，加上它时只打印最后一行结论，不打印中间过程。

**练习 4｜写个测试（练 pytest）**
新建 `tests/test_check_env.py`，给 `inspect_env_format` 写两个测试：一个是正常内容应该返回 True，一个是带中文标点的内容应该返回 False。提示：可以用 `tmp_path` 这个 pytest 内置夹具创建临时文件。

**练习 5｜改造成类（练面向对象）**
把 `check_python`、`check_packages` 这些函数改成一串「检查项」对象，每个对象有自己的名字和检查方法，`main` 里循环执行它们。

> 练习 5 是真正的分水岭——做出来说明你已经理解「函数是一等公民」这件事。做不出来也没关系，Day 4 学完类再回来做。

做完任何一个，都可以让我帮你 review。
