# Week 01 交接文档

> 写给下一个对话的开场材料。一周一个对话，这份文件就是接续点。
> 写于 2026-10-07（Day 14），下面「现在能跑什么」里的命令都实测过。

## 一句话状态

Week 01「LLM 基础与 API」走完 7 天（Day 8~14）。本周交付物是一个**能连续聊天、
带打字机效果、会记账、会裁剪上下文、还带简易长期记忆的 CLI 机器人** `chat_cli/`，
30 条测试全绿。**还差**：3 分钟演示视频没录、三条面试问题的答案没写。

## 这一周做出了什么

| 产出 | 位置 |
|---|---|
| 6 份演示脚本（Day 8~13） | `weeks/week01_llm_api/day08_*.py` … `day13_*.py` |
| **本周交付物**：带长期记忆的聊天机器人 | `weeks/week01_llm_api/chat_cli/`（591 行代码 + 27 个测试函数） |
| 一份笔记 | `notes/流式块解剖.md`——流式返回的每个字段干嘛用（含实测数据） |
| Day 8 交付物：参数对比记录 | `weeks/week01_llm_api/day08_参数对比记录.md` |
| 真实故障记录（本周 7 条） | `FAILURES.md` |
| 本周提交 | 31 次（从 Week 00 交接之后算起） |

**交付物由五个模块组成**（这是 Day 13 README 里那份「架构说明」的骨架）：

```
chat_cli.py      接命令、分流、REPL 循环      ← 碰网络、碰屏幕
conversation.py  对话历史、裁剪、换人设       ← 纯状态，能脱离网络测
llm.py           发请求、重试、流式、带超时    ← 碰网络
cost.py          token 数 → 钱               ← 纯计算，能脱离网络测
memory.py        事实存本地文件、拼进 system  ← 读文件，能脱离网络测
```

## 现在能跑什么（命令都实测过）

```bash
# 0）环境自检（不联网）
.venv\Scripts\python.exe check_env.py
# 预期最后一行：环境就绪，可以开始 Day 1 了。   ← 「Day 1」是旧文案，见「留的尾巴」

# 1）本周交付物：聊天机器人（需要网络）
cd weeks\week01_llm_api\chat_cli
..\..\..\.venv\Scripts\python.exe chat_cli.py --system "只回答一句话，不超过 20 个字"
# 预期：欢迎语 + 「你> 」提示符；打一句话，回答一个个字冒出来（打字机效果）
# 会话里可用：/remember 我叫刘小明、/clear、/cost、/exit

# 2）交付物的测试（30 条，不联网）
..\..\..\.venv\Scripts\python.exe -m pytest -v        # 预期 30 passed

# 3）六个演示脚本的离线路径（都不联网、不花钱）
cd ..\..\..
.venv\Scripts\python.exe weeks\week01_llm_api\day08_roles_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day09_token_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day10_messages_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day11_streaming_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day12_resilience_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day13_memory_demo.py
# 预期：六个都跑到最后一行、退出码 0（实测输出 110~144 行不等）

# 4）仓库测试（9 条）与代码检查
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest_tmp tests
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
# 预期：9 passed / All checks passed! / 73 files already formatted
```

**需要联网、会花一点钱的两条**（额度和网络都要有）：

```bash
# Day 8 的 temperature 对比实验（两个温度各 5 次）
.venv\Scripts\python.exe weeks\week01_llm_api\day08_temperature_demo.py

# 任意演示加 --live 都会真调一次模型，例如：
.venv\Scripts\python.exe weeks\week01_llm_api\day13_memory_demo.py --live
```

**本周那条关键验收**（Day 13 真跑过）：

```
你> /remember 我叫刘小明
记住了：我叫刘小明
你> /clear
已清空历史，清掉了 1 轮对话
你> 我叫什么？
你叫刘小明。                 ← 历史清空了，记忆还在（事实存在 facts.json，每轮拼进 system）
```

## 环境要点

- **解释器**：仓库内的 `.venv\Scripts\python.exe`（Python 3.13.9）
- **编辑器**：PyCharm Community Edition 2023.2.1。两处设置要配对：Project 解释器指向
  `.venv`；默认测试运行器改成 pytest
