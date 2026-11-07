# Day52 学习路线

**2026-11-07：Day52 已经答疑与订正验收，下一单元 Day53 尚未开工。**
五种流式情境与补充 HTTP 500 检查通过，两道观察已核对；学员原答保留。
A 三轮、B1 两轮及 B2 20:28 演示均确认亲跑，客观数据已转录；学员原答保留。
C 的 23:01 版本亲跑 5/5 已确认，后续状态检查与收尾由 AI 单独验证，不改原轮次数据。
SSE 主段曾估约半天到一个自然日、C 开工曾估约半个自然日，均含实现、排错与观察订正；
这些是排期历史，实际学习小时未测，不把答疑过程折算为连续学习耗时。

**2026-11-07 开工：整体暂估约 1 个自然日，每天仍按 3～5 小时。** 包含到期复验、
前置复习、读演示、独立实现、排错、运行和订正，不按代码行数估计。
原先先交前置 A，估约 1/3～1/2 个自然日；这段已核对，原估保留供校准。
若理解或排错明显超量，先调整后段范围再重估，不要求加时赶完。

**11 月 7 日前置调整：** 连续答疑说明 HTTP 工具的角色还需要单独建立，当前先用
[请求角色概览](day52_web_roles_demo.py) 对照普通函数、TestClient 和真实端口调用。
它替代下面旧两份演示的必跑要求，旧演示保留作 API 查阅，不叠加三份运行任务。
剩余前置暂按约 1/3～1/2 个自然日安排，包含理解、试跑和一道观察；原整体一天为开工估计，
前置核对后再估 SSE 剩余量，不要求本次直接进入 SSE。

## 本次的位置与目标

Day51 的应用已经能用 TestClient 在进程内检查；本单元的前置 A 已把应用接到真实本机 HTTP。
SSE 格式与 HTTPX 逐行读取已在 B1/B2 核对；C 由学员实现流式客户端及最终状态判断。

本周继续以约四个自然日为协调目标，但不会为守住初版预算跳过必要前置。
前置复用旧问答应用；C 使用独立人工事件服务，不重写问答或会话历史。
不做前端、鉴权或额外的异步/并发练习。当前目标是读懂一次 HTTP 响应中的分段事件，
保留部分文本，区分完成、失败、缺少结束事件和主动停止。
C 不验收独立编写流式服务端或真实模型流式生成；与旧 RAG 的服务整合留到阶段整合，
502/504 映射和标准 trace 留到 Day53。

## 已完成内容与查阅入口

1. 已完成的 A 不重做。回看角色时查 [请求概览](day52_web_roles_demo.py)、
   [Uvicorn](day52_uvicorn_demo.py)、[HTTPX](day52_httpx_demo.py)。
2. B1/B2 不重跑。回看时查 [格式演示](day52_sse_format_demo.py) 与
   [HTTPX 逐行演示](day52_httpx_stream_demo.py)。
3. [完成的 C 函数](../../exercises/day52_stream_exercises.py) 保留学员实现和主程序对照输出，
   长题干已清成一行 docstring，解析工具导入保持启用。[解析工具](day52_stream_support.py)
   是 AI 提供的运行支持，下面保留调用接口。
4. 两道观察与亲跑客观数据在同一 [记录](day52_记录.md) 的 C；原答和原始日志保留。

## C 接口速查

`read_answer_stream(base_url, mode, stop_after=None)` 是已完成的客户端函数。

| 输入 | 含义 |
|---|---|
| base_url（str，必填） | 已启动服务的地址，入口负责准备 |
| mode（str，必填） | 人工服务情境 normal/error/truncated/slow；入口保证有效 |
| stop_after（int 或 None，默认 None） | 收到几个非空 delta 后主动停；None 表示不主动停 |

发送一次 GET 到 base_url + /answer/ + mode，使用 timeout=READ_TIMEOUT（0.5 秒）、
trust_env=False，先检查 HTTP 状态，再逐步读取，所有出口关闭响应。
`iter_sse_events(response.iter_lines())` 已实现，逐条交出
`{"event": str, "data": dict}`，data 已解析，不再 loads。delta 的 data 是
`{"text": str}`，空文字不计数；done 的 data 是 {}；error 的 data 是
`{"error_type": str}`；其他事件忽略。工具会原样传出读取异常。

返回固定三键：`{"state": str, "text": str, "error_type": str | None}`，
text 始终保留已经收到的文字。

| 终止依据 | state | error_type |
|---|---|---|
| 收到 done | completed | None |
| 收到 error 事件 | error | 事件中给出的类型名 |
| 本地 httpx.ReadTimeout | error | ReadTimeout |
| 未收到终止事件就读到 EOF | incomplete | None |
| 先达到 stop_after | interrupted | None |

HTTP 状态异常等其他错误继续向调用方抛出；HTTP 200、文本看似完整和流结束均不能替代 done。
read timeout 是等待后续一段网络数据的上限，不是整个请求的总时限。

## 命令（仓库根目录）

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day52_stream_exercises.py --case normal
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day52_stream_exercises.py
```

默认入口检查全部五组；--case 还支持 error/truncated/interrupt/timeout，可单独排查。

以下是已完成 A 的查阅入口，不要求重跑：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day52\day52_web_roles_demo.py
```

