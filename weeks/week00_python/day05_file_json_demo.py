"""文件和 JSON：把数据存到磁盘上，再读回来。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day05_file_json_demo.py

这个脚本会在同目录下建一个 outputs/ 文件夹放临时产物，
你在 .gitignore 里能看到 outputs/ 本来就是被忽略的。
"""

import json
from pathlib import Path

# 关键的一行：不管从哪个目录运行这个脚本，都能找到它旁边的文件。
# __file__ 是这个脚本自己，.parent 是它所在的文件夹。
HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "outputs"
SAMPLE = HERE / "day05_sample.json"


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 读文件：为什么要用 with")
# ============================================================

say(
    "这是什么：把磁盘上的一个文件打开、读出里面的文字、再关上。",
    "为什么需要：程序一退出，内存里的东西全没了。工具列表、对话记录、检索结果",
    "           想留下来，就得写进文件；下次运行时再读回来。",
    "场景：你 Day 3/4 的 MOCK_DOCS 是写死在代码里的，真实项目里这些数据住在文件里。",
)
print()

OUTPUT_DIR.mkdir(exist_ok=True)
demo_file = OUTPUT_DIR / "hello.txt"
demo_file.write_text("第一行\n第二行\n", encoding="utf-8")

say("先看最原始的写法（能用，但有个隐患）：")
handle = demo_file.open(encoding="utf-8")
content = handle.read()
handle.close()  # 必须自己记得关
say(f"  读到：{content!r}")
print()

say("再看推荐的写法：")
with demo_file.open(encoding="utf-8") as finished:
    text = finished.read()
say(f"  读到：{text!r}")
print()

say("两者的区别在「中途出错」的时候：")
try:
    with demo_file.open(encoding="utf-8") as handle2:
        handle2.read()
        raise RuntimeError("假装读到一半程序出错了")
except RuntimeError as error:
    say(f"  捕获到异常：{error}")
say(
    f"  可是文件还是被关上了吗？handle2.closed = {handle2.closed}",
    "",
    "with 的作用就是这个：不管代码块里正常结束还是抛异常，退出时都会自动关闭文件。",
    "手动 open/close 的写法里，只要中间抛了异常，close() 就永远轮不到执行，",
    "文件句柄会一直占着（Windows 上表现为「文件被占用，删不掉」）。",
    "",
    "等价的手写版本是 try/finally，但既然有 with，就没有理由手写。",
)


# ============================================================
section("2. encoding：中文环境最容易踩的一脚")
# ============================================================

say(
    "这是什么：读文件时要告诉 Python「这个文件用哪种编码存的」。",
    "为什么需要：编码不对，中文就会变成乱码或者直接报错。",
    "场景：Windows 中文系统的默认编码不是 utf-8，而绝大多数现代文件都是 utf-8。",
)
print()

say("我写一个 utf-8 的中文文件，然后故意不写 encoding 去读它：")
demo_file.write_text("中文测试", encoding="utf-8")
try:
    demo_file.read_text()  # 故意不写 encoding，用系统默认编码
    say("  居然读出来了（说明这台机器的默认编码正好是 utf-8）")
except UnicodeDecodeError as error:
    say(
        f"  报错：{type(error).__name__}",
        f"        {str(error)[:70]}",
    )
print()

say(
    "解决办法只有一个字：写。",
    '  demo_file.read_text(encoding="utf-8")',
    '  open(path, encoding="utf-8")',
    "",
    '凡是读写文本文件，一律显式写 encoding="utf-8"，不要依赖系统默认值——',
    "你的代码换到别人机器上（或者换成 Linux 服务器）行为会变。",
    "",
    '顺带记一句：写 CSV 的时候还要加 newline=""，否则 Windows 上会多出空行。',
    "现在知道有这回事就行，用到再查。",
)


# ============================================================
section("3. pathlib：路径不要用字符串拼")
# ============================================================

say(
    "这是什么：Python 自带的一套路径工具，用对象表示路径，而不是字符串。",
    "为什么需要：字符串拼接的路径在 Windows 和 Linux 上写法不同，还容易拼错。",
    "场景：脚本要读「和自己放在一起的数据文件」，而你可能从任何目录运行它。",
)
print()

say(
    f"  这个脚本自己在哪里：{HERE}",
    f"  它旁边的样例数据：  {SAMPLE.name}",
    f"  这个文件存在吗：    {SAMPLE.exists()}",
    f"  同目录下有几个 .py 文件：{len(list(HERE.glob('*.py')))}",
    f"  用 / 拼路径：        {HERE / 'outputs' / 'x.json'}",
    "",
    "常用的一小把：",
    "  Path(__file__).parent   → 脚本所在目录（最常用，解决「换个目录跑就找不到文件」）",
    "  a / b / c               → 拼路径（不用管系统用 / 还是 \\）",
    "  p.exists()              → 在不在",
    "  p.mkdir(exist_ok=True)  → 建目录，已存在也不报错",
    "  p.read_text() / p.write_text() → 一次读/写完整文本，省掉 open",
)


