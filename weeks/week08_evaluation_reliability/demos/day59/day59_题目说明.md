# Day59 题目说明：成本与延迟基线

本页是 [练习](day59_measure_exercises.py) 的完整题面：调用点、全部判分情形、
现场运行步骤与预算。完整规则在下面 A、B 两节；练习文件已清理为函数与类型注解。

## 量什么

| 指标 | 计时边界 | 用途 |
|---|---|---|
| `retrieval_ms` | 从编码问题开始，到检索返回候选结束 | 判断检索是不是瓶颈 |
| `ttft_ms` | 从发起生成请求，到第一个非空正文 delta | 用户看到第一个字的等待 |
| `generation_ms` | 从发起生成请求，到流结束 | 生成总耗时 |
| `end_to_end_ms` | 检索 + 生成 | 用户等完整回答的时间 |
| `prompt_tokens` / `completion_tokens` | 流式响应的 usage | 分清输入贵还是输出贵 |
| `cost_cny` | token × Day47 价格快照 | 单题费用，不是账单 |

索引固定：`notes/python-notes.md`，8 行/重叠 2、检索前 3 条；模型与资料都不换。
费用按 `day47_price_snapshot.json` 的统一高峰价换算，不推断实际计费时段。

## A：`percentile(values, p)`

调用点：`report` 入口与你的 `summarize_measurements` 都会调用它。
方法固定为**最近秩**：排序后取第 `ceil(p/100 × n)` 个（从 1 起）。

| # | 输入 | 期望 |
|---|---|---|
| 1 | `[10,20,30,40]`，P50 | `20.0` |
| 2 | `[10,20,30,40]`，P95 | `40.0` |
| 3 | `[5]`，P50 | `5.0` |
| 4 | `[40,10,30,20]`，P75 | `30.0` |
| 5 | `[1,2,3]`，P100 | `3.0` |
| 6 | P0 | `ValueError` |
| 7 | P101 | `ValueError` |
| 8 | 空列表 | `ValueError` |
| 9 | `[1, True, 3]` | `ValueError`（bool 不算数字） |
| 10 | `p=True` | `ValueError` |

## B：`summarize_measurements(rows)`

调用点：`report` 入口读取 `measurements.json` 后调用一次。
`rows` 每项至少含上面七个测量字段；返回值恰好这些键。**每个指标是两个独立的键，
不是嵌套字典**：`retrieval_p50` 与 `retrieval_p95` 分开，不能写成
`{"retrieval": {"p50": ..., "p95": ...}}`。

| 键 | 类型 | 含义 |
|---|---|---|
| `count` | `int` | 样本数 |
| `retrieval_p50` / `retrieval_p95` | `float` | 检索耗时百分位 |
| `ttft_p50` / `ttft_p95` | `float` | 首字耗时百分位 |
| `generation_p50` / `generation_p95` | `float` | 生成耗时百分位 |
| `end_to_end_p50` / `end_to_end_p95` | `float` | 端到端百分位 |
| `prompt_tokens` / `completion_tokens` | `int` | 合计 |
| `total_tokens` | `int` | 两者之和 |
| `total_cost` | `float` | 费用合计 |
| `mean_cost` | `float` | `total_cost / count` |

判分情形：

| # | 输入 | 期望 |
|---|---|---|
| 1 | 三行样本 | 各百分位、token 与费用按最近秩/求和得出 |
| 2 | 单行样本 | 各 P50 与 P95 都等于该行值 |
| 3 | 空列表 | `ValueError` |
| 4 | 缺 `cost_cny` | `ValueError` |
| 5 | `ttft_ms` 是字符串 | `ValueError` |
| 6 | 真实测量行带 `id`、`raw_text` 等附加键 | 仍按必需字段汇总，附加键忽略 |
| 7 | `rows` 不是 list | `TypeError` |

提示：先做参数与字段校验，再算；百分位复用 A，不要另写一套排序口径。

## 现场运行与预算

1. 离线检查：`--part a` 应 10/10，`--part b` 应 7/7。
2. 单题试跑：`--part live --limit 1`（1 次调用），确认检索、首字、用量都有值。
3. 全量：`--part live`（8 次调用），保存 `measurements.json`。
4. 汇总：`--part report`，读逐题表与 P50/P95。
5. 重复测量：`--part repeat`（3 轮 × 8 题 = 24 次调用），看同题波动，再写记录。

预算：单题 1 次 + 全量 8 次 + 重复 24 次 = **33 次调用**。失败不自动重试；
失败题写进 `errors`，不影响其他题。

## 重复测量（`--part repeat`）

单次测量分不开「真实差异」和「网络/排队噪声」，所以再跑 3 轮：
第 1 轮 q01…q08，第 2 轮再一遍，第 3 轮再一遍，共 24 次。索引只建一次；
每行带 `round`；第 1 轮同时充当预热。

输出 `repeat_measurements.json`，并打印每题的首字与端到端 `min/median/max`。
读法：先看同题三次的跨度；若跨度大于你预期的优化收益，单次前后差异不能当结论，
要用中位数或再增加轮次。三次不算独立样本，汇总 P95 时说明这是按题重复。

## 跑完看什么

`--part live` 每题打印检索、首字、生成、用量与费用；失败题单独列出。
`--part report` 打印逐题表与 `count`、token 合计、P50/P95、总费用与单题均值。
`--part repeat` 打印每题次数与首字/端到端的 min/median/max，并保存
`repeat_measurements.json`。
观察写在 [记录](day59_record.md)；每次运行在 `outputs/` 下新建目录，失败也保留。
