# Week09 HANDOFF：方向 A｜MCP Server

## 1. 一句话状态

从空目录做到一个**可安装、可配置、真实模型能调用**的 notes MCP Server：
工具 3 个、资源 2 个（index + 模板）、提示词 1 个、三种错误形态、pyproject + 入口点 + 三份宿主配置 + MIT、
pytest 10 个契约测试 + stdio 冒烟 + CI、真实模型经自建宿主导通并逐条核对引用。
Day64～69 全部验收；Day70 闭卷变式、口头三件套、资源补练完成。

## 2. 现在能跑什么

```powershell
# 安装（仓库根）
.venv\Scripts\python.exe -m pip install -e .
# 装好后任意目录可用
notes-mcp-server

# 直接跑 server（stdio，等 JSON-RPC）
.venv\Scripts\python.exe -m projects.mcp_server.server

# 项目测试
.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests\test_notes_mcp.py -v   # 10 passed
.venv\Scripts\python.exe -m pytest -p no:cacheprovider                              # 27 passed

# 静态检查
.venv\Scripts\python.exe -m ruff check weeks\week08_evaluation_reliability weeks\week09_advanced projects tests

# 检查器
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day68_ci_test_exercises.py    # 9/9
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day69_host_exercises.py       # 10/10（需要 outputs/live_*.json）

# 真实模型宿主
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day69\day69_host.py --fake
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day69\day69_host.py --live --question "我的笔记里怎么处理流式块？"
```

预期：安装后命令存在；测试 27 passed；两个检查器 9/9、10/10；`--live` 在 `demos/day69/outputs/` 生成带工具调用与回答的 JSON。

## 3. 环境要点

- 解释器：仓库 `.venv`（Python 3.11+；CI 用 3.13）。
- 依赖：`requirements.txt` / `requirements-ci.txt` 已含 `mcp==2.3.0`；宿主另用 `openai`、`python-dotenv`。
- 模型：`.env` 里 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`；`deepseek-flash` 是 thinking 模型，
  多轮工具必须回传 `reasoning_content`；收尾用 `deepseek-chat` 生成自然语言。
- 语料：默认仓库 `notes/`；测试用 `demos/day65/corpus`；`NOTES_ROOT` 由宿主 `env` 传。
- Windows 坑：`pyproject.toml` 不能带 BOM；`pytest` 用 `-p no:cacheprovider --basetemp=`；
  stdio 子进程在受限沙箱里会失败，需在学员终端跑；`ruff format --check` 遇长行会 panic，先 `ruff format` 再 `--check`。
- 真实调用只能在学员终端（有网）跑；AI 沙箱没有外网。

## 4. 留的尾巴

- **第三方宿主没真机验证**：Claude Desktop / Inspector 未装，暂以自建宿代跑；三份配置是按文档写的，未逐个启动验证。
- **HTTP 传输未做**：只做了 stdio；远程部署、认证、多用户、限流、观测都没做。
- `mcp==2.3.0` 是 pin 的；升级 SDK 要回归工具/资源/错误形态与 stdio。
- `read_note` 名字必须带 `.md` 是靠描述与错误消息提示的，schema 没加 `pattern`。
- 资源 `--with-index` 对照实验（有/无索引的轮数差）没跑，记录里留了空间。
- 作品集材料（一句话定位、架构图、演示视频、独立仓库）还没开始。

## 5. 下一周目标与建议的第一步

Week10 是项目上的最后一周。**学员定的总目标（2026-11-26）**：把前几周的成果结合起来，
做一个**真实可用的 agent 工具**，包含工具调用、循环控制、RAG、MCP 等功能。

计划文档原写「作品集定型」；实际调整为「整合成可用项目」，作品集材料（一句话定位、
架构图、运行方式、取舍、已知缺陷）作为这周的自然产出，不单独当目标。

建议第一步：**先写一句话定位 + 画一张架构图**，再动手接代码。

- 一句话定位：谁（哪类用户）在什么场景下，用它解决什么重复劳动；
- 架构图：宿主/入口 → agent 循环（工具调用、步数上限、错误恢复）→ 工具层（RAG 检索、
  文件读取、MCP client）→ 数据（notes/、评测集、MCP server）；
- 在图上标出：哪些是本周新写的整合逻辑，哪些是复用 Week03～09 的成果。