# ============================================================
section("4. JSON 字符串 和 Python 字典，是两种东西")
# ============================================================

say(
    "这是什么：JSON 是一种文本格式，用来把结构化数据写成字符串。",
    "为什么需要：程序之间传数据要靠文本（HTTP 请求、模型返回、配置文件都是 JSON）。",
    '场景：模型返回的 {"name": "搜索", "arguments": {...}} 是**字符串**，',
    "     不是字典，不能直接下标取值——这是新手最容易混淆的一点。",
)
print()

raw = '{"name": "search_docs", "arguments": {"top_k": 3}}'

say(
    f"  raw 本身是什么类型：{type(raw).__name__}",
    f"  raw 长这样：{raw}",
    "",
    "  试着把它当字典用：",
)
try:
    raw["name"]
except TypeError as error:
    say(f"    报错：{error}")
    say("    这个报错的意思就是「字符串不能用文本下标取值」。")
print()

data = json.loads(raw)
say(
    f"  用 json.loads 转过之后：{type(data).__name__}",
    f"  现在可以取值了：data['name'] = {data['name']!r}",
    f"  嵌套的那层也变成了字典：data['arguments'] = {data['arguments']}",
    f"  再转回字符串：json.dumps(data) = {json.dumps(data)}",
    "",
    "四个方法，靠「有没有 s」区分：",
    "  json.loads(字符串) → 字典      loads 的 s = string",
    "  json.dumps(字典)   → 字符串    dumps 的 s = string",
    "  json.load(文件对象) → 字典     不带 s 的吃文件对象",
    "  json.dump(字典, 文件对象)      不带 s 的写文件对象",
)


# ============================================================
section("5. 写 JSON 给人看：两个参数")
# ============================================================

data = {"title": "工具调用", "count": 2}

say(
    "  默认 dumps（中文被转义成 \\uXXXX，还挤成一行）：",
    f"    {json.dumps(data)}",
    "",
    "  加上 ensure_ascii=False 和 indent=2：",
    json.dumps(data, ensure_ascii=False, indent=2),
    "",
    "  ensure_ascii=False → 中文原样输出，人看得懂（默认 True 会转成 \\u5de5\\u5177）",
    "  indent=2           → 缩进两格，一行一个字段，方便肉眼对比",
    "",
    "要发给程序看的 JSON 其实用默认值更稳（纯 ASCII，不怕编码问题）；",
    "要存下来自己看的、要提交到仓库的，就用这两个参数。",
)


# ============================================================
section("6. 串起来：读 → 改 → 写")
# ============================================================

say(
    f"现在完整走一遍：读 {SAMPLE.name}，改一个字段，写到 outputs/ 下的新文件。",
)
print()

with SAMPLE.open(encoding="utf-8") as source:
    dataset = json.load(source)

dataset["version"] = dataset["version"] + 1
for document in dataset["documents"]:
    document["reviewed"] = True

target = OUTPUT_DIR / "day05_sample_v2.json"
with target.open("w", encoding="utf-8") as sink:
    json.dump(dataset, sink, ensure_ascii=False, indent=2)

say(
    f"  新文件写到：{target}",
    f"  它存在吗：{target.exists()}",
    "",
    "  内容是这样的：",
    target.read_text(encoding="utf-8"),
)

say(
    "",
    "要注意什么：",
    "  1. 写文件前先确认目录存在。这次能成功是因为前面 mkdir 过；",
    "     目录不存在时 open('w') 会抛 FileNotFoundError。",
    "  2. 上面读的时候用了带 s 还是不带 s 的方法，回看一下——",
    "     读文件对象用 json.load，写文件对象用 json.dump。",
    "  3. 改数据之前先想清楚是「改内存里的副本」还是「改原文件」。",
    "     这里改的是内存里的 dataset，原文件一直没动，直到最后一步才写出新文件。",
)


section("总结")
say(
    "1. 读文件用 with，它会保证退出时关闭文件（哪怕中途抛异常）",
    '2. 读写文本一律显式 encoding="utf-8"，别依赖系统默认',
    "3. 路径用 pathlib.Path，Path(__file__).parent 能定位到脚本旁边",
    "4. JSON 字符串 ≠ 字典；loads/dumps 吃字符串，load/dump 吃文件对象",
    "5. 写给人看用 ensure_ascii=False + indent=2",
)
