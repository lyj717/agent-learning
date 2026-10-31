# Week 05 交接文档

交接日期：2026-10-31。下一会话先读根 `AGENTS.md`、本文件，再读 Week 06 计划与实际进度。
排期订正留痕：10 月 30 日 AI 在 Day 41 后提前宣布整周完成，学员指出 Day 42 尚未安排；
当时已撤回整周完成状态。10 月 31 日 Day 42 补做并完成当次验收后，本文更新为正式交接。

## 一句话状态

Day 36～42 完成当次验收：学员接通自有 Markdown 资料的加载、切分、向量化、Qdrant 存储与检索、
原文回查及带引用问答，完成十题真实基线、观察与阶段复盘。代码与理解经过答疑、订正，
本次验收不等于跨天独立掌握。

资料使用仓库的 `notes/python-notes.md`，全文 137 行；窗口 8 行、重叠 2 行，生成 23 条片段，
每题取 3 条候选。全文快照固定在同一次 batch 中，后续回查不重新读取变化后的磁盘文件。

第 1～6、9、10 题的观察核心判断首轮通过，第 7、8 题经具体反馈订正。
十题的问题及期望由 AI 按学员明确要求整理，真实运行、观察和复盘由学员完成；
复盘第 1 题用过 AI 模板，第 3 题及讲解提纲用过 AI 应学员请求提供的示例，不记为独立首答。
详细批改只在聊天中反馈，学习记录保留学员原稿、必要订正留痕和真实输出。

Day 42 使用新的 AI 内存资料，学员实现按引用顺序回查原文的 `trace_citations`，经多轮
答疑订正后通过十二组结果与输入不变检查，并完成亲跑、来源观察和三项人工故障现场判断。
A 两题结论与请求计数首答正确，第 2 题理由在聊天补充；B 观察核心正确，C 核心判断通过，
引用未覆盖与证据矛盾的用语区别在聊天补充。此为当次变式验收，不是整周全部机制闭卷首答通过。

## 现在能跑什么

以下命令从仓库根目录运行。前四条不调用回答模型，A/B 只读已有 embedding 缓存。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --help
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --part sources
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --part b
```

预期：sources 显示原文及行号；A 有 25 项对照一致与 3 组预期参数错误；B 有 118 项对照一致与
2 组预期参数错误，覆盖正常、不足、空候选、坏出处、未知引用、非 stop、坏 JSON 和请求异常。
A/B 终端输出自动保存在 `demos/day41/outputs/checks/` 的独立目录，含日志和运行来源信息。

Day 42 的独立引用回查入口不调用模型、embedding 或数据库：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day42_trace_exercises.py --part sources
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day42_trace_exercises.py --part b
```

预期：显示两份内存全文；B 十二组结果与十二组输入不变检查一致。该函数只核对被引用
片段的编号及原文出处，独立于 Day 41 请求前对所有候选的核验；回答事实支持仍由人工判断。

