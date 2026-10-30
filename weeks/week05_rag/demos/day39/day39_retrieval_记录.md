# Day 39｜存储、候选与原文核对

这是学员待填记录，数据与结论由你亲自运行、核对后填写。今天的 A/B 使用 AI 教学资料；
它们不算你自有资料的问答基线。本文件集中保存观察，练习文件末尾不再重复写。

2026-10-24：以下 A/B 运行数据来自学员贴出的实际输出，由 AI 按学员授权转录；
解释、判断与原因继续由学员填写。

## 今天的观察

### 1. A：写入、重写和重开，记录数怎样变化？

运行练习 `--part a`，从输出填写：

本次独立库目录：`C:\Users\dell\Documents\Codex\2026-09-24\s\agent-learning\weeks\week05_rag\demos\day39\outputs\exercise_a_a6ktc7zj`。
输入为 3 对片段与向量，模型为 `BAAI/bge-small-zh-v1.5`，每条期望维度为 512。

| 核对项 | 我的实际结果 |
|---|---|
| 首次提交数与首次库记录数 | 提交 3 条；库记录数 3 条 |
| 同一快照再次提交数与库记录数 | 再提交 3 条；库记录数仍为 3 条 |
| 空批次返回值 | 0 |
| 错误维度批次的异常与测试集合记录数 | ValueError；测试集合记录数 0 条 |
| 关闭后重开得到的记录数 | 3 条；按编号读回 3 条 |
| 输入未改动 | True |

挑一条实际记录，写下数据库 id、原片段 id、source 和原行范围：

- 数据库 id：`1`
- 原片段 id：`notes/office.md#L1-L3`
- source：`notes/office.md`
- 原行范围：第 1～3 行

解释：为什么同一快照再提交后，记录数不按提交数累加？数据库 id 和原片段 id 各用在哪里？
两个正文相同而来源不同的片段，是否都保留了？用实际字段说明：
记录按id提交，同一快照再提交第二次只会更新上一次的记录，两次内容一样就没有变化
数据库id用于记录进入数据库后的point
原片段id用于确认片段的来源
都保留了
数据库 id=1；原片段 id=notes/office.md#L1-L3
来源=notes/office.md；原行=1～3
正文='# 办公设备使用教学资料\n借用投影仪需要在前台登记。\n归还时请同时交回遥控器和电源线。'；模型=BAAI/bge-small-zh-v1.5
数据库 id=3；原片段 id=archive/office.md#L1-L3
来源=archive/office.md；原行=1～3
正文='# 办公设备使用教学资料\n借用投影仪需要在前台登记。\n归还时请同时交回遥控器和电源线。'；模型=BAAI/bge-small-zh-v1.5
### 2. B：limit、并列候选和恢复后的片段

运行 `--part b`。记录第一个问题在 limit=1、2、5 时的实际条数，并选择 limit=2 的
结果记录原片段 id、source、行范围与分数；相同分数时不要求固定先后顺序。

| 核对项 | 我的实际结果 |
|---|---|
| limit=1 / 2 / 5 的实际条数 | 分别为 1 / 2 / 3 条 |
| limit=2 的第一条：原片段 id、来源、范围、分数 | `archive/rooms.txt#L5-L5`；`archive/rooms.txt`；第 5～5 行；0.750611 |
| limit=2 的第二条：原片段 id、来源、范围、分数 | `rooms/guide.txt#L2-L2`；`rooms/guide.txt`；第 2～2 行；0.750611 |
| 空集合查询结果 | `[]` |
| limit=0 与 511 维查询的异常 | 两者均为 ValueError |

解释：结果里的原片段编号与数据库的 17/29/43 是不是一回事？哪些字段必须从 payload
恢复？limit 变大是否就意味着每条结果都更有用？用这次输出说明：
不是一回事，page_content，id，metadata中的source，line_start，line_end都要从 payload
恢复。
limit变大并不就意味着每条结果都更有用
问题为”会议结束后需要关闭哪些设备？“ limit=5时，新增的候选正文为”餐补报销应附支付凭证。”
这条结果并没有什么用

### 3. B：有候选，原文就能回答问题吗？

找到“会议室空调最低温度是多少？”这一组，记录 limit=2 时的实际候选与分数：

| 候选 | 原片段 id | source | 原行范围 | 余弦分数 | 正文 |
|---|---|---|---|---|---|
| 1 | `archive/rooms.txt#L5-L5` | `archive/rooms.txt` | 第 5～5 行 | 0.571262 | 会议结束后请关闭投影仪和空调。 |
| 2 | `rooms/guide.txt#L2-L2` | `rooms/guide.txt` | 第 2～2 行 | 0.571262 | 会议结束后请关闭投影仪和空调。 |

回看 B 打印的带行号原文，它有没有给出所问的具体信息？原文依据是什么？
问题为会议结束后需要关闭哪些设备？ 正文='会议结束后请关闭投影仪和空调。' 给出了具体信息
问题为会议室空调最低温度是多少？  正文='会议结束后请关闭投影仪和空调。'  并没有给出具体信息
比较“空集合返回空列表”和“返回了候选但原文不足以回答”，两种情况分别说明什么？
空集合返回空列表说明没有资料可以查询
返回了候选但原文不足以回答说明资料可能与问题主题相关但没有提供所问的具体信息
## 自有资料基线｜在 Day 41 验收前补齐约 10 条

