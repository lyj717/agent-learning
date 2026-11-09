# Day54｜并发控制前置与练习记录

2026-11-08 开工。Day54 整体暂估约 1～1.5 个自然日，包含此前预留的复习缓冲，
每天仍按 3～5 小时；不是每个子段各用 1～1.5 天，实际学时未测。
本次只先做下面两道约 10～15 分钟的异步前置短检验。

## A：旧异步知识短检验（先闭卷，不运行）

这些语法在 Week00 Day06 做过。本节判断是否需要先补课，不假设见过就已熟练。
代码都在普通 Python 脚本中运行，不涉及 FastAPI、模型或 HTTP 请求。
回忆不起来可以写“不确定”，先不要翻旧源码、查文档或运行代码。
下面每段代码各自独立；在题目后的作答区写判断，不需要新写函数。

### 1. 函数调用、执行与返回结果

```python
import asyncio

events: list[str] = []


async def read_notice() -> str:
    events.append("read")
    return "二楼"


async def main() -> str:
    pending = read_notice()
    events.append("created")
    answer = await pending
    events.append("received")
    return answer


result = asyncio.run(main())
```

写出 result 的值、events 最后的排列顺序。再说明：
  result:""二楼" events:["created","read","received"]
- 执行 `pending = read_notice()` 后，pending 接到的是函数本身、一个待执行对象，
  还是字符串“二楼”？
  一个待执行对象
- read_notice 的函数体是在上面哪一步开始执行的？
  await pending


### 2. 并发结束顺序与结果顺序

```python
import asyncio

finished: list[str] = []


async def read_piece(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    finished.append(name)
    return name


async def main() -> list[str]:
    values = await asyncio.gather(
        read_piece("书架资料", 0.03),
        read_piece("门口通知", 0.01),
    )
    return values


result = asyncio.run(main())
```

假设两次等待均正常到期，没有额外阻塞或异常：

- 写出 finished 与 result 各自的顺序，说明它们为什么可能不同。
  finished:["门口通知","书架资料"] result: ["书架资料", "门口通知"]
  finished按delay的大小顺序，result看传给 gather 的参数位置
- 如果把 `await asyncio.sleep(delay)` 这一整行换成 `time.sleep(delay)`，
  并补上 `import time`，两个调用还能在等待期间交替推进吗？解释原因即可，
  不要求猜测具体毫秒数。
  不能交替推进，只能串行进行，因为time.sleep不是并发函数，阻塞了运行事件循环的线程，等待期间其他协程无法继续执行

## B：共享并发上限

先看两个小演示：名额管理、异步动作调用；再在
`../../exercises/day54_concurrency_exercises.py` 中只实现 call_with_limit。
题面已列出动作来源、调用方法、返回值和三种场景，不需要先读验收器。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 完成结果 | 来源确认 |
|---|---|---|---|
| Semaphore 演示 | `outputs/semaphore_demo_20261109_161700_839776_a85f934f` | completed，断言通过 | 学员确认亲跑 |
| 异步动作演示 | `outputs/async_action_demo_20261109_180556_117436_5ea9b4de` | completed，断言通过 | 学员确认亲跑 |
| 并发上限练习 | `outputs/concurrency_exercise_20261109_182934_003489_c7ccaa20` | 3/3 通过 | 学员确认亲跑 |

| 场景 | 配置名额 | 实际最大同时执行数 | 每份动作调用次数 | 结束时运行数 | 名额恢复 | 原结果/异常保持 |
|---|---|---|---|---|---|---|
| normal_one | 1 | 1 | 各 1 次 | 0 | True | True |
| normal_two | 2 | 2 | 各 1 次 | 0 | True | True |
| error_then_next | 1 | 1 | 各 1 次 | 0 | True | True |

练习组的异常类型为 `["TimeoutError"]`，失败均未触发防挂起超时（`timed_out` 为 False）。

每轮 run_info.json 保存入口、来源、配置、源码摘要和完成状态，console.log 保存实际与期望。
两个演示分别有 semaphore_demo.json、async_action_demo.json；练习有逐组 JSON 和
concurrency_checks.json。峰值取 peak_active，次数取 action_calls，结束数取 active_at_end，
名额取 slots_restored，原对象取 originals_match，不要求手抄终端全文。
这些是本机人工等待的实际行为；模型和 HTTP 调用均为 0，不当作真实服务商性能。

### 观察与判断（学员填写）

1. normal_one 与 normal_two 都有四份工作，各自的最大同时执行数是多少？
   结合输出解释“总任务数”和“正在占名额的任务数”的区别；为什么块内 await 等待期间，
   这份工作仍应占着名额？

   作答：分别是1和2，总任务数是总共需要完成的任务数，正在占名额的任务数是当前占据名额的任务数
   如果不算占着名额，让其他任务进入就会导致任务数失控

2. error_then_next 的失败资料抛出什么异常，后面两份是否仍执行？
   根据原异常保持、调用次数、结束时运行数和名额恢复解释：
   后续工作能继续，是因为吞掉了异常，还是因为归还了名额、由调用方汇总异常？

   作答：TimeoutError，后面两份依然执行
    后续工作能继续是因为归还了名额并由调用方汇总异常
    原异常会被原样抛出给调用方，调用次数每个任务都为1，说明都继续工作了，结束时运行数为0以及名额恢复=True说明任务在结束或异常后会主动结束占用，

## 后续状态

速率限制与旧重试组合后段再交付，当前不预填运行数据、观察或结论。
Day51B/Day52 到期复验仍在 11 月 9～10 日窗口；本节是更早的异步知识回温，
不能代替那两项复验。Day53 的延迟复验在 11 月 10～11 日，均未提前记通过。
