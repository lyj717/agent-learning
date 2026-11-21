# Week08 交接（2026-11-21）

## 1. 一句话状态

Week08 的评测与可靠性主线已完成：规则判分、模型裁判、成本/延迟测量、一次同批优化对照、
五类失败模式检查、GitHub Actions 离线 CI 与手动 live 都有验收证据。
**但业务仍是教学数据**：评测集只有 8 题，live CI 只跑一次冒烟，没有接完整 RAG/服务链路。

## 2. 现在能跑什么

```powershell
# 全部离线测试：17 passed
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest_tmp tests

# Day61 五类失败检查：正常版/故障版 10/10
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day61_failure_exercises.py

# Day62 workflow 静态检查：10/10
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day62_ci_exercises.py

# Day62 手动 live 冒烟：1 次调用，约 0.0002 元
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\demos\day62\day62_live_smoke.py
```

各日入口与预算见 `weeks/week08_evaluation_reliability/README.md` 与各 `dayNN_题目说明.md`。

远端 CI：`.github/workflows/ci.yml`
- push/PR：只跑离线 job；
- 手动 Run workflow 勾 `run_live`：跑 1 次冒烟；
- 最近一次手动运行：https://github.com/lyj717/agent-learning/actions/runs/44701577259

## 3. 环境要点

- Python 3.13，虚拟环境 `.venv`；CI 用 `requirements-ci.txt`，不装 fastembed/Qdrant。
- GitHub Secrets：`LLM_API_KEY`、`LLM_BASE_URL`；`LLM_MODEL` 未设时脚本默认 `deepseek-flash`。
- CI 的 Node 20 / ubuntu-latest 提示只是警告；需要时再升级 `checkout@v5`、
  `setup-python@v6` 或固定 `ubuntu-24.04`。
- Windows 下 pytest 临时目录有跨账号 ACL 问题（`[WinError 5]`）；用独立
  `--basetemp`，必要时管理员清理。
- 所有运行输出在各自 `outputs/`，已被 `.gitignore` 排除；失败日志保留，不覆盖。

## 4. 留的尾巴

1. **q06 规则/裁判口径冲突**：证据没覆盖 Pydantic 时，模型答 `insufficient` 是诚实的，
   规则仍按 `Field/default_factory` 记 `not_answered`；需要改规则用例，或把
   `not_answered` 标成该证据下的预期。
2. **空引用未被代码强制**：`cited_ids=[]` 时 `citation_ok` 应为 `null`，目前只在 prompt
   和记录里约定；应加一条确定性检查（`citation_ok is None` 当且仅当 `cited_ids` 为空）。
3. **Day60 优化没有拆变量**：同时改了切块 8→4 行和检索 3→2 条，−46ms 不能归因；
   后续可做两次单变量对照。
4. **评测集太小**：8 题只够教学与回归演示，不够线上长尾；扩充时要补标注与分歧集。
5. **live CI 只冒烟**：没有在 CI 跑完整评测；完整评测仍手动、按预算执行。
6. **Day63 阶段变式/口头/HANDOFF**：已完成并验收；发布评审 5 道阻断、口头三件套通过。

## 5. 下一周目标与建议第一步

Week09 **选定 A｜MCP Server**：复用已有的 notes 检索或工具授权，包成一个可安装/可运行的
MCP Server，带 README、测试与 CI（现有 workflow 可直接扩展）；B/C/D 只作了解。

第一步（约半天）：读 `docs/ai-agent-12周学习计划.md` 第 9 周和 MCP 官方 Quickstart，
写清「给谁用、解决什么问题、最小可用接口（list_tools / call_tool）」，先跑通一个
echo 或 files 工具，再接 notes 检索，最后开 Day64。
