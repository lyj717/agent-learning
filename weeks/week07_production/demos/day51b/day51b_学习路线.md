# Day51B 学习路线

**2026-11-07 状态：本次代码与两道观察经答疑订正验收。** 学员确认亲跑 A 9/9、
B 原检查 19/19；补齐路径编号清理边界后 AI 复验通过，来源分别记在
[记录](day51b_记录.md)。练习题干已清理，接口速查保留在本文件，以下学习顺序供回看。

**11 月 6 日减量后的当前安排：Day51B 约半天到一天，每天按 3～5 小时折算。**
保留状态归属、旧问答整合、会话历史与失败不写历史；复习、排错、亲跑和观察仍计入。
这是缩减范围后的估计，不是硬性完成时限，卡在必要前置时应先补课。
原估 B 为 1.5～2 天，包含额外的端口和客户端单元，保留为历史，不继续执行该范围。

## 当前目标与停靠点

- 本次完成：认识路径参数和应用内状态，接通旧问答与 HTTP，验证各会话历史独立，
  同应用换客户端保留、新应用独立，以及失败不追加。
- 真实端口与客户端并入 Day52 的共用启动环境，沿用本次应用，不另做一套业务练习和记录。
- 502/504 的细分异常映射留到 Day53 失败追踪时练。本次让旧函数异常由框架返回普通 500，
  只核对阶段 error 和历史不污染。

这次的主要新机制是“应用持有状态，多个请求按会话编号访问各自记录”。
路径参数是读取会话记录需要的小 API，先独立讲。先给这两份小演示，
完整问答服务由你在练习里接起来。

11 月 6 日排错补充：已写的历史列表混入其他会话，先看
[字典中的分组列表](day51b_grouped_lists_demo.py)，认识“键对应列表”、首次创建、
追加和读取；再回到 B 的保存与查询位置。不新增一套练习或观察记录。

你继续写服务端；FastAPI 调用你登记的处理函数。运行入口已经提供检索、请求、日志回调，
你无需重写这三个函数；用它们调用集中提供的旧 answer_with_trace 即可。
本次的检索和回答都是人工替身，保留真实旧消息组装、校验和阶段日志，不请求服务商。

## 先做哪一步

Day48 短复验于 11 月 6 日核对，Day51B 于 11 月 7 日验收，原学习顺序保留如下。

1. 先在 [记录](day51b_记录.md) 写两道 Day48 到期短复验，先不翻旧报告。
2. 跑 [路径参数](day51b_path_parameter_demo.py)，弄清 URL 里的编号怎样成为函数参数。
3. 跑 [应用内状态](day51b_application_memory_demo.py)，观察同应用换客户端与新建应用的区别。
4. 打开 [公共旧函数](../shared/rag_functions.py)，看索引与 answer_with_trace 的接口。
   trace_call、build_grounded_messages、check_grounded_reply 的实际实现也集中在同一文件。
5. 在 [练习](../../exercises/day51b_service_exercises.py) 完成 A，再完成 B。
   A 是旧模型机制迁移；B 给接口、字段、回调契约和验收，由你独立组织整合。
   A 目标 9/9 组、B 目标 19/19 组；A 沿用已有模型方式，不另设模型观察题。
6. 告知亲跑后，AI 转录客观数据；学员只填两道核心观察，详细批改留在聊天。

第一段建议先做到第 3 步，确认“字典何时创建、谁在后续请求中使用它”后再接问答。
Day50 的到期短复验仍在 11 月 7～8 日，Day51A 在 11 月 8～9 日，尚未发生不打勾。

