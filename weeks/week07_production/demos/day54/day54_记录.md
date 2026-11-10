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

## C：时间窗口内的开始次数（2026-11-09）

先读 [窗口限额演示](day54_rate_limit_demo.py)（从 demonstrate_async 读起），
再在 [C 练习](../../exercises/day54_rate_limit_exercises.py) 实现 `WindowLimiter.acquire`；
入口会并发提交三组，按开始时刻判断是否超窗口。

- 演示与练习都是本机人工计时，不请求模型或 HTTP；窗口只有 0.15～0.2 秒，只为看清先后。
- 固定窗口只保证单进程内每个窗口最多 limit 次开始：它不等于“任意连续 window 秒内
  最多 limit 次”的滑动窗口，也不代表分布式限流或服务商的 429 行为。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 完成结果 | 来源确认 |
|---|---|---|---|
| 窗口限额演示 | `outputs/rate_limit_demo_20261109_210533_524866_b66bf63f` | completed | 未确认（unconfirmed） |
| C 练习 | `outputs/rate_limit_exercise_20261109_222756_620529_867dec87` | 3/3 通过 | 学员确认亲跑（按日志转录） |

| 场景 | limit / window | 实际开始时刻（秒） | 任意窗口内最多开始 | 全部执行 | 总耗时（秒） | 通过 |
|---|---|---|---|---|---|---|
| two_per_window | 2 / 0.2 | 0.0001, 0.0001, 0.2014, 0.2014, 0.4018 | 2 | True | 0.402 | True |
| one_per_window | 1 / 0.15 | 0.0001, 0.1542, 0.3111 | 1 | True | 0.311 | True |
| idle_reset | 3 / 0.15 | 0.0001×3, 0.2011×3 | 3 | True | 0.201 | True |

开始时刻取 start_times，峰值取 max_in_any_window，是否全部执行取 all_started，
总耗时取 elapsed；逐组 JSON 和 rate_limit_checks.json 都在本轮目录里。

### 观察与判断（学员填写）

1. B 的 `normal_two` 是“同时 2 个”，C 的 `two_per_window` 是“0.2 秒内 2 次开始”。
   两处都写着 2，它们限制的是同一件事吗？结合两边输出说明区别。

   作答：不是同一件事，normal_two是一个时刻内最多同时处理两个事件，two_per_window是每0.2秒限制最多只能有2个事件开始

2. 演示里的错误示范 B 五份都执行了，结果却违规。你的实现在等不到名额时靠什么避免这一点？
   如果把“睡醒后重新判断”去掉，会在上面哪一行的数据里暴露？

   作答：先睡，睡醒后重新判断； 任意窗口内最多开始这一数据

## D：重试的次数与异常边界（2026-11-10）

先读 [重试边界演示](day54_retry_boundary_demo.py)（从 demonstrate_async 读起），
再在 [D 练习](../../exercises/day54_retry_exercises.py) 实现 `call_with_retry`；
六种情形、期望调用次数和期望间隔都写在函数题面里，不需要打开检查器。

- 演示与练习用的都是人工判定的错误，不请求模型或 HTTP。
- 本节不接窗口限额；“重试会再占一个开始名额”由观察 2 回答。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 完成结果 | 来源确认 |
|---|---|---|---|
| 重试边界演示 | `outputs/retry_boundary_demo_20261110_181523_910445_b53c9a63` | completed | 学员确认亲跑 |
| D 练习 | `outputs/retry_exercise_20261110_190446_747852_a5d16f0e` | 6/6 通过 | 学员亲跑（按日志转录） |

| 情形 | attempts / base | 实际调用次数 | 实际间隔（秒） | 返回或异常 | 通过 |
|---|---|---|---|---|---|
| ok_now | 3 / 0.05 | 1 | 无 | 返回字典 | True |
| timeout_then_ok | 3 / 0.05 | 2 | 0.053 | 返回字典 | True |
| exhausted | 3 / 0.05 | 3 | 0.061, 0.109 | RateLimitedError | True |
| bad_request | 3 / 0.05 | 1 | 无 | BadRequestError | True |
| value_error | 3 / 0.05 | 1 | 无 | ValueError | True |
| attempts_one | 1 / 0.05 | 1 | 无 | TimeoutError | True |

调用次数取 calls，间隔取 intervals，结果取 result / error_type；
逐组 JSON 与 retry_checks.json 都在本轮目录里。

### 观察与判断（学员填写）

1. exhausted 组的调用间隔是多少？为什么不是每次都等 0.05 秒？次数用完时抛出的是哪一个对象？

   作答：实际为[0.061, 0.109],如果每次都等0.05秒，所有的异常都在0.0.5后重试反而可能加重负担，次数用完时抛出的是最后一次的异常

2. 把一次重试看成一次新的“开始”，一份失败两次才成功的工作，在“每 0.5 秒 1 个名额”的窗口里
   会占掉几个名额？这会让整体等待变长还是变短？结合 C 的窗口规则说明。

   作答：总共占三个名额，会让整体等待变长，每 0.5 秒 1 个名额并且一次重试看成一次新的“开始”的话每次重试就至少需要等待0.5秒后才能开始

## 后续状态

D 已六组通过，两道观察已核对；Day54 已收尾。下一步是 Day53 延迟复验（11 月 10～11 日窗口）
与 Day55 的安全失败路径、容器与最简页面；Day51B/Day52 的到期复验已在 11 月 9 日核对
（经提示与订正）。
