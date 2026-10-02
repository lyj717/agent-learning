"""异步：等网络的时候别干等着。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day06_async_demo.py

这份演示里的「请求」都用 asyncio.sleep 模拟，所以不联网也能跑，
耗时数字是真实的。想看真的网络请求，做 day06_exercises.py 的第二题。
"""

import asyncio
import time


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 先看问题：等待的时候，程序在做什么")
# ============================================================

say(
    "这是什么：程序发起网络请求后，要等服务器回应——这段时间 CPU 其实在闲着。",
    "为什么需要异步：闲着的时间可以用来干别的事。",
    "场景：Agent 一轮里要调 3 个工具，每个要 1 秒。",
    "     串行调要 3 秒；同时发出去，1 秒就能全回来。",
)
print()


async def fake_fetch(name: str, delay: float) -> str:
    """模拟一次网络请求：等 delay 秒后返回结果。"""
    await asyncio.sleep(delay)  # ← 异步版的 sleep：等的时候让出控制权
    return f"{name} 的结果"


TOOLS = [("天气工具", 0.4), ("检索工具", 0.4), ("翻译工具", 0.4)]


async def call_one_by_one() -> tuple[list[str], float]:
    """一个调完再调下一个（串行）。"""
    start = time.perf_counter()  # perf_counter()：高精度计时器，用来量耗时
    results = []
    for name, delay in TOOLS:
        results.append(await fake_fetch(name, delay))
    return results, time.perf_counter() - start


async def call_together() -> tuple[list[str], float]:
    """三个一起发出去，等最慢的那个（并发）。"""
    start = time.perf_counter()
    # gather(*协程)：把多个任务一起交给事件循环并发执行，
    # 返回的顺序和传入顺序一致（不是谁先回来谁在前，第 7 节会演示）
    results = await asyncio.gather(*(fake_fetch(name, delay) for name, delay in TOOLS))
    return list(results), time.perf_counter() - start


# asyncio.run(协程)：启动事件循环、把协程跑完、返回它的结果。
# 整个程序只在入口写一次
serial_results, serial_time = asyncio.run(call_one_by_one())
say(
    "  串行：一个一个调",
    f"    结果：{serial_results}",
    f"    总耗时：{serial_time:.2f} 秒（0.4 × 3）",
)
print()

together_results, together_time = asyncio.run(call_together())
say(
    "  并发：三个一起发",
    f"    结果：{together_results}",
    f"    总耗时：{together_time:.2f} 秒（只等了最慢的那个）",
    "",
    f"  差 {serial_time / together_time:.1f} 倍左右。这就是异步最直接的收益。",
    "",
    "  注意一件事：并发不是「同时运行」。Python 还是单线程，",
    "  它只是在「等待第一个请求回应」的空档里，把第二个请求也发出去。",
    "  因为等待期间 CPU 本来就闲着，所以这么做不违反「一次只能干一件事」。",
)


# ============================================================
section("2. async def 和 await 到底是什么")
# ============================================================

say(
    "  async def 定义的是「协程函数」。调用它不会执行函数体，",
    "  而是返回一个「协程对象」——这一点和生成器很像（Day 6 上半场的知识）。",
    "  await 的意思是：在这里等它出结果，等的时候把控制权交出去。",
)
print()


async def quick_task() -> str:
    return "做完了"


coro = quick_task()
say(
    f"  调用 quick_task() 拿到：{coro}",
    f"  它的类型是：{type(coro).__name__}",
    "  函数体一行都没跑——想让它跑，得 await 它，或者交给事件循环。",
)
coro.close()  # 手动关掉，不然解释器退出时会提示「协程从未被 await」
print()

say(
    "  想让协程真正跑起来，需要一个「事件循环」，最省事的入口是 asyncio.run：",
    f"    asyncio.run(quick_task()) → {asyncio.run(quick_task())!r}",
    "",
    "  规律记这三条：",
    "    1. 异步函数只能被 await，或者在事件循环里跑",
    "    2. await 只能写在 async def 里面",
    "    3. 程序的入口用 asyncio.run(...) 起一个事件循环，只写一次",
)

say(
    "",
    "  「程序的入口」指哪儿？就是最开始被执行的那段代码——脚本里是模块顶层那几行，",
    '  更规范的写法是放进 if __name__ == "__main__": 里面。',
    "",
    "  为什么强调「只写一次」：asyncio.run 做的是一整套动作——",
    "    新建一个事件循环 → 把协程跑完 → 关掉这个循环",
    "  所以有两件事不能做：",
    "    · 不能在已经跑着循环的地方再调它，会报",
    "      RuntimeError: asyncio.run() cannot be called from a running event loop",
    "    · 也不该到处各写一个，每处都新建又销毁一个循环，白白浪费",
    "  正确做法是：入口跑一次，把所有异步工作都塞进这一个循环里，",
    "  要并发就在里面用 gather —— 就像第 1 节那两个函数。",
    "",
    "  什么时候不用自己写？",
    "    Web 框架（FastAPI 之类）自己会起循环，你的 async 视图函数只管被它调用；",
    "    在视图函数里写 asyncio.run 会直接撞上上面那个报错。",
    "    Jupyter / IPython 里本来就有循环在跑，直接 await 就行。",
    "",
    "  本文件为了方便一节一节地看，在顶层写了好几个 asyncio.run；",
    "  教学脚本这样写没问题，真实项目请收成一个 main()，只在入口调一次。",
)

