# Day67 题目：把项目打包成「别人装得上」

今天不写新的 MCP 机制，做交付层：元数据、入口点、包发现、README 与宿主配置。
检查器只读文件、跑一次模块冒烟，**不安装**；18 组全过就算完成。

## 你要写/改的四个文件

| 文件 | 内容 |
|---|---|
| `pyproject.toml`（仓库根，新建） | 项目元数据、依赖、入口点、打包哪些包 |
| `projects/__init__.py`（新建） | 空文件即可，标记 `projects` 是包 |
| `projects/mcp_server/README.md` | 把模板里的 `TODO` 换成真内容 |
| `LICENSE`（仓库根，新建） | 你选的许可证全文；README 里说明选它的理由 |

不要改检查器，不要改 `projects/mcp_server/server.py` 的入口函数签名。

## `pyproject.toml` 的固定字段

| 段 | 值 |
|---|---|
| `[build-system].requires` | `["setuptools>=68"]` |
| `[build-system].build-backend` | `"setuptools.build_meta"` |
| `[project].name` | 你定，例如 `notes-mcp-server` |
| `[project].version` | `"0.1.0"`，必须与 `projects/mcp_server/__init__.py` 的 `__version__` 一致 |
| `[project].requires-python` | `">=3.11"`（写成含 `>=` 的字符串即可） |
| `[project].dependencies` | 含一项 `"mcp>=2.3,<3"` |
| `[project.scripts]` | `notes-mcp-server = "projects.mcp_server.server:main"` |
| `[tool.setuptools].packages` | `["projects", "projects.mcp_server"]` |

`[project.scripts]` 右边是「模块:函数」：装好之后，系统里多一个 `notes-mcp-server`
命令，执行它就等于 `from projects.mcp_server.server import main; main()`。

## README 要写什么

模板在 `projects/mcp_server/README.md`，把每个 `TODO` 换掉。检查器会看：

| # | 要求 |
|---|---|
| 10 | 至少一个代码块里含 `pip install` 命令 |
| 11 | 至少一个代码块里同时有 `mcpServers` 与 `command`（Claude Desktop） |
| 12 | 正文写明 `.cursor/mcp.json`（Cursor 的配置位置） |
| 13 | 至少一个代码块里同时有 `"servers"` 与 `"type": "stdio"`（VS Code） |
| 14 | 正文出现 `NOTES_ROOT`（环境变量说明） |
| 15 | 正文出现 `notes-mcp-server`（装好后的命令名） |
| 16 | 仓库根有 LICENSE 文件，且 README 提到许可证 |

三份配置的外层键不同：Claude Desktop 与 Cursor 用 `mcpServers`，VS Code 用 `servers`
并且每条要 `"type": "stdio"`。`command` 一律写绝对路径（Python 解释器或装好的命令），
`env` 里传 `NOTES_ROOT`。

## 检查器怎么判（18 组）

- **A 组 1～8**：`pyproject.toml` 存在且可解析；项目名非空；版本与
  `projects/mcp_server/__init__.py` 一致；`requires-python` 含 `>=`；依赖里有
  `mcp>=2.3,<3`；入口点等于 `projects.mcp_server.server:main`；打包列表含
  `projects` 与 `projects.mcp_server`；`projects/__init__.py` 存在。
- **B 组 9～16**：README 存在；上表第 10～16 条。
- **C 组 17～18**：`python -m projects.mcp_server.server` 在空 stdin 下能正常退出（20 秒超时）；
  `projects.mcp_server.server.main` 可导入且可调用。

## 跑法

```powershell
# A：打包配置
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day67_packaging_exercises.py --part a
# B：README 与许可证
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day67_packaging_exercises.py --part b
# C：模块冒烟
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day67_packaging_exercises.py --part c
# 一起
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day67_packaging_exercises.py
```

预期：A 8/8、B 8/8、C 2/2，合计 18/18。

## 想自己验一次安装（可选）

检查器不安装。想亲眼看入口命令，可以：

```powershell
.venv\Scripts\python.exe -m pip install -e . --no-deps --no-build-isolation
.venv\Scripts\notes-mcp-server.exe
```

第二条会在空 stdin 下立刻退出；如果卡住，Ctrl+C。装坏了用
`pip uninstall notes-mcp-server` 卸掉。这台机器的 pip 临时目录有时会因权限失败，
失败就把报错记进记录，不影响检查器判分。

## 数据来源与预算

- 全部离线，**0 次模型调用**；检查器只读文件，不改仓库。
- 每次运行在 `demos/day67/outputs/` 下新建目录，保存 `console.log`、`run_info.json`、
  `results.json`；失败也保留。
- `DAY67_RUN_ORIGIN` 默认 `unconfirmed`；AI 自验标 `ai_validation`。
