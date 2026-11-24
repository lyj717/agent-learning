# Day66 题目：资源、提示词与三种错误形态

今天把笔记暴露成 **资源**（宿主可加载），再加一个 **提示词模板**（用户可挑），
最后把「工具 / 资源 / 提示词」的失败形态分清。两部分：A 文件函数，B 注册与协议行为。

## 你要改哪两个文件

| 文件 | 你要做的 |
|---|---|
| `projects/mcp_server/search.py` | 实现 `resolve_note`、`list_note_paths`、`load_note`（A） |
| `projects/mcp_server/server.py` | 注册两个资源、一个提示词、一个工具（B） |

不要改检查器，也不要改 `notes_root()`。

## 接口

```python
def resolve_note(root: Path, name: str) -> Path:
    """把笔记的相对名字解析成绝对文件路径，保证不越界。"""

def list_note_paths(root: Path) -> list[str]:
    """列出 root 下所有 Markdown 的相对 POSIX 路径，升序。"""

def load_note(root: Path, name: str) -> str:
    """按名字读一篇笔记，返回全文。"""
```

注册部分：

```python
@mcp.resource("note://index")
def note_index() -> str: ...          # 列出所有相对路径，用一个换行符连接

@mcp.resource("note://{+path}")
def note_body(path: str) -> str: ...  # 读一篇；{+path} 才匹配带斜杠的路径

@mcp.prompt()
def review_note(name: str) -> str: ...  # 返回一段请模型复盘 note://<name> 的文字

@mcp.tool(name="read_note")
def read_note_tool(name: str) -> str: ...  # 调 load_note，ValueError 转 ToolError
```

`resolve_note` / `list_note_paths` / `load_note` 的完整参数、返回与异常写在
`search.py` 的 docstring 里，以那里为准。三条容易做错的：

1. `list_note_paths` 返回的是**相对路径**（`notes/agent-notes.md`），不是绝对路径，也不是 `Path`。
2. `resolve_note` 只接受 `.md` 文件；目录、绝对路径、越界、不存在都要抛 `ValueError`。
3. 资源处理器里抛的异常**不会**把消息带给客户端（见下面错误形态）；工具里的 `ToolError` 才带。

## 调用点：客户端会怎么调

检查器用进程内 `Client(mcp)`，`NOTES_ROOT` 指向 `demos/day65/corpus`：

```python
# 资源
await client.list_resources()                 # 看到 note://index
await client.list_resource_templates()        # 看到 note://{+path}
text = (await client.read_resource("note://index")).contents[0].text
text = (await client.read_resource("note://notes/agent-notes.md")).contents[0].text

# 提示词
prompt = await client.get_prompt("review_note", {"name": "python-notes.md"})
prompt.messages[0].content.text               # 渲染出的 user 消息

# 工具
result = await client.call_tool("read_note", {"name": "missing.md"})
result.is_error                                # True
```

失败时两种形态，别混：

- **工具**失败 → `result.is_error=True`，`content[0].text` 带原因；
- **资源/提示词**失败 → 客户端抛 `MCPError`，`error.error.code` 是 `-32602`（未知 URI）
  或 `-32603`（处理器异常），消息可能被泛化。

## 固定输入表

### A. 文件函数（11 组）

| # | 调用 | 期望 |
|---|---|---|
| 1 | `resolve_note(CORPUS, "notes/agent-notes.md")` | 返回该文件的绝对路径 |
| 2 | `resolve_note(CORPUS, "notes/../notes/agent-notes.md")` | 同一个路径 |
| 3 | `resolve_note(CORPUS, "../outside/secret.md")` | `ValueError` |
| 4 | `resolve_note(CORPUS, "C:\\Windows")` | `ValueError` |
| 5 | `resolve_note(CORPUS, "missing.md")` | `ValueError` |
| 6 | `resolve_note(CORPUS, "notes")` | `ValueError`（是目录） |
| 7 | `list_note_paths(CORPUS)` | 5 条，升序：`archive/old.md`、`binary.md`、`empty.md`、`notes/agent-notes.md`、`notes/python-notes.md` |
| 8 | `list_note_paths(CORPUS / "no-such-dir")` | `ValueError` |
| 9 | `load_note(CORPUS, "notes/agent-notes.md")` | 与源文件全文逐字相等 |
| 10 | `load_note(CORPUS, "binary.md")` | `ValueError`（不是 UTF-8） |
| 11 | `load_note(CORPUS, "missing.md")` | `ValueError` |

（`CORPUS` = `demos/day65/corpus`，沿用 Day65 的固定语料。）

### B. 资源、提示词与工具（10 组）

| # | 动作 | 期望 |
|---|---|---|
| 12 | `list_resources` 的 URI | 含 `note://index` |
| 13 | `list_resource_templates` | 含 `note://{+path}` |
| 14 | 读 `note://index` | 文本恰为 5 条相对路径用 `\n` 连接 |
| 15 | 读 `note://notes/agent-notes.md` | 文本与源文件逐字相等 |
| 16 | 读 `note://nope.md` | 抛 `MCPError`，code `-32603`（且 12/14/15 已通过才计） |
| 17 | 读 `unknown://x` | 抛 `MCPError`，code `-32602`（且 12/14/15 已通过才计） |
| 18 | `get_prompt("review_note", {"name": "python-notes.md"})` | 消息文本非空且含 `python-notes.md` |
| 19 | `get_prompt("no_such_prompt", {})` | 抛 `MCPError`（且 18 已通过才计） |
| 20 | `call_tool("read_note", {"name": "missing.md"})` | `is_error=True`，消息含文件不存在的原因 |
| 21 | `call_tool("read_note", {"name": "binary.md"})` | `is_error=True`，消息说明编码问题 |

第 16、17、19 组带前置条件：如果资源/提示词根本没注册，它们也会抛错，但那不算通过。

## 跑法

```powershell
# A：文件函数
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py --part a
# B：注册与协议
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py --part b
# 一起
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py
```

预期：A 11/11、B 10/10，合计 21/21。

## 数据来源与预算

- 全部离线，**0 次模型调用**；语料是 Day65 的 `demos/day65/corpus/`。
- 每次运行在 `demos/day66/outputs/` 下新建目录，保存 `console.log`、`run_info.json`、
  `results.json`；失败也保留。
- `DAY66_RUN_ORIGIN` 默认 `unconfirmed`；AI 自验标 `ai_validation`。

## 交付前自查

- [ ] `search.py` 没有 `NotImplementedError` 残留
- [ ] `list_note_paths` 返回相对 POSIX 路径的 `list[str]`
- [ ] `resolve_note` 拒绝绝对路径、越界、非 `.md`、目录、不存在
- [ ] 资源模板写成 `note://{+path}`（不是 `{path}`）
- [ ] 提示词返回的是字符串；工具 `read_note` 用 `@mcp.tool(name="read_note")`
- [ ] 检查器 21/21
