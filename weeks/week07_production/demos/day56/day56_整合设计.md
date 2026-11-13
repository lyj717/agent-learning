# Day56｜整合设计（先写清楚，再写代码）

2026-11-11。Day56 目标：把已经验收的零件接成一个能跑、能查、能讲的服务，并完成口头解释与交接。
预计约 1 个自然日，分两步：

- **A（本次，约 30～40 分钟）**：写整合设计，不写代码；
- **B（下一次，约 3～4 小时）**：按设计实现、跑 1/5/10 并发梯度、查一次失败 trace、写交接。

先读下面零件，再回答五个问题。答完告诉 AI，批改通过后再进入 B。

## 可用零件

| 零件 | 位置 | 接口与作用 |
|---|---|---|
| 旧 RAG | `demos/shared/rag_functions.py` | `answer_with_trace(question, retrieve_fn, request_fn, emit) -> dict`，同步，失败抛原异常 |
| 阶段追踪 | `exercises/day53_span_exercises.py` | `trace_stage(tracer, request_id, stage, action)`，同步，正常返回、失败标 ERROR 再抛 |
| 窗口限额 | `exercises/day54_rate_limit_exercises.py` | `WindowLimiter(limit, window)`，`await acquire()`，没名额就等 |
| 并发上限 | `asyncio.Semaphore(n)` | `async with sem`：同时最多 n 份在跑 |
| 重试 | `exercises/day54_retry_exercises.py` | `call_with_retry(action, job_id, attempts=3, base_delay=0.05)`，async，action 也是 async |
| 错误映射 | `exercises/day55_error_exercises.py` | `error_response(exc, request_id) -> (status, body)` |
| 会话历史 | `demos/shared/service_functions.py` | `create_chat_app` 里的字典与 `/sessions/.../history` |
| 运行环境 | `demos/day53/day53_trace_runtime.py` | `local_tracing(run_dir)` 给出 tracer |

## 五个问题

**1. 一次成功请求的顺序**

从 HTTP 进入 FastAPI 开始，到返回 JSON 结束，按顺序列出经过的组件（校验、窗口限额、并发上限、
追踪、RAG、写历史、返回）。写成一行箭头链，例如：
`请求 → 校验 → …… → 返回`。

作答：请求 -> 校验 -> 并发上限 -> 窗口限额 -> 追踪（RAG)  -> 写历史 -> 返回

**2. 三个限制/失败机制放哪里**

窗口限额、并发上限、重试分别放在链路的哪一步？为什么是这个顺序（谁在外层、谁在内层）？

作答：先并发上限再窗口限额，再重试：
并发上限管“同时有几份逻辑工作在跑”，放外层；
窗口限额管“单位时间内开始几次”，放在每次尝试前；
重试在最内层，所以重试会重新占窗口名额。

**3. trace 的范围**

span 应该包住哪一段？一次请求发生两次重试，是 1 个 span 还是 3 个？`request_id` 应该写在哪、
为什么它能把日志和 span 对上？

作答：包住action，发生两次重试是3个，`request_id`应该写在span的属性里，因为日志里也带同一个 request_id，所以能从日志找到 span，反之亦然

**4. 失败路径**

RAG 抛 `TimeoutError` 时：谁捕获、映射成什么状态码、返回体里有什么、这次请求要不要写历史？
如果重试两次后仍失败，和第一次就失败，处理上有区别吗？

作答：错误映射来捕获，映射成504，返回体里是细节和request_id。不写历史
重试两次后失败”和“第一次就失败”最终处理一样，都是抛最后一次异常、映射 504，区别是耗时更长、多占了两个窗口名额。

**5. 并发梯度的预期**

按 1、5、10 三档并发打同一个服务（窗口限额 2 次/秒、并发上限 2），你预期分别先撞到哪个限制？
怎么从 `/health`、响应状态、trace 和日志判断瓶颈在哪一层？

作答：1不会撞限制，5会撞窗口限额，10可能会超时
/health 仍然秒回说明进程没被拖死；
状态码都是 200、只是变慢说明在排队；
trace 里 span 时长仍很短，但请求总耗时很长说明等待发生在 span 外面，也就是限额/信号量；
日志时间戳能看出请求是陆续开始的。

