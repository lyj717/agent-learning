# agent-learning

从零到 AI Agent 开发岗的学习仓库。每天写代码，每天提交，绿格子本身就是学习证据。

## 目标与节奏

- 总周期：Python 补齐 7 天 + 主线 12 周
- 每周投入：工作日 4.5 小时，周末 7 小时
- 交付标准：每周一个能演示、能讲清楚的东西

详细计划见 `docs/` 目录：

| 文件 | 内容 |
|---|---|
| `docs/ai-agent-12周学习计划.md` | 全程规划、作品集要求、面试题库 |
| `docs/python-7天补齐清单.md` | Python 补齐的知识点与练习 |
| `docs/21天详细日程表.md` | 前 21 天逐时段日程 |
| `docs/学习媒介与资源指南.md` | 用什么学、怎么筛选资源 |
| `docs/agent面试八股文.md` | 面试题库 + 参考答案 + 14 天背诵计划 |
| `notes/check_env逐行讲解.md` | 把 check_env.py 拆成 8 关讲 Python 语法 |

## 目录结构

```
agent-learning/
├── docs/         学习计划与参考资料
├── notes/        学习笔记（python-notes.md 等）
├── weeks/        每周的代码与产出，按 weekNN_主题 命名
└── projects/     作品集项目（最后要能给别人看的）
```

**命名约定**：每周的代码放 `weeks/weekNN_主题/` 下，当周的交付物在该目录的 README 里说清楚。

## 进度表

完成一项就把 `[ ]` 改成 `[x]`。

- [ ] Week 00｜Python 补齐 + 环境配置
- [ ] Week 01｜LLM 基础与 API（交付：流式 CLI 聊天机器人）
- [ ] Week 02｜结构化输出与工具调用（交付：多工具信息抽取器）
- [ ] Week 03｜Agent 核心循环，手写不用框架（交付：ReAct Agent）
- [ ] Week 04｜框架与记忆（交付：LangGraph 重写版）
- [ ] Week 05｜RAG 基础（交付：带引用的文档问答）
- [ ] Week 06｜高级检索与评测（交付：检索指标报告）
- [ ] Week 07｜工程化与可观测性（交付：带 trace 的服务）
- [ ] Week 08｜评测与可靠性（交付：自动评测 + CI）
- [ ] Week 09｜进阶：MCP / 多智能体（交付：可用的 MCP Server）
- [ ] Week 10｜作品集定型（交付：3 个项目 + 演示视频）
- [ ] Week 11｜面试专项与投递
- [ ] Week 12｜面试冲刺与复盘

## 每周固定动作（不要省）

1. 读 10 条目标岗位 JD，更新 `jd-keywords.md`
2. 更新简历里的一行内容
3. 把踩过的坑写进 `FAILURES.md`
4. 录一段 3 分钟讲解视频，回看并记下讲不清的地方

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
| 编辑器 | `C:\Users\dell\AppData\Local\Programs\VSCode\Code.exe`（免安装版，开始菜单里有快捷方式） |
| Python 解释器 | 仓库内的 `.venv\Scripts\python.exe` |
| 依赖清单 | `requirements.txt` |

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

删完之后，`pytest.ini` 里那两行临时配置（`addopts` 和 `cache_dir`）就可以去掉了。

> 免安装版不会自动更新，需要升级时重新解压一份新版覆盖即可。

## 本周要交付的那「一个东西」

> 每天开工前在这里写下今天的交付物，收工时确认是否完成。

| 日期 | 今天的交付物 | 完成 |
|---|---|---|
|  |  | [ ] |
|  |  | [ ] |
|  |  | [ ] |
