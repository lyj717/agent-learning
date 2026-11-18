# Day61 题目说明：失败模式与确定性检查

本页是 [练习](day61_failure_exercises.py) 的完整题面：五类失败模式、检查函数、
判分情形、运行方式与预算。练习文件已给出函数签名与断言目标，答案留空。

## 五类失败模式与教具

| 模式 | 教具函数 | 正常版 | 故障版（`DAY61_VARIANT=bad`） |
|---|---|---|---|
| 无限循环 | `run_agent_loop(max_steps)` | 步数 ≤ 上限 | 多走 4 步 |
| 工具误用 | `dispatch_tool(name, arguments)` | 未知工具抛 `ToolError` | 照样返回成功 |
| 幻觉引用 | `answer_with_citations(question)` | 引用都在证据内 | 引用不存在的编号 |
| 格式崩坏 | `parse_answer(raw)` | 缺键/非 JSON 抛 `FormatError` | 只做 `json.loads` |
| 越权/注入 | `authorize_tool(tool, path)` | 删除、路径穿越抛 `PermissionError` | 全部放行 |

## 五个检查函数

| 函数 | 要检查的信号 | 故障版应发生 |
|---|---|---|
| `check_loop_limit` | 返回的 `steps` ≤ `max_steps` | `AssertionError` |
| `check_tool_allowlist` | `dispatch_tool("delete_file", ...)` 抛 `ToolError` | `AssertionError` |
| `check_citation_grounding` | `cited_ids` 非空且都在 `evidence_ids` 内 | `AssertionError` |
| `check_format_schema` | 合法解析；缺键/非 JSON 抛 `FormatError` | `AssertionError` |
| `check_tool_authorization` | 删除与 `../` 路径抛 `PermissionError` | `AssertionError` |

`check_format_schema` 用三条固定输入：

- 合法：`{"status": "answered", "answer": "x", "cited_ids": ["c1"]}`
- 缺键：`{"foo": 1}`
- 非 JSON：`not json`

后两条应抛 `FormatError`，用 `pytest.raises(FormatError)` 接住。

每条检查的固定输入：

| 检查 | 固定调用 |
|---|---|
| `check_loop_limit` | `run_agent_loop(max_steps=5)` |
| `check_tool_allowlist` | `dispatch_tool("delete_file", {"path": "notes/a.md"})` |
| `check_citation_grounding` | `answer_with_citations("示例问题")` |
| `check_format_schema` | 上面三条字符串 |
| `check_tool_authorization` | `authorize_tool("read_file", "notes/a.md")`；`authorize_tool("delete_file", "notes/a.md")`；`authorize_tool("read_file", "../secret")` |

调用点：练习的 `main()` 把五个函数交给 `run_checks`；`tests/test_day61_failure_modes.py`
再把它们逐个接进 pytest。

## 判分情形（共 10 项）

| # | 运行 | 期望 |
|---|---|---|
| 1 | 正常版 × `check_loop_limit` | 不抛异常 |
| 2 | 故障版 × `check_loop_limit` | `AssertionError` |
| 3 | 正常版 × `check_tool_allowlist` | 不抛异常 |
| 4 | 故障版 × `check_tool_allowlist` | `AssertionError` |
| 5 | 正常版 × `check_citation_grounding` | 不抛异常 |
| 6 | 故障版 × `check_citation_grounding` | `AssertionError` |
| 7 | 正常版 × `check_format_schema` | 不抛异常 |
| 8 | 故障版 × `check_format_schema` | `AssertionError` |
| 9 | 正常版 × `check_tool_authorization` | 不抛异常 |
| 10 | 故障版 × `check_tool_authorization` | `AssertionError` |

注意：故障版必须是 `AssertionError`。如果检查直接让 `ToolError`、
`PermissionError` 或 `JSONDecodeError` 冒出来，说明没有用 `pytest.raises` 接住，
检查器会判为「没有咬住」。

## 运行方式

```powershell
# 检查器：正常版 / 故障版各跑一遍
.venv\Scripts\python.exe -B -X utf8 weeks\week08_evaluation_reliability\exercises\day61_failure_exercises.py

# pytest 外壳：五个检查逐个收集
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest_tmp_day61 tests/test_day61_failure_modes.py
```

无需模型调用，不依赖网络；每次运行保存 `console.log` 与 `run_info.json` 到
`demos/day61/outputs/`，失败也保留。

## 跑完看什么

检查器打印每组「正常版状态 / 故障版状态 / 是否符预期」，最后汇总 10 项。
pytest 应 5 passed。记录里还要补五类失败模式的真实证据（来自本仓库的运行或日志），
不是只写「理论上会这样」。
