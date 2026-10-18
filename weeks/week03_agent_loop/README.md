# Week 03｜Agent 核心循环（手写）

**规则**：这一周不许用框架。自己写主循环、自己解析模型输出、自己决定终止条件。

**交付物**：不用任何框架的 ReAct Agent。

## 当前目录与运行入口（2026-10-18）

本周练习集中在 `exercises/`，演示、辅助脚本和资料按单元放在 `demos/dayNN/`；
Day 26 两部分沿用 `demos/day26a/`、`demos/day26b/`。下面的文件路径均相对本周目录，
命令仍从仓库根目录运行。直接在脚本所在目录启动也可找到依赖、资料与 worker；
真实入口从脚本位置定位仓库根目录的 `.env`。

目录整理后的离线检查：21 个入口分别从仓库根目录和脚本目录启动，42 次均正常退出；
Day 27 的 12 组情境、Day 28 的 6 组变式、两份检索资料及两个 worker 均已核对。
Day 23、24、28 的真实入口也已分别运行一次：共 7 次模型请求，三个进程均正常退出；
Day 24 查到 18 元后算得 126 元，Day 28 查到 7 元后算得 42 元并通过入口自检。
这些是 AI 对迁移后教具的验证，没有填入学员实验记录。

## 开工状态（2026-10-11）

Week 02 的 Day 15～21 已验收，接续 `../week02_tools/HANDOFF.md`。
视频在面试复习时补录，JD 与简历在项目结束后统一处理，不作为开工门槛。
`docs/21天详细日程表.md` 只逐日排到 Day 21；下面是依据周计划拟定的节奏，
按实际完成情况调整，一天没验收就先接着做。

**本阶段练习节奏**：先由演示逐步拆解新机制，再用能单独运行的小题练习；
Day 27～28 由学员把这些部分整合成完整 Agent 并验收。Day 22 的 `fake_chat`
拆解后再写 `run_agent`，就是这一节奏的起点。

**后续实现路线**：Day 24 起沿用 Week 02 的原生 `tool_calls`，手写循环与工具执行。
Day 23 的正文 JSON 是解析、类型校验的对照练习，不是完整 Agent 必须采用的协议。
其中检查工具名、参数类型的思想继续使用；`finish_reason` 要按原生接口分别处理
`tool_calls` 与 `stop`，不能直接照搬 Day 23 的“只接受 stop”。

| 天 | 本日重点 | 状态 |
|---|---|---|
| Day 22 | 离线最小循环、状态、轨迹、最终答案与步数上限 | 已完成：四组情境输出符合预期，错误回填与调用 ID 已核对 |
| Day 23 | 输出协议与解析校验，接入真实模型 | 已完成：解析与校验练习、真实输出观察均验收 |
| Day 24 | 本地文件检索与计算器，多步依赖 | 已完成：多文件检索上限、工具回填和真实先查后算观察均验收 |
| Day 25 | 受限代码执行工具与权限边界 | 已完成：语法白名单、应用授权和两份观察均验收 |
| Day 26A | token / 成本统计与预算停止判断 | 已完成：三题、五组预算情境和观察均验收；跨天复验待进行 |
| Day 26B | 单次调用超时、任务时限与重复调用检测 | 前后两部分练习及观察均已验收；跨天复验待进行 |
| Day 27 | 整合项目、验证日志与失败路径 | 已完成：新资料检索、三工具循环、12 组离线情境和观察均验收 |
| Day 28 | 验收、白板复盘、交接 | 已完成：闭卷预测、六组离线变式、一次真实模型链条与记录均验收 |

## Day 22：先看清循环在保存什么

先用自己的话口头复述 Week 02：请求里有什么、谁执行工具、原 assistant
与 tool 结果怎么配对、什么时候继续请求。再打开本日演示。

