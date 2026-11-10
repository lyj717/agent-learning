# Day54 学习路线

## 当前目标与预计跨度（2026-11-08）

Day53 已验收并完成本地提交。Week07 要把 Agent 做成有调用记录、能控制负载的服务；
Day54 负责理解并限制同时执行的工作数量，再区分时间窗口内允许开始多少次请求。
它不要求重新实现旧 RAG、SSE、会话存储或追踪工具。

**整个 Day54 暂估约 1～1.5 个自然日，每天仍按 3～5 小时。** 包含此前预留的复习缓冲、
异步知识回温、读演示、独立实现、运行排错、观察与订正，不是各子段各用这份时间。
原计划表约半天只作为历史初估保留，未计足长期未用的异步知识和接收异步动作的迁移成本。
这不是实测耗时或必须完成的时限；前置暴露缺口时先补课，再缩减重复并重估剩余量。

- 第一个自然日：先核对旧异步知识，必要时用独立小演示补齐；再学并发上限、
  共享同一个限制器及结束/异常后的名额归还，完成一个小应用练习。
- 需要的后半个自然日：区分速率限制与并发上限，接续旧重试的次数和异常边界，
  做小规模离线对照。一次只交付一个主要新机制，不把整套业务服务同时接入。

新知识先在本机人工任务中验证，不调用模型或真实服务商做压力测试。
真实端口下的负载、整条服务组合和瓶颈结论在阶段整合验证，不能用离线等待冒充真实模型性能。

## 本次先做什么

前置已核对：第 1 题首答正确，第 2 题 gather 顺序和阻塞原因经反馈订正通过，原作答保留。
本例较短等待先完成；一般仍以实际执行 append 的先后为完成顺序，不是列表自动按 delay 排序。
现在接 B；只引入共享并发上限，不同时加每秒限速、重试、HTTP 或 trace。

1. 先运行 [Semaphore 独立演示](day54_semaphore_demo.py)，从 demonstrate_async 读起。
   看对象在哪里创建、名额何时占用与归还、locked 表示什么，以及名额用尽时怎样等待。
2. 再运行 [异步动作调用演示](day54_async_action_demo.py)，分清 action、调用后对象和 await 后结果。
   示例中的函数赋值只展示来源；练习由入口直接传入函数，不要在自己的实现中重新赋值。
3. 在 [B 练习](../../exercises/day54_concurrency_exercises.py) 只实现 call_with_limit。
   创建共享对象、并发提交、动作、统计和汇总均已实现；题面旁列出全部接口，不需看验收器。
4. 亲跑三组后，在 [记录的 B](day54_记录.md) 写两道观察。客观数据确认亲跑后由 AI 转录。

本次建议先看完两份小演示；理解后再写练习，不要求一次做完 B。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_semaphore_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_async_action_demo.py
# 函数写好后运行
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day54_concurrency_exercises.py
```

所有入口从任意目录运行都把新日志保存到本单元 outputs；本节没有需要安装的新包。
Semaphore 演示保存 locked 的实际状态、等待先后与异常后归还；异步动作演示保存实际类型与结果。
练习保存 concurrency_checks.json 和每组 JSON，表格所需字段都能直接取得；失败也保留日志。

## B 的接口与边界

`asyncio.Semaphore(value=1)` 返回名额管理对象；本练习由调用方创建并共享，不在学员函数里重建。
`async with semaphore:` 先等待并取得一个名额，块内可 await；退出时自动归还，异常继续传出。
`locked()` 不带参数，返回是否无法立即取得名额的 bool，不能把 False 当作没有任务占用。
本节共享同一事件循环内同一个对象，不据此声称跨进程总上限。

`action` 是已写好的 async 函数，接收当前 job_id 字符串；`await action(job_id)` 一次后拿到
`{"job_id": str, "answer": str}` 原字典。Callable 表示可调用，Awaitable 表示调用后可等待；
两个注解均从 collections.abc 导入，练习已启用。普通动作的返回规则与新异步接口不能混用。
完整异常和次数契约在函数旁。异常由调用方汇总，不要求包装器把它变成成功字典。

并发数统计的是“取得名额后、动作尚未结束”的份数，包括动作内部正在 await 的时间。
正常组各四份工作，共享 1 与 2 个名额对照；失败组共享 1 个名额，首份失败后另两份仍执行。
只需完成一个包装函数，自己决定受控块的范围；不要求重写批量调度或安装新框架。

需要直观看过程时，可运行 [gather 顺序小演示](day54_gather_order_demo.py)，先读 demonstrate_async。
它只交换两次调用的传入位置，显示传入顺序、实际完成顺序和返回列表，不引入并发限制器。
无须新增观察表，也不要求把控制台全文抄回记录。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_gather_order_demo.py
```

