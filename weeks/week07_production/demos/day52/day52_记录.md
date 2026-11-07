# Day52｜真实 HTTP 与 SSE

2026-11-07 开工，整体暂估约 1 个自然日，每天按 3～5 小时；包含前置复习、
阅读演示、独立实现、排错和观察。这是排期估计，不是实测时长或完成时限。
本次先完成前置 A，约占 1/3～1/2 个自然日：到期短复验和真实 HTTP 启动环境。
SSE 主练习在前置核对后接续，不在本次重复实现 RAG 或会话历史。

## Day50 到期短复验（先闭卷 10～15 分钟）

以下是人工新情境；先不翻 Day50 源码。用自己的话或伪代码作答即可。

1. 已实现的 `trace_call("r52", "generate", action, emit)` 中，`action` 是调用方
   传入的无参数函数，`emit` 已实现、只收一个事件字典且不会报错。
   情况一 `action()` 正常返回 `None`；情况二它抛出 `TimeoutError("样例故障信息")`。
   分别复现调用、事件和返回/抛出的先后顺序；说明 `action` 调用几次、
   各事件怎样关联同一次请求，以及失败事件中记录什么异常信息。

   作答：
   正常情况：
      执行顺序：emit start → action() → emit ok → 返回 None
      action 调用次数：1
      调用方最后拿到：None
   异常情况：
      执行顺序：emit start → action() → emit error → 原样抛出异常
      action 调用次数：1
      调用方最后收到：TimeoutError("样例故障信息")
   关联同一次请求的依据：request_id
   失败事件记录的异常信息：TimeoutError

2. 某次问答取到唯一证据 `public.md#L1-L1`，消息准备成功，`request_fn` 正常返回
   `finish_reason="stop"`，原始文本是合法 JSON：
   `{"status":"answered","answer":"演示回答","cited_ids":["other.md#L1-L1"]}`。
   该引用不属于本次证据。`generate` 与 `validate` 分别应出现什么事件，
   整个问答能否正常返回？说明“生成正常结束”和“回答通过校验”的区别。

   作答：generates：start → ok，validate：start → error
   不能正常返回，生成正常结束说明模型返回了回答，回答通过校验说明模型的回答通过了 JSON 的字段、类型和状态，以及引用编号是否属于本次证据

## A：客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 实际结果 | 来源确认 |
|---|---|---|---|
| 请求角色概览（当前必跑） | outputs/web_roles_demo_20261107_170353_277468_b4da492a | 普通调用返回地点字典；TestClient/真实 HTTP 均 200，地点均为二楼服务台；停止后 ConnectTimeout，无 HTTP 响应；服务已停止 | 11 月 7 日学员确认亲跑 |
| Uvicorn 独立演示（已运行可保留，不要求补跑） | outputs/uvicorn_demo_20261107_172951_977690_25103a57 | GET /ping 返回 200，正文为“本机服务已收到请求”；服务已停止 | 11 月 7 日学员确认亲跑 |
| HTTPX 调用 Day51 应用（按需查阅，不要求补跑） | outputs/httpx_demo_20261107_170715_343283_8b7fb3e0 | 健康/问答/历史均 200；空白问题 400，捕获 HTTPStatusError；换客户端后仍有 1 条历史；服务已停止 | 11 月 7 日学员确认亲跑 |

数据来源：每轮 outputs/ 下的 console.log、server_info.json 和 server.log；
角色概览另存 roles_result.json；旧 Uvicorn 演示另存 uvicorn_result.json，
旧 HTTPX 演示另存 http_responses.json。模型调用均为 0，会实际访问本机端口。
11 月 7 日前置调整：概览替代旧两份演示的必跑要求，不新增重复记录任务。
旧演示未运行的行可留空；已存在的日志照常保留，不要求重跑。
以上三轮均 completed、model_calls=0；来源确认记在本记录，不改原始 run_info.json。
Uvicorn 运行后仅补充了启动调用链注释，原运行的源码摘要保持；另两份演示的当前摘要与运行时一致。

## A：观察与判断（学员填写）

1. 仅执行 `app = FastAPI()` 是否已经能让另一个进程通过端口访问它？
   哪个调用开始监听？再以概览的 `GET /notice` 为例，说明 HTTPX、Uvicorn、
   FastAPI、`read_notice` 各负责哪一步；若已理解旧应用，也可选 `POST /ask` 与
   `common_post` 说明同样的分工，两条路径任选一条，不增加第二道观察。

   作答：不能，从调用uvicorn.run后开始监听
   HTTPX是一个python库，负责发送请求
   Uvicorn负责接收请求并监听端口
   FastAPI负责分配工作
   read_notice负责执行

## B1：SSE 事件格式（已交付，学员先跑演示）

前置 A 于 11 月 7 日经答疑核对通过。SSE 剩余主段暂估约半天到一个自然日，
包含生成器复习、独立实现、运行、边界判断和订正；当前先认识事件格式。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 实际结果 | 来源确认 |
|---|---|---|---|
| SSE 格式演示（18:02） | outputs/sse_format_demo_20261107_180248_425124_7933ee1c | 200；text/event-stream；两条 notice；整份 JSON 解析为 JSONDecodeError；服务已停止 | 11 月 7 日学员确认亲跑 |
| SSE 格式演示（18:31） | outputs/sse_format_demo_20261107_183115_732758_b0ee48db | 200；text/event-stream；两条 notice；整份 JSON 解析为 JSONDecodeError；服务已停止 | 11 月 7 日学员确认亲跑 |

