# Day55 学习路线

## 当前目标与预计跨度（2026-11-10）

Week07 的最后一组任务：安全失败路径、容器打包、最简页面。计划表原估约 3/4 个自然日，
按实际工作量重估为 **约 1～1.5 个自然日**（每天 3～5 小时），分三段交付：

1. **A 安全失败路径**（约半天）：先做 A1「错误映射与信息暴露」——内部异常怎样变成对外
   响应、哪些内容绝不能出去；A2「权限与注入边界」另排一小段。
2. **B 容器打包**（约 1/4 天）：本机暂未安装 Docker，先准备 Dockerfile 与启动说明，
   真实构建/启动不伪报，等条件具备再验证。
3. **C 最简页面**（约 1/4 天）：一个能对话、看引用和耗时的最小页面。

本次先做 A1，约 1～1.5 小时；做完再估 A2 与 B/C。

## A1 做什么（2026-11-10 已验收）

先跑 [错误暴露演示](day55_error_leak_demo.py)（从 demonstrate 读起）：看“原样返回异常消息”
会泄露什么，再看按类别映射后的状态码与固定文案。

再在 [A1 练习](../../exercises/day55_error_exercises.py) 实现
`error_response(exc, request_id) -> tuple[int, dict[str, str]]`：

- 入口把异常和公开编号传给你，检查器逐组比对状态码、正文键值与敏感串；
- 规则：TimeoutError→504、ConnectionError→502、ValueError→400、其他→500；
  正文只有 `detail` 和 `request_id` 两个键，不出现异常消息、类型名、路径、密钥、堆栈；
- 五组情形（timeout、connection、bad_value、unknown、runtime）与期望正文都列在题面里。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day55\day55_error_leak_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day55_error_exercises.py
```

验收结果：五组 5/5，正文只有 `detail` 与 `request_id`，密钥、路径与堆栈均未出现；
两道观察已核对。下一步 A2。

## A2 做什么（2026-11-10 已验收）

先跑 [工具授权演示](day55_tool_auth_demo.py)（从 demonstrate 读起）：看只查工具名时
`../private` 仍被放行，以及注入文本怎样诱导出 `delete_file`。

再在 [A2 练习](../../exercises/day55_tool_auth_exercises.py) 实现
`authorize(tool_name, args, policy) -> tuple[bool, str]`：

- 工具名不在 `policy` → `(False, "工具不在白名单")`；
- `read_file`：`path` 缺失/空 → “缺少参数”；不以 `prefix` 开头或含 `..` → “路径越界”；
- `search`：`query` 缺失/空 → “缺少参数”；超过 `max_len` → “查询过长”；
- 通过则 `(True, "允许")`；原因只能是五个固定短句，不拼接路径或文档内容。

八组情形（read_public、read_traversal、read_outside、read_missing、search_ok、
search_empty、search_long、injected_delete）与期望结果都列在练习题面里。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day55\day55_tool_auth_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day55_tool_auth_exercises.py
```

验收结果：八组 8/8；路径穿越、越界路径、空参数、超长查询与被注入的 `delete_file`
全部被拒，原因均为固定短句；两道观察已核对。下一步 B 容器（等 Docker）与 C 页面。

边界：只做授权判断，不执行工具、不读文件；策略是代码常量，不由模型或外部文档生成；
输出过滤、密钥存放与容器放到后续小段。

## 边界

- A1 只做错误响应与信息暴露；提示词注入、工具越权、输出过滤不在这一题里解决。
- 502/504 表示上游依赖失败，不是本地参数错误；没有真实服务商调用，全部为人工异常。
- 容器：本机 `docker` 命令不存在，B 段只能先准备配置，验证状态如实记录。
- 页面：只做最简 HTML 与 fetch，不做鉴权、样式打磨或前端框架。

## 后续

A1 验收后接 A2（权限与注入边界），再 B 容器配置与 C 页面；Day56 做新情境整合、
口头解释与交接。
