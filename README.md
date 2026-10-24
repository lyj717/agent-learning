# agent-learning

从零到 AI Agent 开发岗的学习仓库。用亲手实现、运行观察、独立排错和项目讲解记录能力；提交次数和代码行数不作为学习验收标准。

## 目标与节奏

- 学习顺序：Python 补齐 + 主线 12 个阶段，保留原来的 Week / Day 编号；编号不强行对应自然周或日期。
- **实际节奏**：每天约 3~5 小时，每个 Week 阶段以约 4 个自然日完成为目标；AI 协调各 Day 的任务量，每次开工先报预计自然日。轻单元约 1/3～1/2 天，Day 34 的整合量按 1 天校准，复习、排错与订正计入预算。
- 每推进 3~4 个新单元，留半个学习日复习；每个自然周留半天到一天弹性时间。
- 交付标准：每阶段有可演示成果，可以是同一项目的新版本；关键机制另做跨天独立复现。
- 具体时间安排、复习方式和阶段取舍见 [学习计划](docs/ai-agent-12周学习计划.md) 与 [日程表](docs/21天详细日程表.md)。

**当前接续点（2026-10-24）**：[Week 05 Day 39：本地向量库与检索](weeks/week05_rag/README.md#day-39把向量存起来再找回原文) 的 A/B 与三道观察经答疑、订正完成当次验收，函数题干已清理。接下来先做已安排的消化与旧机制短复验，再进入尚未开工的 Day 40。Day 36～39 的跨天独立复验仍待做，引导后通过不算独立理解证据，观察原稿保留。原估 Day 39 约半天、Week 05 约四个自然日是排期预算，不是实测耗时；具体资料与约十条基线在 Day 41 前分步准备，不作为 Day 39 收尾门槛，现有仓库 Markdown 笔记可以使用。Week 04 主线与真实亲跑已收尾，旧机制只补实际缺口，见 [交接文档](weeks/week04_frameworks/HANDOFF.md)。

详细计划见 `docs/` 目录：

| 文件 | 内容 |
|---|---|
| `docs/ai-agent-12周学习计划.md` | 全程规划、作品集要求、面试题库 |
| `docs/python-7天补齐清单.md` | Python 补齐的知识点与练习 |
| `docs/21天详细日程表.md` | 时间块、跨天复习、前 21 个单元与后续节奏 |
| `docs/学习媒介与资源指南.md` | 用什么学、怎么筛选资源 |
| `docs/agent面试八股文.md` | 随阶段复盘的题库 + 面试前 14 个复习单元 |
| `notes/check_env逐行讲解.md` | 把 check_env.py 拆成 8 关讲 Python 语法 |
| `notes/流式块解剖.md` | 流式返回的每个字段干嘛用（Week 01 Day 11，含实测数据） |
| `notes/卡住了怎么办.md` | 卡住时的排查卡片，别在原地空转 20 分钟 |

## 目录结构

```
agent-learning/
├── docs/         学习计划与参考资料
├── notes/        学习笔记（python-notes.md 等）
├── weeks/        每周的代码与产出，按 weekNN_主题 命名
└── projects/     作品集项目（最后要能给别人看的）
```

**命名约定**：每周的代码放 `weeks/weekNN_主题/` 下，当周的交付物在该目录的 README 里说清楚。

每周的练习入口放在 `exercises/`，演示、教具与当天的数据放在 `demos/dayNN/`，
跨天复用的教具放在 `demos/shared/`。例如 Day 34 练习是
`weeks/week04_frameworks/exercises/day34_graph_exercises.py`，支持文件是
`weeks/week04_frameworks/demos/day34/day34_support.py`。已有的独立项目目录保持原位置。

## 进度表

勾选表示该阶段主线已完成，不能代替延后事项和独立复验的记录。当前状态以本周 README 为准，HANDOFF 保留交接日期与后续订正。

- [x] Week 00｜Python 补齐 + 环境配置（跨机器运行、3 分钟讲解仍待确认，见该周 HANDOFF）
- [x] Week 01｜LLM 基础与 API（交付：流式 CLI 聊天机器人 —— `chat_cli/` 多轮 + 流式 + `/cost` + `/clear` + `/remember`，30 条测试全绿；3 分钟演示视频还没录）
- [x] Week 02｜结构化输出与工具调用（交付：双模式信息抽取与三工具问答项目；JD、简历和演示视频按学员安排后补）
- [x] Week 03｜Agent 核心循环，手写不用框架（交付：ReAct Agent；重复判据的延迟复验待补）
- [x] Week 04｜框架与记忆（交付：带文件检查点、人工确认与本地业务防重的 LangGraph 重写版；跨天独立复验待补）
- [ ] Week 05｜RAG 基础（交付：带引用的文档问答）
- [ ] Week 06｜高级检索与评测（交付：检索指标报告）
- [ ] Week 07｜工程化与可观测性（交付：带 trace 的服务）
- [ ] Week 08｜评测与可靠性（交付：自动评测 + CI）
- [ ] Week 09｜进阶方向选一项（交付：可用的 MCP Server 或其他选定方向成果）
- [ ] Week 10｜作品集定型（交付：两个主要项目 + 一个复用已有能力的小工具）
- [ ] Week 11｜面试专项与投递
- [ ] Week 12｜面试冲刺与复盘

## 复习、收尾与延后事项

1. 学员在关键机制完成后 2~3 天做一次 10~15 分钟闭卷复现；阶段结束再做变式与口头解释。AI 在本周 README 简记依据，不另设每日打卡表。
2. 学员把观察写在当天练习或独立交付物里；AI 维护 `FAILURES.md`、检查格式、核对当前文档。
3. 每阶段结束由 AI 写 `HANDOFF.md`，说明已完成、待确认、延后和下阶段第一步；验收收尾后本地提交，学员自行推送。
4. **沿用学员已确认的安排**：JD 统计和简历留到学习项目结束后统一处理；正式演示视频在面试复习时补录。当前保留口头讲解和真实轨迹，不把这些延后事项列为开工门槛。

文档分工：根 README 负责总览与接续点，docs 负责学习顺序与验收原则，本周 README 负责具体任务，HANDOFF 是带日期的交接快照，notes 用于查方法，实验记录保留当时的设置、数据与结论。

## 常用 Git 命令

```bash
git status                      # 看现在有哪些改动
git add .                       # 把所有改动加入暂存区
git commit -m "说明这次做了什么"   # 提交，写清做了什么
git push                        # 推到 GitHub（需要先关联远程仓库）

git switch -c feature/xxx       # 新建分支（做实验性改动时用）
git switch main                 # 切回主分支
git log --oneline               # 看提交历史
```

提交信息尽量写「做了什么」，而不是「update」。例如 `完成 Day 5 环境变量与日志`。

## 安全约定

- API 密钥只放 `.env`，**永远不要提交到仓库**。`.gitignore` 已经屏蔽了 `.env`。
- 需要分享配置时，复制 `.env.example` 填写，不要复制 `.env` 本身。
- 提交前用 `git status` 扫一眼，确认没有把密钥、个人数据、公司资料加进去。

## 开发环境

本机的编辑器与解释器位置，换机器时按这个重建即可。

| 项目 | 位置 |
|---|---|
| 编辑器 | PyCharm Community Edition 2023.2.1：`C:\Program Files\JetBrains\PyCharm Community Edition 2023.2.1\bin\pycharm64.exe` |
| Python 解释器 | 仓库内的 `.venv\Scripts\python.exe` |
| 依赖清单 | `requirements.txt` |

PyCharm 里有几处要注意（换机器时别忘了）：

- **Project 解释器**指向仓库里的 `.venv\Scripts\python.exe`
- **默认测试运行器**改成 pytest：Settings → Tools → Python Integrated Tools →
  Default test runner（用 unittest 的话，`def test_xxx()` 这种函数式测试一个都收集不到）
- **PyCharm 2023.2 对 pytest 8+ 的支持不好**：如果测试面板显示「没有发现测试」，
  升级 PyCharm 就能解决（在终端里直接跑 `pytest` 不受影响）

**常用命令**

```bash
# 环境自检（不含联网调用）
.venv\Scripts\python.exe check_env.py

# 环境自检 + 真实调用一次模型
.venv\Scripts\python.exe check_env.py --live

# 装新依赖（走国内镜像，虚拟环境里已配好）
.venv\Scripts\python.exe -m pip install 包名

# 格式化与检查代码
.venv\Scripts\python.exe -m ruff format .
.venv\Scripts\python.exe -m ruff check .

# 跑测试（两种写法都行，配置在 pytest.ini 里）
.venv\Scripts\pytest.exe
.venv\Scripts\python.exe -m pytest -v
```

> 测试放在 `tests/` 目录，文件名必须是 `test_*.py`，函数名必须是 `test_*`——
> 这是 pytest 的命名约定，不符合的名字它不会执行。

### 排错：`[WinError 5] 拒绝访问`

如果报错指向这两个位置，说明目录的权限不对（被别的账号创建过）：

- `C:\Users\dell\AppData\Local\Temp\pytest-of-dell`
- 仓库根目录下的 `.pytest_cache`

用管理员权限的 PowerShell 删掉它们（注意用完整路径，管理员窗口里的 `%TEMP%`
指向的不是你的临时目录）：

```
Remove-Item "C:\Users\dell\AppData\Local\Temp\pytest-of-dell" -Recurse -Force
Remove-Item ".pytest_cache" -Recurse -Force
```

本仓库在 2026-09 遇到过这个问题，已清理完毕，现在的 `pytest.ini` 里没有绕过配置。

> 补充：AI 在这台机器上跑测试时也会留下同类目录——**名字带 `dell`，权限却属于另一个账号**。
> 判断和处理办法写在 `AGENTS.md` 的「在这台机器上跑命令的注意」一节。

## 本周要交付的那「一个东西」

> 每天开工前在这里写下今天的交付物，收工时确认是否完成。

| 日期 | 今天的交付物 | 完成 |
|---|---|---|
| 2026-10-07 | Day 15：抽取成功率记录（10 条；解析 100%、记录级完全匹配 70%） | [x] |
| 2026-10-08 | Day 16：脏数据与重试记录（四条不崩 + 注入式重试走通） | [x] |
| 2026-10-09 | Day 17：工具调用流程图（计算器最小闭环，两条问题各走 2 步 / 1 步） | [x] |
| 2026-10-09 | Day 18：多工具与选择（天气 + SQLite + 选择记录） | [x] |
| 2026-10-10 | Day 19：错误回填、自纠与最大轮数（离线四组自测通过，真实计算器调用报错后改参成功；记录见练习末尾） | [x] |
| 2026-10-10 | Day 20：双模式项目、README、真实演示轨迹与面试素材（视频留到面试复习时录制） | [x] |
| 2026-10-10 | Day 21：限时白板复盘与口头问答；JD 和简历留到项目结束后 | [x] |
| 2026-10-11 | Day 22：离线 Agent 循环、停止状态与逐步轨迹（四组情境通过，观察已验收） | [x] |
| 2026-10-11 | Day 23：输出协议、解析与校验（两份练习和真实输出观察已验收） | [x] |
| 2026-10-12 | Day 24：本地文件检索、带出处的工具观察与先查后算（两份练习和真实输出观察已验收） | [x] |
| 2026-10-12 | Day 25：受限数值代码执行与工具权限边界（两份练习和观察已验收） | [x] |
| 2026-10-13 | Day 26A：模型用量累计与预算停止（三题及观察已验收） | [x] |
| 2026-10-13 | Day 26B 前半：单次调用超时与任务总时限（三题及观察已验收） | [x] |
| 2026-10-14 | Day 26B 后半：连续重复工具调用检测（三题及观察已验收） | [x] |
