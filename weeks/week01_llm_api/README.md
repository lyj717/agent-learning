# Week 01｜LLM 基础与 API

**目标**：把「调模型」变成一件闭着眼睛也能做对的事。

**交付物**：流式 CLI 聊天机器人。

## 本周材料

分工：**演示和讲解由 AI 搭好，实验、记录、练习题由学员自己完成。**

| 天 | 材料 | 谁做 | 是什么 |
|---|---|---|---|
| Day 8 | `day08_roles_demo.py` | AI 搭・学员跑 | system / user / assistant 三种角色讲解（离线，`--live` 才联网对照） |
| Day 8 | `day08_temperature_demo.py` | AI 搭・学员跑 | 只负责跑出 temperature 对比的原始数据，不给结论 |
| Day 8 | `day08_exercises.py` | **学员做** | 验证学习成果的题（留了空，会大声报 `NotImplementedError`） |
| Day 8 | `day08_参数对比记录.md` | **学员填** | Day 8 交付物：自己跑、自己观察、自己下结论 |
| Day 9 | `day09_token_demo.py` | AI 搭・学员跑 | token 与成本讲解：官方价格表、多轮滚雪球、思考 token 的账（离线可跑，`--live` 实测 usage） |
| Day 9 | `day09_exercises.py` | **学员做** | 三题搭出一个迷你 `/cost` 核心：算一次调用、模拟多轮输入、算整段会话 |
| Day 10 | `day10_messages_demo.py` | AI 搭・学员跑 | 多轮对话的原理：历史在谁手里、`/clear` 清的是什么、三个坑（离线，`--live` 验证「不带历史就失忆」） |
| Day 10~ | `chat_cli/` | **学员写** | **本周交付物**：多轮聊天机器人。Day 10 要写 `conversation.py` 和 `chat_cli.py`，验收测试在 `chat_cli/tests/` |

跑法（在仓库根目录）：

```bash
# 角色讲解（默认不联网）
.venv\Scripts\python.exe weeks\week01_llm_api\day08_roles_demo.py

# 想真的调 3 次看差别（需要网络）
.venv\Scripts\python.exe weeks\week01_llm_api\day08_roles_demo.py --live

# temperature 实验（需要网络，会消耗少量额度）
.venv\Scripts\python.exe weeks\week01_llm_api\day08_temperature_demo.py

# 练习：自己写，跑通看输出对不对
.venv\Scripts\python.exe weeks\week01_llm_api\day08_exercises.py

# Day 9：token 与成本的讲解（默认离线，不花钱）
.venv\Scripts\python.exe weeks\week01_llm_api\day09_token_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day09_token_demo.py --live   # 真的发一次，看 usage

# Day 9 练习：把成本估算函数写出来
.venv\Scripts\python.exe weeks\week01_llm_api\day09_exercises.py

# Day 10：多轮对话的原理（默认离线，不花钱）
.venv\Scripts\python.exe weeks\week01_llm_api\day10_messages_demo.py
.venv\Scripts\python.exe weeks\week01_llm_api\day10_messages_demo.py --live   # 真聊两轮

# Day 10 交付物：多轮聊天机器人（骨架留给你写）
cd weeks\week01_llm_api\chat_cli
..\..\..\.venv\Scripts\python.exe -m pytest -v      # 14 个测试，写好之前是红的
..\..\..\.venv\Scripts\python.exe chat_cli.py       # 写完了就能连续聊天
```

学员做完练习和参数对比记录后，交给 AI 对答案、挑毛病。

**进度与计划的差异（Day 9 ~ Day 10）**：计划表写「Day 9 交付 `/cost` 命令」，
但 Week 01 的 CLI 骨架要到 Day 10 才搭。所以 Day 9 的交付物是**成本估算函数**
（练习第 1、3 题），Day 10 把它搬进 `chat_cli/cost.py`，`/cost` 命令就自然有了。

同样地，`main` 里的出错处理（`try/except`）本来是 Day 10 骨架里的一句提示，
按计划表它是 **Day 12「上下文管理与容错」** 的内容，所以挪到 Day 12 一起做，
`chat_cli.py` 里留了 `TODO(Day 12)` 的书签。

## 官方文档去哪看（Day 8 ~ Day 14）

计划表里的「读官方 Quickstart」，指的是**你这家模型服务商的官方文档**，
不是第三方教程。你的 `.env` 指向 DeepSeek，中文文档在这里：

| 页面 | 地址 | 和哪天的课有关 |
|---|---|---|
| 首次调用 API（Quickstart） | https://api-docs.deepseek.com/zh-cn/ | Day 8：base_url、密钥、最小请求、system/user 角色 |
| 创建对话补全 API | https://api-docs.deepseek.com/zh-cn/api/create-chat-completion | Day 8~12：`messages`、`role`、`temperature`、`max_tokens`、思考模式 |
| 模型 & 价格 | https://api-docs.deepseek.com/zh-cn/quick_start/pricing | Day 9：估算花费 |
| Token 用量计算 | https://api-docs.deepseek.com/zh-cn/quick_start/token_usage | Day 9：token 怎么数 |
| 速率限制 | https://api-docs.deepseek.com/zh-cn/quick_start/rate_limit | Day 12：限流怎么处理 |
| 错误码 | https://api-docs.deepseek.com/zh-cn/quick_start/error_codes | Day 12：断网、限流、超限怎么读 |

为什么计划反复强调「以官方文档为准」：接口细节更新很快，第三方教程常常是旧的。
Day 8 读前两页就够，读的时候留意 `temperature` 和 `max_tokens` 那两段——
它们和你跑实验看到的现象直接相关。

小提醒：模型名以官方文档为准（文档现在写的是 `deepseek-flash`）。`.env` 里
若是旧名字也能跑，但既然来了文档，顺手对一下。

## 每日清单

- [x] Day 8｜读官方 Quickstart，理解 system/user/assistant，temperature 对比实验
- [x] Day 9｜token 与成本（交付：成本估算函数；`/cost` 命令 Day 10 接进 CLI）
- [x] Day 10｜多轮对话，实现 `/clear`（`chat_cli` 能连续追问，答得出上一轮说过的名字）
- [ ] Day 11｜流式输出，打字机效果
- [ ] Day 12｜上下文裁剪、失败重试、简易长期记忆
- [ ] Day 13｜整合 + README + 演示视频
- [ ] Day 14｜复盘，回答三个面试问题

## 验收标准

- [ ] 断网、限流、超长输入三种情况都不崩溃
- [ ] 能解释「上下文越用越贵」和「流式为什么让用户感觉更快」