数据来源：本轮 console.log、sse_format_result.json、server_info.json；
包含实际状态码、Content-Type、原始正文、事件条数、两条解析后数据及服务停止状态。
两轮均 completed、model_calls=0，源码摘要与当前演示一致；原始 run_info.json 保持。

### 观察与判断（学员填写）

1. 从演示第 4 节“实际正文如下”之后、“正文结束。”之前的文本中选一条事件，
   指出事件名、数据和结束标记。这段文本就是 response.text，题面称为“原始正文”。
   输出的两条事件属于几次 `/notices` 的 HTTP 响应？本题只看格式，不根据打印时刻判断到达速度。

   作答：
   event: notice
data: {"text": "\u660e\u5929\u4e0a\u5348\u5f00\u653e"}

   事件名：notice 数据：{"text": "\u660e\u5929\u4e0a\u5348\u5f00\u653e"} 结束标记为一空行
   1次HTTP响应


## B2：HTTPX 逐行读取（11 月 7 日核对通过）

B1 观察于 11 月 7 日经“原始正文”题意澄清后核对通过，原答保留。
本节只认识客户端 stream/iter_lines 与提前停止；主练习的业务终止判断随后接续。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 实际结果 | 来源确认 |
|---|---|---|---|
| HTTPX 逐行读取演示 | outputs/httpx_stream_demo_20261107_202807_859425_43ea4074 | 完整读取 1/2/3；提前停止只读到 1；两次响应均关闭；随后健康检查 200；最终服务已停止 | 11 月 7 日学员确认亲跑 |

数据来源：本轮 console.log、httpx_stream_result.json、server_info.json；
可核对完整/提前停止读取的行、计数、响应关闭状态、健康检查和服务停止状态。
逐行到达时间保留为实测数据，不要求匹配某个固定毫秒数。
本轮 completed、model_calls=0，运行版本早于字符串方法说明与表达式拆分；
原始源码摘要和日志保持，AI 对补充说明后的行为验证另记，不改成本轮运行结果。

### 观察与判断（学员填写）

1. 结合第 4 节的提前停止案例，说明 break 和离开内层 httpx.stream 的 with 各做了什么；
   随后的 /health 仍返回 200 说明什么？写清“本次响应”和“整份服务器”的区别。

   作答：break退出了循环，with退出本次响应
   返回200说明服务器还在运行。本次响应是整份服务器中的一次响应，退出本次响应不等于退出整份服务器

## C：流式客户端与终止判断（11 月 7 日经答疑核对验收）

只实现 [练习文件](../../exercises/day52_stream_exercises.py) 中的 read_answer_stream。
人工事件服务和逐条解析工具已提供；本题验收客户端读取、保留部分文本和最终状态分类，
不将其记为独立完成流式服务端或真实模型流式调用。

### 客观运行数据（确认亲跑后由 AI 转录）

运行目录：outputs/stream_exercise_20261107_230107_410193_2d297d46

来源确认与通过组数：11 月 7 日学员确认 23:01 亲跑，5/5；completed、model_calls=0，服务已停止。

| 情境 | HTTP 状态 | 最终 state | 实际 text | error_type | 本次响应已关闭 |
|---|---|---|---|---|---|
| normal | 200 | completed | 请到二楼取书。 | None | True |
| error | 200 | error | 请 | TimeoutError | True |
| truncated | 200 | incomplete | 请 | None | True |
| interrupt | 200 | interrupted | 请到二楼取书。 | None | True |
| timeout | 200 | error | 请 | ReadTimeout | True |

数据来源：本轮 checks.json 的 cases 与 passed/total、console.log、run_info.json，
服务停止状态见 server_info.json。单情境运行只转录对应行，不补造其他情境的数据。
每组请求次数、健康检查和失败详情保留在原始日志，不要求再抄一份。
以上仅转录 23:01 版本，原源码摘要与元数据保持；当前提交的摘要不同，
AI 对当前版本的验证另记，不把 AI 运行或后续修改并入本轮亲跑结果。

### 观察与判断（学员填写）

1. 对比 normal 和 interrupt：文本内容与 HTTP 状态码是否足以判断正常完成？
   结合实际读到了什么、因什么停止，说明两组最终状态的依据。

   作答：不足以判断是否正常完成
   normal 和 interrupt的'text'都为'请到二楼取书。'
   normal正常停止，interrupt因达到stop_after上限主动停止
   normal：{'state': 'completed', 'text': '请到二楼取书。', 'error_type': None}
   interrupt：{'state': 'interrupted', 'text': '请到二楼取书。', 'error_type': None}

2. error、truncated、timeout 都可能只留下“请”。分别说明它们为什么停止、
   最终怎样分类；哪组异常信息来自事件，哪组来自本地异常？

   作答：
   error:事件遭遇异常
   truncated:没有遇到done和error
   timeout:读超时
   error和timeout属于error，truncated属于incomplete
   error来自事件，timeout来自本地异常