已完成 B1/B2 的演示保留作查阅：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day52\day52_sse_format_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day52\day52_httpx_stream_demo.py
```

旧独立演示按需查阅，不要求重复运行：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day52\day52_uvicorn_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day52\day52_httpx_demo.py
```

上述入口也支持在其他目录通过脚本绝对路径运行；根目录通过脚本位置确定。
本机需要新增基础包 Uvicorn 0.54.0，已写入根 requirements.txt；沿用 FastAPI、HTTPX，
不装额外 SSE 插件。`--serve --port` 是已搭好环境调用的内部服务入口，正常学习使用默认入口。

## 谁负责什么，旧代码在哪里

角色概览用自己的 `read_notice` 返回固定地点；先认下面的分工，再看旧问答应用的复用入口。

| 组件 | 身份与本次用途 |
|---|---|
| HTTP / HTTPS | 通信规则；HTTPS 为 HTTP 通信提供加密保护，不是 Python 库 |
| HTTPX | Python 客户端库，可以请求 HTTP 或 HTTPS 地址；本例只用本机 HTTP |
| TestClient | 程序内向指定 app 提交测试请求，不启动 Uvicorn 或监听端口 |
| 已有 FastAPI 应用 | 你已写好的服务端业务，包含请求校验、问答和历史 |
| Uvicorn | 独立进程监听本机端口，把收到的请求交给 FastAPI 应用 |
| FastAPI | 按请求方法和路径找到处理函数，也能做输入校验；具体回答逻辑由你写 |
| read_notice / common_post | 具体业务函数；概览的前者由 AI 演示，后者来自学员已验收的旧应用 |
| 公共启动环境 | AI 已搭好，负责选端口、启动、等待就绪、保存子进程输出和停止；不要求重写 |

已验收的 `ChatRequest`、`create_chat_app` 实际实现集中到
[service_functions.py](../shared/service_functions.py)，注明原练习出处、输入输出和边界；
旧问答四份函数仍在 [rag_functions.py](../shared/rag_functions.py)，原练习都保留。
[day52_app.py](day52_app.py) 只提供已实现的人工检索、请求、日志回调，
供旧应用运行，不是本次需要补写的新函数；本次模型调用为 0。
[day52_runtime.py](day52_runtime.py) 是运行背景，先用即可，不要求学习 socket 或子进程实现。

## 输出和每一格数据从哪里来

每轮在本目录 outputs/ 新建目录，失败也保留：

- console.log、run_info.json：当前模式、配置、来源、控制台和异常。
- roles_result.json：角色概览的普通返回值、两种请求的响应、停止后的连接错误及停止状态。
- sse_format_result.json：SSE 格式演示的响应头、原始正文、事件数、解析后内容及整份 JSON 解析异常。
- httpx_stream_result.json：完整读取的逐行时间、提前停止读到哪里、响应关闭状态及健康检查结果。
- checks.json：C 的实际/期望返回值、请求次数、HTTP 状态、响应关闭、健康检查和通过组数。
- server.log：独立服务进程的输出与报错；HTTPX 演示含旧问答的实际阶段事件。
- server_info.json：实际地址、端口、进程号与退出时是否已停止。
- uvicorn_result.json：第一份演示收到的实际状态码、URL 与正文。
- http_responses.json：第二份演示逐次实际请求的方法、URL、状态、正文及捕获的客户端异常。

默认来源为 unconfirmed，AI 验证标为 ai_validation；确认学员亲跑后才转录表格，
不把 AI 试跑当作学员数据。先建记录模板再逐格核对上述来源，观察仍由学员写。
这里是真实本机 TCP/HTTP，业务数据是人工教具，没有请求服务商或读取密钥。

## 官方资料只读哪几小节

- [Uvicorn Settings](https://uvicorn.dev/settings/)：只看 Configuration Methods 的
  `uvicorn.run(app, host=..., port=...)` 和 Socket Binding 的 host/port；
  用来区分应用对象与监听进程，不用读 workers、TLS 或部署配置。
- [HTTPX QuickStart 的 Streaming Responses](https://www.python-httpx.org/quickstart/#streaming-responses)：
  B2 只看 with httpx.stream 和 iter_lines 的段落，对应逐行读取；其他客户端 API 暂不扩展。
- [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/)：B1 只看
  What are Server-Sent Events、Non-async path operation functions、ServerSentEvent，
  对应文本事件、普通 def/yield 与事件对象；跳过异步、重连与 POST 示例。
- [HTTPX Exceptions](https://www.python-httpx.org/exceptions/)：C 按需只查 ReadTimeout，
  对应等待后续数据超时；[Timeouts 的 read timeout](https://www.python-httpx.org/advanced/timeouts/)
  说明这是等待一段数据的时限，不是整份响应必须完成的总时限。

Day51 A/B 的延迟复验仍按 11 月 8～10 日窗口安排，尚未发生不勾选；
Day52 在 11 月 9～10 日安排 10～15 分钟闭卷复现终止事件、EOF、主动停止和读超时，
阶段末再做变式；该复验尚未发生。本单元已核对 Day50 到期复验，不重跑旧留出评测。
