# Day53｜标准追踪的前置与练习记录

2026-11-08 开工。整体暂估约一个自然日，每天仍按 3～5 小时；本次先交约
1/3～1/2 天的前置 A，包含到期复验、认识 trace/span、亲跑和简短观察。
这是排期估计，实际学习小时未测；后段练习在前置核对后接续，不要求本次做完整单元。

## Day51A 到期短复验（先闭卷 10～15 分钟）

先不翻旧源码，也不运行本题。按题面给出的接口，用自己的话写判断即可。
这是旧机制的新输入，不需要编写新框架。

1. 某个 `POST /inspect` 已登记，参数使用 Day51A 的严格请求模型：
   question 必填，必须是至少一个字符的字符串；top_k 默认 2，必须是 1～4 的整数；
   不允许额外字段。处理函数进入后先 strip question，若只剩空字符串便抛 HTTP 400，
   否则正常返回 200。分别填写实际 HTTP 状态码、是否进入这个处理函数。
   本题没有自定义框架异常处理器。

   | 请求 JSON | HTTP 状态码 | 是否进入处理函数 |
   |---|----------|----------|
   | `{}` | 422      | 否        |
   | `{"question": 12}` | 422      | 否        |
   | `{"question": "   "}` | 400      | 是        |
   | `{"question": " 查询借阅规则 "}` | 200      | 是        |

   任选一条框架拒绝和一条业务拒绝，说明拒绝发生在哪一层：

   作答：{"question": 12}：属于框架拒绝，发生在校验层，{"question": "   "}：属于业务拒绝，发生在调用层

2. 已创建 `app = FastAPI()`，也定义了无参数函数 read_notice，函数每执行一次就把
   一个已有计数器加一，并返回 `{"place": "二楼"}`。计数初始为 0，应用没有其他路由。
   TestClient 已准备好，不涉及启动端口。
   第一次 `GET /notice` 时尚未登记该函数；然后执行
   `app.add_api_route("/notice", read_notice, methods=["GET"])`，再请求一次相同路径。
   写出两次状态码、各次请求后计数器的值；解释定义函数与登记路由各做了什么。

   作答：第一次：状态码404，计数器0 第二次：状态码200，计数器1
   定义函数是完成一个功能，登记路由是将路径方法与这个函数匹配

## A：trace/span 独立演示

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | span 数 | trace 数 | 根 span 数 | 来源确认 |
|---|---|---|---|---|---|
| trace/span 演示 | `outputs/trace_span_demo_20261108_164601_788142_07f506b2/` | 5 | 3 | 3 | 学员于 11 月 8 日确认亲跑；日志 completed |

数据来源：本轮 run_info.json、console.log、trace_summary.json 和 otel_spans.json。
前者保存配置、来源、源码摘要与完成状态；摘要文件保存数量及各段的 name、trace_id、
span_id、parent_span_id、ended、elapsed_ms；otel_spans.json 是实际 SDK 全字段记录。
具体编号、顺序和耗时保留在这些文件，不要求手抄五份编号或匹配固定毫秒数。
摘要里的 parent_span_id 对应 SDK 原始 JSON 的 parent_id，trace_id/span_id 来自 context。
AI 交付前试跑标 ai_validation，不计作学员亲跑，不预填本表。

### 观察与判断（学员填写）

1. 根据本轮 read_rule、render_card 与 notice_job 的字段，说明两个阶段各以谁为
   直接上级，以及哪一个字段证明它们属于同一条轨迹。

   作答：read_rule和render_card 以notice_job为直接上级，notice_job的直接上级为None；trace_id证明它们属于同一条轨迹

2. standalone_first、standalone_second 先后使用同一个 tracer，是否属于同一条轨迹？
   结合实际 trace_id 与 parent_span_id 说明。再根据段内/段后的打印，说明离开一个
   span 的 with 后，那个 span 和 tracer 分别处于什么情况。

   作答：不属于同一条轨迹，
   standalone_first： trace_id=0fd69b1950241100ab596f84c3c452df parent_span_id=None
   standalone_second: trace_id=d446441a31838d777be6cde62c5cdf8b parent_span_id=None
   离开一个 span 的 with 后，span 会结束 tracer会继续存在

## B：属性与状态小演示

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | span 数 | 来源确认 |
|---|---|---|---|
| 属性演示 | `outputs/span_attributes_demo_20261108_175104_652067_b3ad0648/` | 1 | 学员于 11 月 8 日确认亲跑；日志 completed |
| 状态演示 | `outputs/span_status_demo_20261108_175821_349296_dfcd98ab/` | 3 | 学员于 11 月 8 日确认亲跑；日志 completed |

来源为各轮 run_info.json、console.log、otel_spans.json 和 trace_summary.json。
本节只需运行并看懂，不另写一套观察；应用判断集中在下面 C。

## C：阶段追踪短练习

完成代码在 `../../exercises/day53_span_exercises.py` 的 trace_stage 中；完整接口保留在学习路线。
亲跑同一文件时，四组打印实际与期望，结果另存 exercise_checks.json。

### 客观运行数据（确认亲跑后由 AI 转录）

| 本轮目录 | 通过组数 | 四组 action 调用次数 | 两组异常是否原样传出 | 来源确认 |
|---|---|---|---|---|
| `outputs/span_exercise_20261108_190534_754976_09ffe360/` | 4/4 | 按 ok_child、empty_child、timeout_child、invalid_root 顺序均为 1 次 | TimeoutError、ValueError 均原异常对象传出 | 学员于 11 月 8 日确认函数亲跑；日志 completed |

每组实际 span 在本轮目录对应的小目录中，编号看 trace_summary.json，
属性、状态及异常事件看 otel_spans.json；不要求抄写四份完整 JSON。

本表转录 19:05 学员亲跑轮；它与清题干前的完成版只差后续排版，已通过还原排版后的
源码摘要核对。验收后仅清理说明文字，执行逻辑保持；19:08 与收尾的 AI 验证另存，
均为 4/4，不替换本轮编号或原始运行元数据。

### 观察与判断（学员填写）

1. `empty_child` 和 `timeout_child` 都没有得到可用正文，它们的阶段状态是否相同？
   根据实际 status、error_type 和 action 调用次数解释；说明异常消息是否进入 span。

   作答：不相同，empty_child: status=OK error_type=None action=1
   timeout_child:status=ERROR error_type=TimeoutError action=1
   empty_child的空正文属于正常返回，因此状态为OK
   timeout_child没有得到可用正文是因为运行时出现了异常，因此状态为ERROR
   异常消息没有进入span，并向span记录了异常类型名然后向调用方继续抛出原异常对象

2. `ok_child` 与 `invalid_root` 的阶段 span 分别有没有直接上级？从对应的记录中指出
   parent_span_id 如何判断。为什么保存 request_id 属性不能代替 trace_id 的轨迹关联？

   作答：ok_child:name=format_notice parent_span_id=4a24b59c26defce3 name=request_work parent_span_id=None 一个阶段span有直接上级，一个没有
   invalid_root：name=validate parent_span_id=None 没有直接上级
   parent_span_id看这个span是不是在另一个span下创建的
   request_id与trace_id并不相同，request_id相同trace_id并不一定相同，反之亦然