每轮独立保存 console.log、run_info.json 与 gather_order.json；模型和 HTTP 调用均为 0。
AI 交付前验证单独标 ai_validation，不认定学员亲跑或预填短检验答案。

这是 Week00 Day06 的旧知识换输入：调用 async 函数后拿到什么、await 何时执行，
gather 的结果顺序和阻塞等待的影响。旧练习中已写过这些内容，不据此假设现在仍熟练。
若仍混淆函数、待执行对象和最终结果，先单独回温，不直接进入异步回调的整合题。

Semaphore 与异步动作小演示和 B 练习已交付；B 已于 2026-11-09 验收（学员亲跑 3/3，
两道观察核对通过，题面已清理）。
新回调会在题面写清谁提供、怎样调用/等待、返回结构、异常、跳过条件和次数，
不会要求先读验收器。旧同步重试代码不会未经讲解就塞进异步函数。

## C 的接口与边界（2026-11-09 交付）

先跑 [窗口限额演示](day54_rate_limit_demo.py)（从 demonstrate_async 读起），
再在 [C 练习](../../exercises/day54_rate_limit_exercises.py) 只实现 `WindowLimiter.acquire`。

`WindowLimiter(limit, window)` 的字段在 `__init__` 已就位：`limit` 是每个窗口允许开始的次数，
`window` 是窗口长度（秒），`lock` 保护计数，`window_start` 为 None 表示还没开窗，
`count` 是本窗口已放行几次。`await acquire()` 无参数、无返回值：有名额就占一次并立即返回；
名额用完要等到下个窗口；每次调用最终都要返回，不能丢工作或忙等。时间用
`asyncio.get_running_loop().time()`，sleep 必须在锁外。

三组检查：`two_per_window`（2 次、0.2 秒、5 份）、`one_per_window`（1 次、0.15 秒、3 份）、
`idle_reset`（3 次、0.15 秒；先 3 份，停 0.2 秒再来 3 份，第二批不该等）。
判定看任意窗口内最多开始几次、是否每份都执行、总耗时是否达到应有的等待。

边界：固定窗口在相邻两窗交界处最多可放 2×limit 次，它不是滑动窗口；本节只做单进程内计数，
不涉及 429、重试、HTTP 或跨进程共享。旧重试的次数与异常边界，以及“重试再次占用窗口配额”，
放在下一学习日。

关于锁：本题临界区里没有 `await`（读时间、判断、`count += 1`），在单线程事件循环里不会被别的
任务插队，所以当前实现里锁不是必需的。保留它是为了以后临界区出现 `await`（例如查共享存储、
等另一个限额器）时仍然正确；那时没有锁，两份额外的工作会同时看到“还有一个名额”。

## 2026-11-10 补课：异步调度前置（约 2～2.5 小时）

C 的代码已 3/3、观察已核对，但学员反馈锁、共享状态与“谁调用这个函数”还没弄懂，暂不提交。
学员另指出：此前的演示和练习都由 AI 搭好环境，自己只写被调用的函数，从没创建过 Task。
因此补课里单独加一份 Task 演示和一道动手题。

先读四份独立演示，每份只回答一个问题：

