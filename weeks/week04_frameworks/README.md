# Week 04｜框架与记忆

**交付物**：用 LangGraph 重写第 3 周的 Agent（带持久化记忆与人工确认）。

Week 是阶段编号，按验收推进；默认每天 3~5 小时，较重单元可跨天。

## 当前接续点（2026-10-16）

Week 03 的 Day 22～28 主线已验收，证据与限制见
[交接文档](../week03_agent_loop/HANDOFF.md)。Day 29 的状态更新与固定边已验收：
学员完成 A、B 和观察订正，AI 恢复反向实验后遗留的边并实跑检查。Day 30 的条件边
已完成 A、B 和四道观察。Day 31 的消息合并、追加与同 ID 修订已验收；
首次观察中的 ID 混淆经讲解后由学员订正，独立掌握留待跨天复验。Day 29～31 的关键机制
仍须在完成后 2～3 天闭卷复验。

Day 26B 重复判据的延迟复验仍待进行。它在 10 月 14 日完成，10 月 15 日 Day 28
已做过一次新轨迹预测；同日再做不能记成隔天复验，安排在 **10 月 16～17 日或
下一次满足间隔的学习日**用 10～15 分钟复现，不作为本阶段开工门槛。
JD、简历、视频沿用原先的延后安排。

## 本阶段顺序

这是学习单元，不是必须在七个自然日内完成的日历。只提前准备当前单元的代码。

| 单元 | 主要机制与产出 | 状态 |
|---|---|---|
| Day 29 | 状态更新与固定边：筛选资料后生成简报 | 2026-10-15 已验收；延迟复验待做 |
| Day 30 | 条件边：根据模型结果走工具节点或结束，工具回到模型 | 2026-10-16 已验收；延迟复验待做 |
| Day 31 | 消息合并：新增消息与按消息 ID 修改；对照原 tool_call_id 配对 | 2026-10-16 已验收；延迟复验待做 |
| 消化半日 | 闭卷画状态流转、定位顺序/合并错误，补实际缺口 | 待安排 |
| Day 32 | 检查点：一种本地持久化方案、会话标识、重新启动后继续 | 待开始 |
| Day 33 | 人工确认与恢复：确认前不执行，用执行次数检查重复生效 | 待开始 |
| Day 34 | 学员整合：把 Day 27 的工具、停止规则接入框架版 | 待开始 |
| Day 35 | 同题对比、恢复变式、口头解释与交接 | 待开始 |

条件边先用固定模型结果拆解；真实模型接入时由 AI 先验证联网教具，学员再运行自己的
实验。预算、时限、重复判据沿用 Week 03 的行为契约；不会因为换框架就默认由库保证。

## 开工前短检查

- [ ] 不看旧答案讲清手写版的消息回填、停止原因与工具边界。
- [ ] 用短题检查 Week 00 留下的 `*args/**kwargs` 和 Week 01 自评的异常分类；先看现在是否会，只补实际缺口。

题目与回答空位都在 `day29_state_exercises.py` 顶部，不另外写一份记录。
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
| `day29_state_demo.py` | 一个节点整理关键词；对照未返回字段的保留和列表字段的替换 |
| `day29_state_exercises.py` | 顶部短检查；A 写筛选节点；B 接两节点；末尾写观察 |

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
.venv\Scripts\python.exe -B weeks\week04_frameworks\day29_state_exercises.py --part warmup

# 读演示：完全离线，不需要 .env
.venv\Scripts\python.exe -B weeks\week04_frameworks\day29_state_demo.py

# 分别重跑 A、B 的三组对照
.venv\Scripts\python.exe -B weeks\week04_frameworks\day29_state_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\day29_state_exercises.py --part b
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
| `day30_conditional_demo.py` | 固定假模型对普通／加急请求选不同路线，只演示一次选路，不写完整回环 |
| `day30_conditional_exercises.py` | A 写本轮回复的选路函数；B 接模型、工具与返回模型的边；末尾写观察 |

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
.venv\Scripts\python.exe -B weeks\week04_frameworks\day30_conditional_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\day30_conditional_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\day30_conditional_exercises.py --part b
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
| `day31_messages_demo.py` | 同一条固定路线对照无合并规则时覆盖、有规则时追加及同消息 ID 修订 |
| `day31_messages_exercises.py` | A 回填本地查询的一条 tool 消息；B 配消息规则并接两节点，末尾写观察 |

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
.venv\Scripts\python.exe -B weeks\week04_frameworks\day31_messages_demo.py
.venv\Scripts\python.exe -B weeks\week04_frameworks\day31_messages_exercises.py --part a
.venv\Scripts\python.exe -B weeks\week04_frameworks\day31_messages_exercises.py --part b
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

## 跨天复验安排

- [ ] Day 26B 重复判据：按上面的时间窗口用新轨迹复现；AI 届时出题，尚未发生。
- [ ] Day 29 完成后 2～3 天：用 10～15 分钟闭卷写“节点部分更新 + 两节点连接”，
  预测一个先读后写导致旧数据残留的结果；按实际完成日期安排，不机械绑定 Day 32。
- [ ] Day 30 完成后 2～3 天：闭卷画出 model 条件选路、tool 返回 model 的路线，
  再判断一组“历史有点单、本轮已答复”的新输入；尚未发生。
- [ ] Day 31 于 2026-10-16 完成；2～3 天后闭卷区分追加、同消息 ID 更新和工具调用 ID 配对。
- [ ] Day 35 用新输入与恢复情境验收，不把 AI 验证教具记成学员通过。

## 必做顺序

- [ ] 用图表达：模型节点、工具节点、条件边
- [ ] 确认消息合并规则，再用一种本地方案持久化状态，支持中断后继续；区分检查点与长期用户记忆
- [ ] 在教学数据上加一个需要确认的操作，验证未确认不执行、恢复后不会重复生效
- [ ] 用同一组问题比较手写版与框架版，说明状态管理、调试与维护上的取舍

先看 [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) 中的 State、Reducers、Messages 和 Nodes，逐项对应自己的手写循环。消息合并要考虑新增与修改已有消息，不能只记成列表相加。

## 选修

其他 Agent 框架、摘要记忆、向量记忆、用户画像和更换数据库不作为本阶段门槛。

## 验收标准

- [ ] 能解释状态在节点之间是怎么传递的
- [ ] 能说出「什么时候不该用框架」
- [ ] 用执行次数和消息轨迹验证中断恢复，不只看最后答案
- [ ] 关键机制完成 2~3 天后，做过一次 10~15 分钟闭卷复现；AI 记录实际证据