say(
    "",
    "  这个「调用不执行」的脾气，和上一份演示里的生成器一模一样——",
    "  在 Python 里它们本来就是同一套机制的两种用法，一行一行对照着看：",
    "",
    "    调用它得到什么：生成器 → generator 对象；协程 → coroutine 对象",
    "    谁让它跑起来：  生成器 → next() / for；",
    "                    协程 → await / asyncio.run / asyncio.gather",
    "    跑到一半会停：  生成器 → 停在 yield，把值交出去；",
    "                    协程 → 停在 await，等结果拿回来",
    "    怎么接着跑：    都从刚才停下的地方继续",
    "    能用几次：      都只能一次",
    "                    （生成器遍历完就空；协程重复 await 会报",
    "                     RuntimeError: cannot reuse already awaited coroutine）",
    "",
    "  但方向是相反的：生成器「往外给」，协程「往里等」。",
    "  协程停在 await 上的这段空档，控制权交回事件循环，它就能去推另一个协程——",
    "  三个请求同时在飞，就是这么来的。这也是它和生成器最大的区别所在。",
    "",
    "  两者交汇的地方在最后一节：async def 里同时写 await 和 yield，",
    "  就是「异步生成器」，用 async for 消费。",
)


# ============================================================
section("3. 最容易犯的错：该 await 的地方忘了 await")
# ============================================================

say(
    "  忘了 await 的后果很隐蔽：不报错，但什么都没发生。",
    "  先做个实验：下面 inner_task 里有两行 print，看它们什么时候出现。",
)
print()


async def inner_task() -> str:
    print("      【inner_task 开始跑】")
    await asyncio.sleep(0.05)
    print("      【inner_task 跑完】")
    return "inner_task 的结果"


async def forgot_await() -> None:
    say("  ① 写了 await：")
    result = await inner_task()
    say(f"      拿到：{result!r}")
    print()

    say("  ② 忘了 await：")
    unawaited = inner_task()  # 只造了个协程对象，函数体一行都没跑
    say(f"      拿到：{unawaited!r}")
    say("      上面那两行【】出现了吗？没有——函数体压根没开始跑，")
    say("      连它内部那句 await 也没轮到执行。")
    unawaited.close()  # 收尾，避免解释器提示「协程从未被 await」


asyncio.run(forgot_await())
say(
    "",
    "  所以要分清两件事：「函数里写了 await」和「await 被执行了」。",
    "  async 函数被调用时只造出一个协程对象，函数体要等到被 await、",
    "  或者交给事件循环（asyncio.run / gather）之后才开始跑——",
    "  这跟「调用生成器函数不执行函数体」是同一个道理。",
    "",
    "  怎么认出来：日志里如果出现 <coroutine object ...>，多半就是漏了 await。",
    "  另一个线索是运行结束时 Python 会提示「coroutine ... was never awaited」——",
    "  上面第 ② 段如果去掉 close()，你就会看到这条警告。",
)


# ============================================================
section("4. 为什么必须用 asyncio.sleep，而不是 time.sleep")
# ============================================================

say(
    "  这两个看起来一样，但一个会让出控制权，另一个会把整条流水线堵死。",
)


async def blocking_fetch(name: str, delay: float) -> str:
    """错误示范：在异步函数里用同步的 time.sleep。"""
    time.sleep(delay)  # noqa: ASYNC251  ← 故意写错：事件循环会在这里停住
    return f"{name} 的结果"


async def call_with_blocking() -> float:
    start = time.perf_counter()
    await asyncio.gather(*(blocking_fetch(name, delay) for name, delay in TOOLS))
    return time.perf_counter() - start


blocking_time = asyncio.run(call_with_blocking())
say(
    f"  用 time.sleep 并发三个 0.4 秒的任务，耗时 {blocking_time:.2f} 秒",
    f"  用 asyncio.sleep 同样三个任务，耗时 {together_time:.2f} 秒",
    "",
    "  明明写了 gather（并发），却还是排着队跑完了——因为 time.sleep 期间",
    "  事件循环无法切换到别的任务，所有并发都失效了。",
    "",
    "  所以异步代码里有一条硬规矩：**不要调用阻塞式函数**。",
    "  网络请求要用 httpx.AsyncClient 而不是 requests；",
    "  读文件这种暂时没有异步版本的活，可以丢给线程池执行（知道有这回事即可）。",
)


