"""Day 6 练习：生成器、异步并发、流式输出。

写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day06_exercises.py

本日考点（想不起来去查 docs/python-7天补齐清单.md 的 Day 6，
或翻今天的三份材料 day06_generator_demo.py、day06_decorator_demo.py、
day06_async_demo.py）：
  - 生成器：函数里有 yield，调用不会立刻执行；只能遍历一次
  - 流式输出：逐字给出 + end=""、flush=True
  - 异步：async def / await / asyncio.run，gather 并发
  - 异步代码里不能有阻塞调用（time.sleep 会让并发失效）

三道题对应清单里的三条练习：第 1 题写生成器，第 2 题写并发请求，
第 3 题在 day06_stream_example.py 里逐行注释（只做标着【今天能答】的五条，
带【等 Week 01】的先跳过——那条涉及 API 调用，是 Week 01 的内容）。
卡住就按 notes/卡住了怎么办.md 里的六招走，还不行再问我。
"""

import asyncio
import time

import httpx

# 第 2 题用的三个网址（都是稳定的公共站点）
URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://pypi.org",
]

# 第 1 题模仿模型回复用的句子
TEXT = "杭州今天 22 度，多云。"


def stream_text(text: str, delay: float = 0.03):
    """第 1 题：把一段话逐字「流」出来。
    要做的：
        1. 遍历 text 里的每个字符
        2. 每交出一个字符之前，先 time.sleep(delay) 一下，
           假装这是模型生成 + 网络传输花的时间
        3. 用 yield 把字符交给调用方
    期望结果：
        list(stream_text("abc", 0)) 得到 ['a', 'b', 'c']
        主程序里逐字打印，能看到打字机效果（每个字之间隔 0.03 秒）
    """
    for char in text:
        time.sleep(delay)
        yield char


async def fetch_one(client: httpx.AsyncClient, url: str) -> tuple[str, int]:
    """抓一个网址，返回 (网址, 状态码)。这一题不用改它。"""
    response = await client.get(url)
    return url, response.status_code


async def fetch_all_serial(urls: list[str]) -> tuple[list[tuple[str, int]], float]:
    """第 2 题（串行版）：一个抓完再抓下一个。
    要做的：
        1. 记下开始时间（time.perf_counter()：高精度计时器，用来量耗时）
        2. async with httpx.AsyncClient(timeout=10) as client: 建一个客户端
        3. for 循环里逐个 await fetch_one(client, url)，结果收进列表
        4. 返回 (结果列表, 总耗时)
    期望结果：
        三个网址的耗时相加 ≈ 总耗时（每个都要排队等）
    """
    start = time.perf_counter()
    s_result = []
    async with httpx.AsyncClient(timeout=10) as client:
        for url in urls:
            s_result.append(await fetch_one(client, url))
    return s_result, time.perf_counter() - start


async def fetch_all_together(urls: list[str]) -> tuple[list[tuple[str, int]], float]:
    """第 2 题（并发版）：三个请求一起发出去。
    要做的：
        1. 记下开始时间
        2. 同样用 async with httpx.AsyncClient(timeout=10) as client:
        3. 用 asyncio.gather 把所有请求一起交出去
        4. 返回 (结果列表, 总耗时)
    期望结果：
        总耗时 ≈ 最慢那个请求的耗时，明显小于串行版
    """
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as client:
        t_result = await asyncio.gather(*(fetch_one(client, url) for url in urls))
    return t_result, time.perf_counter() - start


async def compare_fetch() -> None:
    """跑两种版本，把耗时摆在一起看。"""
    try:
        serial_results, serial_time = await fetch_all_serial(URLS)
        together_results, together_time = await fetch_all_together(URLS)
    except httpx.HTTPError as error:
        print(f"  网络不通，跳过真实请求：{type(error).__name__}: {error}")
        print("  可以先看 day06_async_demo.py 里用 sleep 模拟的那组耗时对比")
        return

    print(f"  串行：{serial_time:.2f} 秒")
    for url, status in serial_results:
        print(f"    {status}  {url}")
    print(f"  并发：{together_time:.2f} 秒")
    for url, status in together_results:
        print(f"    {status}  {url}")
    if together_time > 0:
        print(f"  快了大约 {serial_time / together_time:.1f} 倍")


if __name__ == "__main__":
    print("=== 第 1 题：逐字流出这段话 ===")
    print("  ", end="")
    for char in stream_text(TEXT):
        print(char, end="", flush=True)
    print()
    print(f"  收集成一个列表看：{list(stream_text('流式', 0))}")

    print("\n=== 第 2 题：串行 vs 并发 ===")
    asyncio.run(compare_fetch())

    print("\n=== 第 3 题：逐行注释 ===")
    print("  去 day06_stream_example.py 里，只答标着【今天能答】的五条；")
    print("  带【等 Week 01】的留着，等学到那一周再回来")


# ============================================================
# 现象与原因（做完之后填）
# ============================================================
#
# 1. 用一句话回答 Day 6 的验收标准：流式输出为什么让用户「感觉」更快？
#    （提示：总时间有没有变？变的是哪一个时间？）
#   流式输出只是生成一点就输出一点，总时间并没有变，变的是用户看见第一次输出的时间
#
# 2. 生成器为什么第二次遍历是空的？想再遍历一次该怎么做？
#   生成器只能遍历一次，遍历完就结束了
#   想再遍历一次只能再创建一个新的生成器
# 3. 你在 day06_async_demo.py 里看到：用 time.sleep 并发三个任务耗时多少，
#    用 asyncio.sleep 耗时多少？为什么差这么多？
#   time.sleep:1.20s       asyncio.sleep:0.40s
#   time.sleep依旧是串行执行，耗时为三个相加,asyncio.sleep才是并发执行，为0.40S
# 4. 第 2 题里，你实测的串行总耗时和并发总耗时分别是多少？差几倍？
#    （如果网络不通，就填演示里那组模拟数据，并说明为什么）
#   串行：1.99s 并发：0.99s 差了2.2倍
#   串行是一个一个访问，耗时是三个相加   并发是一起访问，耗时是最慢的那一个
# 5. 异步代码里，为什么 asyncio.gather 里面写的是 fetch_one(client, url)
#    而不是 await fetch_one(client, url)？
#   加上await的话又变成一个一个串行执行了
