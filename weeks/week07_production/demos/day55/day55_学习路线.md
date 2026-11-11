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

## B 做什么（2026-11-10 交付，待亲跑）

容器这段把现有离线问答应用打进镜像：

- **镜像**是只读模板，**容器**是它的一次运行实例；
- 根目录 [Dockerfile](../../../../Dockerfile) 的每一行都有注释：基础镜像、环境变量、
  先装依赖再拷代码、暴露端口、`0.0.0.0` 启动；
- [.dockerignore](../../../../.dockerignore) 排除 `.venv`、`outputs`、`.git`、密钥文件——
  它们不属于镜像，传进去只会拖慢构建、甚至泄露数据；
- [运行入口](day55_server.py) 只做一件事：`app = make_app()`，把 Day51/Day52 的应用交给 uvicorn；
- 依赖只列在 [requirements-docker.txt](../../../../requirements-docker.txt)，不含测试与开发工具。

```powershell
# 仓库根目录执行
docker build -t week07-service:v1 .
docker run -d --name week07 -p 8000:8000 week07-service:v1
docker ps --filter name=week07
docker logs week07
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType 'application/json' -Body '{"session_id":"demo","question":"where"}'
docker images week07-service:v1
docker rm -f week07
```

边界：不做 Compose、HTTPS、鉴权或多阶段构建；镜像里不放密钥；真实构建结果以亲跑日志为准，
失败也保留日志。

验收结果：`week07-service:v1` 构建成功（279MB），容器 `Up`，`/health` 200、`/ask` 正常；
学员另改出 `Dockerfile.learner` 加非 root 用户，重建后 `id -u` 为 1000。首次构建曾因
Docker Hub 认证接口超时失败，属网络问题，未记为 Dockerfile 错误。

## C 做什么（2026-11-11 交付）

最简页面只做一件事：把 `/ask` 返回的 JSON 显示出来。

- [页面入口](day55_web.py)：复用 `make_app()`，再加一个 `GET /` 返回 [index.html](static/index.html)；
- 页面里 `<input>`、按钮和输出区已经搭好，`ask()` 里留了四个 TODO：
  发 POST、解析 JSON、算耗时、把回答/引用/耗时写进页面；
- 浏览器打开页面后，输入“地点”，应看到“请到二楼取书。”、引用 `public.md#L1-L1` 和毫秒数。

```powershell
.venv\Scripts\python.exe -m uvicorn weeks.week07_production.demos.day55.day55_web:app --port 8002 --reload
# 浏览器打开 http://127.0.0.1:8002/
```

验收：页面能加载；正常提问显示回答、引用和耗时；空问题能看到错误提示（不是静默失败）。
边界：单页、不引前端框架、不做鉴权或样式打磨；页面只消费已有接口。

验收结果（2026-11-11）：页面 200；提问“地点”返回 `请到二楼取书。` 与 `public.md#L1-L1`；
空输入返回 422 并在页面显示校验错误；耗时在页面显示。页面 JS 逻辑由学员伪代码给出，
AI 只修正语法，HTML 与服务入口由 AI 提供。

## 边界

- A1 只做错误响应与信息暴露；提示词注入、工具越权、输出过滤不在这一题里解决。
- 502/504 表示上游依赖失败，不是本地参数错误；没有真实服务商调用，全部为人工异常。
- 容器：本机 `docker` 命令不存在，B 段只能先准备配置，验证状态如实记录。
- 页面：只做最简 HTML 与 fetch，不做鉴权、样式打磨或前端框架。

## 后续

A1 验收后接 A2（权限与注入边界），再 B 容器配置与 C 页面；Day56 做新情境整合、
口头解释与交接。
