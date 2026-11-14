# Week 08｜评测、可靠性与成本

**阶段交付物**：自动评测集 + 可复现的回归检查 + GitHub Actions CI 回归报告，
外加一份按瓶颈选择的成本/延迟优化对照与失败模式清单。

## 当前接续：Day58 已验收（2026-11-14），下一步 Day59

Week07 已完成（服务化主线与 Day56 整合），交接见
[Week07 HANDOFF](../week07_production/HANDOFF.md)。按交接建议，本周先盘点
Week06 已有的评测资产，再定基线与留出、最后才接 CI，不先换模型、不先做优化。

Week06 可直接复用的资产：

- 30 条标注（24 dev、6 holdout）与固定原文快照：`week06_retrieval_eval/demos/day44/`
- 片段级指标 `score_query`、`evaluate_queries`：`demos/shared/evaluation_functions.py`
- 人工回答判分与 `summarize_reviews`：`demos/shared/answer_functions.py`
- 运行留证工具 `run_logged`：`demos/shared/run_logs.py`（本周继续复用，不重写）
- Day47 的判分口径（回答完整性与引用支持分开、判分只针对实际跑过的题）

Week07 留的尾巴不在本周重做：真实 RAG/SSE 组合、工具授权接入 HTTP、真实服务商
负载都仍按原记录如实标记。本周只在评测与回归这条线上使用已有的离线组件。

## 本周排期：7 个自然日

**2026-11-13 订正**：上一版把「约 4 个自然日的工作量估计」直接当成了排期跨度，只排四天。
一个 Week 按 7 个自然日铺开；四天只是工作量基准，不是计划长度。本页按七天重排。

四天排不下本周必做：成本与延迟若合并成一天，就只能「量一下、顺手改一下」，
无法先测瓶颈再做同批对照；失败模式、CI 与阶段验收挤在同一天，CI 也没有时间等
推送后的真实运行。所以补三天，而不是把四天摊薄。每天仍按 3～5 小时；
本周约 5.5～6.25 天学习工作量，7 天里留 0.75～1.5 天缓冲（复习、排错、补课），
不把缓冲当成必须填满的任务。

| 单元 | 主要任务 | 主机制 | 预计自然日 |
|---|---|---|---|
| Day57 | 规则匹配判分 + 冻结基线回归；观察与记录（已开工） | 规则判分 | 约 3/4～1 天 |
| Day58 | 模型裁判：评分项、结构化输出；学员先独立判 8 题，再与裁判逐题对齐、抽样分歧 | LLM-as-judge | 约 1 天 |
| Day59 | 成本与延迟的基线测量：每题费用、P50/P95、首字延迟，按证据定瓶颈 | 测量与归因 | 约 1 天 |
| Day60 | 按瓶颈实施**一项**优化，同批前后对照，写清收益、代价与适用条件 | 成本或延迟优化 | 约 1 天 |
| Day61 | 失败模式清单五类，每类一条真实证据与可自动检查的判据；接进 pytest | 失败模式与检查 | 约 3/4～1 天 |
| Day62 | GitHub Actions：离线测试、手动 live 入口、预算说明；推送后观察一次真实运行 | CI 接入 | 约 1/2～3/4 天 |
| Day63 | 阶段变式（含 Week07 Day54～56 复验）、三件套口头解释、HANDOFF | 阶段验收 | 约 1/2 天 |

合计约 5.5～6.25 天工作量，7 天跨度内留 0.75～1.5 天缓冲。只做一项成本或延迟优化（Day60），
另一项只做到能测量、能解释；不铺开四种成本手段，也不做第二种延迟优化。

真实模型调用集中在 Day58～60，手动 `--live`，每单元 8～12 次，失败也保留日志；
Day58 开工前单独确认预算。CI 只跑离线确定性检查，不让每次提交花钱。

## Day57：规则判分与冻结基线（2026-11-13 开工，11-14 验收）

**完成情况**：`judge_answer` + `compare_baseline` 已实现并验收，A 14/14、B 9/9，
两版回归对比与四道观察已完成，[记录](demos/day57/day57_记录.md) 的客观数据已转录。
补第 9 组乱序输入后，学员补上返回前 `sorted()`；引用行号与每题规则字段表也按实际数据补齐。

先读演示，再做题：

1. [规则判分演示](demos/day57/day57_rule_judge_demo.py)：规则层判什么、为什么先做它、
   以及「全部命中却把做法说反了」的盲区。
2. [基线对比演示](demos/day57/day57_baseline_diff_demo.py)：baseline 是什么、
   四类变化、为什么总通过数会骗人、CI 该拦哪一类。
3. 打开 [题目说明](demos/day57/day57_题目说明.md) 与
   [练习](exercises/day57_eval_exercises.py)，实现 A 的 `judge_answer`；
   `--part a` 全过再写 B 的 `compare_baseline`；最后跑 `--part regression`。

补充：对 `compare_baseline` 的双层循环有疑问时，跑
[按键查找演示](demos/day57/day57_lookup_demo.py)（约 5 分钟），看比较次数从 16 次
降到 4 次；不影响验收。

