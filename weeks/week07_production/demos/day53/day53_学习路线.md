# Day53 学习路线

## 当前安排（2026-11-08）

短复验已核对：第 1 题首答正确，第 2 题首次响应经反馈订正为 404，整体经订正通过。
A 两道观察已核对通过，16:46 演示已确认亲跑并转录客观数据。
B 两轮演示及 C 的 19:05 函数运行已确认亲跑并转录，C 通过 4/4，第 2 题观察正确。
两道 C 观察现已订正核对通过：正常空返回标 OK，抛异常标 ERROR；只记录类型名，原异常继续传出。
Day53 完成本次经答疑订正验收，长题干清为一行功能说明，学员逻辑与原始观察保留。
同一个 tracer 可以反复创建记录，
默认关联取决于当前父 span，外层 local_tracing 的 with 只提供工具，没有创建父 span。

Day52 已验收；Day53 开工时整体暂估约一个自然日，仍按每天 3～5 小时安排，包含复习前置、
理解新对象、读演示、独立实现、排错、亲跑、观察与订正，不按代码行数估计。
初版半天估计保留在本周历史表；本次新估依据 trace/span 与 SDK 对象的认知跨度。
Day50～52 已推进三个新单元，Day53 后、Day54 前另预留半个学习日复习与订正，
接续 11 月 9～10 日的到期复验；这是本周复习缓冲，不用延长每日学习时长消化。

前置 A 原先按约 1/3～1/2 天安排，现已核对；未记录实际小时。
后段 B/C 暂估约半天到一个自然日：理解属性、状态与异常边界，独立写一个函数，
亲跑四种情境，再写两道观察并订正。整体约一天是开工初估，不是当日硬时限。
以上为交付后段时的估计，实际学时未测；当前单元已验收，不要求学员重跑已完成部分。

本单元只选 OpenTelemetry，一次运行在本机保存标准 span；不引入云账号、后台搭建、
Collector、自动 HTTP 采集、真实模型调用或跨进程传播。
原先同排 Day53 的 502/504 映射移到阶段整合，沿用已学 HTTPException，
不在今天另起一条新主线。该调整保留历史安排，不表示映射已完成。

## 本单元查阅顺序

1. 先运行 [B1 属性演示](day53_span_attributes_demo.py)，从 demonstrate 读起：
   看创建时的 attributes 和之后的 set_attribute 各做什么，返回值是什么。
2. 再运行 [B2 状态演示](day53_span_status_demo.py)：分清默认 UNSET、显式 OK/ERROR、
   with 结束记录与 Python 异常传出，观察实际保存的字段。B 不另写观察题。
3. [C 完成代码](../../exercises/day53_span_exercises.py) 实现 trace_stage。
   参数、四种动作与异常规则保留在下方完整接口，不需要读验收器猜契约。
4. 亲跑练习后，在同一 [记录](day53_记录.md) 的 C 写两道观察；客观数据确认后由 AI 转录。

已完成的 A/B 和函数不重做。Day51B/Day52 仍在 11 月 9～10 日窗口，不提前打勾。

## 命令（仓库根目录）

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day53\day53_span_attributes_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day53\day53_span_status_demo.py

