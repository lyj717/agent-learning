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
```

学员做完练习和参数对比记录后，交给 AI 对答案、挑毛病。

## 每日清单

- [x] Day 8｜读官方 Quickstart，理解 system/user/assistant，temperature 对比实验
- [ ] Day 9｜token 与成本，实现 `/cost` 命令
- [ ] Day 10｜多轮对话，实现 `/clear`
- [ ] Day 11｜流式输出，打字机效果
- [ ] Day 12｜上下文裁剪、失败重试、简易长期记忆
- [ ] Day 13｜整合 + README + 演示视频
- [ ] Day 14｜复盘，回答三个面试问题

## 验收标准

- [ ] 断网、限流、超长输入三种情况都不崩溃
- [ ] 能解释「上下文越用越贵」和「流式为什么让用户感觉更快」
