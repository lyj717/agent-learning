# Day50 接口与验收边界

这是短接口说明；保存格式与请求关联先看原两份演示，不熟悉 action 时补看
[函数传参小演示](day50_action_demo.py)。旧业务说明在 `../shared/rag_functions.py`。
路径沿用 Day40/41 的“候选→消息→一次生成→校验”，今天把检索与生成换成离线回调，
保留已学过的消息和响应形状。不是新的一轮模型评测。

## A：trace_call

### 先看这题整体在做什么

A 是首次尝试“给调用方提供一个执行工具”的场景。可以先回看 action 演示开头的
Day45 sorted/key 对照：之前你是工具的使用者，提供排序函数；本题换到工具作者这一侧，
负责调用别人提供的函数。先从这个角色变化理解题目，再看下面的日志要求。

直接调用一个函数，能拿到它的结果；本题让你做一个带记录的执行入口：
由 trace_call 调用这个函数一次，并额外留下“开始了、做了多久、成功还是失败”的事件。
动作返回的结果仍交给调用方，日志另外通过 emit 保存。

以已经讲过的人工通知为例，调用方会这样使用你写的函数：

```python
result = trace_call("r-001", "read_notice", read_notice, emit)
```

| 调用方提供的参数 | 本例含义 | 你在本函数里的职责 |
|---|---|---|
| request_id = "r-001" | 这次请求的标签 | 放进每条事件 |
| stage = "read_notice" | 当前动作的名字 | 放进每条事件 |
| action = read_notice | 已经定义好的通知函数 | 用 action() 执行一次 |
| emit | 已经准备好的日志保存函数 | 用 emit(事件字典) 送出日志 |

对照下面两种行为来理解完成标准：

| 传入动作的行为 | 日志应收到什么 | 调用方最后收到什么 |
|---|---|---|
| 返回字符串“借阅室今天 18 点关闭。” | start 事件，随后 ok 事件；ok 中带实测毫秒数 | 同一个字符串 |
| 抛出 TimeoutError | start 事件，随后 error 事件；error 中带实测毫秒数和异常类名 | 原来那个 TimeoutError 继续向外抛 |

正常路径的时间顺序：记开始 → 执行动作并计时 → 记成功和耗时 → 返回动作结果。
先把这条正常路径接通，再补失败路径；最终继续使用 A 的五组对照验收。
日志通过 emit 送出，return 返回的是动作结果。这是两份不同用途的输出。
动作具体业务由传入函数负责，trace_call 专心管执行过程和记录。

### 参数、事件字段与边界

四个参数均必填：request_id/stage 为调用方控制的非空标签；action 是无参数函数；
emit(event) 接收事件字典、返回 None。action 可以返回任意对象，也可能抛普通 Exception。
emit 在本课视为可靠回调；持久化失败、并发写入及中断善后在后续单元处理。

`action` 是普通参数名，不是库里的固定函数，也不需要额外 import。
调用方把某个函数传给它，`trace_call` 内用 `action()` 执行这次动作。
`Callable[[], Any]` 中的 `[]` 表示调用时不传参数，`Any` 表示返回类型不限。
A 的对照工具已经定义并传入各组动作，学员负责调用和包装，不用另写一个固定 action。
`stage` 只标记阶段名称，不会自动根据标签选择检索或生成函数。
`emit` 则是另一种回调：`emit(事件字典)` 负责送出日志，和无参数的 `action()` 分工不同。

这里“发 start/ok/error”指调用 `emit(事件字典)`，让字典的 `state` 取相应字符串，
不是调用 `emit("start")`。A 接到的 emit 只有一个字典参数，保存目录已由调用方准备好。
对照工具内部的 `_emit(run_dir, events, event)` 是底层保存函数；
传给 A 的包装函数是 `emit(event)`，它在内部补上已有的 run_dir 与 events，A 不再传路径。

每次 action 执行前发开始事件，正常返回后发成功事件，抛普通 Exception 时发错误事件。
错误事件保存后，在 except 内单独写 `raise`，将刚捕获的同一个异常继续交给外层；
不把错误当成正常结果返回，也不重新构造异常。字典字段严格如下：

| state | 必有字段 | 字段类型 |
|---|---|---|
| start | request_id、stage、state | 全部 str |
| ok | 上面三项、elapsed_ms | elapsed_ms 为非负 float，单位毫秒 |
| error | 上面四项、error_type | error_type 是异常类名 str，例如 TimeoutError |

最小示例结构：`{"request_id": "某次请求的ID", "stage": "retrieve", "state": "start"}`。
成功必须原样返回 action 的对象；失败记事件后原样抛出同一个异常，不改成成功返回值。
不要使用 str(error)、repr(error)、完整 traceback 或把 action 的输入/输出并入事件。
start 之后计时，在 action 完成/抛错时取差值；本课阶段时长不包含 emit 的写入耗时。
trace_call 不负责生成 ID，也不负责打开文件；emit 是参数，不是待实现的新函数。

## B：answer_with_trace

Day50 已验收，练习题干已清理为简短 docstring；完成的调用流程见
[answer_with_trace](../../exercises/day50_trace_exercises.py)，接口与阶段边界保留在本文件。
需要先把有参数的函数变成无参数动作时，参见 [action 演示](day50_action_demo.py) 最后一节。
retrieve_fn、request_fn、emit 均由调用方提供，整合函数负责调用，不重写它们的实现。
emit 接收一个事件字典、返回 None，沿用 A 的约定。

