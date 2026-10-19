# Week 04｜框架与记忆

**交付物**：用 LangGraph 重写第 3 周的 Agent（带持久化记忆与人工确认）。

Week 是阶段编号，按验收推进；默认每天 3~5 小时，每个 Week 以约 4 个自然日完成为目标，由 AI 协调任务量。

**工作量校准（2026-10-19 学员反馈）**：本周前几天的独立知识点单元可按
1/3～1/2 个自然日安排；学员随后明确将 **Day 34 调整为 1 个自然日**，整个
**Week 阶段约 4 个自然日**，覆盖同日较早的 Day 34 1.5～2 天估计。
此处是后续排期基准，不是实际耗时记录，不改写已经完成的日期与验收证据。
以后每次“开始 DayX”，AI 先报告预计自然日、主要工作量，较重时列出分天目标；
结合本周剩余必做主动分配复习、实现与排错时间。Day 35 开工时据此确定范围和估计，
复用已完成的 Day 34 图，合并重复任务，保留检查点、人工确认与恢复变式的关键验收。

## 当前接续点（2026-10-19）

Week 03 的 Day 22～28 主线已验收，证据与限制见
[交接文档](../week03_agent_loop/HANDOFF.md)。Day 29 的状态更新与固定边已验收：
学员完成 A、B 和观察订正，AI 恢复反向实验后遗留的边并实跑检查。Day 30 的条件边
已完成 A、B 和四道观察。Day 31 的消息合并、追加与同 ID 修订已验收；
首次观察中的 ID 混淆经讲解后由学员订正，独立掌握留待跨天复验。Day 29～31 的关键机制
仍须在完成后 2～3 天闭卷复验。Day 32 已把新概念拆成独立小演示；学员完成 A、B
和四道观察，AI 用隔离数据库复跑通过。Day 33 已完成 A、B 与四道观察订正并验收，
AI 实跑批准、拒绝和同编号重试通过。Day 34 的 A～D 代码复验通过：A、B、C 共 14 组
单节点对照、16 组完整图及用量与路由边界检查均符合要求；两道短题、五道观察已完成
订正并验收，练习脚手架已清理。Day 35 的三个函数与三道观察现已通过本次验收；
文件检查点、人工确认、跨进程恢复和业务防重符合要求。清理题干后复跑批准、拒绝、
重试、停止与会话隔离通过，测试 `9 passed`，Ruff 检查与格式检查通过。
Week 04 主线收尾，接续见 [HANDOFF](HANDOFF.md)；跨天独立复验仍按下方清单待做。

Day 26B 重复判据的延迟复验仍待进行。它在 10 月 14 日完成，10 月 15 日 Day 28
已做过一次新轨迹预测；同日再做不能记成隔天复验，安排在 **10 月 16～17 日或
下一次满足间隔的学习日**用 10～15 分钟复现，不作为本阶段开工门槛。
JD、简历、视频沿用原先的延后安排。

## 目录调整后的运行方式（2026-10-18）

练习集中在 `exercises/`，演示与当天数据在 `demos/dayNN/`。
下面的文件位置与命令已按新目录更新。Day 34 的练习从
`exercises/day34_graph_exercises.py` 启动，教具在 `demos/day34/day34_support.py`；
跨目录代码使用明确的包导入，直接运行时自动定位仓库根目录。

AI 验证：28 个 Week 04 脚本分别从仓库根目录与脚本目录导入，56/56 通过；
离线演示与已完成练习共 56 次运行通过；用隔离数据库验证跨进程接续、新会话隔离、
审批恢复与只读查看，8/8 通过。Day 34 的 16 组教具情境经过旧循环及消息转换验证通过，
这项检查不代表学员的新图已经完成。已有 SQLite 文件的内容保持不变。

目录修复当时，Day 34 A 已能导入并启动，但请求前到期的分支返回 `usages=None`，
用量汇总会抛 `TypeError`。2026-10-19 后续订正已通过复验，详见下方批改记录；
目录修复时保留的学员原实现与当时问题仍按历史记录说明。

## 本阶段顺序

这是学习单元，不是必须在七个自然日内完成的日历。只提前准备当前单元的代码。

| 单元 | 主要机制与产出 | 状态 |
|---|---|---|
| Day 29 | 状态更新与固定边：筛选资料后生成简报 | 2026-10-15 已验收；延迟复验待做 |
| Day 30 | 条件边：根据模型结果走工具节点或结束，工具回到模型 | 2026-10-16 已验收；延迟复验待做 |
| Day 31 | 消息合并：新增消息与按消息 ID 修改；对照原 tool_call_id 配对 | 2026-10-16 已验收；延迟复验待做 |
| 消化半日 | 闭卷画状态流转、定位顺序/合并错误，补实际缺口 | 待安排 |
| Day 32 | 检查点：一种本地持久化方案、会话标识、重新启动后继续 | 2026-10-17 已验收；跨天复验待做 |
| Day 33 | 人工确认与恢复：确认前不执行，用执行次数检查重复生效 | 2026-10-18 引导练习与观察已验收；独立迁移待后续验收 |
| Day 34 | 学员整合：把 Day 27 的工具、停止规则接入框架版 | 2026-10-19 代码、两道短题与五道观察订正验收通过；独立复验待做 |
| Day 35 | 接入检查点与人工确认，再做同题对比、恢复变式与交接 | 2026-10-19 代码与三道观察验收通过；预计半天是排期估计，非实测耗时；独立复验待做 |

条件边先用固定模型结果拆解；真实模型接入时由 AI 先验证联网教具，学员再运行自己的
实验。预算、时限、重复判据沿用 Week 03 的行为契约；不会因为换框架就默认由库保证。

## 开工前短检查

- [ ] 不看旧答案讲清手写版的消息回填、停止原因与工具边界。
- [ ] 用短题检查 Week 00 留下的 `*args/**kwargs` 和 Week 01 自评的异常分类；先看现在是否会，只补实际缺口。

题目与回答空位都在 `exercises/day29_state_exercises.py` 顶部，不另外写一份记录。
先用约 10 分钟闭卷回答，交给 AI 看过再决定是否需要补课。

## Day 29：状态怎样经过节点和边

**今天的交付物**：学员写出资料筛选节点与两节点图，并根据真实运行填写练习末尾的观察。
只新增“节点交回部分更新，图保存状态并沿边执行”这一机制。

读代码时只跟一条数据流：`initial` 是进入图前的整份状态；`select_sources` 收到它，
只返回 `hits` 与 `trace` 的更新；图把这两个字段写入状态，其余字段仍保留；
`render_report` 收到更新后的状态，再返回 `report` 与下一条轨迹；到 `END` 时
`invoke` 才交回最终状态。节点本身只做普通 Python 工作。A 练的是“返回哪些更新”，
B 练的是“谁来执行下一步，以及下一步读到哪一份状态”。

这条固定路线用顺序调用两个普通函数也能实现；今天先看清图的接口和数据传递，
后续条件边、检查点和人工确认才会用到更多框架能力。若只看最终报告看不出区别，
把 `initial["hits"]` 的“旧结果”、筛选后的 `hits`、`render_report` 打印的出处
逐项对照；不要凭最终文字猜执行过程。

| 文件 | 用途 |
|---|---|
| `demos/day29/day29_state_demo.py` | 一个节点整理关键词；对照未返回字段的保留和列表字段的替换 |
| `exercises/day29_state_exercises.py` | 顶部短检查；A 写筛选节点；B 接两节点；末尾写观察 |

按这个顺序做：

1. 先写练习文件顶部三道短检查，保留原预测。`--part warmup` 可核对参数收集与解包。
2. 运行演示，按 `main → KeywordState → trim_keyword → build_keyword_graph` 顺读源码。
   `TypedDict` 是字典的键与值类型说明，运行中的状态仍是普通字典；本日初始字段已全部给齐。
3. 完成 A：`select_sources`。直接右键运行默认只检查 A，对照三组分数门槛与原输入是否变化。
4. 完成 B：`build_review_graph`。取消对应导入注释，运行配置填 `--part b`。
   `render_report` 已提供，它只负责把筛选结果变成简报；图的连接由学员写。
5. 填末尾观察。第 3 题先预测，再临时调换边、运行对照，最后恢复正确顺序；
   第 4 题在 Day 29 只核对状态与节点的对应，按结果选路留到 Day 30。

在仓库根目录执行的等价命令：

```powershell
# 开工短检查第 2 题：先写预测，再核对
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day29_state_exercises.py --part warmup

# 读演示：完全离线，不需要 .env
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day29\day29_state_demo.py

# 分别重跑 A、B 的三组对照
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day29_state_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day29_state_exercises.py --part b
```