2026-10-28 接续说明：本表继续作为 Day 41 唯一的十条基线表，不再复制一份。
学员已选择仓库根目录下的 `notes/python-notes.md`。问题和期望先由学员读原文填写，
再用 Day 41 的 batch 读取本表已填问题，复用一次建库与同一全文快照运行。
“实际候选”可记录对应结果 JSON 的路径和关键 id/分数；“判断与原因”分别说明
检索是否命中、回答内容是否正确、引用是否支持结论。结果 JSON 保存了候选、原始
响应、用量与校验结果，不要求在多处重复抄写。原有三道教学观察保留在上方。
下方旧 query 命令保留供复看；Day 41 按本周 README 的新入口运行即可，不必把同题重复跑两遍。

这里的一条是一个测试问题，约十条就是约十个问题。可以围绕自己选定的一两份现有
学习笔记提问，不要求准备十份资料。问题里既包含原文能支持回答的，也留少量原文
没有提供所问信息的；由学员读原文确定，不由检索结果反推期望。

“基线”指当前版本还没进一步优化时的检索结果。先保存这一版，以后调整切分或检索
方式，再用同一批问题比较。当前只记录检索候选；生成模型的回答在后续单元接入。

今天优先完成上面的三道观察；下面的资料选择与样本可分步准备，不额外加一套同构练习。
问题与期望来源由你先核对原文填写，再运行查询记录实际候选，保留优化前基线。

资料格式沿用已选的 UTF-8 文本或 Markdown。记录所选目录、相对文件列表、所用模型与
切分设置；模型和默认窗口设置可从本周 README 与已有代码核对，不猜未记录的数据。

我的资料根目录、相对路径列表及运行设置：

此处与 Day 41 记录的实际运行设置只需填写一处，另一处写文件链接即可。

先显示原文与行号，尚未写完 A/B 也能运行这条入口。把示例路径替换为自己的：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day39_vector_store_exercises.py --part sources --source-root "C:\我的资料目录" --paths notes.md handbook.txt
```

两题完成后，逐条运行自己的问题，终端会打印模型、库目录、实际候选的编号、正文、
来源、行范围和余弦分数。每次创建新的独立库目录，避免覆盖上一次记录。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week05_rag\exercises\day39_vector_store_exercises.py --part query --source-root "C:\我的资料目录" --paths notes.md handbook.txt --question "这里换成我的实际问题" --limit 2
```

“期望来源/无答案”由你读取所选原文判断；无答案样本说明为什么所选资料不足即可，
不编造原文位置。“实际候选”来自 query 命令；“判断与原因”由你逐条核对。今天不要求
填写生成模型的答案或引用正确率，这些等后续单元接入后再观察。

2026-10-30 补充：按学员明确要求，十条问题与期望由 AI 根据所选
`notes/python-notes.md` 原文整理，含八条有答案、两条资料不足的问题。下列行号指
包含答案依据的原文位置，检索片段可以覆盖更大的行范围，不要求窗口边界与期望行号相同。