四个参数均必填。question 已保证为非空字符串，不增加新的业务参数校验题。
retrieve_fn(question) 返回 list[Document]，片段已由旧加载/出处流程核对，
每项有 id、正文和 source/line_start/line_end；本题不重新建库或重写原文回查。
request_fn(messages) 返回已有响应结构，例如：

```python
{
    "raw_text": '{"status":"insufficient","answer":"资料不足","cited_ids":[]}',
    "finish_reason": "stop",
    "usage": None,
}
```

本题不读取 usage；未知用量不记为零，token 与费用在后续接真实请求时沿用旧规则。

### 四个阶段什么时候开始、什么时候结束

`retrieve / prepare / generate / validate` 是 **stage：当前做哪件事**。
`start / ok / error` 是 **state：这件事开始、正常返回或报错**。

B 按业务顺序调用 A。每调用一次 A，A 先记录该阶段的 start，再执行这次传入的动作；
动作正常返回，A 记录 ok 并把结果交回 B；动作抛普通异常，A 记录 error 并继续抛出。
B 只有在 A 正常返回后才继续执行后面的代码；异常传出时，后续阶段不会开始。
阶段推进依据函数返回或抛异常，B 不用读取日志里的 state 来决定下一步。
`stage` 字符串用来标记日志，实际做什么由本次传入的无参数动作决定。

| 阶段 | 进入条件与输入 | 动作范围；正常结束时得到什么 | 正常结束后的去向 |
|---|---|---|---|
| retrieve | 问答开始，已有 question | 调用 retrieve_fn(question)；返回 evidence 候选列表就结束并记 ok，[] 也算正常返回 | 在 A 返回后判断 evidence：空则返回本次 ID、checked=None，问答结束；非空才进入 prepare |
| prepare | evidence 非空，已有 question 和 evidence | 调用旧 build_grounded_messages(question, evidence)；messages 返回就结束并记 ok | 进入 generate |
| generate | prepare 已返回 messages | 只调用一次 request_fn(messages)；原响应字典返回就结束并记 ok，此处不判断内容是否合格 | 进入 validate |
| validate | generate 已返回原响应，另有本次 evidence | 先检查 finish_reason；非 stop 就抛 ValueError；为 stop 才调用旧 check_grounded_reply(raw_text, evidence)，返回 checked 就结束并记 ok | 返回本次 ID、checked，问答结束 |

任一阶段的动作抛普通异常，都在**当前阶段**记 error、继续向外抛，后续阶段不执行。
四个阶段都用同一个请求 ID，各自把对应的动作交给 A；已经写好的检索动作只负责检索。

关键对照：

- 检索返回 []：retrieve ok，问答正常结束；没有 prepare、generate 或 validate 事件。
- 候选列表非空但某项缺 source：retrieve 已正常返回，所以仍是 retrieve ok；
  prepare 读取 source 时抛 KeyError，因此是 prepare error，后续不开始。
- 请求调用抛 TimeoutError：generate error；没有响应可校验，不进入 validate。
- 请求返回 finish_reason="length"：generate ok，因为请求函数正常返回了字典；
  进入 validate 后，结束原因检查抛 ValueError，因此是 validate error。
- 请求返回 stop，但 raw_text 是坏 JSON 或引用越界：仍是 generate ok，随后 validate error。

下面的每一项表示一条独立追加的日志，箭头表示时间顺序：

```text
全部成功：
retrieve start → retrieve ok → prepare start → prepare ok
→ generate start → generate ok → validate start → validate ok → 返回结果

空候选：
retrieve start → retrieve ok → 返回 checked=None

请求返回了字典，但 finish_reason="length"：
retrieve start → retrieve ok → prepare start → prepare ok
→ generate start → generate ok → validate start → validate error → 异常向外抛
```

进入下一阶段会产生新日志，前面的日志保持原样。generate ok 只表示请求函数正常返回，
不表示响应已经通过校验；validate ok 也只表示通过本题的结束原因、结构与引用编号检查，
不证明回答在语义上正确。

用同一个随机 request_id 调用 A 包住各阶段；本题不强制新增 request 根阶段。
finish_reason 的检查属于 validate 的动作和计时范围；这样检查抛出的 ValueError 才由 A
记为 validate error。validate 的 ValueError 不带响应正文。
需要传参时，可以用零参数 lambda 或内部函数交给 A；没有规定具体写法。

返回恰有两个字段：

```python
{"request_id": "32位UUID十六进制字符串", "checked": None}
```

`checked` 非空时就是旧校验函数返回的 `{status: str, answer: str, cited_ids: list[str]}`。
空候选时只执行 retrieve，checked 为 None，不发生成请求；空候选本身不是异常。
所有输入均不得修改。两次问答即使问题相同，也要有不同 ID；失败 ID 从事件里找。

## 运行证据与判断

命令每次新建 outputs/ 下的目录。console.log 保存完整对照，run_info.json 保存配置、
来源和最终状态；events.jsonl 保存实际事件；checks.json 保存各组通过/失败。
未实现时明确抛 NotImplementedError，日志 state=failed；不把它当环境故障。
AI 验证使用 DAY50_RUN_ORIGIN=ai_validation，默认 unconfirmed，不据文件存在判断亲跑。
记录表 A/B 每一格都来自对应目录与上述文件；观察 1/2 来自 B/A 的事件，观察 3 比较计时边界。

本课为单进程的阶段事件，阶段名在一次请求中不重复。标准 trace 的 span_id、父子关系、
跨服务传播及会话隔离不在本课实现，也不据今天的日志宣称它们已经通过验收。
