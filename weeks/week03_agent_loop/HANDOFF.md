# Week 03 交接文档

> 写给 Week 04 对话。开工先读根目录 `AGENTS.md`、本文件和 `weeks/week04_frameworks/README.md`。

## 一句话状态

Day 22～28 的手写 Agent 主线已验收：学员在 `day27_integrated_exercises.py` 接起原生工具调用、三把工具、消息回填、轨迹、预算、时限与重复停止；Day 28 换“暮云贴纸”完成闭卷预测、六组离线变式和一次真实模型先查后算。学员的预测、运行记录与限制判断保存在 `day28_验收记录.md`；AI 没有代写这些答案。

## 现在能跑什么

在仓库根目录运行，离线入口不需要密钥：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day27_integrated_exercises.py
# 预期：12 组情境分别展示正常答复、工具错误、权限、预算、时限与重复停止。

.venv\Scripts\python.exe -B weeks\week03_agent_loop\day28_variant_exercises.py
# 预期：预算复验为 530/70 token、cost_budget；重复复验为末尾 1/2 条；
# 六组变式分别得到 final_answer、final_answer、final_answer、final_answer、max_steps、cost_budget。

# 需要根目录 .env 和网络；明确传 --live 才发送真实请求。
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day28_live_check.py --live
# 学员当次记录：3 次请求，search_notes → calculator → 最终答复，42 元，catalog.txt:4。

.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp=.pytest_tmp tests
.venv\Scripts\python.exe -B -m ruff check .
.venv\Scripts\python.exe -B -m ruff format --check . --exclude 1.py
```

2026-10-15 收尾检查：9 个 pytest 通过，Ruff 检查通过；排除用户无关的未跟踪 `1.py` 后，137 个 Python 文件格式合格。测试创建的 `.pytest_tmp` 已清理。真实模型答复可能变化，学员当次的原始 ID 和 token 用量见验收记录，不拿 AI 的验证输出替代学员记录。

## 环境要点

- 解释器是仓库内 `.venv\Scripts\python.exe`（Python 3.13.9），编辑器为 PyCharm。运行配置的“脚本形参”填 `--live`；默认入口不联网。
- 真实请求从根目录 `.env` 读取 `LLM_API_KEY`、`LLM_BASE_URL`，模型未配置时默认 `deepseek-flash`；密钥文件不提交。
- Day 28 真实入口只向模型暴露 `search_notes`、`calculator`。`run_code` 仍是受限数值语法工具，且由应用参数 `allow_code` 授权；它不是操作系统级 Python 沙箱。
- 真实响应的 token 数可用于核对用量，但 `known_cost_yuan` 仍用 Day 27 的教学假价计算，不能当作实际账单。
- 任务时限在每次请求前检查；已开始的阻塞调用由单次调用超时控制。Windows 上跑 pytest 用上面的参数，避免在系统临时目录留下权限不符的文件夹。

## 留的尾巴

1. Day 26B 后半的重复判据已在 Day 28 新轨迹上正确复现，但间隔约 1 天；按原计划在 Week 04 开工后再做一次 10～15 分钟的延迟闭卷复验。没有发生前不勾选。
2. 一次真实模型链条证明当前问题可走通，不证明其他问题、网络故障或所有停止路径都可靠；这些路径已有离线固定情境，后续评测继续积累。
3. JD 统计、简历修改仍留到整个学习项目结束后，演示视频仍留到面试复习时；都不是 Week 04 开工门槛。
4. 未跟踪的根目录 `1.py` 与本阶段无关，AI 未修改或纳入提交。它本身不符合 Ruff 格式，因此全仓格式检查需排除该文件；不要因为这项格式问题改动学员的其他代码。

## 下一周目标与建议第一步

Week 04 只用 LangGraph 把手写版重写为状态、模型节点、工具节点和条件边，再学消息合并、检查点与人工确认。先按 `weeks/week04_frameworks/README.md` 用短题检查 `*args/**kwargs` 和异常分类，同时做上面的重复判据延迟复验；然后把 Day 27 的 `messages`、`trace` 和停止分支逐项映射到图中的状态和边。先读 [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) 的 State、Reducers、Messages、Nodes 几节，不提前实现完整图。继续保持 AI 搭台、学员写练习与观察的分工。
