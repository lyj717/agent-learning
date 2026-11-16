# Day60 题目说明：缩小证据的前后对照

本页是 [练习](day60_optimize_exercises.py) 的完整题面：改动、调用点、
全部判分情形、现场步骤与预算。完整规则在下面 A 节；练习文件已清理为函数与类型注解。

## 这次只改什么

| 配置 | 每块行数 | 重叠 | 检索条数 | 单题证据行数上限 |
|---|---|---|---|---|
| baseline | 8 | 2 | 3 | 24 |
| optimized | 4 | 1 | 2 | 8 |

同一个向量模型、同一批 8 题、同一次会话；每轮交替先后顺序：
第 1 轮 baseline→optimized，第 2 轮反过来，第 3 轮再 baseline→optimized。

注意：这里同时动了「切块大小」和「检索条数」两个变量，属于一个压缩包。
若结果有变化，不能单独归因给其中一个；需要拆开时另做单变量对照。

## 数据形状（先看这里）

`measure` 的 `rows` 是两套条件混在一起的，每行带 `condition`、`round`、`id`。
按条件过滤后，**每个题号会出现 3 次**（默认 3 轮），不是每题一行：

```text
condition=baseline, round=1, id=q01, end_to_end_ms=1247
condition=baseline, round=2, id=q01, end_to_end_ms=1455
condition=baseline, round=3, id=q01, end_to_end_ms=1289
condition=baseline, round=1, id=q02, ...
```

所以 A 的输入是「每个 id 多行」的基线行和优化行。先按 id 分组，把每组三个
`ttft_ms`、`end_to_end_ms`、`cost_cny` 各取中位数（标准库
`statistics.median`，练习文件已导入），得到每题一个代表值；
再配对两套条件算差值。直接对 48 行求和/平均会把轮数和离群值混进来。

## A：`compare_conditions(baseline, optimized)`

调用点：`report` 入口把同一次 `measure` 的两组行传进来，各调用一次。

| # | 输入 | 期望 |
|---|---|---|
| 1 | 两题各两轮 | 逐题中位数、差值、整体均值与费用合计按定义算出 |
| 2 | 单题单轮，两套相同 | 差值为 0 |
| 3 | baseline 为空 | `ValueError` |
| 4 | 两边题号集合不同 | `ValueError` |
| 5 | 缺 `cost_cny` | `ValueError` |
| 6 | 输入不是 list | `TypeError` |

返回结构：

```text
{
  "questions": [
    {"id", "baseline_ttft", "optimized_ttft", "ttft_delta",
     "baseline_end_to_end", "optimized_end_to_end", "end_to_end_delta",
     "baseline_cost", "optimized_cost", "cost_delta"}, ...
  ],
  "baseline_mean_end_to_end", "optimized_mean_end_to_end", "end_to_end_delta_mean",
  "baseline_total_cost", "optimized_total_cost", "cost_delta_total"
}
```

差值统一用 `optimized - baseline`，负数表示优化后更低。逐题先取中位数，
再对题求平均/求和。输入含 `id`、`ttft_ms`、`end_to_end_ms`、`cost_cny`。

## 现场运行与预算

1. 离线检查：`--part a` 应 6/6。
2. 成对测量：`--part measure`（3 轮 × 2 套 × 8 题 = **48 次调用**）。
3. 质量检查：`--part quality`（Day57 规则 + Day58 裁判，**16 次裁判调用**）。
4. 对照报告：`--part report`（离线，读测量算差值）。

合计 **64 次调用**（48 + 16），费用约 0.15 元；失败不自动重试，
失败记录写进 `errors`，不影响其他行。索引只建一次。

## 跑完看什么

`--part measure`：两组各自的首字/端到端/费用中位数；失败行单独列出。
`--part quality`：逐题的规则通过情况、裁判 `answer_ok`/`citation_ok`，
以及两套配置各自的通过数。
`--part report`：逐题端到端与费用差值、整体均值、费用合计。

质量判读顺序：先看规则与裁判的通过数是否下降；再看下降的题是哪一题、
少了哪段证据；最后人工抽查不一致的题。没有下降才能谈「采纳」。

观察写在 [记录](day60_record.md)；每次运行在 `outputs/` 下新建目录，失败也保留。
