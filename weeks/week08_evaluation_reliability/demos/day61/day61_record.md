# Day61 记录：失败模式清单与确定性检查

只填客观运行结果与自己的判断；检查项与教具见
[题目说明](day61_题目说明.md)。五类模式的真实证据要来自本仓库的实际运行或日志。

## 1. 运行结果

| 入口 | 结果 | 输出目录 |
|---|---|---|
| Day61 检查器 | 正常版/故障版共 10 项，符合 10/10 | `outputs/check_20261118_164122_697845_7639aaef` |
| pytest 外壳 | 5 passed | `tests/test_day61_failure_modes.py`（终端输出） |

## 2. 失败模式清单

| 模式 | 真实证据（文件/日志/运行）                                                                                                                                               | 对应检查 | 故障版是否被抓住 |
|---|--------------------------------------------------------------------------------------------------------------------------------------------------------------|---|---|
| 无限循环 | FAILURES.md 2026-10-10「模拟天气不支持南京，模型第三轮改查了北京」 Day20 真实运行连续三轮查天气，靠三轮上限才停；check_loop_limit 检查 steps <= max_steps                                                | `check_loop_limit` | 是 |
| 工具误用 | FAILURES.md 2026-10-11「Day 23 协议校验漏了值的类型」 Day23 的 read_action 对非字符串工具名没做类型检查；check_tool_allowlist 用 pytest.raises(ToolError) 守分发层。                           | `check_tool_allowlist` | 是 |
| 幻觉引用 | Day60 quality.json q06/q08 的 citation_ok=true 且 cited_ids=[]                                                                                                 | `check_citation_grounding` | 是 |
| 格式崩坏 | FAILURES.md 2026-10-07「JSON 模式把 max_tokens 调小」 JSON 模式在额度不足时返回空串，json.loads 直接报错；check_format_schema 要求缺键/非 JSON 抛 FormatError。                              | `check_format_schema` | 是 |
| 越权/注入 | weeks/week07_production/demos/day55/day55_tool_auth_checks.py 的 injected_delete、../private 证明工具名白名单不够；check_tool_authorization 用 PermissionError 守工具名与路径两道边界 | `check_tool_authorization` | 是 |

## 3. 观察与原因

1. 五类里哪一类最适合直接进 CI，哪一类只能自动检查一部分？
   分别说明判据和仍需人工/模型的部分。

   答：无限循环最适合进CI，设置一个max_steps，到阈值直接强制退出即可
   幻觉引用只能自动检查一部分，「cited_ids 是否都在 evidence_ids 里」，CI 能直接查；
   「引用片段是否真的支持结论」才是语义，需要裁判或人工。



2. 你的检查在故障版下都失败了吗？有没有哪一条一开始写得太松、
   故障版也能通过？后来把断言改成了什么？

   答：故障版都被抓住了，没有太松；最初 check_format_schema 把 dict 和 set 直接比较，正常版反而失败，后来改成 set(data) == {...}



3. Day60 暴露的 q06（规则判失败、裁判判通过）和 q08（无引用却被判引用通过），
   分别属于五类里的哪一类？应该加在哪一层：规则、裁判、人工，还是检查器？

   答：严格说两者都不是模型幻觉，都没有编造引用。q08 是裁判没按「空引用 → citation_ok=null」执行，属于引用校验/裁判口径问题；q06 是规则用例与证据不一致，属于评测规则层。 
   要加的是：裁判 prompt 明确空引用填 null；检查器加一条「cited_ids 为空时 citation_ok 必须为 null」；q06 还要改规则用例，或把 not_answered 标成该证据下的预期



4. 这套确定性检查能防住什么、防不住什么？举一个它抓不到、
   必须靠裁判或人工的例子。

   答：这套检查只防「特定结构信号」，不防「结构合法但语义错」
   例子：回答引用了真实存在、但和结论无关的片段——编号在证据内，五个检查全过，裁判/人工才能看出不支持。


