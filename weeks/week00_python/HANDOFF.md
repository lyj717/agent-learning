# Week 00 交接文档

> 写给下一个对话的开场材料。一周一个对话，这份文件就是接续点。
> 写于 2026-10-04。

## 一句话状态

Python 补齐的 7 天全部走完，本周交付物是一个**真跑得起来的 CLI 工具** `chat_cli/`。
验收标准还差两条没确认，见「留的尾巴」。

## 这一周做出了什么

| 产出 | 位置 |
|---|---|
| 7 天的演示与练习（31 个 `.py`） | `weeks/week00_python/` |
| **本周交付物**：CLI 小工具 | `weeks/week00_python/chat_cli/`（用法见它自己的 README） |
| 速查表：我要干什么 → 用什么 | `notes/python-notes.md` |
| 卡住时的六招排查法 | `notes/卡住了怎么办.md` |
| 真实故障记录（3 条） | `FAILURES.md` |
| 仓库约定 | `AGENTS.md` |

## 现在能跑什么（都已实际验证过）

```bash
# 环境自检
.venv\Scripts\python.exe check_env.py

# 本周交付物：问模型一句话，流式打印回答
.venv\Scripts\python.exe weeks\week00_python\chat_cli\chat_cli.py "用一句话说明什么是流式输出"

# 工具自己的测试（预期 3 passed）
cd weeks\week00_python\chat_cli
..\..\..\.venv\Scripts\python.exe -m pytest -v

# 仓库测试与代码检查
.venv\Scripts\python.exe -m pytest        # 只跑 tests/ 目录
.venv\Scripts\python.exe -m ruff format .
.venv\Scripts\python.exe -m ruff check .
```

## 环境要点

- **解释器**：仓库内的 `.venv\Scripts\python.exe`（Python 3.13.9）
- **编辑器**：PyCharm Community Edition 2023.2.1。两处设置要配对：
  Project 解释器指向 `.venv`；默认测试运行器改成 pytest
- **密钥**：仓库根目录的 `.env`，三个变量 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
  （当前接的是 DeepSeek）。`.env` 永不提交
- **依赖**：`requirements.txt`（openai、httpx、python-dotenv、pydantic、rich、pytest、ruff）
- **两个已知环境坑**（细节见 `AGENTS.md`）：
  1. `[WinError 5]`——AI 用的沙箱账号建出来的目录，你写不进去，名字带 `dell` 权限却属于别人
  2. PyCharm 2023.2 与 pytest 8+ 的测试面板不兼容：显示「没有发现测试」时用终端跑，或升级 IDE

## 留的尾巴

1. `*args` / `**kwargs` 只在 `day04_class_demo.py` 的装饰器那节露过一次，没专门练
   —— 留到 Week 04 读框架源码时补
2. Week 00 的验收标准还差两条：**换台机器 5 分钟跑通**、**对着代码讲 3 分钟**
3. `docs/` 里有两处写着「装 VS Code」（学习计划的历史文本），实际用的是 PyCharm

## 下一周：Week 01｜LLM 基础与 API

**交付物**：流式 CLI 聊天机器人。

和已经做完的 `chat_cli/` 相比，差别主要在三点：

- **多轮对话**——要维护一段 messages 历史，每次请求都带上（Day 4 的 `Conversation`
  和 Day 7 拼的 `messages` 就是现成的地基）
- **参数更完整**——温度、最大长度、系统提示的可配置化
- **错误处理与超时**——网络不稳时怎么表现

**建议的第一步**：读 `docs/ai-agent-12周学习计划.md` 里 Week 01 那一段和本文件，
然后打开 `chat_cli/llm.py`——它已经能发请求、能流式接收，Week 01 主要是把
「一次问答」扩成「一段对话」。

## 给下一个对话的三条提示

1. **先读约定**：`AGENTS.md`——演示怎么写、库函数要注释、提交与推送的分工、这台机器的坑
2. **用户偏好**：中文；先讲「这是什么」再给代码；库里来的函数旁边补一行注释；
   AI 只做本地提交，推送由用户自己执行
3. **别破坏已有的东西**：`notes/` 和 `docs/` 里的手工对齐是有意的，
   `ruff.toml` 已经把那两个目录排除在格式化之外