# C 完成版：四组均应通过；学员已完成亲跑，不要求重复运行。
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day53_span_exercises.py
```

也可从其他目录通过脚本绝对路径运行，输出仍落在本单元 outputs/。
本机沿用已有 opentelemetry-api 1.45.2，新装匹配的 opentelemetry-sdk 1.45.2；
requirements.txt 固定这两个直接依赖，安装由 AI 处理。

## 谁负责什么

你现在以应用开发者的身份，在一段工作外面加标准记录；业务依旧由普通 Python 代码执行。

| 名字 | 它是什么、由谁准备 |
|---|---|
| OpenTelemetry（OTel） | 本课选择的标准追踪工具，依赖和本地配置由 AI 准备 |
| tracer | 创建 span 的工具对象，由 local_tracing 通过 with 的 as 交给演示 |
| span | 某段工作的记录对象，进入 start_as_current_span 的 with 后取得 |
| trace | 一组有关联的 span 组成的轨迹，使用共同的 trace_id 关联 |
| trace_id | SDK 为整条轨迹给出的编号，不等于旧业务 request_id |
| span_id / parent_span_id | 本段编号 / 直接上级编号；根段没有上级 |
| 本地运行环境 | 真实 SDK 的 provider、processor、内存 exporter 和 JSON 保存；AI 已实现 |

运行背景见 [day53_trace_runtime.py](day53_trace_runtime.py)，无需先通读或重写。
与旧 RAG、HTTP 服务的完整组合仍留阶段整合，当前不改已验收的旧函数。

## A 的 API 怎么用（需要时回看）

`tracer.start_as_current_span(name, record_exception=False, set_status_on_exception=False)`：
name 是必填字符串，仅为记录起名，不会执行同名函数。该调用提供给 with 使用，
进入时开始记录并设为当前段，as span 取得记录对象；嵌套新段默认以当前段为父段，
离开时结束本段并恢复先前当前段。end_on_exit 默认 True，本课保持默认。
两个异常开关原默认 True，本课关闭自动记录异常消息及自动标状态；B2 学习手工安全失败标记。
其他可选项 attributes、context 等本节不用，没有新增需要学员提供的回调参数。

`span.get_span_context()`：无参数，返回编号信息对象，读取 trace_id 和 span_id。
`span.is_recording()`：无参数，返回 bool；本例全量记录，段内 True，结束后 False。
它说明本段是否仍在记录，不说明 tracer 是否还能创建新段。

## B 的 API 与 C 的角色

- 创建时可选 `attributes={"request_id": "公开编号"}`，给新 span 附键值。
  `span.set_attribute(key, value)` 的两个参数必填，返回 None；它修改这个 span。
  字段名用字符串，本题只需字符串值；不把完整字典结果当一个属性值。
- `from opentelemetry.trace import Status, StatusCode`；完成版已经启用这些导入。
  `Status(status_code=StatusCode.UNSET, description=None)` 构造状态对象，
  `span.set_status(Status(StatusCode.OK))` 或 ERROR 修改该 span，返回 None。
  本题不传 description。正常默认 UNSET 不等于 ERROR，本题要求正常显式标 OK。
- 状态不是 HTTP 状态码，也不是旧 RAG 的业务 state；没有正文的正常返回仍按正常执行标 OK。
  set_status 不负责传出异常，裸 raise 不负责给 span 标状态，两件事分别完成。
- C 是工具作者任务，沿用 Day50 的外部动作角色：调用方把已写好的 action 作为参数传入，
  你在 span 内执行 `action()` 一次，拿到业务字典；tracer 则是工具对象，用它创建段。
  配置、外层请求段、动作实现和验收由 AI 提供，不要在自己的函数里重新定义它们。
- C 的业务结果只返回给调用方；追踪只收 request_id、stage，失败时再加 error_type。
  两个异常开关保持 False，不调用 record_exception，也不把异常消息放进属性或状态描述。

两份演示各自使用自己的最小案例和 SDK 环境；完整的 action 包装逻辑留给 C。
本次不接旧 RAG、HTTP 服务器、模型 token 或成本字段，不要求重写 SDK 配置。

## C 完整接口（完成版查阅）

`trace_stage(tracer, request_id, stage, action) -> dict[str, object]`，四项均必填：

- tracer 是调用方已配置的 Tracer 工具对象；request_id 是公开业务编号字符串；
  stage 是本段名称字符串。函数只创建一个名为 stage 的 span，不调用同名业务函数。
- action 是调用方已经实现并传入的无参数动作，你以工具作者身份调用 `action()` 一次，
  不重新赋值、定义、跳过或重试它。它返回 `{"answer": str, "citations": list[str]}`，
  例如 `{"answer": "二楼", "citations": ["rule-2"]}`，也可正常返回空正文和空引用。
  包装器不检查或重构这个结果，返回收到的同一个字典对象。
- action 可能抛 TimeoutError、ValueError 等普通 Exception；包装器作失败标记后裸 raise，
  原异常对象继续传出。异常消息仍属于原异常，不能写入 span。
- 正常属性为 request_id、stage，状态显式 OK；异常状态 ERROR，另记 error_type 类型名字符串。
  不写状态描述、正文、引用、完整返回、异常消息或堆栈，不创建异常事件。
  创建时 record_exception=False、set_status_on_exception=False，with 负责结束并恢复当前段。
- 调用方已有当前父 span 时，新增段使用该父段并共享 trace_id；没有父段时成为根段。
  request_id 只是属性，不能替代 SDK 的轨迹与父子关联。

四组离线动作由 AI 提供，不请求模型、HTTP 或真实密钥：ok_child 正常非空返回，
empty_child 正常空返回，timeout_child 抛 TimeoutError；前三组各有外层 request_work。
invalid_root 抛 ValueError，没有外层段。两组异常消息里的人工敏感标记只用于检查是否误记。
原结果、原异常对象、动作次数、当前段恢复与实际 SDK 字段均由运行入口对照检查。

## 每格数据从哪里来

每轮新建 outputs/trace_span_demo_时间_后缀/，失败也保留：

- run_info.json：入口、配置、来源、源码摘要与完成/失败状态。
- console.log：讲解、实际调用打印、段内/段后状态与关联字段。
- otel_spans.json：由实际 SDK ReadableSpan.to_json 得到的全字段记录列表。
- trace_summary.json：本节需要的数量与编号关系，保留 SDK 的结束顺序。

摘要是 AI 从 SDK 实际对象摘出的字段：其中 parent_span_id 对应原始 JSON 的 parent_id；
trace_id/span_id 在原始 JSON 的 context 中。两份文件层次不同，表达的是同一批编号关系。

这些都是本地追踪的真实 SDK 记录；业务文字是人工教具，model_calls=0。
默认来源 unconfirmed，AI 验证为 ai_validation；学员确认运行后再转录客观数据，
判断、原因和观察仍由学员填写。

B 每轮同样保存上述四个文件，目录前缀分别是 span_attributes_demo、span_status_demo；
C 的前缀是 span_exercise，额外保存 exercise_checks.json，包含每组调用次数、实际状态、
异常类型、原对象保持、父段与安全字段检查；各案例子目录保存实际 SDK span。
记录中 B 的 span 数来自摘要；C 的通过组数、四组次数和两组原异常检查均来自检查 JSON。

## 官方资料去哪看、看哪些

- [OpenTelemetry Python Instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)：
  A 只看 Creating spans、Creating nested spans，核对 with 和父子关系；
  Acquire Tracer 仅用来辨认配置对象，不要求重写。
  B 看 Add attributes to a span、Set span status；Record exceptions in spans 只用于认识
  record_exception 会保存异常，本课为限制消息记录不调用它，不照搬该节记录完整异常的代码。
- [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)：
  只看 Tracer、Spans、Span Context，核对工具、记录段和编号分别是什么。
- [Python Tracer API](https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html#opentelemetry.trace.Tracer.start_as_current_span)：
  按需查 name、record_exception、set_status_on_exception、end_on_exit 的默认值；
  当前不读传播、链接和采样扩展。

Day50 延迟复验已于 11 月 7 日经反馈订正核对；本次不重做。
Day51A 短复验已于 11 月 8 日经反馈订正核对通过；A 运行与观察已核对。
B/C 学员亲跑与两道观察均已核对，Day53 本次验收完成。Day53 关键机制在 11 月 10～11 日
或满足间隔的学习日做短复验，阶段整合再验，均未发生。
