# Week 03｜Agent 核心循环（手写）

**规则**：这一周不许用框架。自己写主循环、自己解析模型输出、自己决定终止条件。

**交付物**：不用任何框架的 ReAct Agent。

## 开工状态（2026-10-11）

Week 02 的 Day 15～21 已验收，接续 `../week02_tools/HANDOFF.md`。
视频在面试复习时补录，JD 与简历在项目结束后统一处理，不作为开工门槛。
`docs/21天详细日程表.md` 只逐日排到 Day 21；下面是依据周计划拟定的节奏，
按实际完成情况调整，一天没验收就先接着做。

**本周练习节奏**：平日先由演示逐步拆解新机制，再用能单独运行的小题练习；
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
| Day 26 | 超时、token / 成本预算、重复调用检测 | 待开始 |
| Day 27 | 整合项目、验证日志与失败路径 | 待开始 |
| Day 28 | 验收、白板复盘、交接 | 待开始 |

## Day 22：先看清循环在保存什么

先用自己的话口头复述 Week 02：请求里有什么、谁执行工具、原 assistant
与 tool 结果怎么配对、什么时候继续请求。再打开本日演示。

ReAct 把推理与行动交替起来，让后续行动能根据外部结果调整。
读 [ReAct 原论文摘要](https://arxiv.org/abs/2210.03629) 的 Abstract 即可，
今天关注“行动取得新信息，再用于下一步判断”，暂时不用读实验指标。
仓库面试题对应 Q1、Q3、Q4，写完练习后再对照。

| 文件 | 用途 |
|---|---|
| `day22_agent_loop_demo.py` | 逐节讲解；内含假模型、乘法工具、结果打印，演示正常结束与步数耗尽 |
| `day22_agent_loop_exercises.py` | 学员完成的循环，返回状态和轨迹；末尾保留运行观察 |

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day22_agent_loop_demo.py
# 已完成的练习：打印四组情境和非法上限的运行结果。
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day22_agent_loop_exercises.py
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
| `day23_protocol_demo.py` | 按「是什么／为什么／场景／代码／注意」讲两种决定、语法与协议的边界；`--live` 真请求一次模型 |
| `day23_json_parse_exercises.py` | 小练习 A：检查结束原因、空正文、JSON 语法和最外层类型 |
| `day23_decision_exercises.py` | 小练习 B：分别校验 `final` 和 `action` 的字段、类型、工具白名单 |

在仓库根目录依次运行：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day23_protocol_demo.py
# 小练习 A：对照正文解析的六组输入
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day23_json_parse_exercises.py
# 小练习 B：对照最终答复和工具行动
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day23_decision_exercises.py
# 最后观察一次真实模型输出；需要根目录 .env 和网络
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day23_protocol_demo.py --live
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
| `day24_retrieval_demo.py` | 单文件检索、出处、列表回填、先查后算；`--live` 观察真实模型的原生工具调用 |
| `day24_notes/products.txt`、`day24_notes/stock.txt` | 两份虚构商品资料；工具只在这个固定目录内查找 |
| `day24_search_exercises.py` | 练习 A：复用演示的单文件匹配，自己写多文件搜索与结果总数上限 |
| `day24_observation_exercises.py` | 练习 B：调用自己的检索或已有计算器，返回带原 ID 的 tool 消息 |

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
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day24_retrieval_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day24_search_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day24_observation_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day24_retrieval_demo.py --live
```

两份练习和末尾观察已完成；函数题干已清理为一行说明。
演示的检索只查 `products.txt`；练习 A 扩展到两份文件。演示的循环是 AI 教具，
周末再由学员把自己的多文件检索、工具回填与循环整合。
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
真实模型调用留到周末整合时接入。

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
| `day25_code_demo.py` | 先看允许计算和语法树入门，再看拒绝文件调用、变量不跨调用保留及子进程入口 |
| `day25_code_worker.py` | AI 提供的受限解释器；`check_tree` 查白名单，`eval_number` 只计算获准节点 |
| `day25_syntax_exercises.py` | 小练习 A：从语法树找第一个不被允许的节点 |
| `day25_permission_exercises.py` | 小练习 B：由应用授权；未授权时不执行工具，仍按原 ID 回填 |

### 按这个顺序做

1. 在 PyCharm 打开 `day25_code_demo.py`，直接右键运行。先顺着第 1～5 节
   看输出，再读文件开头的 `main` 和后面的 `run_limited_code`。
2. 按需打开 `day25_code_worker.py`，只看 `check_tree` 与 `eval_number`：
   前者决定哪些语法能进入，后者计算它们；不用重写整份执行器。
3. 练习 A 已完成：右键运行，对照 `None`、`Call`、
   `Import`、`While`、`Constant` 和 `SyntaxError`，填文件末尾的观察。
4. 练习 B 已完成：右键运行。
   比较“应用未授权”与“已授权但代码被白名单拒绝”，填文件末尾的观察。

仓库根目录的等价命令：

```powershell
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day25_code_demo.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day25_syntax_exercises.py
.venv\Scripts\python.exe -B weeks\week03_agent_loop\day25_permission_exercises.py
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

## 清单

- [x] 理解「思考 → 行动 → 观察」的循环
- [ ] 设计终止条件：拿到答案 / 达到最大步数 / 超时或超预算
- [ ] 自己写主循环与输出解析
- [ ] 接 3 个工具：检索、计算器、沙箱执行
- [ ] 完整日志：每步的思考、工具调用、观察结果都打印
- [ ] 加最大步数与成本上限

## 验收标准

- [ ] 能说清「为什么框架会掩盖 bug」
- [ ] Agent 在工具连续报错时不会无限循环
