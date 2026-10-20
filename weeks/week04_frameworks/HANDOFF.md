# Week 04 交接文档

> 交接日期：2026-10-19。给 Week 05 新对话使用；先读根目录 `AGENTS.md`，再读本文件。
> 2026-10-20 收尾：Day 35 `--live` 已由 AI 实测，学员现已确认亲自测试，Week 04 主线和真实接入补验完成；跨天独立复验继续保留尾项。

## 一句话状态

Day 29～35 主线与真实接入补验已完成；Day 35 已完成带文件检查点和人工确认的报价图，
三个函数订正后七组隔离实跑通过，短复习与三道观察已验收。真实模型适配由 AI 按学员
授权接入并实测，学员于 10 月 20 日确认已亲自测试并要求收尾。跨天独立复验仍有尾项。

清理题干后，跨进程批准、拒绝、重复恢复、同业务编号重试、提前停止、会话隔离及
两组四字段对照复跑通过。测试 `9 passed`，Ruff 检查及 197 个 Python 文件格式检查通过。
清理前后非 docstring AST 一致，学员回答原文保留；既有两份 SQLite 文件校验值未变。
本次临时文件已清理，进度、故障台账与本地提交按收尾流程同步。

本阶段成品复用 Week 03 的工具与停止规则，由 LangGraph 管理状态更新及节点执行。
Day 35 的完整主线是“查资料、计算报价 → 生成草稿 → 暂停审核 → 批准后保存一条记录”。
这里的发布只是写入本地 SQLite 模拟发件箱，不发送邮件、不发货、不转账。
三道观察在练习文件末尾；AI 检查输出和交接说明不冒充学员观察。

## 现在能跑什么

以下原有命令均从仓库根目录运行，使用离线假模型和教学数据，不需要 API 密钥。
10 月 20 日新增的真实模型命令在本节末尾，使用根 `.env` 的已有配置。

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

### 2026-10-20 真实接入补充

按学员要求给同一 Day 35 图增加 `--live`，没有重写学员图或替填观察。Day 34 模型节点
只增加可选 `chat_fn`，Day 35 支持层按已保存的 live 情境传入真实适配器，原离线行为保留。
学员补充运行预计约 1/3 个自然日，完整说明在本周 README“真实模型接入补充”。

```powershell
$day35Exercise = 'weeks\week04_frameworks\exercises\day35_persistent_review_exercises.py'
.venv\Scripts\python.exe -B $day35Exercise --live --phase start --ticket-id live-01
.venv\Scripts\python.exe -B $day35Exercise --live --phase status --ticket-id live-01
.venv\Scripts\python.exe -B $day35Exercise --live --phase resume --ticket-id live-01 --decision allow
```

三条命令用相同新会话编号。start 才联网；status/resume 重印历史不代表新请求。
默认真实检查点与发件箱为 `demos/day35/day35_live_checkpoints.sqlite` 和
`day35_live_outbox.sqlite`，与离线数据分开；查看/恢复也带 `--live` 来选同一默认文件。
复用根 `.env` 的 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL；SDK 自动重试关闭，默认四次
模型请求、单次 50 秒、任务 180 秒、token 上限 20000。金额仍按教学假价估算。

AI 实测三次 `deepseek-flash` 请求完成真实检索和计算，草稿 88 元、出处 catalog.txt:2，
输入/输出 token 分别为 1988/206；退出后无模型凭据也能查看、批准和重复恢复，模型历史
与用量不增加，发件箱一条。旧库校验值未变；16 组原离线图、同题两组对照及测试
`12 passed`。这是 AI 验证接入，不代替学员亲跑或跨天独立复现。

**同日最终确认**：学员随后表示“我已经测试过了，结束 Week4”，据此记录真实入口亲跑
完成。没有将 AI 的 token 数字写成学员的数据，也不推导为学员跑过所有拒绝、超时、
缺失用量分支或已能闭卷重写。Week 04 完成收尾，原回答和现有数据库继续保留。
最终收尾复查 `12 passed`，本周及新增测试共 44 个 Python 文件的 Ruff 检查与格式检查
通过；本次临时目录已清理，Week 05 草稿和依赖改动不纳入本周提交。

真实接入的掌握要求：能解释同接口替换 `chat_fn`、完整 messages 和工具 schema 的用途、
SDK 返回到三项字典再到节点更新的过程、点单与工具观察配对，以及超时记账和审核恢复。
目标是能阅读、讲解并参考文档改写；CLI、路径、SDK 对象转换和校验细节允许查阅。
不把背整份辅助脚本作为新周门槛，独立改写能力留待短复习检查。

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

Week 05 在另一接续处已有 Day 36 教具与未完成练习；继续时先读其当前 README 和已存在
文件，不因本交接再次创建一套。AI 读实时进度及 `docs/ai-agent-12周学习计划.md` 第 5 周，
再按学员当前进度确定下一步和剩余工作量。
每天按约 3～5 小时、Week 阶段约 4 个自然日安排；每次开始 Day 都先报预计自然日，
以 Day 34 整合量约 1 天校准，合并重复任务并给复习、排错和订正留时间。
此交接只记录下阶段目标，不在当前对话提前布置新课或产出学员资料。