需要真实回答时沿用既有配置；每次创建新的运行目录，不覆盖本次基线：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --part ask --live --question "不确定一个函数有哪些参数、怎么使用时，可以怎样查看说明？"
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day41_rag_exercises.py --part batch --live
```

batch 只读取 Day 39 原表的编号和问题，不读取期望或学员判断；同次只建一次库并复用全文快照。
模型只接受完整 stop 响应，不自动重试。结构检查通过仍需人工核对事实与引用支持。

## 文件与真实基线入口

- 成品入口：[Day 41 练习](exercises/day41_rag_exercises.py)，A 返回 source → 全文的字典，
  B 返回 candidates、response、checked、request_count、error 五键。
- 旧函数统一查阅：[RAG 公共函数](demos/shared/rag_functions.py)，保留功能、输入、返回类型与边界说明；
  Day 36～40 原练习继续作为学习历史，不要求逐份找复用函数。
- 唯一问题表、期望、候选与学员观察：[Day 39 记录](demos/day39/day39_retrieval_记录.md)。
- 模型完整回答、配置、引用、用量与阶段复盘：[Day 41 记录](demos/day41/day41_rag_记录.md)。
- 新情境引用回查与人工现场判断：[Day 42 记录](demos/day42/day42_验收.md)。
  学员亲跑位于 `demos/day42/outputs/checks/b_20261031_154608_346876_3b5cb253/`，
  十二组中五组正常返回、七组按预期抛 ValueError，输入均未改动，本次无真实模型请求。
- 本机原始结果：`demos/day41/outputs/run_jg_k2_vk/`，含 `run_info.json`、
  `sources_snapshot.json`、`question_01.json`～`question_10.json`；库位于其 `db/`。

本次学员 batch 共 10 次真实回答请求，每题 1 次；模型为 deepseek-flash，全部 stop、error=null。
模型 status 为 7 条 answered、3 条 insufficient，这不是答对题数。用量合计输入 8110、输出 826、
总计 8936 token；运行时长和实际费用未记录，没有做全文模型调用的实测对比。

原文快照 SHA256：`923b660e3d09527cf9a54be9bee4a67c78fb0e5b7c67cc5cca8007ff92e623df`。
原始 outputs、缓存和数据库按仓库约定不提交 Git；本机换目录或换机器时须另行保留所需原始输出。
已提交的 Markdown 保留候选、分数、模型回答及用量，不能假设 Git 克隆会恢复本机 outputs。

## 环境与已知边界

- Windows，解释器 `.venv\Scripts\python.exe`，Python 3.13.9。
  本机版本：fastembed 0.9.0、qdrant-client 1.19.1、langchain-core 1.6.10、openai 3.19.2。
- embedding 固定为 `BAAI/bge-small-zh-v1.5`、512 维、CPU；默认 `local_files_only=True`，
  缓存在 `demos/day38/outputs/embedding_model/`，无需重新下载或训练模型。
- 回答客户端沿用 Day 40 与根 `.env` 配置；不打印凭据，SDK 自动重试为 0。
- 数据库 point id 是整数，原片段 id 单独保存于 payload.chunk_id；恢复 Document.id 用后者，
  再核对 source、line_start、line_end、正文和编号格式，不能用候选排名或 point id 代替出处。
- 学员亲跑的部分临时目录在默认 AI 沙箱下读不到；此前用只读提权核对成功，未改 ACL、删用户数据库或重跑基线。
- `store_chunks` 是固定快照写入，不是完整的增量同步器：不能据此宣称已支持修改资料后的旧片段清理。
- 学员指定的 PyCharm scratch.md 已在十条观察原文归档、逐条核对后删除，不再作为填写入口。

## 留的尾巴与收尾证据

2026-10-30 清理 A/B 题干后再跑：A 25 项、B 118 项一致，另有 3/2 组参数错误符合预期；
现有测试 `12 passed`，本周 39 份 Python 文件 Ruff 与格式检查通过。
清理前后函数非 docstring AST、学员复盘、十条观察和十条模型回复一致，收尾没有新增真实回答请求。
AI 验证使用独立来源标记，验证日志及临时检查文件由 AI 清理，学员原始输出与模型缓存保留。

2026-10-31 Day 42 清理题干后，根目录与练习目录的 help/sources/B 共 6/6 入口通过，
两次 B 各 24 项一致；现有测试 `12 passed`，本周 43 份 Python 文件 Ruff 与格式检查通过。
清理前后执行 AST、学员原答与亲跑日志核对保留；记录仅注明亲跑摘要对应清理前代码，
没有更新原始日志或新增真实回答请求。日志来源支持其他单元显式指定路径与来源变量，
Day 41 默认行为保留。

- Day 40 两道概念短复验已在 10 月 31 日 Day 42 A 完成；仅确认这两项判断，未做全套独立重写。
- Day 41 于 11 月 1～2 日或下次满足 2～3 天间隔的学习日，用新问题做 10～15 分钟独立变式。
  没有发生的复验不能打勾。
- 复盘第 2 题末句仍写“索引未命中”，前文已正确说明检索没找全；作为术语尾项保留原稿，
  后续复验区分“材料未入库”和“已入库但没选入候选”，不再追加同构抄写题。
- 学员仍不清楚怎样改进切块、认为候选质量不高；下一阶段以本次失败证据检验，不提前代填改进结论。
- Week 04 的旧机制复验沿用原交接的待办，只补实际缺口，不重做已验收主线。

## 下一周目标与第一步

Day 42 已完成当次验收，下一步进入 Week 06；已有延迟复验按到期日期保留，不预先勾选。

Week 06 按总计划学习检索优化与评测。先读当前 `weeks/week06_retrieval_eval/README.md` 和计划，
保留这份基线，先定义命中、完整回答和引用支持的判分口径及分母，再按失败证据选一种改进。

优先回看问题 7、8：问题 7 未取回第 40～41 行的排序取数依据，问题 8 未取回第 78 行的结构说明；
问题 8 的 dir(x) 事实在候选中，但未被实际引用覆盖。这些对应不同层次，不能都归为模型乱答或切块差。
第 2、9 题已分别取回包含这些行的片段，说明相关材料已入库。

先做一组控制变量对比，保留没有提升或变差的结果，再决定是否增加其他方法；
新样本逐步扩展并保留留出检查。界面、多轮、第二个向量库与多种优化不作为开工门槛。
本地提交由 AI 完成，推送仍由学员执行。
