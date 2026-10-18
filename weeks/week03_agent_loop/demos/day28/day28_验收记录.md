# Day 28｜独立变式验收记录（学员填写）

今天先用离线教具做稳定复验，再用真实模型检查同一个 Agent 循环。先填第 1～3 节的**预测**，这时不要运行
`day28_variant_exercises.py`，也不要翻 Day 27 的主循环；再完成代码并运行，填写
第 4～5 节。最后用 `day28_live_check.py --live` 做一次真实请求，填写第 6 节。
实际结果要如实记录；若与预测不同，保留原预测并解释差别。

## 1. 闭卷画流程（运行前）

新问题：“暮云贴纸买 6 包多少钱？请说明单价出处。”不用写代码，按请求序号写出
assistant 点单、tool 观察、下一次请求和最终答复之间的关系。说明工具算出数字后，
为什么不能立刻把它当作 Agent 的最终答复。

我的预测：
第 1 次请求：assistant 点单 ___预计调用工具search_notes_关键词为暮云贴纸__
→ 程序执行工具，得到 tool 观察 ___预计返回观察暮云贴纸：单价 7 元/包，规格 24 枚。___
→ 把点单和观察放入消息历史

第 2 次请求：assistant 根据前面的观察 ___预计调用工具calculator__表达式为7 * 6_
→ 程序执行工具，得到 tool 观察 ___预计返回观察：_42_
→ 把点单和观察放入消息历史

后续请求：assistant 看到工具结果后给出最终答复 ___共42元，单价出处catalog.txt:4___
工具算出数字后，还要发送下一次请求得到答案，如果此时因为各种报错返回模型就得不出最终答复

## 2. 预算跨天复现（运行前）

用 `day28_variant_exercises.py` 中的 `REVIEW_USAGES`、`REVIEW_TOKEN_LIMIT`、
`REVIEW_COST_LIMIT_YUAN` 和 Day 27 的 `TEACHING_PRICE`，不调用旧函数，预测
请求数、累计输入 / 输出 / 总 token、已知成本，以及下一次请求前的停止原因。

我的预测：请求数：2  累计输入：530 累计输出：70  总token：600 已知成本：0.00081   stop_reason:cost_budget


运行后对照到的实际值及差别（先留空）：
用量汇总：{'requests': 2, 'prompt_tokens': 530, 'completion_tokens': 70, 'missing_usage': 0, 'known_cost_yuan': 0.00081}
下一次请求前的停止原因：cost_budget

## 3. 重复调用跨天复现（运行前）

看同一文件中的 `REVIEW_TOOL_TRACE`。分别只取前 3 条、取全部 4 条，预测
末尾连续相同观察的条数与 `repeat_limit=2` 时的停止原因；解释第三条为何
使计数变化。不要把调用 ID 或 JSON 键顺序当成重复判据。

我的预测：取前3条：连续相同观察的条数为1，停止原因为None
取全部4条：连续相同观察的条数为2，停止原因为repeated_call
第三条的观察与第二条不同，不能算连续相同

运行后对照到的实际值及差别（先留空）：
工具轨迹前 3 条：末尾连续 1 条；停止原因 None
工具轨迹前 4 条：末尾连续 2 条；停止原因 repeated_call

## 4. 新问题运行证据（完成代码并运行后）

正常情境：实际 `stop_reason`、`steps`、答复金额与单价出处；列出一次 assistant
点单与对应的 tool 观察 ID。

我的记录：
stop_reason:final_answer steps:3 答复 暮云贴纸 6 包共 42 元；单价出处 catalog.txt:4
第 2 次 assistant 点单：calculator({"expression": "7 * 6"})；ID day28_calc
 第 2 次 tool 观察：ID day28_calc；content 42


算式报错后修正：第一次计算的错误观察是什么？下一次计算参数改成什么？为何
这里不应被判作连续重复？

我的记录：
工具执行失败：ValueError: 计算器只支持数字、括号和 + - * /，不支持变量或函数调用
"expression": "7 * 6"
因为两次的工具调用以及观察结果都不同


代码获准与未授权：两次 `run_code` 的观察各是什么？授权由哪里决定？

我的记录：
工具执行失败：PermissionError: 本次请求未获代码执行权限
"ok": true, "value": 42
授权由程序参数决定