环境已在仓库 `.venv` 安装 `langgraph==1.2.15`，写入根 `requirements.txt`。
换环境时用 `.venv\Scripts\python.exe -m pip install -r requirements.txt`。
今天使用 LangGraph 本地执行，候选资料与分数为人工教学数据；没有真实检索或模型评分。

官方文档只读与当下对应的小节：

- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)：今天读 **State / Schema、
  Reducers / Default reducer、Nodes、Edges / Normal edges**。对应字段定义、部分更新、注册函数、
  执行顺序；Messages 部分留到 Day 31，对照消息新增和修改。
- [Python 3.13 TypedDict](https://docs.python.org/3.13/library/typing.html#typing.TypedDict)：
  看第一个字典类型例子及“运行时仍是普通 dict”的说明，理解它与 Pydantic 校验的区别。
- [LangGraph 安装说明](https://docs.langchain.com/oss/python/langgraph/install)：
  仅需了解本地库的安装；本日没有增加模型服务商 SDK。

- [x] 完成开工短检查，AI 针对 `*args/**kwargs` 缺口补讲。
- [x] AI 实跑演示；学员在练习观察中说明节点返回更新与最终状态的区别。
- [x] A、B 三组对照均符合预期，原输入未修改。
- [x] 学员完成调换顺序的实验与末尾观察，能用证据指出问题。
- [x] AI 实跑批改、清已验收脚手架、检查格式与故障台账，并做本地提交。

### 2026-10-15 AI 批改补充

这份补充保留学员在练习文件中的原预测与观察，不把 AI 的订正写成学员原答。

- A 的三组筛选与输入不变检查均通过；B 在恢复 `START → select → render → END`
  后，三组报告、出处、轨迹和输入不变检查均通过。反向实验留下的
  `render → END` 多余边已由 AI 连同顺序一起修正。
- 开工短检查第 2 题的原预测与实际输出不一致；文件已保留两行真实输出，
  还需学员用自己的话补充“定义处收集、调用处展开”以及两种调用为何收到同样参数。
- 观察第 2 题的补充已指出无命中时新 `hits` 是空列表、与输入中预置的旧列表不同；
  `question` 未被更新所以保留。这能解释 `hits`，还需说清“上次报告”由哪个节点更新。
- 观察第 3 题对反向顺序的预测与实测一致；补充中的“简报与最终 hits 一致”却与
  实测矛盾：简报生成时 `render` 读到“旧结果”，随后 `select` 把最终 `hits` 改为本次筛选结果。
  “输入不变不能证明流程正确”这一半判断正确。学员再据这两处输出订正“一致”。
- 观察第 4 题的状态与节点映射正确。AI 提前问了条件边选路和工具返回路线，超过
  Day 29 的固定边内容；本题不再要求补答这一部分，移到 Day 30 讲和练。

### 2026-10-15 验收补充

学员随后将短检查第 1 题的第二条消息订正为“观察消息”，并补写第 2 题中
`*args/**kwargs` 在定义处收集、在调用处展开；两种写法的实跑返回值相同。
观察第 2 题补充了新 `hits` 替换旧字段、`render` 改写报告，观察第 3 题将
反向路线下的“报告与最终 hits 一致”订正为“不一致”。保留原预测和批改记录，
这些订正是在讲解后完成，独立掌握情况留待 2～3 天后的闭卷复验。
正常路线的实跑轨迹为“收到候选 → 筛选资料 → 生成简报”，`render` 打印本次筛出的
出处；反向路线的轨迹忠实记录了错误的执行顺序。学员原观察的“trace 错乱”保留原稿。
观察第 4 题的 `tool` 对应本地工具执行，模型发出的点单仍属于模型消息。

AI 实跑 Day 29 演示、开工小实验和 A、B 各三组，均符合预期；仓库现有测试
`9 passed`。已清理完成练习中的题干提示，保留学员代码、原预测和观察。

## Day 30：模型节点运行后，条件边选哪一站

**今天只新增条件边**。Day 29 的节点仍返回状态更新；条件边的选路函数读更新后的状态，
只返回下一节点名或 `END`。工具节点完成后用一条固定边回到模型节点；本课的假模型按预设
列表继续点单，并在最终答复里使用工具观察。模型节点只发出 assistant 点单，执行与回填
发生在 tool 节点。
本日用固定假模型和本地教学数据；不引入真实模型调用、消息专用合并规则、检查点或预算整合。

| 文件 | 用途 |
|---|---|
| `demos/day30/day30_conditional_demo.py` | 固定假模型对普通／加急请求选不同路线，只演示一次选路，不写完整回环 |
| `exercises/day30_conditional_exercises.py` | A 写本轮回复的选路函数；B 接模型、工具与返回模型的边；末尾写观察 |

按这个顺序做：

1. 运行演示，先按 `main → DeliveryState → fixed_model_reply → choose_next → check_rule → build_demo_graph`
   顺读，再对照两条输出。`decision` 是演示自定义的教学字段，不是服务商原生响应字段。
   看清“节点返回更新字典”和“选路函数返回目的地”有什么不同。
2. 做 A：`route_after_model` 改用 Week 03 熟悉的 `finish_reason` 和最新 assistant 消息里的
   `tool_calls`。默认运行四组对照；第三组特意在历史里放了旧点单，不能据此误走工具。
3. 做 B：取消练习顶部标出的导入注释，连接 `START → model`、从 `model` 出发的条件边、
   `tool → model` 固定边。`fixed_model_node` 与 `run_local_tool` 已提供，不必重写。
   用 `--part b` 对照零次、一次、两次本地查询的节点轨迹、消息角色、点单与观察 ID。
4. 在练习文件末尾填四道“现象与原因”；本日没有另一份待填记录。完成后交给 AI 实跑批改。

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day30\day30_conditional_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day30_conditional_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day30_conditional_exercises.py --part b
```

演示与已完成的 A、B 均可直接运行。
阅读官方 [Graph API 的 Conditional edges](https://docs.langchain.com/oss/python/langgraph/graph-api#conditional-edges)
和 [Agent 回环示例](https://docs.langchain.com/oss/python/langgraph/workflows-agents#agents)：
今天只看 `add_conditional_edges` 如何使用路由函数，以及 model 条件选路、tool 固定回 model
的连线。选路函数如果直接返回节点名或 `END`，本课不需要 `path_map`；不要从 model
同时加固定边和条件边，否则可能运行两条路线。

- [x] AI 实跑演示；学员的 A、B 分清节点返回状态更新与条件边返回目的地。
- [x] A 四组下一站与期望一致，输入未修改。
- [x] B 三组的轨迹、答复、消息角色和调用 ID 与期望一致，输入未修改。
- [x] 学员完成四道观察；与 Day 27 的 `if` 对应关系已在批改中说明，独立掌握待复验。
- [x] AI 批改后清题目脚手架、检查格式与故障台账，再做本地提交。

### 2026-10-16 验收补充

学员写的 `route_after_model` 只根据本轮最新 assistant 消息及 `finish_reason` 选路：
本轮点单到工具，答完到 `END`，矛盾回复抛 `ValueError`。这对应 Day 27 手写循环里
“点单继续执行工具，否则结束”的 `if`。`build_agent_route_graph` 正确连接
`START → model`、从 `model` 出发的条件边与 `tool → model` 固定边。
A 四组实跑一致；B 零、一次、两次查询分别执行 1、3、5 个节点，消息角色、调用 ID、
轨迹、答复与期望一致，原输入未改。四道观察与输出一致。第 4 题更精确的表述是：
没有配置合并规则时，节点返回的整个新列表会替换旧列表；保留学员原答，不把批改写成
学员当时的措辞。AI 清理题干后完成 Ruff 检查，仓库现有测试 `9 passed`。

## Day 31：消息列表怎样追加和修订

**今天只新增消息合并规则**。Day 30 的节点为保留历史，手动返回
`state["messages"] + [新消息]`；现在在状态类型的 `messages` 字段上配置
`add_messages`，节点只返回本轮的一条消息。新消息 `id` 会追加，已有 `id` 会按原位置
替换；普通字段仍按 Day 29 学过的方式整份替换。`tool_call_id` 用于配对点单与工具观察，
不决定消息合并。演示和练习都用固定教学数据，不请求真实模型或网络。

| 文件 | 用途 |
|---|---|
| `demos/day31/day31_messages_demo.py` | 同一条固定路线对照无合并规则时覆盖、有规则时追加及同消息 ID 修订 |
| `exercises/day31_messages_exercises.py` | A 回填本地查询的一条 tool 消息；B 配消息规则并接两节点，末尾写观察 |

按这个顺序做：

1. 顺读演示的 `main → PlainState / MergedState → post_draft → revise_draft → build_demo_graph`，
   再运行。先看第 4 节直接调用 `add_messages(left, right)` 的两次输出：新 ID 追加、
   同 ID 在原位置修改。再看第 5 节图如何自动用它合并，比较最终消息数 **1 与 2**、
   `revise` 进入时看到的消息 ID，找出变化发生在哪个字段。
   `AIMessage`、`HumanMessage` 是消息对象，不会自己发模型请求；其属性用 `.type`、
   `.id`、`.content` 读取，和 Day 30 的简化字典消息不同。
2. 做练习 A 的 `record_tool_result`：只返回一条 `ToolMessage` 的更新。消息自身 `id`
   从状态的 `observation_message_id` 取，`tool_call_id` 从最新 assistant 点单取。
   默认运行两组；最后一组对照只是检验合并键，不代表一次真实调用正常返回两份结果。
3. 做练习 B：按题干取消导入注释，给 `ReceiptState.messages` 加规则，连接
   `START → record → confirm → END`。`confirm_receipt` 已提供；它应读到先新增的观察，
   再用相同的消息 ID 修订内容。用 `--part b` 对照两组的消息条数、类型、ID 和内容。
4. 在练习末尾填写四道“现象与原因”，完成后交给 AI 实跑批改。本日没有另一份记录 md。

在仓库根目录运行：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day31\day31_messages_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day31_messages_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day31_messages_exercises.py --part b
```

演示与已完成的 A、B 均可直接运行。
官方文档只读 [Graph API 的 Working with messages in graph state](https://docs.langchain.com/oss/python/langgraph/graph-api#working-with-messages-in-graph-state)
与 [`add_messages` API](https://reference.langchain.com/python/langgraph/graph/message/add_messages)：
今天只看 `Annotated[..., add_messages]`、新消息追加及同消息 ID 更新。
再看 [`ToolMessage` 的 `tool_call_id`](https://reference.langchain.com/python/langchain-core/messages/tool/ToolMessage)，
对照 Day 30 的点单 ID 与观察 ID；删除消息留到确有需要时再学。Day 31 不做检查点、
人工确认或完整 Agent 整合，做完后先安排半日消化与未完成的延迟复验。

- [x] 学员依据演示说明普通列表覆盖、新消息追加与同消息 ID 修订的差别。
- [x] A 两组返回一条 tool 观察，消息 ID 与调用 ID 来源正确，原输入未修改。
- [x] B 两组保留 human、ai、tool 三条消息，同消息 ID 修订内容而不增加条数。
- [x] 学员根据真实输出完成四道观察，并在讲解后订正 ID 混淆。
- [x] AI 批改后清练习脚手架、做 Ruff 和故障台账，再做本地提交。

### 2026-10-16 验收补充

学员完成 A、B 和四道观察后，首次回答曾混淆消息自身 `id` 与调用 ID，且未说清
`add_messages` 如何保留旧消息。AI 对照实跑输出讲解后，学员把第 1～3 题改为：
合并按 `message.id`、点单和观察按调用 ID 配对；图在 `record` 返回一条 tool 消息后
把它与已有的 human、ai 消息合并。第 4 题关于普通列表最终只剩一条 tool 消息的预测正确。
第 3 题学员引了 `confirm` 读到三条和最终仍三条的输出，最终修订内容的证据见 AI 订正。
这是讲解后的订正，独立掌握留待跨天闭卷复验。

AI 实跑演示及 A、B：A 两组各返回一条 tool 消息，消息自身 ID 不同、调用 ID 相同，
合并后为两条且原输入未改；B 两组最终均为 `human → ai → tool` 三条，tool 观察在
同消息 ID 处修订，原输入未改。已将已完成题目的长题干清为单行 docstring，
记录 `ToolMessage` 与列表形状不符的真实报错；Ruff 检查通过，仓库测试 `9 passed`，
本次 pytest 临时目录已清理。

## Day 32：程序关掉后，图怎样找到上一轮状态

**今天的主要新机制是本地检查点**。此前演示把 SQL、运行配置、保存器和读取结果压在
一份文件里，初学者需要边看边猜前置概念。现在每个新概念先用一份能单独运行的小演示
讲清，再用最后一份整合演示看跨进程接续。练习仍只验收检查点的安装、读取和新旧会话
输入；不要求手写 SQL。本课的“继续”是已结束会话接收新输入；运行中等待人工确认的恢复
留给 Day 33。

| 顺序 | 文件 | 只看这一件事 |
|---|---|---|
| 1 | `demos/day32/day32_sql_basics_demo.py` | 从零认识表与行、SQL 和 SQLite；先看全部三行，再筛选出一张工单最近的一行 |
| 2 | `demos/day32/day32_config_demo.py` | 用普通 Python 字典拆开 `config`，分清状态内容与会话编号；这里还不运行图 |
| 3 | `demos/day32/day32_invoke_demo.py` | 单独看 `graph.invoke(input, config)` 怎样运行图、两个参数与返回值；不装保存器 |
| 4 | `demos/day32/day32_sqlite_saver_demo.py` | 对照没装与装了 `SqliteSaver` 的两次图调用，认识 `compile(checkpointer=saver)` |
| 5 | `demos/day32/day32_state_snapshot_demo.py` | 写入前后读取 `StateSnapshot.values`，看 `get_state` 只读、不执行节点 |
| 6 | `demos/day32/day32_checkpoint_demo.py` | 用文件保存检查点，在两个独立 Python 进程里看到 0 → 1 → 2 |
| 可选 | `demos/day32/day32_checkpoint_view.py` | 在 PyCharm 运行，只读文件里该会话最新的状态，不增加次数 |
| 练习 | `exercises/day32_checkpoint_exercises.py` | A 给工单图装保存器；B 判断新旧工单并提交本轮消息；末尾写观察 |

按这个顺序读和做：

1. 先顺读 SQL 演示源码，再运行看输出。三行教学数据存于 `:memory:` 临时表，不是
   LangGraph 的内部表，也不会修改 `.sqlite` 文件。弄清 `execute` 把 SQL 交给数据库、
   `fetchall` 读多行、`fetchone` 读一行或得到 `None`。
2. 看 `config` 演示。`{"configurable": {"thread_id": "ticket-a"}}` 是运行配置，不是
   节点处理的状态；`ticket-a` 和 `ticket-b` 在同一存储位置中选不同会话。脚本里的
   `saved_by_thread` 是普通字典类比，明确不是框架内部实现。
3. 单独看 `invoke` 演示。`graph` 是编译好的图，`graph.invoke(input, config)` 才真正
   运行节点；第一个参数给本轮状态输入，第二个参数给运行配置，可省略。默认返回本轮
   最终状态。本例不装保存器，因此即使用同一个 `thread_id`，三次都传 0 仍都得到 1。
4. 看保存器演示。无保存器时，第二轮再次传 `turns=0`，得到 1、1；装了保存器后，
   第二轮**只传新请求**，节点实际读到旧 `turns=1`，得到 1、2。`checkpointer` 是
   `compile` 的参数名，传入的 `saver` 才是 `SqliteSaver` 对象；这里的数据库在内存里，
   关闭程序后会消失。
5. 看读取快照演示。新 `thread_id` 的 `get_state(config)` 会返回 `StateSnapshot` 对象，
   在**本例必填字段还未写入时** `.values` 是 `{}`；运行一次 `invoke` 后，再读到
   `request` 与 `turns=1`。重复 `get_state` 不会多执行节点。练习 B 的新工单也按
   `.values` 是否为空判断；不要用“返回对象是不是 `None`”判断。
6. 最后运行文件保存演示。第一条命令传 `turns=0`，让节点算到 1；第一个 Python 进程
   结束后，第二条命令带 `--continue`，只传新 `request`，节点却从旧的 1 算到 2。
   `DB_FILE` 固定文件位置，`CONFIG` 中的 `thread_id` 选其中的会话。若先前跑过首轮，
   新的首轮仍显式传 0；第二轮才接续。PyCharm 第二次在运行配置的脚本参数里填
   `--continue`；文件按脚本位置定位，不受工作目录影响。`.sqlite` 是数据库文件，
   不要在 PyCharm 中把它当普通文本打开；可选的查看脚本会打印可理解的字段。
7. 然后做练习 A、B。B 用 `ticket_id` 建 `config`，先读旧快照；新工单传 0 与一条
   `HumanMessage`，旧工单只传本轮新消息。按输出复制第二次运行命令，并用另一新 ID
   对照隔离。观察题由你根据自己的运行结果填写；AI 不预填。本日没有独立记录 md。

在仓库根目录依次运行：

```powershell
# 五个独立概念：每次只读一份源码与对应输出
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_sql_basics_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_config_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_invoke_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_sqlite_saver_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_state_snapshot_demo.py

# 整合演示：第一次从 0 开始；第二次在新的 Python 进程里接上旧次数
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_checkpoint_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_checkpoint_demo.py --continue

# 可选：只读取刚保存的状态
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day32\day32_checkpoint_view.py

# 练习 A；B 的第二次 followup 命令从首次输出复制
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day32_checkpoint_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day32_checkpoint_exercises.py --part b --phase first
```

环境已安装 `langgraph-checkpoint-sqlite==3.1.2`，并写入根 `requirements.txt`；换环境时按
依赖清单安装。Day 32 的脚本完全离线，不需要 `.env`。演示与练习生成的 `*.sqlite` 文件在脚本
旁边，已被 `.gitignore` 忽略；需要继续旧会话时不要删除对应文件。演示和练习里的客服
信息是教学数据，不是学员的运行观察。

官方文档先看 [`invoke` API](https://reference.langchain.com/python/langgraph/pregel/main/Pregel/invoke)
的 `input`、`config` 两项与 Returns，其他选项暂不要求；再看
[Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
中的 **Threads、Get state、Checkpointer libraries**，看 `thread_id` 如何选会话、
`get_state` 返回的状态快照、SQLite 为何需要单独安装；
[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 中只看开头与
**Checkpointer vs. store** 对照，区分本课的线程状态与跨线程的长期记忆。

- [x] 学员读完独立小演示，并通过两次独立运行的练习解释旧状态怎样接续。
- [x] A 能把图状态写进本地检查点；B 同一工单两次运行得到 2 → 4 条消息、1 → 2 次回复。
- [x] 换新工单 ID 能从零开始；学员据真实输出完成四道观察。
- [x] AI 实跑批改后清练习脚手架、检查格式与故障台账，再做本地提交。

### 2026-10-17 演示订正

学员反馈原演示的参数解析、随机 ID、路径与快照细节太密集。AI 已改成固定文件与会话 ID、
两条命令只对照 `turns` 的 0 → 1 → 2。简化时曾误用相对数据库路径；从脚本目录运行
复现 `sqlite3.OperationalError: unable to open database file` 后，改为按脚本位置定位数据库。
AI 用不同工作目录和两个独立进程复测通过；原学员 SQLite 文件未清理。练习与观察尚待学员完成。

### 2026-10-17 再次教学订正

学员指出：原演示虽能看到 `turns` 接续，却没有教 `config` 是什么、检查点是什么，
更没有展示「没旧状态」怎么从 `get_state` 的结果判断；SQL 小演示的若干 Python 调用也未在
输出中解释清楚。现已让检查点演示按「运行配置 → 未使用会话的空 `.values` → 已有会话的
旧字段 → `invoke` 执行 → 再读新状态」顺序打印；SQL 演示逐条解释 Python 调用和 SQL
语句，练习 B 题干补上必要的入参、返回形状。AI 用独立临时数据库分两个 Python 进程复测
0 → 1 → 2，未把该结果写成学员观察。学员目前写了 A 的实现，B 和四道观察仍待完成。

### 2026-10-17 分拆前置概念的订正

学员再次指出，把几个新概念堆在原演示里，轻补几句话仍无法从零看懂。AI 现把 SQL、
`config`、`SqliteSaver`、`StateSnapshot.values` 各写成独立可运行的小演示：SQL 先打印
全部三行再筛选；保存器用未安装与已安装的两组输出对照；快照在写入前后读取。原演示收为
最后的跨进程整合，不再承担所有概念的首次讲解。上面按新顺序列出命令。小演示与整合
演示的试跑只验证 AI 教具，不代表学员已完成练习或观察。后来学员单独问到 `invoke` 的
参数，AI 再在 `config` 与保存器演示之间增加一份不装保存器的 `invoke` 小演示。

### 2026-10-17 Day 32 验收

学员完成 A、B 和四道观察，并反馈分拆后的演示更容易理解。Q1 的旧状态恢复与 Q3 的
两种 ID 均已由学员订正；Q1 把输入字典的 `messages` 键写成 `message`，属于一处待留意的
笔误，学员原答保留。AI 将练习题干清为简短 docstring，并在隔离 SQLite 文件中分进程
实跑：A 为 2 条消息、1 次回复；B 同工单从 2 条、1 次接到 4 条、2 次；新工单重新从
2 条、1 次开始。仓库测试 9 项通过。下一次按跨天复验安排检查能否独立说出
`thread_id`、消息 ID、`get_state` 与 `invoke` 的作用。

## Day 33：先暂停等人确认，再恢复执行

**今天只新增一个主要机制：在节点里暂停，等人给决定后恢复。** Day 32 的“继续”是
已结束会话接收一条新输入；今天的图还停在 `review` 节点。`interrupt(问题)` 把问题交给
外部并保存暂停位置；第一次 `invoke` 的输出含 `__interrupt__`。人决定后，用同一
`thread_id` 调用 `graph.invoke(Command(resume=决定), config)`，这个决定成为节点里
`interrupt` 的返回值。恢复会从该节点**开头**重新执行，因此确认前不能先做真实动作。

| 顺序 | 文件 | 这一次只看什么 |
|---|---|---|
| 1 | `demos/day33/day33_interrupt_demo.py` | `interrupt` 接口：必填 `value`、可选 `response_schema`、暂停输出、返回时机和使用条件 |
| 2 | `demos/day33/day33_resume_demo.py` | `resume` 参数：创建命令与执行命令的区别；文字、`False`、字典回答的值与类型 |
| 3 | `demos/day33/day33_replay_demo.py` | 节点重跑机制：只用 `before/after` 位置记录，观察恢复从哪里重新执行 |
| 4 | `demos/day33/day33_side_effect_demo.py` | 副作用：客服生成通知文案，再模拟发送到客户收件箱；对照返回值与客户实际收到的条数 |
| 5 | `demos/day33/day33_idempotency_demo.py` | 幂等：纯 Python 对照同编号重试和新编号请求，实际动作数为 1、1、2 |
| 6 | `demos/day33/day33_checkpoint_resume_demo.py` | 最后整合：完整审核图、文件检查点、恢复、条件边、获准后的模拟动作与去重 |
| 练习 | `exercises/day33_approval_exercises.py` | A 自己写暂停审核；B 自己写恢复入口；对照批准、拒绝和重复编号 |
| 可选答疑 | `demos/day33/day33_response_schema_demo.py` | 对照普通格式字典仅提供说明、带类型的 schema 实际校验，以及错误回答的 ValidationError |
| 可选复习 | `demos/day33/day33_node_update_demo.py` | 同一函数普通调用与作为图节点运行的区别：谁把返回字典应用到状态，以及其他字段为何保留 |

前五份按知识点分别设计案例和最小运行环境，不导入另一份演示的业务图。先读各自的接口
说明和输入输出，再看标为已学运行环境的支持代码。`interrupt`、`resume`、重跑演示各用
全新的内存 SQLite；副作用、幂等两份演示只用普通 Python。最后一份才把知识点接成业务图，使用脚本旁的
`demos/day33/day33_integrated_review.sqlite` 文件，不会操作 Day 32 或旧版教具的数据库。它用 `--resume` 代表教学中
“人已批准”，不调用真实发布系统；在 PyCharm 第二次运行时，把 `--resume` 填到
运行配置的脚本参数里。练习换成配送申请：AI 给定图路线和模拟动作，学员只写
`request_review` 与 `resume_dispatch`。A 用 `--part a` 单独观察暂停，B 用 `--part b`
对照批准与拒绝。两个函数现已完成，题干已清为简短 docstring。
题末保留学员根据实际输出填写的四道“现象与原因”；今天没有另一份记录 md。

从仓库根目录运行：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_interrupt_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_resume_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_replay_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_side_effect_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_idempotency_demo.py

# 跨进程整合：第一条暂停；等它退出后再运行第二条恢复
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_checkpoint_resume_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day33\day33_checkpoint_resume_demo.py --resume

# 复跑已完成练习：A 观察暂停，B 观察批准和拒绝两组
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day33_approval_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day33_approval_exercises.py --part b
```

官方文档读 [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) 的
**Pause using interrupt、Resuming interrupts、Rules of interrupts** 三节：分别对应
第一份输出里的 `__interrupt__`、第二份的 `Command(resume=...)`，以及第三份的节点重跑。
第一份中的可选 `response_schema` 只需了解用途；本日练习不要求结构化回答校验。
Day 33 先用已学过的 `invoke`，不要求学习文档里的 `stream_events`。模拟动作使用进程内
列表，只证明本次教学运行的次数；真实发货或转账还需用持久的业务编号防重复，检查点本身
不保证外部动作在异常重试时恰好执行一次。

- [ ] 学员分别运行五份知识点演示，能说明接口参数、返回值、重跑位置、副作用与同编号去重。
- [ ] 学员在两个进程运行文件整合演示，看到暂停时 `next=('review',)`、恢复后 `next=()`。
- [x] 学员完成练习 A、B：未确认 0 次，批准 1 次，拒绝 0 次，同编号重复请求仍 1 次。
- [x] 学员依据自己的输出完成四道观察并订正；AI 已验收并清理练习脚手架。

### 2026-10-18 按知识点重做演示

学员读完初版前两份后指出，它们沿用同一个审批案例并互相导入业务图，本质仍是一份演示
切成几段。现将 `interrupt` 与 `resume` 各自改为接口课，单独对照参数、值和类型；节点重跑
另用位置记录，副作用与幂等也各用一份纯 Python 演示。最后的整合文件才连接完整审核与执行流程。AI 的试跑只
验证教具，学员的练习与观察仍待完成。

### 2026-10-18 首次交作业批改

AI 实跑学员 A 与 B：A 暂停在 `('review',)`、外部动作数为 0；B 批准后
`approved=True`、状态次数和外部次数均为 1；拒绝后为 False、0、0；同编号再次请求
仍只有一条动作记录。学员代码逻辑正确，AI 已修导入顺序与格式，原始观察保留。
第 2、4 题正确；第 1 题需把节点名称与 `.next` 的元组形状区分开，第 3 题需补清
“LangGraph 从中断节点开头重跑，再到 interrupt 取回回答”的时序，并说明打印重跑
与批准后的配送动作次数不同。当前保留题干，待学员补充后再完成验收收尾。

学员同时指出最终演示与练习仍太像，本次题目不重做；从 Day 34 起默认只给知识点演示、
清楚的练习提示与验收，把综合实现留给学员。若确需完整演示，练习另用关键决策不同的
情境。本次通过属于引导练习，独立迁移留待 Day 34～35 的新输入与恢复变式验收。

### 2026-10-18 Day 33 验收

学员补充第 1、3 题后，四道观察可以通过：`.next` 已写为 `('review',)`；
能够区分审核节点从暂停到恢复打印两次，与批准才执行配送、拒绝不执行配送。
第 3 题“interrupt 得到值后重跑”的措辞保留原稿，批改时补充准确时序：
恢复时先从节点开头重跑，走到 `interrupt` 才取得 `resume` 的值。

AI 再实跑 A、B：首次暂停 0 次；批准后状态次数与外部次数均为 1；拒绝均为 0；
同编号重复请求仍为 1。只清理完成练习的题干和导入格式，保留学员逻辑、观察与上面的
首次批改记录。上方未勾选的演示阅读与跨进程操作没有逐项确认，不冒充学员完成证据。
本次引导练习验收完成，独立整合仍由 Day 34～35 检验。

收尾验证：仓库现有测试 `9 passed`，使用 `-p no:cacheprovider`，未新增
`.pytest_cache`；Ruff 检查通过。格式检查排除不属于本次的根目录 `1.py`，
其余 160 个 Python 文件通过；本次测试的 `.pytest_tmp` 已清理。

同日后续订正：学员要求直接修改第 3 题的时序表述，AI 已在练习原句处改为
“恢复时先从 review 节点开头重新执行，走到 interrupt 时才取得 resume 的值”，
并注明订正日期与来源；上面的验收记录保留当时的批改过程。

## Day 34：自己把手写 Agent 接成图

**今天要交付一个能按原行为停止的框架版 Agent。** Day 29～33 分别练过状态、条件边、
消息合并、检查点与人工确认；今天先把 Day 27 的单任务循环接成图。AI 给本地工具、
固定模型回复、输入和对照输出，学员完成模型节点、工具节点、停止判断、路由、接图与
公开返回结果。没有可逐行搬进练习的完整整合演示。

新增的接口知识只处理一件事：**旧字典消息与消息对象怎样转换**。旧假模型读
`message['role']`，消息对象用 `.type`；旧工具点单参数在 `function.arguments` 中是
JSON 文本，`AIMessage.tool_calls` 的 `args` 则是字典。这些形状不能混用，先分别学会
两个方向的转换。它们都不调用模型、不执行工具。

| 文件 | 用途 |
|---|---|
| `demos/day34/day34_to_messages_demo.py` | 独立讲 `convert_to_messages`：一批字典变消息对象，角色、参数和 ID 怎样对应 |
| `demos/day34/day34_to_native_demo.py` | 独立讲 `convert_to_openai_messages`：单条与列表返回形状、参数 JSON 与可选参数 |
| `demos/day34/day34_usage_vs_timeout_demo.py` | 答疑对照：正常返回消息但 usage=None，与抛 TimeoutError 没拿到响应 |
| `exercises/day34_graph_exercises.py` | 学员完成 A～D 七个函数、两道短题与五道观察；已验收并清理长题干 |
| `demos/day34/day34_support.py` | 六个公开接口集中说明参数、返回值与例子；直接运行打印手册，底层复用旧工具与停止函数，不实现图 |

以下为当天练习安排，现已完成验收，保留用于回看学习过程：

1. 先在练习末尾用 10～15 分钟闭卷回答两道短题，查自己是否还记得消息合并与无进展重复。
   写完保留原预测，再看旧实现；没有进行前不勾跨天复验。
2. 分别运行两份演示，从 `main` 顺读源码与输出；每次只看一个转换接口。
3. **A** 写 `model_node`，运行 `--part a`。只检查一次请求、请求前到期和请求中超时，
   此时尚未接图，也不执行工具。参数的来源、返回形状与轨迹字段都在函数说明里。
4. **B** 写 `tools_node`，运行 `--part b`。使用固定教学点单，可不依赖 A；
   核对单点单、多点单、错误回填与代码权限，不能只处理 `tool_calls[0]`。
5. **C** 写 `check_limits`，运行 `--part c`。这些是预制输入轨迹，分别检查参数键顺序、
   观察更新与多个停止条件同到时的选择，不代表你已运行完整 Agent。
6. **D** 完成两个路由函数、`build_agent_graph` 与 `run_graph_agent`。
   先用 `--part d --case 1` 检查正常链条，再按下表核对失败与变式；最后运行全部情境。
   图的路线由你根据需求接起，不把旧 `for/while` 循环藏进某个节点。
7. 根据输出填末尾五道观察。今天没有独立交付物 md，不另写一份相同记录。

从仓库根目录运行：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day34\day34_to_messages_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day34\day34_to_native_demo.py

# 不记得复用函数的参数或返回值时，直接运行本地接口手册，不用逐个找旧文件
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day34\day34_support.py

# A、B、C 都是单节点检查，写好对应函数后再运行
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part b
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part c

# D 接图后先检查一组，再运行全部 16 组；也可把这些参数填进 PyCharm 脚本形参
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part d --case 1
.venv\Scripts\python.exe -B weeks\week04_frameworks\exercises\day34_graph_exercises.py --part d
```

当前 A～D 已完成，可直接运行单节点或完整图检查。
阅读练习时先看 `AgentState` 与 A～D；下面标出的检查环境只负责准备输入和打印。
`limits` 的七项默认值沿用 Day 27；`usages` 是各次收到响应的原始用量列表，最终公开的
`usage` 是它的汇总。`steps` 统计模型请求尝试次数，工具节点与停止判断都不加次数。
单次超时计一次尝试，但没有收到 usage，故用量汇总的 `requests` 可能比 `steps` 小。

必须保留的边界：请求前检查任务总时限；只把模型最终答复当作 `answer`；整批工具执行
并回填后，再按重复、预算、最大请求次数的顺序检查是否允许下次请求。预算函数自身仍按
token、成本、用量缺失选择。模型本轮已给最终答复时，即使刚达到次数或 token 阈值，
也保留成功结果。这是沿用 Day 27 的契约，不由 LangGraph 自动保证。

| D 编号 | 要核对的区别 | 停止原因 / 请求数 / tool 观察总数 |
|---|---|---|
| 1 | 正常先检索后计算，55 元与出处 | `final_answer` / 3 / 2 |
| 2、4 | 无命中重复与连续失败 | `repeated_call` / 2 / 2 |
| 3 | 坏参数回填后模型解释错误 | `final_answer` / 2 / 1 |
| 5、6 | 代码权限来自应用；获准与拒绝的观察不同 | `final_answer` / 3 / 2 |
| 7、8、9 | 用量缺失、token 阈值、成本阈值 | 各自预算原因 / 1 / 1 |
| 10 | 工具已算完，模型还没最终答复就达到请求上限 | `max_steps` / 2 / 2 |
| 11、12 | 请求前任务已到期 vs 请求中超时 | `task_timeout` / 0 / 0；`call_timeout` / 1 / 0 |
| 13 | 只改数量为 7，不能写死 55 | `final_answer` / 3 / 2，77 元 |
| 14、15 | 同轮两条点单；上限只阻止下一次请求，不截断本轮回填 | 成功 / 2 / 2；`max_steps` / 1 / 2 |
| 16 | 最终答复与 token、次数阈值同时出现 | `final_answer` / 1 / 0 |

D 还先打印一组“历史有点单、本轮已答复”的路由检查，必须结束，不能重做旧工具。
这些期望是 AI 预设的验收要求；只有你完成自己的图并运行，才是学习成果证据。

官方接口只查两页的 **Parameters / Returns / Example**：
[`convert_to_messages`](https://reference.langchain.com/python/langchain-core/messages/utils/convert_to_messages)
对应字典到对象，
[`convert_to_openai_messages`](https://reference.langchain.com/python/langchain-core/messages/utils/convert_to_openai_messages)
对应对象到字典，重点看单条与列表、`include_id`；其余可选参数了解用途即可。
建图忘了再看 [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) 的
**State、Reducers、Nodes、Edges**，对应当前状态更新与条件边，不扩展其他框架接口。

今天每次调用都从一个新任务开始，假模型不支持在同一历史里开始第二个新问题。
文件检查点、人工确认接入自己的图，以及同题对比与恢复后的计数检查，留到 Day 35；
较重时可跨学习日，不把所有验收挤进一个自然日。Day 33 的单进程列表仍不保证跨进程
外部动作去重，这一边界不变。今天没有联网分支，不需要 `.env`，不读写已有 SQLite 文件。

- [x] 学员完成两道短题并订正，已学习两份独立转换演示；不把当次订正记为跨天复验。
- [x] A、B、C 的单节点输入、输出和原输入保留检查通过。
- [x] D 完成节点、停止与接图，16 组预期和旧历史路由对照符合要求。
- [x] 学员写完五道观察并订正，AI 实跑验收；长题干已清理，格式检查与故障台账已完成。

### 2026-10-18 Day 34 教具交付检查

AI 已逐份运行两份独立演示，并验证 16 组预制情境经过两个方向的消息转换后，仍能由
已验收的 Day 27 循环得到指定行为；检查器不会因补消息 ID 改动原输入。
练习从仓库根目录及脚本目录能导入；A～D 仍抛对应的待完成标记，七个函数均留空。
仓库现有测试 `9 passed`，Ruff 检查与排除无关 `1.py` 后的格式检查通过；本次
`.pytest_tmp` 已清理。这些只验证 AI 教具和检查环境，学员新图尚未实现或验收。

同日导入修复：学员反馈支持文件引用标红。现将跨周导入改为明确的
`weeks.week03_agent_loop...` 包路径，并补包标记文件；保留旧脚本内部导入兼容。
根目录与脚本目录的启动检查、转换后的 16 组教具检查和 Ruff 均通过。

同日接口查阅改进：学员指出逐个追读导入文件太麻烦。现在把六个公开接口的定义与
完整说明集中在 `demos/day34/day34_support.py`，查看定义和 IDE 提示可直接看到参数、返回字段、
例子与边界；底层统一通过一个内部 Week 03 模块复用。直接运行支持文件只打印手册，
不执行工具或完整练习。练习题也已改为指向本地说明，学员的节点与观察保持待完成。
六个接口的签名、文档例子和输入保留已核对；16 组教具行为复查通过，支持文件 Ruff 通过。

同日 A 返回接口补齐：原题只说节点交回部分更新，未集中说明各分支的返回键，学员因此
无法确定接口。现明确 `model_node` 四种分支统一返回 `messages / trace / usages /
steps / answer / stop_reason` 六项；原始响应的 `message / usage / finish_reason`
与图状态更新分开说明。A 检查入口打印实际键与期望键，题干列出四种分支的字段要求，
没有改写学员正在编写的函数体。
轨迹继续沿用 Day 27 的四类事件：完整字段与请求计数规则集中在支持文件
`TRACE_GUIDE`；直接运行支持文件时先打印这一节，A 的题干也指向同一处。

### 2026-10-19 C 返回接口与轨迹说明补齐

学员指出 C 的返回值与轨迹要求仍不够明确。现将题干集中写为两项部分更新：
`stop_reason / trace`；继续时原因是 `None`，轨迹不新增；停止时选一个原因，保留
全部旧轨迹后只追加一条含 `step / event / reason` 的 stop 事件。状态中的
`stop_reason` 与事件里的 `reason` 使用同一个原因字符串，键名不同。
`--part c` 的检查入口同步打印实际与期望返回键、新增事件、完整轨迹及不变的请求次数。
本次补充接口与检查环境，学员正在写的函数体和观察保持原样，C 仍待完成验收。

### 2026-10-19 首次函数实跑批改

学员随后完成了 A～D 的函数实现。AI 实跑 A 三组、B 五组、C 六组，并补查最终答复、
用量缺失、混合事件判重、成本与次数同时到达等边界。B 的整批工具执行、错误与权限回填、
调用 ID 配对符合要求；C 的六组加四组额外停止判断均正确。A 的两种超时计数与原因正确，
但成功响应被转换成三条 human 消息，本轮 usage 未加入 usages。

A、B、C 都直接给输入的 trace 追加事件：实跑 A 三组、B 五组均显示原输入被修改，
C 的停止分支也会修改输入。这些是待订正项，不能因脚本退出码为 0 就视为验收通过。

D 的两个路由函数会再次调用节点，且继续、停止方向反了；模型路由还把 tools 写成 tolls。
建图直接报未知目标 end，16 组整图验收暂时无法开始。隔离建图问题检查公开返回接口时，
run_graph_agent 返回的 messages 仍是消息对象，按字典读取 role 会报 TypeError。
AI 仅整理导入与格式，函数逻辑经 AST 比较确认未变；相关 Ruff 检查通过。
保留题干、学员代码、短题原答和未填的观察，等订正后再复验。

### 2026-10-19 第二次函数复查

学员订正后，A 已返回一条 AIMessage；A、B、C 的输入保护检查全部通过，B 五组工具
对照及 C 六组加四组边界判断通过。两个路由只读已有状态，继续与结束方向正确；
公开返回结果的消息已转为字典，隔离检查的六项接口符合要求。

剩余问题集中在两处：A 的点单分支仍漏记本轮 usage，最终答复分支用 list + dict
导致 TypeError，未收到响应的超时分支却加入了 None；模型条件边的 path_map 没有
tools 键，正常链条运行报 KeyError。D 的请求前到期与单次超时可结束，但后者的
usage 统计仍不符合要求；16 组整图尚未通过。AI 仅整理长行格式，逻辑与观察保留。

### 2026-10-19 代码订正复验通过

学员再次订正后，AI 实跑 A/B/C 共 14 组单节点对照，原输入不变检查全部通过；
A 的五组额外用量与超时边界、旧历史仍有点单但本轮已结束的路由检查也通过。
当前学生图的 16 组情境全部符合要求，并核对了公开返回字段、点单与观察配对、
请求轨迹与 steps、已收到响应用量计数、token 汇总及 final/stop 事件的一致性。
相关 Ruff 检查通过，本轮未改学生函数逻辑。

目前代码部分通过，闭卷短题第 1 题仍需区分消息合并与普通 trace 更新，五道观察仍空。
保留学员原答和题目脚手架，待学员完成记录后再做当天最终验收与收尾。

### 2026-10-19 按学员要求提前清理长题干

学员明确要求缩短练习文件，因此提前删除 A～D 的长题干、接口提示与旧教学说明，
每个函数保留一行 docstring；文件从 692 行缩至 547 行。运行入口、对照数据与输出、
短题原答及五道观察全部保留。去除文档字符串后，全模块 AST 完全一致，末尾记录原文
校验一致；Ruff 检查通过。这次清理不代表记录已完成或当天已经验收。

同日按学员要求，将五道观察题改为简短逻辑问答，不要求填写具体数值、调用 ID 或摘录
输出；五处答案仍留给学员，短题原答和可执行代码未改动。

随后学员提供自己绘制的普通边与条件边流程图，明确要求据图整理第 1 题答案。
AI 已按图转写并注明来源，图中的 tool 对应代码的 tools；其余四题未代填。

### 2026-10-19 观察初稿批改

学员完成五道观察后，AI 重新运行当前图的 16 组案例，并核对消息配对、请求计数与
已收到响应的用量记录，全部通过。仓库测试 `9 passed`；Ruff 检查与排除无关 `1.py`
后的格式检查通过，191 个文件格式符合要求。学员代码和回答均未由 AI 改写。

短题第 2 题与观察第 1～3 题可以通过；短题第 1 题仍需区分题设中的两种更新：
`messages` 的 reducer 会保留旧消息，普通 `trace` 若只交回新事件就会替换旧列表。
观察第 4 题的停止优先级正确，但还需说明怎样比较工具名、解析后的参数与观察，
以及末尾连续相同达到限制的条件。观察第 5 题的超时请求计数正确，用量记录需订正：
请求中超时没有收到响应，应保留原用量列表；当前代码已正确处理，与文字回答不一致。
保留原答，待学员订正后再做当天验收与本地提交。

### 2026-10-19 Day 34 最终验收

学员订正短题第 1 题、补全观察第 4 题的连续重复判据，并改正观察第 5 题的超时用量
解释，三处均可通过。AI 只将末尾的 `Non` 笔误改为 `None`，保留其余原答和函数逻辑。
代码复验记录为 A/B/C 共 14 组、额外用量与路由边界、完整图 16 组全部通过；
仓库测试 `9 passed`，Ruff 检查与格式检查通过。本次完成短题与观察订正验收，
没有新发生的跨天闭卷复验。Day 34 收尾完成，Day 35 尚未开始。

## Day 35：保存报价草稿，确认后再发布

**预计约 1/2 个自然日**，按整周约四天的目标控制范围。复习和独立演示约 20～30 分钟，
三个函数约 60～90 分钟，运行对照与简短观察约 20～30 分钟。沿用自己的 Day 34 模型、
工具与停止判断，不重写七个函数，不重跑全部 16 组旧情境，不另填重复记录表。

具体场景：Agent 先查资料、算出报价草稿；图暂停，把草稿交给人确认。人批准后，
给定工具才在本地 SQLite 模拟发件箱中保存一条记录；拒绝则保留草稿并结束。
这里的“发布”只有本地写入，不发送邮件、不发货、不转账。

今天只扩展一个机制：**用稳定的业务编号，让本地动作重试仍只产生一条记录**。
`quote_id` 是今天自定义的“一次报价发布操作的编号”，是普通字符串，不是 LangGraph
内置参数。`thread_id` 找一段图会话，消息 `id` 标识一条消息，`quote_id` 则让模拟发件箱
识别同一笔报价。CLI 未传 `--quote-id` 时用 `offer-加会话编号` 取默认值，只是方便取名；
同一业务换会话重试时可显式传回原 `--quote-id`。这个新名字先由演示介绍，不放进旧知识闭卷复习。
`SqliteSaver`、`interrupt` 和 `Command(resume=...)` 都是旧知识，今天由你接入自己的图。
人工确认放在模型完成之后，恢复后不再请求模型，不把旧的 `started_at` 用来开始新请求。
本课不扩展“扣除人工等待的执行预算”，也不在已结束会话中再提交新问题；新任务换会话。

| 入口 | 做什么 |
|---|---|
| `demos/day35/day35_sqlite_idempotency_demo.py` | 独立讲 SQLite 主键防重、插入结果与参数；只用内存数据库 |
| `demos/day35/day35_state_inheritance_demo.py` | 先前继承写法的答疑留档，按需看；当前状态已改为直接列全字段 |
| `exercises/day35_persistent_review_exercises.py` | 学员写 A 审核、B 模型路由、C 带保存器的图；末尾写短复习与三道观察 |
| `demos/day35/day35_support.py` | 做题查阅入口：完整状态、六个现成节点/路由的输入输出；直接运行打印手册 |
| `demos/day35/day35_runtime.py` | AI 维护的后台：SQL、CLI、状态打印与对照；无需追读才能完成练习 |

运行顺序：

1. 先写练习末尾的短复习，再跑独立 SQL 演示。不熟的会话和消息 ID，回看 Day 31、32；
   `quote_id` 是今天的新名字，在 SQL 演示里认识。暂停与恢复回看 Day 33 独立演示，
   不要求把全部旧演示重读一遍。
2. 写三个函数，按题干给定的参数、返回值与节点名接图。`support.QuoteState` 已直接列出
   全部十三项字段；直接使用 `support.model_node` 等本地接口，参数与返回值就在同一文件。
   做 A、B 看状态，做 C 查六个现成接口；旧 `support.core` 保留兼容，后台代码由 AI 维护。
3. 用下面几组命令核对批准、拒绝、提前停止与业务防重；输出会显示实际状态，不要求抄值。
4. 最后运行 `compare`，根据两种实现的状态与控制方式回答三道逻辑题。交作业后 AI 再验收。

从仓库根目录运行独立演示：

```powershell
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day35\day35_sqlite_idempotency_demo.py

# 做题时查接口：只打印说明，不运行模型、图或数据库。
.venv\Scripts\python.exe -B weeks\week04_frameworks\demos\day35\day35_support.py
```

写完三个函数后再跑下面的练习。PowerShell 先设置脚本位置；PyCharm 的脚本形参只填
`--phase ...` 等参数，不填变量或解释器。以下会话编号若已用过，请整组换成自己的新编号。
若错误实现已经保存过状态，订正后也换新 `ticket-id` 复测，保留旧记录，不要求删库。

```powershell
$day35Exercise = 'weeks\week04_frameworks\exercises\day35_persistent_review_exercises.py'

# 1. 首次到审核暂停；每条命令都会启动一个新的 Python 进程。
.venv\Scripts\python.exe -B $day35Exercise --phase start --ticket-id d35-allow
.venv\Scripts\python.exe -B $day35Exercise --phase status --ticket-id d35-allow
.venv\Scripts\python.exe -B $day35Exercise --phase status --ticket-id d35-new
.venv\Scripts\python.exe -B $day35Exercise --phase resume --ticket-id d35-allow --decision allow
.venv\Scripts\python.exe -B $day35Exercise --phase resume --ticket-id d35-allow --decision allow

# 2. 另一个新会话拒绝发布。
.venv\Scripts\python.exe -B $day35Exercise --phase start --ticket-id d35-deny
.venv\Scripts\python.exe -B $day35Exercise --phase resume --ticket-id d35-deny --decision deny

# 3. 请求上限使模型未能完成草稿；不应进入审核。
.venv\Scripts\python.exe -B $day35Exercise --phase start --ticket-id d35-limit --max-steps 1

# 4. 换会话但故意使用第一组的业务编号，检查数据库防重。
.venv\Scripts\python.exe -B $day35Exercise --phase start --ticket-id d35-retry --quote-id offer-d35-allow
.venv\Scripts\python.exe -B $day35Exercise --phase resume --ticket-id d35-retry --decision allow

# 复用已完成的手写版与框架版，不重写实现。
.venv\Scripts\python.exe -B $day35Exercise --phase compare
```

核对目标：

- 新业务正常首次暂停：报价草稿含 88 元与出处；`next=('review',)`，三次请求、两条工具观察，
  发件箱为零。`status` 只读；未用会话只显示没有旧状态。
- 批准恢复：`next=()`，此报价记录数为一；原消息、请求数、工具与用量不重复。
  对已结束会话再次 `resume`，入口只显示状态，不重新开任务。
- 拒绝恢复：保留草稿，`approved=False`、无发布记录；`final_answer` 表示模型完成草稿，
  发布成功还要看批准状态与实际发件箱。
- 请求上限：`max_steps` 结束，没有审核与发布；同业务编号的重试会话获准后，本次新增为零，
  原记录仍只有一条。检查点按 `thread_id` 定位，动作按 `quote_id` 防重。
- `compare` 正常与上限两组的四项公开结果应相同，学员说明图与手写循环各自管理什么。

数据默认写到 `demos/day35/day35_checkpoints.sqlite` 与 `day35_outbox.sqlite`，前者保存图，
后者记录模拟动作。`--db` 可指定另一个检查点文件，`--outbox` 只在 start 选择动作文件；
resume 使用状态里已保存的动作文件。相对数据路径以 Day 35 目录为基准，不随终端变。
审核与发布不新增原来的四类 trace 事件；`action_count` 与数据库行数单独核对。

官方文档按需查两处：[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
开头的 **Key points about resuming** 与 **Side effects called before interrupt must be idempotent**，
核对同会话恢复、节点从开头重跑及动作防重；[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
的 **Checkpointer vs. store**，只确认检查点保存会话图状态，本课不新增 store 接口。
当前仓库继续使用已验证的 `invoke`，不扩展网页中的流式调用写法。

- [x] 学员完成三个函数订正，AI 隔离实跑七组检查通过。
- [x] 学员完成三道观察；短复习已作答，不把讲解后作答记成独立复验。
- [x] 学员已留下批准、拒绝、提前停止与同业务编号重试记录；AI 只读核对现有会话与发件箱，另用隔离数据库跨进程复跑。
- [x] AI 实跑学员图并检查 Ruff，验收后清理题干、整理 Week 04 HANDOFF 与本地提交。

### 2026-10-19 Day 35 教具交付检查

AI 顺读独立 SQL 演示的源码与完整输出，内存表的三次提交记录数为 1 → 1 → 2；
未创建文件数据库。另用临时参考图在隔离目录验证九组检查：暂停与点单配对、跨进程
查看和批准、拒绝、提前停止、跨会话业务防重、错误恢复保护、预算与超时边界、同题对照、
未完成骨架明确报错，全部通过。现有仓库测试 `9 passed`，Ruff 检查与 195 个文件的
格式检查通过。教具交付时，学员的三个函数仍为 `NotImplementedError`，短复习与观察留空；
这些验证是 AI 教具检查，不是学员实验或当天验收。默认检查点与发件箱未被 AI 创建。

交付前只读入口订正：`status/resume` 遇到不存在的文件时不创建目录或空库，两个隔离
检查通过。本次临时参考脚本、数据库与 pytest 临时目录由 AI 清理，不触碰既有数据。

### 2026-10-19 按学员要求重写 support 的查阅结构

学员反馈 support 看起来晕。现将十三项状态字段直接列在 `QuoteState`，六个现成接口
改为 `support.model_node` 等直接访问形式，每个本地定义都列出输入和返回值；
SQL、命令行与检查输出移到一个 `day35_runtime.py` 后台文件，由 AI 维护。
直接运行 support 只打印按 A/B/C 查阅的接口手册；原 `support.core` 与辅助名字保留兼容。
继承小实验作为先前答疑留档，不再是阅读当前状态定义的前置要求。

七组兼容核对通过：完整状态与消息 reducer 不变，旧图保存的 SQLite 检查点可由新图
跨进程恢复；批准、拒绝、提前停止、防重与对照行为保持一致。学员代码去除 docstring
后的 AST、短复习与观察原文未变。仓库测试 `9 passed`，五份 Day 35 教具的 Ruff
检查与格式检查通过；练习仍在进行，本次没有代填 B/C 或观察，没有结束当天验收。

### 2026-10-19 Day 35 首次函数批改

AI 使用隔离数据库运行学员当前实现：完整图首次模型点单后报 `KeyError: 'tools'`，
因为模型条件边只有 model/review/end 映射，接不住路由返回的 tools。
单独调用 B 时，stop_reason='final_answer' 实际返回 end，应进入 review；
review 是下一站的标签，不是模型写入的停止原因。

为绕开 B/C 的阻断，AI 将学员 A 单独接入最小审核图：传入 allow 后 approved=False，
而 deny 后为 False。A 用 `is` 比较字符串身份，应比较回答内容。审核载荷与其余
连线、保存器接入未发现额外实质问题，但完整批准/拒绝恢复尚不能验收。
AI 仅整理导入与格式，所有函数去除 docstring 后的 AST 和原始观察保持不变；
格式检查通过，Ruff 仍有与 A 对应的 F632 提示，留给学员订正。题干与观察空位保留。

### 2026-10-19 Day 35 函数订正复验通过

学员修正字符串比较、最终草稿停止原因与 tools 映射后，AI 调用当前真实练习入口，
每条命令均启动新 Python 进程，数据库全部置于临时目录。七组检查通过：首次暂停、
跨进程批准恢复、跨进程拒绝、请求上限、跨会话同业务编号防重、会话与入口保护、
四项停止边界。暂停时三次请求与两条工具观察完整配对，批准发布一条、拒绝零条；
恢复不重复消息、轨迹、请求或用量，已结束会话再次 resume 也不重启任务。

手写与框架的两组四字段对照符合要求；最终草稿优先、单次超时、请求前到期和 token
预算边界符合要求。练习与五份教具的 Ruff 检查、格式检查通过，未修改学员逻辑。
短复习含 thread_od 的字段名笔误，不影响已表达的含义；三道观察仍空，保持待完成。
这些是 AI 批改验证，不代填学员观察；验收记录、交接与提交仍待观察完成后收尾。

### 2026-10-19 Day 35 最终验收与阶段交接

学员补写三道观察后复查通过：已区分草稿完成与实际发布、检查点与业务防重，
能说明手写循环与框架分别怎样管理状态和下一步，并给出适用场景。
第 1 题的“从检查点开始”由 AI 在此补充准确边界：使用同一检查点文件和 `thread_id`
提交 `Command(resume=...)` 后，恢复已有状态和待执行的审核节点；该节点从开头重跑，
在 `interrupt` 处取得决定，不重做已完成的模型与工具节点。恢复入口不重传初始消息和计数。
学员原答及短复习中的 `thread_od` 笔误保留，不改写成当时就已完整理解。

AI 清理三个函数的长题干及导入提示，仅留简短 docstring；去除 docstring 后的全模块
AST 与清理前一致，短复习和三道观察原文逐字保留。随后调用清理后的真实练习入口，
以独立 Python 进程验证批准、重复恢复、拒绝、跨会话同业务编号重试、提前停止和新会话
隔离；模型与工具消息完整配对，审核恢复不新增消息、轨迹、请求或用量，批准新增一条、
拒绝零条、同业务重试新增零条。手写与框架两组四字段对照全部一致。

另以只读连接核对学员已有的 `d35-allow/deny/limit/retry` 四段会话末状态及模拟发件箱；
均符合对应要求，发件箱中同业务编号只有一条记录。两份原 SQLite 文件的 SHA-256
校验值未变。仓库测试 `9 passed`，Ruff 检查及 197 个 Python 文件格式检查通过。
本次临时脚本、隔离数据库与 pytest 临时目录由 AI 清理，用户既有数据库和缓存保留。

Week 04 主线与本次观察验收完成，交接见 [HANDOFF](HANDOFF.md)。三道观察经过答疑，
不能替代跨天闭卷复现；未发生的独立复验继续留在下面的未勾选清单中。

## 跨天复验安排

- [ ] Day 26B 重复判据：按上面的时间窗口用新轨迹复现；AI 届时出题，尚未发生。
- [ ] Day 29 完成后 2～3 天：用 10～15 分钟闭卷写“节点部分更新 + 两节点连接”，
  预测一个先读后写导致旧数据残留的结果；按实际完成日期安排，不机械绑定 Day 32。
- [ ] Day 30 完成后 2～3 天：闭卷画出 model 条件选路、tool 返回 model 的路线，
  再判断一组“历史有点单、本轮已答复”的新输入；尚未发生。
- [ ] Day 31 于 2026-10-16 完成；2～3 天后闭卷区分追加、同消息 ID 更新和工具调用 ID 配对。
- [ ] Day 32 于 2026-10-17 完成；2～3 天后闭卷区分 `thread_id` 与消息 ID，并预测同工单接续和新工单隔离。
- [ ] Day 33 于 2026-10-18 完成；2～3 天后用 10～15 分钟闭卷写同会话恢复入口，并预测节点重跑与外部动作次数。
- [ ] Day 34 于 2026-10-19 完成；2～3 天后用 10～15 分钟闭卷说明消息合并与普通列表更新，并在新输入中判断整批工具回填、重复及超时用量。
- [ ] Day 35 完成后间隔 2～3 天，用新情境独立解释恢复、防重和框架取舍；本次学员实现与答疑后的观察已验收，尚未做延迟独立复验。

## 必做顺序

- [x] 用图表达：模型节点、工具节点、条件边
- [x] 确认消息合并规则，再用一种本地方案持久化状态，支持中断后继续；区分检查点与长期用户记忆
- [x] 在教学数据上加一个需要确认的操作，验证未确认不执行、恢复后不会重复生效
- [x] 用同一组问题比较手写版与框架版，说明状态管理、调试与维护上的取舍

先看 [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) 中的 State、Reducers、Messages 和 Nodes，逐项对应自己的手写循环。消息合并要考虑新增与修改已有消息，不能只记成列表相加。

## 选修

其他 Agent 框架、摘要记忆、向量记忆、用户画像和更换数据库不作为本阶段门槛。

## 验收标准

- [x] 能解释状态在节点之间是怎么传递的（本次练习与答疑后观察验收）
- [x] 能说出「什么时候不该用框架」（本次观察验收，独立迁移待复验）
- [x] 用执行次数和消息轨迹验证中断恢复，不只看最后答案
- [ ] 关键机制完成 2~3 天后，做过一次 10~15 分钟闭卷复现；AI 记录实际证据