从仓库根目录运行（全部离线，`model_calls=0`）：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day57\day57_rule_judge_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day57\day57_baseline_diff_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day57_eval_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day57_eval_exercises.py --part b
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day57_eval_exercises.py --part regression
```

预期：A 为 14 组结果 + 14 组输入检查，不一致 0；B 为 9 + 9，不一致 0；
regression 打印 v1/v2 各题结果、通过数、基线自检与四类变化。
基线自检的 regressed 与 fixed 应为空，still_failing 应保留基线里的已知失败
（q02、q08）——它检验你的判分器重放 v1 时和冻结基线是否同一口径，
不是要求四类全空。

每次运行在 `demos/day57/outputs/` 下新建目录，保存 `console.log`、`run_info.json`；
regression 另存 `regression.json`。失败也保留，不覆盖历史。
`DAY57_RUN_ORIGIN` 默认 `unconfirmed`；AI 验证标记 `ai_validation`，不冒充分学员亲跑。

数据文件与全部判分情形见 [题目说明](demos/day57/day57_题目说明.md)；
本轮 8 题、两版回答与基线都是教学数据，不是新的真实模型评测。

## Day58：模型裁判与解析（2026-11-14 开工，11-14 验收）

**完成情况**：A 10/10、B 10/10；人工判读 8 题后跑裁判 8 次，解析失败 0；
答案一致 8/8、引用一致 7/7。q08 在「回答没有引用」时被裁判给了 `true`，
违反评分项，已在记录观察 2 单列。四道观察经一轮修改后通过。
被裁判的是 Day57 的 8 份回答，今天没有重新生成回答；原估约 1 天，实际学习小时未测。

顺序：

1. [裁判口径演示](demos/day58/day58_judge_rubric_demo.py)：评分项怎么拆、
   为什么用二值 + 理由、裁判的偏差与成本。
2. [解析演示](demos/day58/day58_parse_demo.py)：代码块、前后解释文字、缺键与
   类型错误分别怎么处理。
3. 实现 A 的 `build_judge_messages`，`--part a` 10/10；再实现 B 的
   `parse_judge_verdict`，`--part b` 10/10。
4. 先填 [人工标签](demos/day58/day58_human_labels.json)：8 题答案对错、引用支持、
   简短理由。**先人工、后裁判**，没有引用的题 `citation_ok` 填 `null`。
5. 单题试跑 `--part live --limit 1`（1 次），再全量 `--part live`（8 次）；
   两次均完成，解析失败 0，原始返回已保存。
6. `--part compare` 完成：答案一致 8/8、引用一致 7/7；观察写在
   [记录](demos/day58/day58_record.md)，q08 的规则违背也在那里。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day58\day58_judge_rubric_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day58\day58_parse_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day58_judge_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day58_judge_exercises.py --part b
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day58_judge_exercises.py --part live --limit 1
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day58_judge_exercises.py --part live
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day58_judge_exercises.py --part compare
```

预算：单题试跑 1 次 + 全量 8 次 = **9 次调用**，在计划的 8～12 次内；不自动重试。
每次运行在 `demos/day58/outputs/` 下新建目录，保存 `console.log`、`run_info.json`；
live 另存 `judge_results.json`，compare 另存 `agreement.json`。
字段、全部判分情形与标签规则见 [题目说明](demos/day58/day58_题目说明.md)。

## 复验安排

Week07 交接留下的 Day54～56 跨天复现（限额、重试、整合，10～15 分钟闭卷变式）
并入 Day63 阶段变式，不单独占一天；未发生之前不勾选。Day57 的机制在 Day60
开工时用 10～15 分钟复现一次判分口径（不重做整题）；阶段末再换情境做变式。

## 必做顺序

- [x] Day57：规则判分 + 基线回归，14 + 9 组对照与四道观察
- [x] Day58：模型裁判、与人工判分逐题对齐、抽样分歧
- [ ] Day59：成本与延迟基线、瓶颈判断
- [ ] Day60：按瓶颈做一项优化，同批前后对照
- [ ] Day61：五类失败模式清单与自动判据，接进 pytest
- [ ] Day62：GitHub Actions、推送后观察一次真实运行
- [ ] Day63：阶段变式（含 Day54～56 复验）与口头解释

## 验收标准

- 能说清规则匹配、模型裁判、人工判分各判什么、代价是什么、何时该用哪一层
- 被问「怎么保证 Agent 上线不出事」时，能拿出评测集、trace 与失败清单三件套
- 有一批可重复的评测与冻结基线；改坏一题时能被 `regressed` 抓住，而不是只看总数
- 成本与延迟各有基线数据；只做的那一项优化有同批前后对照，写清收益、代价与适用条件
- 失败模式清单来自真实记录，每条能指向一次运行或一份日志
- CI 只跑离线检查；真实模型评测保留手动入口与预算说明，且观察到一次远端运行
- 阶段报告写清任务成功率、引用质量、用量与延迟，并注明样本来源与判分口径
- 能说明这些检查能发现什么、仍有哪些覆盖不到的风险，不承诺「测试通过就绝不出错」

## 范围与暂不做

- 不重做 Week06 的标注与检索对比；不重跑 24 题真实检索。
- 不换模型、不调提示词追求分数；Day60 只按实测瓶颈做一项优化，
  另一个维度只做到能测量、能解释。
- 分级路由、上下文压缩、缓存、并行工具与预取按证据选用，不要求全接；
  已有优化解决主要瓶颈时，优先保留稳定版本与回归证据。
- 不接第二套追踪工具，不新增向量库或线上部署。
- GitHub Actions 的真实触发需要推送后才能在仓库页看到；本机只验证
  workflow 的 YAML、命令与离线测试，未观察到远端运行前不声称 CI 已通过。
- `FAILURES.md` 继续由 AI 维护；学员从真实记录里选能讲清的故障，不为数量制造案例。
