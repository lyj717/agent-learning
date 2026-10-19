# Week 04 交接文档

> 交接日期：2026-10-19。给 Week 05 新对话使用；先读根目录 `AGENTS.md`，再读本文件。

## 一句话状态

Day 29～35 主线已验收；Day 35 已完成带文件检查点和人工确认的报价图，三个函数订正后
七组隔离实跑通过，短复习与三道观察也已通过本次验收。跨天独立复验仍有尾项。

清理题干后，跨进程批准、拒绝、重复恢复、同业务编号重试、提前停止、会话隔离及
两组四字段对照复跑通过。测试 `9 passed`，Ruff 检查及 197 个 Python 文件格式检查通过。
清理前后非 docstring AST 一致，学员回答原文保留；既有两份 SQLite 文件校验值未变。
本次临时文件已清理，进度、故障台账与本地提交按收尾流程同步。

本阶段成品复用 Week 03 的工具与停止规则，由 LangGraph 管理状态更新及节点执行。
Day 35 的完整主线是“查资料、计算报价 → 生成草稿 → 暂停审核 → 批准后保存一条记录”。
这里的发布只是写入本地 SQLite 模拟发件箱，不发送邮件、不发货、不转账。
三道观察在练习文件末尾；AI 检查输出和交接说明不冒充学员观察。

## 现在能跑什么

以下命令均从仓库根目录运行；本周入口使用离线假模型和教学数据，不需要 API 密钥。

