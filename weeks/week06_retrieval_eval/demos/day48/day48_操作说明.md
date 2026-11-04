# Day48｜先固定选择，再检查留出

预计约 1/2 个自然日、2～3 小时。今天主要练习是冻结前的选择、六份回答的判读和阶段报告；没有新代码题。
AI 运行环境复用旧实现，学员不必重写 Day46 的批量循环。六道留出题仍保留 holdout 标签。

## 按这个顺序做

1. 跑 `day48_freeze_demo.py`，理解为什么看过结果后再改参数就属于继续开发。
2. 填 `day48_choice.json`：selected_group 填 `"vector"` 或 `"fused"`；reason 用一句话说明开发证据。可以复用 Day47 自己写过的选择理由。
3. 跑 freeze，只保存选择与版本，不执行留出检索。保留打印的 freeze 目录。
4. 跑 run，传同一个 freeze 目录：本地检索六题，两组都评分；只给事先选定的一组生成六份回答，最多六次请求。
5. 在 run 目录读 `review_pack.md`，填 `reviews.json` 的 reviewed、answer_ok、citation_ok。沿用 Day47 口径；reason 可选，有具体缺项时简记一句即可。
6. 六份判分完成后跑 report，传同一次 run 目录。告诉 AI 跑好了，由 AI 转录客观数据，再写 `day48_报告.md` 第 3 节。

下面命令均从仓库根目录运行；入口也支持从别处使用完整脚本路径运行。
`--freeze-dir`、`--run-dir` 若用相对路径，一律按仓库根目录解释。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\demos\day48\day48_freeze_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\demos\day48\day48_holdout.py --part freeze
```

下一条会真实请求回答模型。把占位文字替换成刚才打印的完整目录；需要时 AI 会给出已填好的命令。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\demos\day48\day48_holdout.py --part run --freeze-dir '这里填 freeze 目录' --live
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\demos\day48\day48_holdout.py --part report --run-dir '这里填 run 目录'
```

## 每份输出在哪里

每次 freeze/run/report 都在 `day48/outputs/` 下新建目录，保留配置、console.log、run_info.json，失败也不覆盖历史。

| 阶段 | 文件与用途 |
|---|---|
| freeze | frozen.json：选择、理由、资料/代码摘要、参数、依赖版本及模型配置；不含密钥 |
| run | holdout_started.json：开始查看本批结果的时间及已有检查目录；不是未见结果的自动证明 |
| run | retrieval_rows.jsonl / retrieval.json：逐题排名、指标、两组汇总及检索阶段耗时 |
| run | responses.json：六份实际回答或错误、用量和生成调用耗时；原样保留 |
| run | review_pack.md：只读的期望、全文依据、候选、实际回答与实际引用 |
| run | reviews.json：人工判断；reviewed=true 后才可正式汇总，JSON 的空值写 null |
| report | report.json / reviews_snapshot.json：同一次 run 的客观汇总与判分快照 |

## 比较边界

- 开发检索是 Day46 的 24 题两组；开发回答是 Day47 有目的选出的 4 题两组，不混称整批开发回答正确率。
- 本日留出检索为 6 题两组；留出答案、引用、token 与生成费用只描述所选方案，另一方案没有生成，不能当成 0。
- 两组共用一次向量检索。vector 计问题编码与向量查询；fused 在这段时间上加关键词排名和 RRF 的耗时。均不含模型加载、建库、人工判分与生成，不能当作独立线上请求的端到端延迟。
- 生成计时与费用沿用 Day47：耗时只包住生成调用；费用按 2026-11-03 的固定价格版本给范围，不是实际账单，缺失不补零。
- 请求失败也保存、计数。若同配置复测，另开新轮并保留旧轮，不跨轮挑答案；看过结果后改方案则注明这批题已参与开发。
- 冻结检查能发现无意的文件/参数变化，不能证明人从未手动看过结果；不把它当作严格防作弊系统。

## 旧函数查阅入口

- `demos/shared/evaluation_functions.py`：project_relevance 映射依据；rank_keywords / fuse_rankings 排名；check_ranked_ids 检查编号；score_query / evaluate_queries 评分。
- `demos/shared/answer_functions.py`：组装输入、检查 JSON/出处、换算费用，以及本日使用的 summarize_reviews（Day47 已验收实现，六键结构和边界见该函数 docstring）。
- `demos/day47/day47_support.py`：AI 的 collect_answer、write_review_pack、resource_summary，负责原始输出和计时，不判断语义。

`probe --live` 仅供 AI 用一条人工资料验证相同请求环境，不使用六道留出题，不是学员必做实验。
