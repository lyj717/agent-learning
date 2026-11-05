# Week 06 交接文档

交接日期：2026-11-04。下一会话先读根 `AGENTS.md`、本文件，再读 Week 07 计划与实际进度。

## 一句话状态

Day 43～49 完成当次验收：在 Week 05 的 RAG 上把样本扩展到 30 条（24 条 dev、6 条 holdout），
完成片段级 Hit/Recall/Precision、关键词 + RRF 融合、24 题开发检索对比、4 题开发回答与引用、
6 题留出检查及阶段报告。Day49 的新情境变式和 3 分钟口头解释通过。
本次验收不等于跨天独立掌握，延迟复验见文末。

本周交付物：[Day48 阶段报告](demos/day48/day48_报告.md)；控制变量对比与各层数据见
[Day46 记录](demos/day46/day46_记录.md)、[Day47 记录](demos/day47/day47_记录.md)。

固定资料是 `notes/python-notes.md` 的 137 行快照，8 行/重叠 2，共 23 块；每路最多 3 条，
最终 k=3，融合常量 60。开发集 24 题（19 有答案、5 无答案），留出集 6 题（5 有答案、1 无答案），
原十题只能算开发集，不能和新 24 题直接比均值。

## 现在能跑什么

以下命令从仓库根目录运行。Day43～46 的对照检查主要离线；Day48 的 report 读取已保存的一轮，
不再请求回答模型。

```powershell
# Day43：A 16 组、B 12 组人工对照
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day43_metrics_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day43_metrics_exercises.py --part b

# Day44：30 条标注完整性；预期开发集 24、留出集 6、待填 0
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day44_labels_exercises.py --part validate --require-complete

# Day45：A 23 组、B 20 组；q07 单题探查
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day45_hybrid_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day45_hybrid_exercises.py --part b
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day45_hybrid_exercises.py --part probe --case q07

# Day46：24 道开发题的整合对照；batch 会加载本地向量模型，不请求回答模型
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\exercises\day46_compare_exercises.py --part a

# Day48：读取已保存的六题 run，重出 report；不新增模型请求
.venv\Scripts\python.exe -B -X utf8 weeks\week06_retrieval_eval\demos\day48\day48_holdout.py --part report --run-dir 'weeks\week06_retrieval_eval\demos\day48\outputs\run_20261104_150911_210806_658d0a56'
```

预期：Day44 显示开发 24、留出 6、待填 0；Day45 A 23/23、B 20/20；Day46 A 24/24；
Day48 report 复现 fused 6/6、引用 5/5，留出检索 vector/fused 为 0.8/1.0（mean_hit）。
Day48 的 `--part run --live` 会真实请求六次，且六题留出已经使用；没有新版本和新留出时不要重跑。

## 环境与已知边界

- Windows，解释器 `.venv\Scripts\python.exe`（Python 3.13.9），配置在根 `.env`；
  回答模型 `deepseek-flash`，嵌入模型 `BAAI/bge-small-zh-v1.5`（512 维、COSINE、本地缓存）。
- 依赖新增 `rank-bm25==0.2.2`；`fastembed 0.9.0`、`qdrant-client 1.19.1`、`openai 3.19.2` 沿用前几周。
- `outputs/` 被 `.gitignore` 忽略，原始 run/report、console 与 responses 只在本机；Markdown 记录保留结论和摘要，
  Git 克隆不会恢复原始日志。换机器时需要另行保留 `demos/day48/outputs/` 等目录。
- pytest 临时目录仍有权限问题：12 项中 3 项不依赖 `tmp_path` 的测试通过，9 项在初始化/清理时报 WinError 5；
  两个测试临时目录删除也被拒。管理员删除命令见 `FAILURES.md` 的 2026-11-04 条目。
  不要把残留当作测试通过或失败证据。
- Day48 本地提交 `ff627cb`；Day49 收尾另作本地提交。推送由学员自己执行。

## 留的尾巴

- **延迟复验都还没有发生，不能勾选**：Day45 在 11 月 4～5 日、Day46/47 在 11 月 5～6 日、
  Day48 在 11 月 6～7 日或满足间隔的学习日，各做 10～15 分钟新情境判断；阶段末再做变式。
- 六道留出题（q25～q30）已经在 Day48 使用并暴露。若根据这次结果改参数、改提示词或改方案，
  这批题应记为参与开发；要做干净检查必须另找新留出题，并在看结果前冻结方案。
- 原十题旧基线继续保留，不重跑覆盖；它已参与开发，不能和新 24 题直接相减。
- 目前最明确的反例是 q01：Day46 中 fused 的 Recall 从 vector 的 1.0 降到 0，Day47 的 q01/fused
  回答也被判错、没有引用。下一步先查 q01 的 `keyword_ids` 为什么漏掉相关块、RRF 怎样把向量第 3 名挤出前 3。
- Day48 报告的建议是**暂定保留融合**：开发检索 vector 略高，开发回答两组 3/4 但错题不同，
  留出检索 fused 更好；留出只有 fused 回答 6/6、引用 5/5，没有 vector 回答对照。
  六题、单次运行，不能把结论外推成“融合全面更好”。
- 费用按固定高峰价换算范围，不是实际账单；检索与生成分开计时，都不是端到端延迟。
  Day47 的 503/超时/中断轮次和 Day48 的 0 失败都保留，不跨轮挑答案。
- Day49 阶段变式与口头解释通过，但仍不等于跨天独立掌握；跨天复验按上面的窗口做。

## 下一周目标与第一步

2026-11-04 Day50 开工接续：本交接列出的 Day48 临时目录权限残留已在沙箱外清理，
旧实验日志保持。当天新验证在沙箱外为 12 passed；原 Day48 的失败证据不回写为通过。
Week07 已按下述建议从请求关联和结构化阶段日志开始，当前任务见其 README。

下一阶段是 **Week 07 工程化与可观测性**，交付“带 trace 的服务”。第一步不要继续加检索优化；
先读 `docs/ai-agent-12周学习计划.md` 的 Week 07 部分，再从 Week05/06 已有 RAG 入口中选一条请求路径，
补请求 ID、结构化日志和一次可核对的 trace，再决定是否包装成服务。Week06 的复验与留出边界继续保留。
