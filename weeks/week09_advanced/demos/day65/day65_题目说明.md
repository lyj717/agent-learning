# Day65 题目：文件层检索与路径边界

今天把 Day64 的 `find_matches` 接到真实目录上，并且让 `folder` 参数不能逃出语料根。
三部分：A 路径解析、B 目录检索、C 注册成 MCP 工具。

## 你要改哪两个文件

| 文件 | 你要做的 |
|---|---|
| `projects/mcp_server/search.py` | 实现 `safe_subdir`（A）与 `search_files`（B） |
| `projects/mcp_server/server.py` | 注册工具 `search_notes`（C） |

不要改检查器，也不要改 `DEFAULT_NOTES_ROOT` 的定义。

## 接口

```python
def safe_subdir(root: Path, folder: str) -> Path:
    """把相对子目录解析成绝对目录，保证不逃出语料根。"""

def search_files(
    root: Path, keyword: str, limit: int = 5, folder: str = ""
) -> list[dict[str, int | str]]:
    """在 root 下的 Markdown 里检索关键词，返回带出处的命中。"""

@mcp.tool()
def search_notes(keyword: str, limit: int = 5, folder: str = "") -> list[dict[str, int | str]]:
    """在本地 Markdown 笔记本里按关键词检索，返回来源文件、行号与原文。"""
```

规则细节都写在 `projects/mcp_server/search.py` 的 docstring 里，以那里为准。这里只补
三条最容易做错的：

1. **`source` 始终相对语料根**，不是相对 `folder`。`folder="notes"` 时也写
   `notes/agent-notes.md`，不是 `agent-notes.md`。
2. **`limit` 是全局上限**，按文件顺序累计，凑够就停；不是每个文件各拿 limit 条。
3. **参数校验在扫描之前**：即使目录里一个 `.md` 都没有，空关键词也要抛 `ValueError`。

## 调用点：工具怎么读语料目录

`search_notes` 每次调用时读环境变量 `NOTES_ROOT`，没有就用 `DEFAULT_NOTES_ROOT`
（仓库根下的 `notes/`）。检查器就是这样注入语料的：

```python
os.environ["NOTES_ROOT"] = "<demos/day65/corpus>"
result = await client.call_tool("search_notes", {"keyword": "关键词", "limit": 3, "folder": "notes"})
# result.is_error 为 False 时，result.structured_content == {"result": [ ... ]}
```

失败时（越界、语料根不存在、参数不合法）返回 `is_error=True`，消息里写原因；
这些错误都由 `ValueError` 转成 `ToolError`，和 Day64 的做法一致。

## 语料

检查器用 `demos/day65/corpus/`，内容是固定的：

| 文件 | 内容要点 |
|---|---|
| `notes/python-notes.md` | 第 3 行含「关键词」 |
| `notes/agent-notes.md` | 第 2 行含「工具」；第 3、4 行含「关键词」 |
| `archive/old.md` | 第 2 行含「关键词」 |
| `empty.md` | 只有空白 |
| `binary.md` | 不是 UTF-8（用 `errors=ignore` 会「读出」关键词，所以必须跳过） |
| `emptydir/` | 没有 `.md` 的目录，用来查「先校验参数」 |

越界用的文件在 `demos/day65/outside/secret.md`，任何一组都不该读到它。

## 固定输入表

### A. `safe_subdir(CORPUS, folder)`（8 组）

| # | folder | 期望 |
|---|---|---|
| 1 | `""` | 返回 `CORPUS.resolve()` |
| 2 | `"notes"` | 返回 `CORPUS/notes` 的 resolve 结果 |
| 3 | `"notes/../notes"` | 合法，返回同一个 `notes` 目录 |
| 4 | `".."` | `ValueError` |
| 5 | `"../outside"` | `ValueError` |
| 6 | `"C:\\Windows"` | `ValueError`（绝对路径） |
| 7 | `"missing"` | `ValueError`（目录不存在） |
| 8 | `"notes/python-notes.md"` | `ValueError`（是文件不是目录） |

### B. `search_files(...)`（10 组）

| # | 调用 | 期望 |
|---|---|---|
| 9 | `(CORPUS, "关键词", 5)` | 4 条，顺序：`archive/old.md:2`、`agent-notes.md:3`、`agent-notes.md:4`、`python-notes.md:3` |
| 10 | `(CORPUS, "关键词", 2)` | 前 2 条（old、agent:3） |
| 11 | `(CORPUS, "关键词", 5, "notes")` | 3 条，source 仍是 `notes/...` |
| 12 | `(CORPUS, "工具", 5)` | 1 条 `notes/agent-notes.md:2` |
| 13 | `(CORPUS, "不存在的词", 5)` | `[]` |
| 14 | `(CORPUS, "   ", 5)` | `ValueError` |
| 15 | `(CORPUS, "关键词", 0)` | `ValueError` |
| 16 | `(CORPUS, "坏文件", 5)` | `[]`（坏编码文件被跳过，不能靠 ignore 读出来） |
| 17 | `(CORPUS, "关键词", 5, "notes/../notes")` | 同第 11 组，3 条 |
| 18 | `(emptydir, "   ", 5)` | `ValueError`（没文件也要先校验参数） |

第 9 组的完整期望：

```python
[
    {"source": "archive/old.md", "line": 2, "text": "关键词：旧的也保留。"},
    {"source": "notes/agent-notes.md", "line": 3, "text": "关键词：描述写清用途。"},
    {"source": "notes/agent-notes.md", "line": 4, "text": "关键词：参数写清含义。"},
    {"source": "notes/python-notes.md", "line": 3, "text": "关键词：元组不可变。"},
]
```

### C. 通过 MCP 工具调用（4 组）

| # | 设置 | 调用 | 期望 |
|---|---|---|---|
| 19 | `NOTES_ROOT=corpus` | `search_notes("关键词", 3, "notes")` | 不报错，3 条（同第 11 组） |
| 20 | `NOTES_ROOT=corpus` | `search_notes("关键词", folder="../outside")` | `is_error=True` |
| 21 | `NOTES_ROOT=corpus/no-such-dir` | `search_notes("关键词")` | `is_error=True` |
| 22 | 不设 `NOTES_ROOT` | `search_notes("流式", 2)` | 不报错，至少 1 条，source 不含绝对路径、以 `.md` 结尾 |

第 22 组用的是仓库真实的 `notes/`，内容以后会变；检查器只要求「至少一条、出处是相对
`.md`」，不比对具体文字。

## 跑法

```powershell
# A：路径解析
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part a
# B：目录检索
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part b
# C：MCP 工具
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part c
# 三部分一起
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py
```

预期：A 8/8、B 10/10、C 4/4，合计 22/22。

## 数据来源与预算

- 全部离线，**0 次模型调用**；语料是 `demos/day65/corpus/` 的固定文件。
- 每次运行在 `demos/day65/outputs/` 下新建目录，保存 `console.log`、`run_info.json`、
  `results.json`；失败也保留。
- `DAY65_RUN_ORIGIN` 默认 `unconfirmed`；AI 自验时标 `ai_validation`。

## 交付前自查

- [ ] `search.py` 里没有 `NotImplementedError` 残留
- [ ] `safe_subdir` 返回的是 `resolve()` 之后的路径，`notes/../notes` 通过
- [ ] `search_files` 的 source 相对语料根，不是相对 folder
- [ ] 坏编码文件不报错、也不出现在结果里（别用 `errors="ignore"`）
- [ ] 参数校验发生在扫描之前（第 18 组）
- [ ] `search_notes` 每次调用时读 `NOTES_ROOT`，而不是 import 时读一次
- [ ] 检查器 22/22
