# Day46｜同一批开发题的控制变量对比

状态：2026-11-02 开工，预计约半个自然日、2～3 小时，含短复验、独立整合、排错、亲跑与观察。
本次对照是同一次运行的“仅向量”与“向量 + 关键词经 RRF 融合”，不是拿上周十题平均值比较本周新题。
资料快照、23 个片段、开发题、标注、每路与最终 k=3 固定，rank_constant=60。
只运行 24 道开发题；6 道留出题继续保留。真实批量已于 2026-11-02 亲跑，客观结果见第 2 节。
2026-11-03 三道观察经答疑订正通过，Day46 完成本次验收；原估时间不是实测耗时。
当前：A 于 2026-11-02 经答疑与订正完成代码验收，AI 人工对照的结果、输入保持、回调次数各 24 组全部通过。
学员已确认真实 batch 亲跑，输出完成并核对。11 月 3 日补齐整批指标、q03 案例依据与无答案计数后验收，
详细反馈在聊天，学员原答保留；不记为独立首答或跨天掌握。

## 1. Day43 到期短复验（先闭卷 10～15 分钟）

先写完本节再看旧函数和演示。若看过旧答案，请如实注明。
本次状态：2026-11-02 经反馈与订正完成本次复验。数值已改正；Recall 分母的“候选数量”称谓在聊天补明为全部标注相关片段数，保留学员原答。不记为独立闭卷首答通过。

1. 新情境的相关编号为 `{甲, 乙, 丙}`，候选排名为 `[丁, 乙]`，k=3。
   写出 retrieved_count、matched_count、Hit@3、Recall@3、Precision@3，说明两个分母。

   我的回答：retrieved_count = 2, matched_count = 1, hit = 1, 
   recall = 0.33, 分母为3，是全部标注相关片段数 precision = 0.33，分母为3，是k的值

2. 现在汇总一批两道检索问题，k=3，条件如下：
   问题 A：原文有答案，预先标注的相关编号为 `{甲, 乙, 丙}`，本次检索实际返回 `[丁, 乙]`（沿用第 1 小题的情境）。
   问题 B：已确认原文没有答案，本次检索实际返回 `[丁]`。
   这批题的 mean_recall、answerable_count、no_answer_count、no_answer_with_candidates 分别是什么？
   问题 B 进入哪个计数，是否进入 mean_recall 的平均？

   我的回答：mean_recall = 0.33 ,answerable_count = 1, no_answer_count = 1, no_answer_with_candidates = 1
   B进入 no_answer_count和no_answer_with_candidates，不进入mean_recall 的平均

## 2. 本次运行依据（确认亲跑后由 AI 读取日志转录）

数据入口：练习 `--part a` 的 console.log；`--part batch` 的 console.log、run_info.json、
report.json 与 vector_calls.jsonl。每次使用新目录，失败也保留。

| 核对项 | 实际结果 |
|---|---|
| A 人工对照、输入不变及回调次数检查 | 本次 batch 的前置检查：24/24 组结果、24/24 组输入保持、24/24 组回调次数均通过，不一致=0；见下方 console.log |
| 本次日志目录、来源及状态 | batch_20261102_222543_590948_483bd721；2026-11-02 22:25:43～22:25:45，state=completed；学员于本次对话确认亲跑，原始 origin=unconfirmed 保留 |
| 原文、标注、代码与公共函数版本摘要 | SHA256 前 16 位：原文 923b660e3d09527c；标注 46b7b4312e2597f7；练习 292fd976fce5b9e6；公共函数 fb5bfc2809599bce；运行环境 b12c3b05a5ff7ccc。完整值见 run_info.json；匹配亲跑版本。11 月 3 日收尾仅清练习题干，执行逻辑不变，原日志摘要不回写 |
| 开发题数、有答案/无答案题数，实际检索题号 | total=24，answerable_count=19，no_answer_count=5；实际检索 q01～q24，每题一次，共 24 次；q25～q30 留出题未检索 |
| 仅向量：mean_hit / mean_recall / mean_precision | 0.894737 / 0.815789 / 0.438596 |
| 融合：mean_hit / mean_recall / mean_precision | 0.842105 / 0.815789 / 0.438596 |
| 两种方案的 no_answer_with_candidates | 仅向量 5；融合 5（无答案题总数均为 5） |
| 按 Recall 逐题比较：提高、相同、下降的有答案题号 | 提高 2 题：q08、q14；相同 15 题：q02、q03、q04、q05、q09、q11、q12、q13、q15、q16、q17、q18、q19、q20、q21；下降 2 题：q01、q07。无答案 5 题单列，不计入这 19 题 |