# ============================================================
section("5. async for：处理流式响应")
# ============================================================

say(
    "这是什么：异步版的生成器 + 异步版的 for。",
    "为什么需要：模型流式返回时，「下一个字」要等网络送来，",
    "           所以产出和消费都必须是异步的。",
    "场景：所有聊天产品边生成边显示的效果，底层就是这个写法。",
)
print()


async def stream_reply(text: str, delay: float = 0.03):
    """异步生成器：一个字一个字地产出。"""
    for char in text:
        # asyncio.sleep(秒)：异步等待，等的期间把控制权让给别的任务
        # （这里不能换成 time.sleep，那会把整个事件循环堵住）
        await asyncio.sleep(delay)
        yield char


async def print_stream(text: str) -> None:
    async for char in stream_reply(text):
        print(char, end="", flush=True)


say("  边等边打印：")
print("    ", end="")
asyncio.run(print_stream("杭州今天 22 度，多云。"))
print()
say(
    "",
    "  和同步版生成器的区别只有两处：函数是 async def，循环是 async for。",
    "  openai / httpx 这些库的流式接口都是这个形状：",
    "    async with client.stream(...) as response:",
    "        async for chunk in response.aiter_text():",
    "            ...",
)


# ============================================================
section("6. 什么时候不该用异步")
# ============================================================

say(
    "  异步只解决一类问题：IO 等待。它不适合另一类问题：算得慢。",
    "",
    "    IO 密集（等网络、等磁盘）  → 异步有效，等的时候能去干别的",
    "    CPU 密集（大量计算、图像处理）→ 异步无效，因为 CPU 一直在忙着，",
    "                                  没空切换；这种情况要用多进程",
    "",
    "  判断方法很朴素：这段代码主要时间花在「等」上，还是花在「算」上？",
    "  等 → 异步；算 → 多进程（了解即可，Agent 开发里绝大多数瓶颈都是等）。",
)


# ============================================================
section("7. gather 的两个细节")
# ============================================================

say(
    "  一、返回顺序和传入顺序一致，不是「谁先回来谁在前」。",
    "     下面故意让第一个最慢，看结果顺序：",
)


async def slow_first() -> str:
    await asyncio.sleep(0.3)
    return "慢的（第一个）"


async def fast_second() -> str:
    await asyncio.sleep(0.05)
    return "快的（第二个）"


async def gather_order_demo() -> list[str]:
    """在一个协程里调用 gather。"""
    return list(await asyncio.gather(slow_first(), fast_second()))


results = asyncio.run(gather_order_demo())
say(
    f"     结果：{results}",
    "     快的那条虽然先返回，但位置没变——这让你不用操心结果和输入的对应关系。",
    "",
    "  提醒一个真实的坑：gather 必须在协程「里面」调用。",
    "  写成 asyncio.run(asyncio.gather(a(), b())) 会报 no current event loop——",
    "  因为括号里的参数在进入事件循环之前就被求值了，那时还没有循环可用。",
    "  正确写法就是上面这样：先包一层 async def，再在里面 await gather。",
    "",
    "  二、其中任何一个抛异常，gather 会把异常抛出来（其他任务已经在跑了）。",
    "     需要「谁成功用谁」时，用 return_exceptions=True 收集，或者逐个任务处理。",
)


# ============================================================
section("8. 要注意什么")
# ============================================================

say(
    "  1. 异步函数里别调用阻塞函数（time.sleep、requests、普通文件读写），",
    "     那会让并发全部失效——第 4 节量给你看了。",
    "  2. await 只能写在 async def 里；程序入口用一次 asyncio.run。",
    "  3. 日志里看到 <coroutine object ...>，基本就是漏了 await。",
    "  4. 别用异步去解决 CPU 密集的问题，那里帮不上忙。",
    "  5. 调试异步代码时，报错信息里的调用栈会比较长，从最后一行往前读。",
    "  6. asyncio.run 只等它拿到的那一个主协程。主协程一结束，循环就关掉了——",
    "     用 asyncio.create_task 起的后台任务如果没人 await，会被直接取消。",
    "     这个坑很安静：任务没跑完就没了，屏幕上一条提示都没有。",
    "     要等它，就放进 gather，或者自己 await 一下。",
)


section("总结")
say(
    "1. 异步解决的是「等网络时 CPU 闲着」这件事，不是让 CPU 变快",
    "2. async def 返回协程对象，await 才会真的执行并取回结果",
    "3. asyncio.gather 并发发起多个任务；结果是按传入顺序排的",
    "4. async for 消费异步生成器——模型流式回复就是这个形状",
    "5. 异步代码里绝不能有阻塞调用，否则并发形同虚设",
)