ReAct 把推理与行动交替起来，让后续行动能根据外部结果调整。
读 [ReAct 原论文摘要](https://arxiv.org/abs/2210.03629) 的 Abstract 即可，
今天关注“行动取得新信息，再用于下一步判断”，暂时不用读实验指标。
仓库面试题对应 Q1、Q3、Q4，写完练习后再对照。

| 文件 | 用途 |
|---|---|
| `demos/day22/day22_agent_loop_demo.py` | 逐节讲解；内含假模型、乘法工具、结果打印，演示正常结束与步数耗尽 |
| `exercises/day22_agent_loop_exercises.py` | 学员完成的循环，返回状态和轨迹；末尾保留运行观察 |

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day22\day22_agent_loop_demo.py
# 已完成的练习：打印四组情境和非法上限的运行结果。
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day22_agent_loop_exercises.py
```

今天完全离线：假模型按固定规则输出，教学摘要为人工编写，不代表真实模型能力。
消息沿用 Week 02 的形状，一步定义为一次模型请求，最终答复也占一步。
现有代码已会回填错误和限制轮数；今天新增的是返回 `stop_reason`、保留完整历史、
记录 `trace`，便于区分“拿到最终答复”和“用完请求次数”。
轨迹记录可观察的请求、行动和结果；接真实模型后不把未提供的内部推理补写成日志。

- [x] 运行演示，能解释工具结果为什么还不等于最终答复。
- [x] 自己完成 `run_agent`，对照四组输出与非法上限检查。
- [x] 在练习末尾填写观察题；数据来自练习的主程序输出。
- [x] AI 实跑批改后清脚手架、检查、更新进度并本地提交。

## Day 23：把模型正文变成可信的下一步

今天在 `message.content` 中约定两种 JSON 对象：`action` 请求一个工具，
`final` 给出最终答复。这是手写 Agent 的练习协议；Week 02 API 原生的
`tool_calls` 是另一个字段，不能把两者混为一谈。JSON 模式只约束语法，
程序还要先检查 `finish_reason`，再检查键、值的类型和工具白名单。

先读 [DeepSeek JSON Output 指南](https://api-docs.deepseek.com/zh-cn/guides/json_mode/)
里的「注意事项」和「样例代码」：重点看为什么提示词里要写 `json`、为什么要给
`max_tokens` 留够额度，以及空正文该怎样看待。它对应本日演示的 `--live`
请求和第一份练习。再看
[Chat Completions API 的 finish_reason 字段](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion)，
只需弄清 `stop` 与 `length` 的差别。

| 文件 | 用途 |
|---|---|
| `demos/day23/day23_protocol_demo.py` | 按「是什么／为什么／场景／代码／注意」讲两种决定、语法与协议的边界；`--live` 真请求一次模型 |
| `exercises/day23_json_parse_exercises.py` | 小练习 A：检查结束原因、空正文、JSON 语法和最外层类型 |
| `exercises/day23_decision_exercises.py` | 小练习 B：分别校验 `final` 和 `action` 的字段、类型、工具白名单 |

在仓库根目录依次运行：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day23\day23_protocol_demo.py
# 小练习 A：对照正文解析的六组输入
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day23_json_parse_exercises.py
# 小练习 B：对照最终答复和工具行动
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day23_decision_exercises.py
# 最后观察一次真实模型输出；需要根目录 .env 和网络
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day23\day23_protocol_demo.py --live
```

两份练习及末尾观察已由学员完成；小练习 A 的 `json` 导入已启用。
今天练的是解析与校验；Day 27～28 整合原生工具调用时按其消息形状使用这些检查思想。

- [x] 完成小练习 A，能解释 `length` 和合法 JSON 列表为什么被拒绝。
- [x] 完成小练习 B，能区分最终答复和工具行动，并拒绝未知工具。
- [x] 自己运行 `--live`，记录真实输出与规则的对照。
- [x] AI 实跑批改、清脚手架、检查并在验收后本地提交。

## Day 24：让计算参数来自查到的资料

**今天新增的能力**：从本地文件取得问题中没有给出的信息，保留出处，
让后一次工具调用使用前一次检索的观察。问题是“青禾笔记本买 7 本多少钱，
单价来自哪里？”资料里的商品与价格全部为教学虚构数据。

与前面几天的关系：Week 02 已会点工具和回填；Day 22 已会循环；
Day 23 练了输入校验。今天增加文件检索和列表结果的 JSON 回填，
继续使用 `message.tool_calls`，不重新写正文里的 `action/final`。
JSON 在这里承载工具参数和工具观察；模型最后仍可用自然语言作答。

| 文件 | 用途 |
|---|---|
| `demos/day24/day24_retrieval_demo.py` | 单文件检索、出处、列表回填、先查后算；`--live` 观察真实模型的原生工具调用 |
| `demos/day24/day24_notes/products.txt`、`demos/day24/day24_notes/stock.txt` | 两份虚构商品资料；工具只在这个固定目录内查找 |
| `exercises/day24_search_exercises.py` | 练习 A：复用演示的单文件匹配，自己写多文件搜索与结果总数上限 |
| `exercises/day24_observation_exercises.py` | 练习 B：调用自己的检索或已有计算器，返回带原 ID 的 tool 消息 |

### 按这个顺序做

1. 在 PyCharm 打开演示，直接右键运行，先看第 1～3 节，再读 `find_in_text`。
   今天只做逐行子串匹配；向量检索、同义词匹配留到后续 RAG 周。
2. 完成练习 A，调用演示中的 `find_in_text`，再右键运行并填末尾两题。
   不用重写逐行匹配；把它用于多个文件，并限制所有文件合计的结果数量。
3. 回看演示第 2～3 节，并读 `demo_tool_message`，完成练习 B 后右键运行。两把工具已在主程序的
   `tool_table` 接好；B 使用你在 A 写的检索，所以先完成 A。
4. 在演示的运行配置 Parameters 里填 `--live` 并运行，依据真实输出填写 B 的观察。
   重点对照检索参数、tool 观察、下一轮算式和最终引用；不要只看答案数字。

命令行等价入口（在仓库根目录）：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day24\day24_retrieval_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day24_search_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day24_observation_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day24\day24_retrieval_demo.py --live
```

两份练习和末尾观察已完成；函数题干已清理为一行说明。
演示的检索只查 `demos/day24/day24_notes/products.txt`；练习 A 扩展到两份文件。演示的循环是 AI 教具，
Day 27 整合时，再由学员把自己的多文件检索、工具回填与循环接起来。
`--live` 最多请求四次，自动读取根目录 `.env`。它会打印每轮结束原因、
工具名与参数、调用 ID、完整工具观察、最终答复，足够核对本日观察题。

查资料时只读以下几处，不用通读：

- [Python 3.13 pathlib](https://docs.python.org/zh-cn/3.13/library/pathlib.html)：
  `Path.glob`、`Path.read_text` 和 `PurePath.name`，对应遍历文件、读中文、保存文件名。
- [DeepSeek Tool Calls](https://api-docs.deepseek.com/zh-cn/guides/tool_calls/)：
  「非思考模式」的样例及流程，复习 `tool_calls → 本地执行 → tool 回填 → 再请求`。
  先后依赖体现在下一次请求能看见上一次工具观察。

- [x] 完成练习 A，能对照出处并区分无命中与报错。
- [x] 完成练习 B，检索列表与计算数字都能回填，原调用 ID 保持一致。
- [x] 运行真实演示并填观察，指出算式中的数字分别来自哪里。
- [x] AI 批改、清脚手架、检查并在验收后本地提交。

## Day 25：谁有权让 Agent 执行代码

Day 24 已有检索和计算器；今天增加第三种工具：接收多行数值代码，
允许单变量赋值与最后一行四则运算。例子是先写 `unit_price = 18`、
`quantity = 7`，再算 `unit_price * quantity`。演示中的代码由教具写好，
真实模型调用留到 Day 27 整合时接入。

**权限边界**：这台机器没有检测到 Docker、Podman 或 Wasmtime。
教具用可信子进程运行一个**语法白名单解释器**，只允许数字、变量、赋值、
负号和四则运算；`open`、`import`、属性访问、函数调用、循环都不执行。
应用另外用 `allow_code` 决定能否调用工具，这个值不能由模型自己在参数里设置。
每次子进程有新的变量字典，最多等待三秒。`python -I` 和子进程本身
不撤销当前账号的文件或网络权限，因此这**不是通用 Python 的操作系统沙箱**。
若以后要运行模型生成的任意 Python，必须另接真正隔离的运行环境；
不能直接把代码字符串交给 `exec`、`eval` 或普通子进程。

| 文件 | 用途 |
|---|---|
| `demos/day25/day25_code_demo.py` | 先看允许计算和语法树入门，再看拒绝文件调用、变量不跨调用保留及子进程入口 |
| `demos/day25/day25_code_worker.py` | AI 提供的受限解释器；`check_tree` 查白名单，`eval_number` 只计算获准节点 |
| `exercises/day25_syntax_exercises.py` | 小练习 A：从语法树找第一个不被允许的节点 |
| `exercises/day25_permission_exercises.py` | 小练习 B：由应用授权；未授权时不执行工具，仍按原 ID 回填 |

### 按这个顺序做

1. 在 PyCharm 打开 `demos/day25/day25_code_demo.py`，直接右键运行。先顺着第 1～5 节
   看输出，再读文件开头的 `main` 和后面的 `run_limited_code`。
2. 按需打开 `demos/day25/day25_code_worker.py`，只看 `check_tree` 与 `eval_number`：
   前者决定哪些语法能进入，后者计算它们；不用重写整份执行器。
3. 练习 A 已完成：右键运行，对照 `None`、`Call`、
   `Import`、`While`、`Constant` 和 `SyntaxError`，填文件末尾的观察。
4. 练习 B 已完成：右键运行。
   比较“应用未授权”与“已授权但代码被白名单拒绝”，填文件末尾的观察。

仓库根目录的等价命令：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day25\day25_code_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day25_syntax_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day25_permission_exercises.py
```

两份练习和末尾观察已由学员完成，函数题干已清理为一行说明。
今天只用离线输入验证权限边界，不需要模型请求。Day 27～28 再把获准的
代码工具接进学员写的完整 Agent 循环；若没有操作系统级隔离，就明确标作
“受限数值代码工具”，不能声称已经支持安全执行任意 Python。

官方文档只看与本课对应的部分：

- [Python 3.13 `ast`](https://docs.python.org/3.13/library/ast.html)：
  `ast.parse`、`ast.walk`，以及 `Call`、`Import`、`Assign` 等节点；
  对照练习 A 的语法树检查。
- [Python 3.13 `subprocess`](https://docs.python.org/3.13/library/subprocess.html)：
  `subprocess.run` 的 `input`、`capture_output`、`timeout`；
  对照演示的可信 worker 调用。
- [Python 3.13 命令行参数](https://docs.python.org/3.13/using/cmdline.html)：
  只看 `-I`；它限制 Python 的导入路径和环境配置，不能把它当成系统权限沙箱。

- [x] 完成练习 A，能解释为什么 `Call` 和字符串常量要被拒绝。
- [x] 完成练习 B，未授权时不调用 runner，且原 `tool_call_id` 不变。
- [x] 填写两份练习末尾的运行观察，分清应用拒绝与执行器拒绝。
- [x] AI 批改、清脚手架、检查并在验收后本地提交。

## Day 26A：给下一次模型请求加预算闸门

Day 22 的 `steps` 数了请求次数，但没有记录每次请求消耗多少 token。
今天只增加一条数据流：**模型响应的 `usage` → 逐轮和累计用量 →
下一次模型请求前的停止原因**。工具本地执行不算模型请求，最终答复那轮也要记账。
继续用 Day 22 的离线循环作背景，不在今天改写完整 Agent。Day 9 的单轮成本公式
已有练习；今天的新东西是把多轮账本接到停止判断。

| 文件 | 用途 |
|---|---|
| `demos/day26a/day26a_budget_demo.py` | 按「是什么／为什么／场景／代码／注意」展示响应、逐轮成本、累计、超支与缺失用量；全部是假数据 |
| `exercises/day26a_budget_exercises.py` | 学员先重写单次教学成本，再写累计与预算判断；主程序打印单次成本和五组情境 |

### 按这个顺序做

1. **先不看旧代码，花 10～15 分钟复述一次**：assistant 的工具点单、对应的
   `tool_call_id`、tool 回填和下一次模型请求是什么关系；然后打开
   `exercises/day22_agent_loop_exercises.py` 核对。把想起来和遗漏的部分写在今天练习文件末尾的热身栏，
   这项热身已于 2026-10-13 完成；26A 自身的跨天复验仍待进行。
2. 在 PyCharm 右键运行 `demos/day26a/day26a_budget_demo.py`，按第 1～4 节看输出。
   注意第一次、第二次模型请求各自的 `usage` 与累计账本；教学单价不是实际价格。
3. 打开 `exercises/day26a_budget_exercises.py`，先自己写 `teaching_cost_yuan`，
   再写 `summarize_usage` 和 `stop_before_next_request`。演示里有同名成本函数，
   但练习不需要导入或回看它。题干交代了入参、返回值和优先顺序；右键运行，
   先对照单次成本，再对照五组预算情境，最后填写文件末尾观察。
4. 观察“超支”一组：这道闸门只在**已发生的请求之后、下一次请求之前**检查。
   如果本次请求本身越过预算，已花掉的额度无法撤回；缺失 `usage` 时不能按零继续。

仓库根目录的等价命令：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day26a\day26a_budget_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day26a_budget_exercises.py
```

三题与末尾观察已由学员完成，函数题干已清理为一行说明。
本单元全部离线，演示中的两次 `usage` 是固定教学数据，不冒充真实模型用量。
成本函数使用元 / 百万 token 的假单价，不含缓存折扣；若以后接真实模型，
要按当时的响应和价格核对。今天只保证**调用前后检查**，不保证某一次请求
绝不会使总量越过预算；也不把估算值冒充实测值。

复习入口：Day 9 的 `../week01_llm_api/exercises/day09_exercises.py` 看单轮成本公式，
Day 17 的 `../week02_tools/demos/day17/day17_tool_calling_demo.py` 看两次真实响应各自的
`usage` 打印，Day 22 的 `exercises/day22_agent_loop_exercises.py` 看 `steps` 与停止原因。
只看对应函数或输出，不用从头重做。

- [x] 闭卷复述旧工具回合，并对照 Day 22 记录想起与遗漏之处；证据在练习末尾。
- [x] 完成单次成本、累计与预算判断，五组情境符合期望。
- [x] 填写练习末尾的观察，区分已知用量、未知用量和已发生的超支。
- [x] AI 批改、清脚手架、检查后在本单元验收时本地提交。

## Day 26B：单次超时、任务时限与重复调用

Day 26 不把预算、超时、重复检测塞进一道首次练习。26A 先完成预算闸门；
26B 再用独立的分步演示和小题处理时间与重复调用。

| 单元 | 学员要练的机制 | 需要能核对的证据 |
|---|---|---|
| 26A | 累计模型请求的用量与成本；根据预算决定是否继续 | 请求次数、每轮与累计用量、预算、停止原因；缺失 usage 不能当 0，估算与实测要区分 |
| 26B 前半 | 单次调用超时与整个任务的时限 | 已用时间、剩余时间、触发位置；循环间检查时限不能冒充能够强制中断阻塞调用 |
| 26B 后半 | 同工具同参数反复出现时停止或交还用户 | 连续调用轨迹、重复判据与停止原因；因果相关的正常多步调用不能误判成死循环 |

先用可控的离线输入触发边界，再做必要的真实请求观察。预算检查要说明：事后发现超预算不能追回已消耗额度；若只做到调用前后检查，就如实标明保障范围。

### 26B 前半：时间边界（已验收）

今天只学时间边界，暂不做重复调用检测。`demos/day26b/day26b_timeout_demo.py` 先用固定时间
演示已用、剩余和下一次调用的上限，再运行 `demos/day26b/day26b_timeout_worker.py` 这个固定慢工具，
分别看到正常返回和单次调用超时。慢工具只模拟检索，输出的是固定教学文本；没有模型请求。

1. 在 PyCharm 右键运行 `demos/day26b/day26b_timeout_demo.py`。先看前三组固定时间：
   只剩 0.5 秒时，下一次调用上限也只能是 0.5 秒；总时限到达后不再开始调用。
   再看慢工具：第一次完成，第二次报 `call_timeout`，并比较设定上限和实际经过时间。
2. 打开 `exercises/day26b_timeout_exercises.py`，按 A1、A2、B 的顺序自己写。
   每题 docstring 给出参数、返回值、期望结果和需要的导入；演示里有同名函数，
   练习文件也给了空位，不必从演示导入。B 开始时取消文件开头两行 import 的注释。
   每写完一题就右键运行，核对该题打印出的实际与期望；后面的题未写会明确报错。
3. 三题完成后，填写练习文件末尾的四条“现象与原因”。
   `task_timeout` 是开始下一次调用前发现总时间已到，`call_timeout` 是正在等待的
   这次调用超时；要能指出两者触发的位置。

仓库根目录的等价命令：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day26b\day26b_timeout_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day26b_timeout_exercises.py
```

`time.monotonic()` 的读数只能相减来测经过时间。`subprocess.run(timeout=...)`
超时后会结束本地子程序并抛出 `TimeoutExpired`；进程启动本身可能造成额外延迟，
不保证总运行时间精确等于设定上限。对应可看 Python 官方文档的
[单调时钟](https://docs.python.org/3.13/library/time.html#time.monotonic)和
[子进程超时](https://docs.python.org/3.13/library/subprocess.html#timeout-behavior)两小节。

- [x] 完成 A1、A2、B，并核对固定时间与慢工具的输出。
- [x] 填写练习末尾的现象与原因，分清两种超时的触发位置；学员记录慢工具实际经过约 0.062 秒。
- [x] AI 批改、清脚手架、检查并在验收后本地提交。

### 26B 后半：重复调用检测（已验收）

这次只练一条规则：**连续工具结果的工具名、解析后的参数、观察都相同，才算一次无进展重复**。
它复用 Day 22 的工具轨迹字段，先在离线数据上练，不改完整 Agent 循环。
`step` 和 `tool_call_id` 仍要保留以便追踪、配对消息，但不参与重复判据。
相同参数查同一任务却得到“处理中 → 已完成”，属于有新观察，不能误停。

| 文件 | 用途 |
|---|---|
| `demos/day26b/day26b_repeat_demo.py` | 依次展示重复检索、改参数、观察更新、中途换工具和三次阈值；全是固定示意轨迹 |
| `exercises/day26b_repeat_exercises.py` | 学员写相邻比较、末尾连续计数和停止判断；主程序逐题打印对照输出 |

按这个顺序做：

1. 在 PyCharm 右键运行 `demos/day26b/day26b_repeat_demo.py`。先看第一次和第二次检索各自的
   assistant 点单与 tool 观察，再看为何它们的 ID 与 JSON 键顺序不同，仍被判为重复。
   随后对照“查询改变”“观察更新”“中途计算”三组，找出哪一项使计数回到 1。
2. 打开 `exercises/day26b_repeat_exercises.py`，依次写 A、B、C。A 比较相邻两条，
   B 只数轨迹**末尾**的连续条数，C 再依据上限决定是否停止；
   每题 docstring 给出参数类型、返回值、期望输出和需要的导入。
   演示里有同名函数，练习文件也留了空位，不用从演示导入。
   写 A 时取消文件开头 `import json` 的注释；每完成一题就运行并核对该题输出。
3. 填写练习文件末尾的四条“现象与原因”。本检测在工具结果写入轨迹**之后**运行，
   因而第二次相同的只读调用已经执行；它阻止的是后续模型请求。

仓库根目录的等价命令：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day26b\day26b_repeat_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day26b_repeat_exercises.py
```

本课的规则只处理参数已校验、观察可比较的只读工具轨迹。
观察若每次都带不同时间戳，可能漏报，因此完整 Agent 仍需最大步数兜底；
会修改数据的工具也需要自己的防重复执行措施。若以后换成真实模型，
需先校验工具名与参数，再根据真实轨迹选择是否继续；
这份演示没有真实模型调用或真实检索结果。

- [x] 完成 A、B、C，15 组对照输出均符合期望。
- [x] 填写四条现象与原因，说明连续性、观察变化与停止位置。
- [x] AI 批改、清脚手架、检查并在验收后本地提交。

2026-10-14 批改补充：练习末尾第 2 条原答保留。中间插入计算器后，
末尾检索与第一次检索不再相邻，计数因此重置；这条规则不判断计算器结果
是否真的推动了任务。

2026-10-14 教具复盘：演示完整实现了练习 A、B、C 的同名函数，案例也高度重合。
学员指出，完成练习只得到“照着演示复现成功”的反馈，难以判断是否能独立应用。
本次的代码和观察验收保留；**独立迁移尚未验收**。Day 27 的整合应给新任务情境、
明确接口和可核对的失败路径，让学员自己决定在循环何处接入重复检测；Day 28
再换一组输入独立验收。不要再提供可逐行搬用的同名完整演示实现。

## Day 27：用新资料整合离线 Agent（已验收）

今天没有新机制，也不再给一份实现了完整主循环的演示。学员把已学过的
原生 `tool_calls` 循环、检索、计算器、受限数值代码工具、预算和停止条件接起来。
商品问题改成“蓝湾便签买 5 本多少钱，单价出处在哪里？”；`demos/day27/day27_notes/`
是新的两份虚构资料，不沿用 Day 24 的答案。`demos/day27/day27_fake_model.py` 只按消息历史
给可控的假点单，要求收到带原 ID 的 tool 回填后才继续；它没有联网，也不是
学员的 Agent 实现。学员完成的检索与主循环保存在 `exercises/day27_integrated_exercises.py`。

按这个顺序做：

1. 打开 `exercises/day27_integrated_exercises.py`，先看 `main` 的对照情境，
   再读 `search_notes` 和 `run_agent` 的接口。不用从头读假模型文件；
   若想看它单独做什么，可右键运行 `demos/day27/day27_fake_model.py`，只看第一次 assistant 点单。
2. 完成 A：把旧的多文件检索迁移到新资料目录；运行后先核对两个文件的出处、
   总上限为 1 时只有一条、无命中返回空列表。这里也完成整合前的检索上限复验。
3. 完成 B：自己把旧工具和判断函数接进主循环。先核对正常先查后算及两种
   `allow_code`，再看无命中、坏参数、连续失败、缺用量、预算和时限。
   `run_code` 仍只支持受限数值代码，`allow_code` 来自应用入参，不来自模型参数。
4. 依据实际输出填写练习末尾“现象与原因”，逐条找轨迹证据；若实际与
   期望不符，就保留真实现象并检查代码。Day 27 的代码和解释都由学员完成。

在 PyCharm 里右键运行该练习文件；仓库根目录的命令行等价入口：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day27_integrated_exercises.py
```

本日离线情境中的 `usage` 是假数据，`TEACHING_PRICE` 是教学假单价；
`slow_model` 的单次超时也是确定性的假模型行为，不代表真实网络超时。
任务总时限只在下一次调用前检查，不能强制中断已开始的阻塞调用；
受限代码工具有自身的三秒等待上限。`max_steps` 仍兜底，工具结果不等于模型最终答复。
本练习允许 `task_limit_seconds=0.0`，专门表示一开始就到期，核对
“不发起模型请求”；日常设置时传正数。
这些限制须如实说明，不能把离线对照说成真实模型测试。

- [x] 完成 A，在新资料上核对多文件结果总上限和出处；另用“松塔文件袋”检索两份资料的第 3 行。
- [x] 完成 B，三把工具可调用，12 组离线情境的答复、步数和轨迹符合预期。
- [x] 填写末尾观察，能解释应用授权、重复判断及预算／时限触发位置。
- [x] AI 实跑批改后清脚手架、检查故障台账与进度，本地提交。

2026-10-15 批改补充：`limit=1` 返回 `catalog.txt:2`，是因为检索按文件名排序，
再按总上限截取；学员的“按顺序”解释与实跑相符。任务时限在已有一次响应后
才触发的边界也单独复测：`steps` 和 stop 的 `step` 都为 1，累计用量保留该响应。
这里验证的是离线固定情境；独立变式仍留给 Day 28。

## Day 28：独立变式验收与交接（已验收）

今天不引入新工具，也没有已实现主循环的演示。先闭卷复现 Day 26A 的用量判断、
Day 26B 的重复判据，再用**暮云贴纸买 6 包**的新问题检验 Day 27 主循环能否复用。
新商品加在 `demos/day27/day27_notes/` 两份虚构资料的第 4 行；Day 27 原题的资料与答案不变。
`demos/day28/day28_fake_model.py` 是 AI 提供的离线点单夹具，按收到的观察给下一步，不是学员的
Agent，也没有真实网络请求。不要先读它的实现来猜运行结果。离线变式完成后，
`demos/day28/day28_live_check.py --live` 用真实模型请求检查同一个 `run_agent` 的先查、后算、
再答链条。真实结果以实际输出为准，一次通过也不能说明所有问题都可靠。

| 文件 | 用途 |
|---|---|
| `demos/day28/day28_验收记录.md` | 学员先写闭卷预测，再补离线与真实运行证据、三分钟讲解要点 |
| `exercises/day28_variant_exercises.py` | 新用量、工具轨迹和六组变式对照；`run_variant` 留给学员 |
| `demos/day28/day28_fake_model.py` | AI 提供的新问题假点单，只用于稳定验收消息回填 |
| `demos/day28/day28_live_check.py` | AI 提供的真实请求入口；只负责连接模型和打印证据，不实现学员主循环 |

按这个顺序进行：

1. 先打开记录模板和练习文件中的 `REVIEW_USAGES`、`REVIEW_TOOL_TRACE`，不运行脚本、
   不回看 Day 27 主循环，填记录第 1～3 节的预测。先预测再运行，才能看出哪里真正会了。
2. 完成 `run_variant`。复用 Day 27 的 `run_agent`，让它新增可选的 `chat_fn` 参数，
   默认仍是旧假模型，本日改传 `day28_fake_model.fake_chat`；不要复制整段主循环。
   新商品在原资料目录中，检索函数和工具协议不需要换。旧的 Day 27 入口仍应正常。
3. 运行新练习，逐组对照正常、错误后修正、代码权限、步数与成本上限。根据真实
   `request`、`tool`、`final`、`stop` 轨迹填写记录第 2～5 节，不用 AI 教具输出冒充
   自己的预测。两种 `code` 情境共用点单，区别由应用传入的 `allow_code` 决定。
4. 离线部分完成后，用 PyCharm 打开 `demos/day28/day28_live_check.py`，在运行配置的 Parameters
   中填 `--live` 再运行。它复用你写的 `run_agent`，最多真实请求四次，打印每次
   `finish_reason`、assistant 点单、tool 观察、调用 ID、最终答复与用量。根据**自己
   跑出的实际输出**填验收记录第 6 节；若失败，保留原始停止原因，检查是哪一步。
   根目录 `.env` 需已有 `LLM_API_KEY` 和 `LLM_BASE_URL`；`LLM_MODEL` 未填时
   默认用 `deepseek-flash`。
5. 用自己的话讲清消息配对与停止条件，并指出离线验证的一项限制。AI 批改后再清
   脚手架、更新本周状态与 `HANDOFF.md`，完成本地提交；推送仍由学员执行。

在 PyCharm 中右键运行练习文件；仓库根目录的等价命令如下。已完成的入口可用来复跑，
真实请求的输出可能变化，验收记录保留学员当时的实际结果。

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day28_variant_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\exercises\day27_integrated_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\demos\day28\day28_live_check.py --live
```

真实请求沿用 Day 24 学过的原生工具协议。只需回看
[DeepSeek 工具调用指南](https://api-docs.deepseek.com/zh-cn/guides/tool_calls/)中工具定义、
`tool_calls` 返回及 `tool_call_id` 回填的例子：它们分别对应本日的工具说明、
assistant 点单和 tool 观察。真实入口只向模型暴露 `search_notes` 与 `calculator`；
`run_code` 的应用授权仍由离线变式验收。真实 token 数来自接口返回，
汇总里的已知成本仍用 Day 27 的**教学假价**估算，不代表实际账单。

- [x] 运行前写流程、预算与重复判据的预测，再用输出核对；预算与两组重复计数均预测正确。
- [x] 复用同一个 Agent 循环，六组新变式符合预期；Day 27 旧情境回归通过。
- [x] 学员运行真实模型入口：先检索、后计算、再答复，共 3 次请求，42 元和 `catalog.txt:4`；原调用 ID、实际 token 与教学估价保存在验收记录。
- [x] 填写运行证据、失败路径、讲解要点与离线／单次真实调用的限制；AI 批改后学员订正了权限观察和停止原因。
- [x] AI 清理练习题干、复查格式与故障台账，写本周 `HANDOFF.md` 并在验收后本地提交。

## 跨天复验接续点

这是待执行安排，不是新的每日作业表。AI 在实际复验后简记日期、证据入口和仍需提示之处。

- [x] 2026-10-13 Day 26 开始前，闭卷复述原 assistant 点单、tool 回填和继续请求的关系；原稿与订正在 `exercises/day26a_budget_exercises.py` 末尾。
- [x] 2026-10-15 Day 28 用未见过的 `REVIEW_USAGES` 闭卷预测累计 530/70 token、成本 0.00081 元和 `cost_budget`，输出核对一致。
- [ ] 2026-10-15 Day 28 用新工具轨迹正确预测末尾计数 1→2 和 `repeated_call`；距 Day 26B 后半约 1 天，短于计划的 2～3 天，Week 04 再做一次延迟复验。
- [x] 2026-10-15 Day 28 新商品 `limit=1` 补测只得 `catalog.txt:4`；学员在 `allow_code` 两种输入下记录了拒绝与数值观察。
- [x] 2026-10-15 新问题变式复用 Day 27 主循环，涵盖算式修正、权限与停止路径；学员先写预测再核对输出。

## 阶段清单（指完整 Agent；此前的小练习状态见上方）

- [x] 理解「思考 → 行动 → 观察」的循环
- [x] 设计终止条件：拿到答案 / 达到最大步数 / 超时或超预算
- [x] 自己写主循环与输出解析
- [x] 接 3 个工具：检索、计算器、受限数值代码工具（不声称通用 Python 沙箱）
- [x] 完整轨迹：请求、工具名与参数、观察、用量与停止原因；不补写内部推理
- [x] 加最大步数与成本上限

## 验收标准

- [x] 先写流程预测，再依据点单／观察的同一 ID、停止轨迹解释循环，并完成新商品变式；讲解要点见 `demos/day28/day28_验收记录.md`
- [x] Agent 在工具连续报错时不会无限循环
- [x] 正常、无命中、坏参数、重复调用、预算和时限情境都有可核对的依据