原始文件：[控制台](outputs/batch_20261102_222543_590948_483bd721/console.log)、
[配置与版本](outputs/batch_20261102_222543_590948_483bd721/run_info.json)、
[逐题结果和汇总](outputs/batch_20261102_222543_590948_483bd721/report.json)、
[24 次向量检索记录](outputs/batch_20261102_222543_590948_483bd721/vector_calls.jsonl)。
表内均值保留六位小数，完整数值见 report.json。

固定配置：8 行/重叠 2，共 23 块；每路最多 3 条，最终 k=3，rank_constant=60；
词项规则 zh-char-ascii-v1。向量模型 BAAI/bge-small-zh-v1.5，512 维，embed 方式、COSINE；
rank-bm25=0.2.2，fastembed=0.9.0，qdrant-client=1.19.1。generation_calls=0。
本轮两组共用每题的一次新向量检索，原始来源标记与日志不回写。
AI 仅读取保存的排名和检索记录，复核相关映射、RRF、单题指标、汇总和版本，没有重新检索或请求回答模型。

## 3. 我的观察

1. 本次 batch 比较的是“仅向量”和“向量 + 关键词经 RRF 融合”两种方案。
   两种方案得到最终候选的方式有什么区别？哪些输入和设置保持相同，所以能逐题比较？
   本轮仅向量对照组与上周十题旧基线有什么关系？

   我的回答：向量组：把 vector_ids 直接作为最终候选 融合组：把同一份 vector_ids 与 keyword_ids 交给 RRF，用得到的 fused_ids 作为最终候选
   评分机制，limit等都一致所以能逐题比较
   问题范围变大了，检索方法依旧不变，候选来源是重新检索得到了，不过与旧结果相同

2. 根据两种方案的汇总和逐题结果，说明整批开发题效果的变化。
   从 report.json 选一题，引用相关编号及两份候选解释变化；没有提高或下降时如实写，不为凑案例改参数。

   我的回答：总体开发题效果不太大，提高2道题，下降2道题，还有15道题相同
   选择Q3，      
   "vector_ids": ["notes/python-notes.md#L49-L56","notes/python-notes.md#L43-L50","notes/python-notes.md#L91-L98"],
   "fused_ids": ["notes/python-notes.md#L49-L56","notes/python-notes.md#L43-L50", "notes/python-notes.md#L85-L92" ],
   平均hit：0.894737 → 0.842105，下降 平均recall：0.815789 → 0.815789，持平  平均precision：0.438596 → 0.438596，持平
   q03的标注相关片段是：notes/python-notes.md#L43-L50和notes/python-notes.md#L49-L56
   两组都找回了这两块，所以均为 matched_count=2、Hit=1、Recall=1、Precision=2/3。换掉的第三条在两组中都不属于标注相关项，因此候选编号变了，指标没有变化。
3. 无答案题返回候选的计数有什么变化？本报告只保存检索结果，没有模型最终回答。
   仅凭候选排名与检索指标，能否判断最终回答是否正确、是否漏答，或引用片段是否支持回答中的具体说法？
   根据本次证据，你建议暂时保留还是回退融合方案，理由是什么？

   我的回答：Q6
   "vector_ids": ["notes/python-notes.md#L1-L8","notes/python-notes.md#L7-L14", "notes/python-notes.md#L43-L50"],
   "fused_ids": ["notes/python-notes.md#L1-L8","notes/python-notes.md#L7-L14", "notes/python-notes.md#L91-L98" ],
   两组的 no_answer_with_candidates 都是 5
   还不能判断最终回答是否正确、是否漏答，或引用片段是否支持回答中的具体说法
   目前建议先保留，虽然目前效果相近，但还没有进入最终模型回答
   