## 命令（仓库根目录）

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51b\day51b_path_parameter_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51b\day51b_application_memory_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51b\day51b_grouped_lists_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day51b_service_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day51b_service_exercises.py --part b
```

## 接口速查

请求模型 `ChatRequest`：`session_id`、`question` 都必填，严格字符串、长度至少为 1，
拒绝额外字段；模型层不去空白，处理请求时再清理和拒绝纯空白。

`create_chat_app(retrieve_fn, request_fn, emit) -> FastAPI` 每次返回一份新应用，
各有独立历史。以下路径按顺序请求验证，未提供持久化或并发控制：

| 方法与路径 | 输入 | 正常响应 |
|---|---|---|
| `GET /health` | 无 | `200`，`{"status":"ok","mode":"offline"}` |
| `POST /ask` | JSON：`session_id:str`、`question:str` | `200`，三键 `session_id:str`、`request_id:str`、`checked:dict\|None` |
| `GET /sessions/{session_id}/history` | 路径中的会话编号 | `200`，`{"session_id":str,"turns":list[历史项]}`；未知会话的列表为空 |

保存和查询使用清理后的编号。一次正常 `/ask` 调用旧 `answer_with_trace` 一次，
按先后保存一条历史；每条历史恰有 `question:str`、`request_id:str`、`checked:dict|None`。
编号由外层字典分组给出，不重复放入历史项。正常 `checked` 含 `status`、`answer`、
`cited_ids`；空证据时原样保留 `checked=None`，正常返回并追加历史。
新应用创建自己的历史，旧应用保留原有历史；同应用换客户端不重建历史。

空白编号或问题返回 `400`，detail 分别是 `session_id 不能只有空白`、
`question 不能只有空白`，不调用旧问答；模型拒绝是 `422`，未知路径 `404`，
错误方法 `405`。旧问答抛异常时不追加历史，框架返回普通 `500`；
不公开异常消息，本单元不细分为 `502/504`。

三个回调已由运行入口提供，本单元仅将它们传给旧问答，不重新实现：
`retrieve_fn(question) -> list[Document]` 检索一次；非空证据才进入
`request_fn(messages) -> dict`，返回 `raw_text`、`finish_reason`；
`emit(event) -> None` 的保存路径由入口固定，只接事件字典，约定自身不抛异常。
完整类型、结构和异常见 [集中保留的旧函数](../shared/rag_functions.py)；
正常、空证据、检索超时替身均不联网，`model_calls=0`。

## 输出与记录的数据来源

每次在本目录 outputs/ 新建目录，保留 console.log、run_info.json；失败也保存。
A/B 另有 checks.json，B 还有 requests.jsonl、events.jsonl。
requests 保存逐组输入、状态码、实际/期望正文、回调次数、转发问题与请求编号；
events 保存旧函数实际发出的阶段事件。都是公开人工教具，不记录真实私人对话。

记录两格对照结果来自各轮 checks.json；观察 1 来自 B 中换客户端、新应用的请求结果，
观察 2 对照“空证据也是正常记录”和“检索超时”两组的状态码、回调次数与阶段输出。
每项均有可核对的数据或源码，不需要重抄终端。
日志默认 origin=unconfirmed，亲跑由学员确认；AI 验证单独标 ai_validation。
此前轮次和失败不覆盖，不把 AI 验证转录成学员实验。

## 本次边界

会话编号在本次只用于历史分组，客户端可以自行选择编号；这不构成身份鉴权。
资料是各会话共用的人工公共证据，本次没有资料权限过滤；Week06 的权限约束尾项继续
留到本周安全单元处理。历史只供读取，不被送进模型，不据此认定实现了多轮模型记忆。
只验顺序请求与应用内存；并发、重启持久化及真实端口留待相应阶段验证。
本节边界说明供阅读，不再要求学员重复写一题鉴权/记忆辨析。

## 官方文档读哪一小段

- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)：
  看最开头的 /items/{item_id} 与同名函数参数，理解路径模板和请求中的实际值；
  本次先用 str，不必读 Enum、复杂路径转换或后面的全部章节。
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)：
  回看 Using TestClient 中“客户端由已有应用创建”及 get/post，
  对照本次“换客户端”和“新建应用”是两种操作。