1. [任务交替](day54_task_order_demo.py)：一个线程里两个任务怎么在 await 处轮流；
2. [调用与 Task](day54_await_states_demo.py)：调用 async 函数、create_task、await 各做了什么；
3. [Task 对象](day54_task_object_demo.py)：Task 的类型、done()/result()/exception() 和异常重新抛出；
4. [什么会挂起](day54_suspend_points_demo.py)：哪些 await 会换人、哪些不会。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_task_order_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_await_states_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_task_object_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_suspend_points_demo.py
```

再完成两份练习：

- [三道预测题](../../exercises/day54_async_predict_exercises.md)：先写输出判断，再运行核对，不写新函数；
- [Task 动手练习](../../exercises/day54_task_exercises.py)：亲手 `create_task` 一个任务，并让两个任务真正并发，
  检查器会看返回类型、`done()` 状态、结果顺序和总耗时。

补完确认后清 C 题面并提交，旧重试边界随后接。补课不改变 C 的已通过结论，
也不把 C 重做成新题。

## D 的接口与边界（2026-11-10 已验收）

先跑 [重试边界演示](day54_retry_boundary_demo.py)（从 demonstrate_async 读起），
再在 [D 练习](../../exercises/day54_retry_exercises.py) 实现 `call_with_retry`。

签名：`call_with_retry(action, job_id, *, attempts=3, base_delay=0.05) -> dict[str, str]`。
`action` 是入口提供的 async 函数，接收 `job_id`，成功返回 `{"job_id","answer"}`；
入口会在六种剧本下调用你的函数，每次尝试调用一次 `action`。

规则：`TimeoutError`、`ConnectionError`、`RateLimitedError` 可重试；`BadRequestError`、
`ValueError` 及其他异常立刻原样抛出；可重试但还有次数时，第 n 次失败后等
`base_delay * 2 ** (n - 1)` 秒；次数用完抛出最后一次的异常对象。

六种情形（ok_now、timeout_then_ok、exhausted、bad_request、value_error、attempts_one）
的 action 行为、期望调用次数与期望间隔，都列在练习函数的题面里，不需要打开检查器。

边界：本节不接窗口限额，也不涉及 429、HTTP 或真实服务商；“一次重试再占一个开始名额”
用记录里观察 2 回答。旧同步重试的代码保留原处，不要求重写或搬运。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day54\day54_retry_boundary_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day54_retry_exercises.py
```

验收结果：六组 6/6（间隔 0.061、0.109 秒），不可重试错误各只调用一次，
两道观察已核对。首版把退避写成累加（第二次等 0.15 秒），检查器当时的容差 +0.1
放过了它；容差收紧到 +0.03 后暴露并订正。Day54 到此完成。

## 与其他安排的关系

原来预留在 Day53 后、Day54 前的约半日复习缓冲纳入本次前置，按实际缺口安排，
不额外加一轮同构练习凑满时间。旧知识已能解释的部分不要求重抄或重跑。
11 月 9～10 日再接 Day51B/Day52 的到期短复验；11 月 10～11 日再接 Day53，
尚未发生不记完成。本次异步短检验不替代这些延迟复验。

限流、重试与并发上限仍是本周必做范围；安全、容器、最简页面、502/504 与服务整合
按原来的后续单元推进，开工时另估完整学习量。Week07 约四天是协调目标，
不能用省略必要前置或延长每日学习时间维持初估。

## 核对后去哪看资料

前置已核对，旧知识资料按需查阅；B 的官方阅读只围绕本次使用的 API。

- [Python 3.13 Coroutines and Tasks](https://docs.python.org/3.13/library/asyncio-task.html)：
  只看 Coroutines、Sleeping、Running Tasks Concurrently，分别核对调用与执行、
  等待时的调度和 gather 的结果顺序；暂不扩展 TaskGroup、取消、线程或跨线程调度。
- [Python 3.13 Semaphore](https://docs.python.org/3.13/library/asyncio-sync.html#semaphore)：
  B 只看 Semaphore 一节，核对 value 参数、async with、acquire/release 和 locked 的含义；
  不扩展其他同步原语。它对应演示中的名额管理，不代替练习的回调契约。
