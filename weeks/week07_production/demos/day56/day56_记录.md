# Day56｜整合验收与交接记录

2026-11-11 开工。Day56 约 1 个自然日：先设计（已完成），再实现整合函数（B1），
然后接 HTTP 服务、跑 1/5/10 梯度、查失败 trace、写交接（B2）。

## B1：整合函数 serve_question

先读 [整合设计](day56_整合设计.md)，再在
[整合练习](../../exercises/day56_integration_exercises.py) 实现 `serve_question`；
五组情形（success、retry_then_ok、exhausted、fatal、concurrency）与期望写在题面里。

### 客观运行数据

| 情形 | 实际调用次数 | 异常 | span 检查 | 通过 |
|---|---|---|---|---|
| success | | | | |
| retry_then_ok | | | | |
| exhausted | | | | |
| fatal | | | | |
| concurrency | | | | |

数据取 integration_checks.json 与各情形目录下的 trace_summary.json。

### 观察与判断（学员填写）

1. 为什么 `action` 要放进 `asyncio.to_thread`？直接调用会让 concurrency 那组出现什么结果？

   作答：因为action是一个同步函数，不放进asyncio.to_thread就会导致异步形同虚设没有任何效果，直接调用会出现同时最多只有1份在跑

2. 为什么 `request` span 包住整个重试循环，而 `answer` span 每次尝试一个？

   作答：request span负责整个请求，answer span负责单次重试，这样既能知道是哪个请求出错也能知道是具体哪一次重试出错

## B2：服务、并发梯度与失败 trace

[day56_gradient.py](day56_gradient.py) 会自动启动 [day56_app.py](day56_app.py)，依次跑
1/5/10 三档并发，再发一次“超时”请求，并按 `request_id` 从 `spans.jsonl` 里找回它的 trace。

### 客观运行数据

| 档位 | 总耗时 | 最大耗时 | 最小耗时 | 状态码 |
|---|---|---|---|---|
| 1 | 60.4ms | 60.2ms | 60.2ms | 200 |
| 5 | 802.6ms | 802.0ms | 7.9ms | 200 ×5 |
| 10 | 2332.1ms | 2331.1ms | 303.3ms | 200 ×10 |

| 失败请求检查项 | 实际结果 |
|---|---|
| 状态码与 detail | 504，`上游超时` |
| request_id | `d39a4016ce7842bd9b23205385881046` |
| 对应 span 数与结构 | 4 个：1 个 `request` 根段 + 3 个 `answer`，同一 trace |
| answer 状态与耗时 | 三个都是 ERROR；0.61、0.477、0.236ms |
| request 耗时 | 509.639ms |

原始输出在 `outputs/day56_gradient_*/` 的 `console.log`、`gradient.json`、`spans.jsonl`。

### 观察与判断（学员填写）

1. 5 档和 10 档里，为什么最大的请求耗时和最小的请求耗时差很多？

   作答：最小的请求不需要等待窗口，而后面窗口不够用了，花费了大量时间在等待窗口上

2. 失败请求的 `request` span 约 510ms，三个 `answer` 都不到 1ms，时间花在哪几段？

   作答：request中等待窗口的时间，失败后的delay等待时间，其中窗口等待占了大头

## 后续状态

Day56 完成：整合设计、B1（5/5）、B2（1/5/10 梯度与 504 trace）、
[口头问答要点](day56_口头问答.md) 与 [本周交接](../HANDOFF.md) 均已交。
尾巴：真实 RAG/SSE 组合、工具授权接入 HTTP、真实服务商负载与额度验证。
下一步 Week08：评测、回归与成本优化。
