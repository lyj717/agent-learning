# Day68 题目：给项目写 pytest，并接进 CI

今天不写新工具，写**项目自己的测试**：进程内 client 的确定性检查 + 一条真正的 stdio 冒烟，
然后把它们接进 GitHub Actions 的 offline job。检查器会真的跑一遍你的测试文件。

## 你要写/改的

| 文件 | 内容 |
|---|---|
| `tests/test_notes_mcp.py`（新建） | 至少 8 个 `test_` 函数，覆盖下面的清单 |
| `.github/workflows/ci.yml` | offline job 里加一个跑 `tests/test_notes_mcp.py` 的步骤 |
| `requirements-ci.txt` | 确认已有 `mcp==2.3.0`（Day64 加过，不用改） |

不要改 `projects/mcp_server/server.py` 的行为；测试只读它。

## 必须覆盖的 10 个契约

| # | 测试什么 | 断言要点 |
|---|---|---|
| 1 | 工具清单 | `tools/list` 同时有 `search_text`、`search_notes`、`read_note`，且三者 `description` 非空 |
| 2 | `search_text` 命中 | 传 `"a\nb 关键词"` 与 `"关键词"`，结构化结果是 `[{"line": 2, "text": "b 关键词"}]` |
| 3 | `search_text` 空关键词 | `is_error=True` |
| 4 | `search_notes` 正常 | `NOTES_ROOT` 指向 `weeks/week09_advanced/demos/day65/corpus`，返回含 `source`、`line`、`text` |
| 5 | `search_notes` 越界 | `folder="../outside"` → `is_error=True` |
| 6 | `read_note` 缺失 | `name="missing.md"` → `is_error=True`，消息非空 |
| 7 | 资源清单 | `list_resources` 含 `note://index`；读它得到 5 条相对路径 |
| 8 | 资源缺失 | 读 `note://nope.md` 抛 `MCPError`（不是 `is_error` 结果） |
| 9 | 提示词 | `get_prompt("review_note", {"name": "python-notes.md"})` 的消息含该名字 |
| 10 | stdio 冒烟 | 用 `subprocess.run(..., timeout=20)` 跑 `python -m projects.mcp_server.server`，空 stdin 下 `returncode == 0` |

测试在 `tests/` 下，pytest 会自动收集；函数名必须 `test_` 开头。

## 测试怎么写才稳

- **进程内**用 `Client(mcp)`，不起进程：`asyncio.run(...)` 或 `pytest-asyncio` 都行（本项目没装，用前者）。
- **语料固定**：用 `monkeypatch.setenv("NOTES_ROOT", str(CORPUS))`（pytest 内建 fixture），
  不要依赖仓库 `notes/` 当前内容；测试结束自动恢复。
- **stdio 冒烟**用 `subprocess.run`，必须写 `timeout=20`；不要用 `Client(StdioServerParameters)`
  起长连接——空 stdin 下 `python -m` 会自己退出，最省事。
- 断言只写「契约」：结构、键、`is_error`、错误码；不要断言模型措辞。

## CI 怎么接

`.github/workflows/ci.yml` 的 `offline` job 里加一步（位置在现有 pytest 之前或之后都行）：

```yaml
      - run: pytest -p no:cacheprovider tests/test_notes_mcp.py
```

现有 `pytest -p no:cacheprovider` 本来也会跑到它，但单独一步能让失败一眼看出是
「MCP 契约坏了」还是「其他测试坏了」。检查器只查这一步在不在。

## 跑法

```powershell
# 你的测试文件
.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests\test_notes_mcp.py -v
# 检查器（会再跑一次你的测试）
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day68_ci_test_exercises.py
```

预期：你的测试 **至少 8 passed、0 failed、0 skipped**；检查器 9/9。

## 数据来源与预算

- 全部离线，**0 次模型调用**；测试用 `day65/corpus` 固定语料。
- 检查器会 `subprocess` 跑 pytest，超时 180 秒；测试文件里不要再起长连接或等输入。
- 每次运行在 `demos/day68/outputs/` 下新建目录，保存 `console.log`、`run_info.json`、`results.json`。
- `DAY68_RUN_ORIGIN` 默认 `unconfirmed`；AI 自验标 `ai_validation`。
