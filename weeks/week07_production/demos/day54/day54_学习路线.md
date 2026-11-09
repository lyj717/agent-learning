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
两道观察核对通过，题面已清理）。速率控制的独立演示与后段练习尚未交付。
新回调会在题面写清谁提供、怎样调用/等待、返回结构、异常、跳过条件和次数，
不会要求先读验收器。旧同步重试代码不会未经讲解就塞进异步函数。

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