2026-10-30 运行转录：学员告知本次 batch 已跑完，AI 从 `day41/outputs/run_jg_k2_vk/`
的十份结果 JSON 转录下表候选，按返回顺序列出，余弦分数保留六位小数；完整精度、正文、
真实模型回复和用量见各行的结果链接。本批候选来源均为 `notes/python-notes.md`，
编号中的 `L起始-L结束` 同时标明原行范围。模型 status、引用和用量汇总见
[Day 41 记录第 3 节](../day41/day41_rag_记录.md#3-约十条自有资料基线只维护原有一份表)，
[十题模型完整回答](../day41/day41_rag_记录.md#模型实际回答2026-10-30-原文转录)也已逐字转录。

观察归档（2026-10-30）：十条“我的判断与原因”已由学员完成，第 7、8 题经反馈订正后
完成本轮观察验收。AI 将十条观察原文逐题归档到下表最后一列，核对一致后按学员要求
删除临时 scratch.md。第 7、8 题的首稿留痕保留在 Day 41 记录，详细批改反馈见聊天；
本轮有答疑与订正，不记作十题全项独立定位或跨天掌握。项目中的问题、期望、运行数据与模型回答继续保留。

| 编号 | 我的问题 | 期望来源与原行范围，或无答案 | 实际候选（id、来源、范围、分数） | 我的判断与原因 |
|---|---|---|---|---|
| 1 | 怎样把多条消息拼成一段文字，让每条消息各占一行？ | `notes/python-notes.md` 第 24 行：先用 `append` 收集到列表，最后用换行符 `join` 拼接。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_01.json)<br>① `notes/python-notes.md#L13-L20`：0.652674<br>② `notes/python-notes.md#L7-L14`：0.642272<br>③ `notes/python-notes.md#L19-L26`：0.568149 | 检索找全了，回答准确完整，引用支持回答 |
| 2 | 字典里的键可能不存在时，怎样读取它，并指定默认值？ | `notes/python-notes.md` 第 38 行：使用 `d.get("k", 默认值)`。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_02.json)<br>① `notes/python-notes.md#L31-L38`：0.618152<br>② `notes/python-notes.md#L43-L50`：0.609625<br>③ `notes/python-notes.md#L37-L44`：0.607127 | 检索找全了，回答准确完整，引用支持回答 |
| 3 | 函数的可选参数需要一个默认列表时，笔记推荐怎样定义参数、在函数内初始化？ | `notes/python-notes.md` 第 50 行：参数默认值写 `None`，函数内用 `if x is None: x = []` 创建列表。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_03.json)<br>① `notes/python-notes.md#L49-L56`：0.715366<br>② `notes/python-notes.md#L43-L50`：0.672991<br>③ `notes/python-notes.md#L91-L98`：0.624220 | 检索找全了，回答准确完整，引用支持回答 |
| 4 | Pydantic 模型转出来的数据要提交给接口时，应该使用哪种转换方式？ | `notes/python-notes.md` 第 74 行：使用 `.model_dump(mode="json")`，避免枚举仍是枚举对象。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_04.json)<br>① `notes/python-notes.md#L67-L74`：0.651270<br>② `notes/python-notes.md#L73-L80`：0.651130<br>③ `notes/python-notes.md#L61-L68`：0.556104 | 检索找全了，回答准确完整，引用支持回答 |
| 5 | 不确定一个函数有哪些参数、怎么使用时，可以怎样查看说明？ | `notes/python-notes.md` 第 91 行：使用 `print(f.__doc__)` 或 `help(f)` 查看说明。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_05.json)<br>① `notes/python-notes.md#L49-L56`：0.676548<br>② `notes/python-notes.md#L91-L98`：0.660281<br>③ `notes/python-notes.md#L43-L50`：0.637012 | 检索找全了，回答准确完整，引用支持回答 |
| 6 | 这份笔记建议每天花多少分钟复习 Python？ | 资料不足：所选笔记没有给出每天复习的分钟数。第 4 行只说明复习方法，不能据此推算时长；不编造答案或引用。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_06.json)<br>① `notes/python-notes.md#L1-L8`：0.634229<br>② `notes/python-notes.md#L7-L14`：0.496693<br>③ `notes/python-notes.md#L43-L50`：0.479350 | 判断正确，原文资料不足 |
| 7 | 想把记录按分数从高到低取前三条，再将对应的文字每条一行拼起来，需要组合笔记中的哪些写法？ | `notes/python-notes.md` 第 40～41 行与第 24 行：用 `sorted(xs, key=lambda x: x["score"], reverse=True)[:3]` 排序取前三条；将对应文字用 `append` 收集到列表，再用 `"\n".join(列表)` 拼接。回答与引用须覆盖排序取数、换行拼接两部分。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_07.json)<br>① `notes/python-notes.md#L13-L20`：0.633556<br>② `notes/python-notes.md#L7-L14`：0.605004<br>③ `notes/python-notes.md#L19-L26`：0.581771 | 检索没有找全，候选没有选到资料中回答这个问题的文本，因此模型返回了insufficient。 |
| 8 | 检查外部数据结构时，怎样用 Pydantic 定义校验模型，又怎样查看这个模型交给大模型时的结构？ | `notes/python-notes.md` 第 71 行与第 78 行：用 `class X(BaseModel):` 配合类型注解定义校验模型，用 `.model_json_schema()` 查看模型结构。回答与引用须覆盖两部分。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_08.json)<br>① `notes/python-notes.md#L67-L74`：0.646155<br>② `notes/python-notes.md#L61-L68`：0.552437<br>③ `notes/python-notes.md#L91-L98`：0.533601 | 检索没有找全，回答准确但不完整，引用支持了部分回答，有部分引用没有覆盖 |
| 9 | Pydantic 的 `.model_dump()` 与 `.model_dump_json()` 的返回形式有什么区别？ | `notes/python-notes.md` 第 73 行：前者转成字典，后者转成 JSON 字符串；不能把两者都说成字典或都说成字符串。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_09.json)<br>① `notes/python-notes.md#L73-L80`：0.697381<br>② `notes/python-notes.md#L91-L98`：0.637336<br>③ `notes/python-notes.md#L67-L74`：0.606499 | 检索找全了，回答准确完整，引用支持回答 |
| 10 | 笔记中「可变默认参数」的踩坑案例，实际运行时打印了什么结果？ | 资料不足：全文未记录该案例的实际运行输出。第 113～120 行只是留空的踩坑模板；第 50 行虽给出推荐写法，也不能据此编造当时的打印结果。 | [结果 JSON](../day41/outputs/run_jg_k2_vk/question_10.json)<br>① `notes/python-notes.md#L109-L116`：0.750592<br>② `notes/python-notes.md#L1-L8`：0.585221<br>③ `notes/python-notes.md#L49-L56`：0.581623 | 判断正确，资料不足 |
