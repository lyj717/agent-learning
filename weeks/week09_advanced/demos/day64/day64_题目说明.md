# Day64 题目：把 `find_matches` 注册成 MCP 工具 `search_text`

今天不写业务系统，只把「一个纯函数 → 一个模型能调用的工具」这条路走通。
文件检索、路径边界、资源与提示词都在后面几天。

## 你要改哪两个文件

| 文件 | 你要做的 |
|---|---|
| `projects/mcp_server/search.py` | 实现 `find_matches(text, keyword, limit=5)` |
| `projects/mcp_server/server.py` | 在 `mcp` 上注册工具 `search_text`，内部调用 `find_matches` |

不要改检查器，也不要改 `projects/mcp_server/__init__.py`。

## 调用点：谁在什么时候调用你的工具

检查器用**进程内连接**发起调用（和 Day64 演示一相同；它不经过 JSON-RPC）：

```python
from mcp import Client

from projects.mcp_server.server import mcp  # 你注册的工具挂在 mcp 上

async with Client(mcp) as client:
    tools = await client.list_tools()  # 看 tools/list
    result = await client.call_tool(
        "search_text",
        {"text": "要检索的全文", "keyword": "关键词", "limit": 3},  # arguments
    )
```

- `text`、`keyword` 是必填参数，检查器每组都会传；
- `limit` 是可选参数，默认 `5`；不传时也必须是 5 条上限；
- 工具抛 `ValueError` 或 `ToolError` 时，客户端拿到的是 `is_error=True` 的结果，
  **不是** Python 异常（只有协议层错误才是异常）；
- 返回值会同时出现在 `result.content`（给模型看的 JSON 文本）和
  `result.structured_content`（给代码用）。返回 `list` 时，SDK 会包一层
  `{"result": [...]}`，检查器会先拆这层包装再比较。

## `search_text` 的接口

```python
@mcp.tool()
def search_text(text: str, keyword: str, limit: int = 5) -> list[dict[str, int | str]]:
    """按行检索关键词，返回命中的行号与原文。"""
```

- **工具名**：必须是 `search_text`（不是 `find_matches`，也不是 `search`）。
- **描述**：docstring 不能为空——它是模型判断「何时该调这个工具」的唯一依据。
- **返回**：`list[dict]`，每项**恰好两个键**：
  `{"line": int, "text": str}`。`line` 从 1 开始；`text` 是整行原文，
  不去首尾空白、不改大小写。
- **无命中**：返回 `[]`，`is_error=False`。
- **参数不合法**：抛出 `ValueError` 或 `ToolError`，消息里说明是哪个参数不合法。

`find_matches` 的完整参数说明、返回结构和异常边界写在
`projects/mcp_server/search.py` 的 docstring 里，以那里为准。

## 固定输入表（13 组，检查器就按这张表跑）

常量：
- `A = "第一行：笔记开头\n第二行：关键词 在这里\n第三行：关键词 也在\n第四行：结束"`
- `B = "Note 大写\nnote 小写\nNOTE 全大写"`

| # | 检查项 | 输入 / 动作 | 期望 |
|---|---|---|---|
| 1 | 工具已注册 | `tools/list` | 工具名里有 `search_text` |
| 2 | 必填参数 | 读 `inputSchema` | `required` 恰为 `text`、`keyword` 两项 |
| 3 | 默认值 | 读 `inputSchema` | `limit` 有 `default=5`，且不在 `required` 里 |
| 4 | 描述 | 读 `description` | 非空、去空白后至少 8 个字符 |
| 5 | 正常命中 | `A`，`"关键词"`，`limit=5` | 恰 2 条：`(2, "第二行：关键词 在这里")`、`(3, "第三行：关键词 也在")` |
| 6 | limit 截断 | `A`，`"关键词"`，`limit=1` | 恰 1 条：第 2 行 |
| 7 | 大小写不敏感 | `B`，`"note"` | 恰 3 条：第 1、2、3 行 |
| 8 | 无命中 | `A`，`"不存在的词"` | `[]`，且 `is_error=False` |
| 9 | 空关键词 | `A`，`"   "` | `is_error=True` |
| 10 | limit 为 0 | `A`，`"关键词"`，`limit=0` | `is_error=True` |
| 11 | limit 为负数 | `A`，`"关键词"`，`limit=-1` | `is_error=True` |
| 12 | 工具不存在 | 调用 `no_such_tool` | `is_error=True` |
| 13 | 参数类型不对 | `text=123` | `is_error=True`（SDK 的参数校验先拦下） |

第 12、13 组不需要你写代码：它们验证的是「失败也是结果」这个行为，
你只要别把异常吞掉、别自己返回错误字符串就行。

## 跑法

先单独测你的函数（不用起 server；把 `a` 那行换成你自己的输入也行）：

```powershell
.venv\Scripts\python.exe -X utf8 -c "from projects.mcp_server.search import find_matches; print(find_matches('a\nb 关键词', '关键词'))"
```

预期：`[{'line': 2, 'text': 'b 关键词'}]`。这一步过了，再去注册工具。

再跑检查器：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day64_mcp_exercises.py
```

预期：13 行逐项结果，最后一行「全过 13/13」。
没过就按行看：`[X] 第 5 组 ... 实际=... 期望=...`。

## 数据来源与预算

- 全部离线，**0 次模型调用**；`A`、`B` 两段文本是检查器里的固定数据，不读仓库文件。
- 每次运行在 `demos/day64/outputs/` 下新建目录，保存 `console.log` 与 `run_info.json`，
  另有 `results.json` 记录逐项结果；失败也保留，不覆盖历史。
- `DAY64_RUN_ORIGIN` 默认 `unconfirmed`；AI 自验时标记 `ai_validation`，不冒充分学员亲跑。

## 交付前自查

- [ ] `search.py` 的 `find_matches` 没有 `NotImplementedError` 残留
- [ ] `server.py` 里 `search_text` 挂在 `mcp` 上，名字拼写与表格一致
- [ ] 空关键词、`limit=0`、`limit=-1` 都真的抛出了异常，而不是返回 `[]`
- [ ] 命中的 `text` 与原文逐字一致（别 strip、别转小写）
- [ ] 检查器 13/13