- **密钥**：仓库根目录 `.env`，三个变量 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
  （当前接 DeepSeek，模型名 `deepseek-flash`）。`.env` 永不提交
- **依赖**：`requirements.txt`（openai、httpx、python-dotenv、pydantic、rich、pytest、ruff）
- **四个已知的坑**（前两个的细节见 `AGENTS.md`）：
  1. `[WinError 5]`——AI 的沙箱账号建出来的目录，你名字却是别人权限
  2. PyCharm 报「未解析的引用 `conversation`」——右键 `chat_cli` → Mark Directory as →
     Sources Root（运行时不受影响，见 `chat_cli/README.md`）
  3. **别用 PowerShell 管道把中文喂给子进程**（会乱码成 `UnicodeEncodeError`），
     要用 Python 的 `subprocess + utf-8` 驱动（见 `AGENTS.md`）
  4. **openai 这个库默认自己重试 2 次**——我们建客户端时写了 `max_retries=0`，
     把重试收归自己的 `retry()` 管（否则最坏 9 次请求，实测一次 create 要 7.6 秒）

## 留的尾巴

1. **3 分钟演示视频没录**（Day 13 计划表块 4 的后半）。提纲在 `chat_cli/README.md`
   的「讲解提纲」那一节
2. **Day 14 的三条面试问题还没写答案**：为什么上下文越用越贵 / 长对话你怎么取舍 /
   流式为什么重要。模板在 `day14_复盘与面试问题.md`
3. **`jd-keywords.md` 还是空表**——Day 14 要求读 10 条 JD 往里填，本周还没做
4. `check_env.py` 最后一行还写着「可以开始 Day 1 了」，是 Day 0 的旧文案
5. 本周验收标准还差第二条没打勾：「能解释『上下文越用越贵』和『流式为什么让用户感觉更快』」
   ——等第 2 条答案写完就能勾
6. Week 00 留下的两条验收仍未确认：换台机器 5 分钟跑通、对着代码讲 3 分钟

## 下一周：Week 02｜结构化输出与工具调用

**为什么是这周**：面试里 Agent 岗问得最多的两件事，就是「让模型输出可用的 JSON」和
「让模型调用你的工具」。这两件事不熟，后面 Week 03 的 Agent 循环无从谈起。

**官方文档去哪读**（都在同一页，已核对过参数名）：
<https://api-docs.deepseek.com/zh-cn/api/create-chat-completion>

- **结构化输出**：找 `response_format` 那一节。设成 `{"type": "json_object"}` 就是 JSON 模式，
  **但文档明确写着：你必须同时在 system 或 user 消息里要求模型输出 JSON**，
  否则模型可能一直吐空白字符直到 `max_tokens` 用尽——表现就是「卡住不动」。
  另外 `finish_reason=length` 时要当心 JSON 被截断。
- **工具调用**：找 `tools`、`tool_choice` 两节，以及函数定义里的 `strict`（Beta，
  保证输出符合你的 JSON schema）。返回侧的线索是 `finish_reason="tool_calls"`——
  模型不是给你答案，而是**要求你执行某个函数**，这就是 Week 03 Agent 循环的起点。

**建议的第一步**：先读上面那一页的 `response_format`，然后照 Day 9 的老办法——
写一个 `day15_*.py` 小实验，让模型从一段杂乱文本里抽出固定 JSON，跑 10 次看成功率。

## 给下一个对话的三条提示

1. **先读约定**：`AGENTS.md`（分工、每日流程、这台机器的坑），再读这份 HANDOFF
2. **分工**：AI 搭演示和骨架、讲清楚、出题、批改；学员跑、写、填，别替他把活干完
   （2026-10-04 第一次交接就是因为替学员把交付物做完了，整个 Day 8 推倒重来）
3. **别破坏已有的东西**：`notes/` 和 `docs/` 里的手工对齐是有意的；`ruff.toml` 已把
   这两个目录排除在格式化之外。另外提交信息写「做了什么」，中文