从“第二步后到上限”和“检索后到成本上限”中选一条失败路径：写出 request、
tool、stop 的顺序及 `steps`，解释 `answer` 为什么仍是 `None`。

我的记录：
第 1 次请求：结束原因 tool_calls；单次用量 {'prompt_tokens': 31, 'completion_tokens': 8}
第 1 次工具观察：search_notes {"keyword": "暮云贴纸", "limit": 2}；ID day28_search；观察 [{"source": "catalog.txt", "line": 4, "text": "暮云贴纸：单价 7 元/包，规格 24 枚。"}, {"source": "stock.txt", "line": 4, "text": "暮云贴纸：现货，按包销售。"}]
第 1 次停止：cost_budget
检测到成本超出以后就直接退出了，模型还没有给出最终答复，因此是None


## 5. 三分钟讲解与限制

不用照读代码，用自己的话讲清：消息如何回填、主循环何时继续、有哪些停止原因。
再写一项本次离线检查**不能证明**的真实环境能力，并说明原因。

我的讲解要点与仍不确定的地方：
消息在chat之后，检测过没有相应超时后，以及调用工具后回填
主循环在没有遇到停止原因的时候继续
有任务超时，响应超时，最终回复，token上限，成本上限，重复响应，最大步数，未知用量这些停止原因
本次离线检查不能证明的有真实调用模型的能力
因为没有连接真正的模型与其对话


## 6. 真实模型端到端检查（离线部分完成后）

运行 `day28_live_check.py --live`。这是你写的同一个 `run_agent`，真实模型自己决定
是否先检索、用什么算式、何时回答。记录第一次请求的 `finish_reason`、实际工具名与
参数、assistant 点单 ID 和对应 tool 观察 ID；再记录检索到的单价出处、计算器算式、
最终答复、`stop_reason`、请求次数和累计 token。若没有走完，保留实际输出并说明停在
哪一步，不把预期流程写成已发生的事实。

我的真实运行记录：
  第 1 次请求：结束原因 tool_calls；真实 token 用量 {'prompt_tokens': 483, 'completion_tokens': 64}
  assistant 点单：search_notes({"keyword": "暮云贴纸", "limit": 2})；ID call_00_iBtMrqimFFpTpx1QZzDq2154
  tool 观察：ID call_00_iBtMrqimFFpTpx1QZzDq2154；content [{"source": "catalog.txt", "line": 4, "text": "暮云贴纸：单价 7 元/包，规格 24 枚。"}, {"source": "stock.txt", "line": 4, "text": "暮云贴纸：现货，按包销售。"}]
  第 2 次请求：结束原因 tool_calls；真实 token 用量 {'prompt_tokens': 626, 'completion_tokens': 44}
  assistant 点单：calculator({"expression": "7*6"})；ID call_00_DmEN9ayTMrqB7rYXODUf3665
  tool 观察：ID call_00_DmEN9ayTMrqB7rYXODUf3665；content 42
  第 3 次请求：结束原因 stop；真实 token 用量 {'prompt_tokens': 683, 'completion_tokens': 63}
  最终答复：暮云贴纸买 6 包共 **42 元**。

单价出处：catalog.txt:4 —— "暮云贴纸：单价 7 元/包，规格 24 枚。"

计算：7 元/包 × 6 包 = 42 元。
结果：final_answer；请求 3 次；答复 暮云贴纸买 6 包共 **42 元**。

单价出处：catalog.txt:4 —— "暮云贴纸：单价 7 元/包，规格 24 枚。"

计算：7 元/包 × 6 包 = 42 元。；累计用量 {'requests': 3, 'prompt_tokens': 1792, 'completion_tokens': 171, 'missing_usage': 0, 'known_cost_yuan': 0.002476}
注意：累计 token 来自真实响应；累计金额仍按 Day 27 的教学假价估算。
本次验收条件通过：真实模型先查、后算、再答，并保留出处与调用 ID。

这一次证明了什么？还不能证明什么（例如其他问题是否都可靠）？`usage` 中哪些是
真实 token，哪一项仍按 Day 27 的教学假价计算？

我的判断：证明了在真模型下可用，但其他错误原因无法证明，
prompt_tokens和completion_tokens是真实的
known_cost_yuan是用假值计算的
