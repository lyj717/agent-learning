# Week 02 交接文档

> 写给 Week 03 对话。先读根目录 `AGENTS.md`，再读本文件和本周 `README.md`。

## 一句话状态

Day 15～21 的结构化输出、Pydantic 校验、三工具调用和错误回填已经完成；本周交付物是 `info_toolbox/` 中可运行的 `extract` / `ask` 双模式项目。Day 21 学员在 4 分钟内画了第一次闭卷图，对照后指出并订正了缺漏，完成三道口头题。

## 现在能跑什么

在仓库根目录执行：

```powershell
# 不联网：查看两个模式的入口
.venv\Scripts\python.exe -B weeks\week02_tools\info_toolbox\app.py --help
# 预期列出 extract、ask 和必填的 text

# 不联网：错误回填、调用 ID、轮数上限四组检查
$env:PYTHONIOENCODING='utf-8'
.venv\Scripts\python.exe -B weeks\week02_tools\day19_error_recovery_probe.py
# 预期四组检查均有 ✓；max_rounds=2 时只请求模型两次

# 需要 .env 中的真实密钥和网络；下面是学员已记录过的运行方式
.venv\Scripts\python.exe -B weeks\week02_tools\info_toolbox\app.py extract "我叫李娜，在深圳做前端。"
# 曾得到 {"name": "李娜", "phone": null, "city": "深圳", "job": "前端"}
.venv\Scripts\python.exe -B weeks\week02_tools\info_toolbox\app.py ask "杭州有几笔已支付订单？"
# 曾调用 query_orders({"city": "杭州"})，本地返回 2 笔、200.0 元

# 仓库检查；2026-10-10 收尾时为 9 passed，Ruff 检查通过，110 个文件格式符合要求
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp=.pytest_tmp tests
.venv\Scripts\python.exe -B -m ruff check .
.venv\Scripts\python.exe -B -m ruff format --check .
```

真实模型的答复可能变化；Day 20 的实际轨迹保存在 `day20_演示与面试素材.md`，项目使用说明和限制保存在 `info_toolbox/README.md`。Day 21 的第一次白板图、参考图和学员订正保存在 `day21_白板复盘.md`。

## 环境要点

- 解释器是仓库内 `.venv\Scripts\python.exe`，Python 3.13.9；编辑器沿用 PyCharm，解释器指向这个 `.venv`。
- 真实请求从仓库根目录 `.env` 读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`；`.env.example` 说明格式，密钥文件不提交。
- `ask` 入口每次调用 `seed_db()` 重建六条模拟订单，生成的 SQLite 文件是运行数据，不提交。天气也是固定模拟快照，不提供实时天气。
- 工具调用最多请求模型三轮。第三轮若仍返回工具调用，本地会执行它，但没有第四轮供模型生成答复，程序返回「达到最大轮数！」。
- 这台 Windows 终端可能使用 GBK 输出；运行会打印 `✓` 的离线自测前，设置 `$env:PYTHONIOENCODING='utf-8'`。跑 pytest 时加 `-p no:cacheprovider --basetemp=.pytest_tmp`，不要在 `%TEMP%` 留下权限不符的目录。

## 留的尾巴

1. 按学员决定，招聘 JD 统计和简历修改留到整个学习项目结束后统一处理；模板保存在根目录 `jd-keywords.md` 和 `day21_白板复盘.md`。这不是 Week 03 开工门槛。
2. Day 20 的三分钟视频留到面试复习时录制；录制位置与日期待填入 `day20_演示与面试素材.md`。Week 01 的视频也仍待补。
3. Day 21 第一次闭卷图画出了主线，但漏了工具说明、原 assistant 点单、错误回填和轮数分支；图下已有对照订正，AI 对少量文字做了批改校正。Week 03 开始 Agent 循环时，可再口头复述一次作为热身。
4. `FAILURES.md` 记录了真实踩坑，包括订单初始化遗漏、南京问题误查北京，以及离线自测的终端编码错误。

## 下一周目标与建议第一步

Week 03 按 `docs/ai-agent-12周学习计划.md` 手写一个不依赖 Agent 框架的 ReAct 循环：思考、行动、观察、再思考；明确最终答案、最大步数、超时和预算等停止条件，并打印每一步轨迹。先读 `AGENTS.md` 与本文件，再看 `info_toolbox/tool_calling.py` 的现有工具回合，接着为下一天搭一个离线可跑的最小循环演示和留白练习。AI 负责脚手架、讲解、检查；学员负责实验和答案。