先查接口或看 SQL 防重机制，不改文件数据库：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day35\day35_support.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day35\day35_sqlite_idempotency_demo.py
```

前者打印六个现成接口的输入输出，完整状态在源码的 `QuoteState` 中列明；后者只用内存数据库，三次提交后的
总记录数应为 1、1、2，展示同业务编号防重及新业务新增。

开始、查看、恢复各启动一次 Python，下面的编号若已用过，就整组换成未用过的编号：

```powershell
$day35Exercise = 'weeks\week04_frameworks\exercises\day35_persistent_review_exercises.py'
.venv\Scripts\python.exe -B $day35Exercise --phase start --ticket-id d35-handoff-allow-01 --quote-id offer-handoff-01
.venv\Scripts\python.exe -B $day35Exercise --phase status --ticket-id d35-handoff-allow-01
.venv\Scripts\python.exe -B $day35Exercise --phase resume --ticket-id d35-handoff-allow-01 --decision allow
```

首次应生成含 88 元与出处的草稿，停在 `next=('review',)`；尚未发布。
`status` 查看不会继续执行。批准后 `next=()`，此业务编号在发件箱中有一条记录；
消息、工具观察、请求次数和用量不因审核恢复而重算。已结束会话再次恢复也不重开任务。
拒绝分支在另一个新会话恢复时传 `--decision deny`，应保留草稿、无发布记录。
同业务跨会话重试需要显式复用 `--quote-id`；完整对照命令见本周 README 的 Day 35。

比较旧手写版和框架版，或只查看旧图的一组结果：

```powershell
.venv\Scripts\python.exe -B $day35Exercise --phase compare
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part d --case 1
```

`compare` 不运行新审核图；它比较 Day 27 手写版与 Day 34 框架版，正常和请求上限两组的
`answer`、`stop_reason`、`steps`、`usage` 应分别一致。相同结果不等于两者的状态与控制方式相同。
手写版由循环、变量和判断维护流程；框架版的节点返回更新，由图应用规则并执行边和路由。

## 环境与容易混淆的边界

- 解释器使用仓库 `.venv\Scripts\python.exe`，依赖在根 `requirements.txt`。
  已固定 `langgraph==1.2.15`、`langgraph-checkpoint-sqlite==3.1.2`；本次没有升级依赖。
- PyCharm 使用仓库解释器，脚本选择 `exercises/day35_persistent_review_exercises.py`，
  脚本形参只填 `--phase ...` 等选项。导入路径由脚本定位仓库根目录，不依赖工作目录。
- 练习集中在 `exercises/`；教具和当天数据在 `demos/dayNN/`。
  Day 35 做题查 `day35_support.py`；SQL、CLI、对照和状态输出在 AI 维护的 `day35_runtime.py`。
  `QuoteState` 已直接列全十三项字段；继承小实验只是先前答疑留档，不是当前阅读前置。
- `--ticket-id` 的值成为 `config['configurable']['thread_id']`，用来选择检查点会话。
  同一个检查点文件里，新 `thread_id` 不会读到旧会话。消息 `id` 用于消息自身的合并与修订；
  `tool_call_id` 配对工具点单与观察；这些编号不负责业务防重。
- `quote_id` 是自定义的一次报价发布业务编号，不是 LangGraph 内置配置。
  默认是 `offer-` 加会话编号；同一业务换会话重试时，要显式传回原业务编号。
- 默认检查点文件是 `demos/day35/day35_checkpoints.sqlite`，保存图状态和执行位置；
  模拟发件箱是 `demos/day35/day35_outbox.sqlite`，保存报价业务记录。
  `--db` 选择检查点文件，`--outbox` 只在 `start` 选择发件箱；恢复使用状态中已保存的动作路径。
  相对数据路径以 Day 35 目录为基准，`status/resume` 不为不存在的文件新建空库。
- `final_answer` 表示模型已完成草稿；是否发布还要看人工批准与实际发件箱记录。
  审核和发布不新增模型请求，也不新增原来的四类 `trace`；动作由 `action_count` 和数据库行数核对。
- 恢复从暂停节点开头重跑，走到 `interrupt` 才取到 `Command(resume=...)` 的值；
  本图暂停在模型与工具之后的审核节点，所以不重跑之前的报价生成。
  恢复入口不重传初始 `messages/steps/usages`，避免覆盖或重复已有进度。
- 本地防重靠稳定业务编号和 SQLite 主键唯一约束；同编号、同草稿只保留一条，
  同编号却换草稿会报错。这不是外部系统动作恰好执行一次的通用保证。
  检查点也不是长期用户记忆；本周没有引入 store、用户画像或向量记忆。

已有数据库、`-wal/-shm` 文件及既有 `__pycache__` 属于用户环境，不能为复测删库清空。
SQLite 主文件与这两类伴随文件均已加入 Git 忽略规则，不作为学习代码提交。
AI 批改使用隔离临时路径，仅清自己本次创建的文件。根目录无关的 `1.py` 不纳入本阶段提交。
AI 跑 pytest 使用 `-p no:cacheprovider --basetemp=.pytest_tmp`，避免 `%TEMP%` 权限问题；
若另设嵌套 basetemp，先建立父目录。用 `-B` 或环境变量避免新建字节码缓存。

## 真实尾项与掌握情况

本周代码和观察的当次验收，不能替代间隔后的独立复现。以下尚无实际完成证据：

- 消化半日，以及 Day 26B 重复判据的延迟复验。
- Day 29～31 的部分更新、条件路由、消息合并与两类消息编号，10～15 分钟闭卷复现。
- Day 32～33 的会话隔离、同会话恢复、节点重跑与动作次数，间隔后换输入复现。
- Day 34 于 2026-10-19 完成，2～3 天后用新输入解释整批回填、普通列表更新、重复与超时用量。
- Day 35 三道观察是在答疑后完成，后续需用新情境检验恢复、防重及框架取舍的独立理解。

下一阶段先用短题检查实际缺口，补课只补缺口，不把所有旧课全重做一遍；没有发生的复验不能勾选。
本次只读核对了学员已有的 `d35-allow/deny/limit/retry` 四段会话末状态及发件箱，
符合对应分支与同业务编号只有一条记录的要求；这不是延迟闭卷复现的证据。
JD、简历仍留到学习项目结束后统一处理，正式视频留到面试复习时；不把它们列为新周开工门槛。

## Week 05 的目标与建议第一步

Week 05 做带出处的文档问答：读取资料 → 切分 → 向量化 → 存储 → 检索 → 结合命中内容回答。
先采用一种切分方式和一个向量库，理解 chunk、来源编号和元数据；
没有支持答案的证据时说明没找到，不编引用。第二种切分、多轮改写和扫描件处理为选修；
混合检索、重排等留给下一阶段按实际失败选择，不在开工一次塞入。

资料由学员选择可直接读取的文本或文本型 PDF；约十条“问题 + 期望来源/无答案”样本也由学员准备。
AI 负责独立知识点演示、清楚接口、数据出口和批改，不替学员填评测样本、实验结果或结论。
新 API 仍按知识点独立演示，参数、返回值、用法和边界讲清；综合实现优先留给练习。

建议下一步是在 Week 05 新对话说“读 AGENTS.md 和 Week 04 HANDOFF，开始 Day36”。
AI 先读实时进度及 `docs/ai-agent-12周学习计划.md` 的第 5 周，再估 Day 36 完整用时和任务范围。
每天按约 3～5 小时、Week 阶段约 4 个自然日安排；每次开始 Day 都先报预计自然日，
以 Day 34 整合量约 1 天校准，合并重复任务并给复习、排错和订正留时间。
此交接只记录下阶段目标，不在当前对话提前布置新课或产出学员资料。
