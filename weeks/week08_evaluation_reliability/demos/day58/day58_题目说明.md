# Day58 题目说明：模型裁判与解析

本页是 [练习](day58_judge_exercises.py) 的完整题面：调用点、全部判分情形、
现场运行步骤与预算。完整规则在下面 A、B 两节；练习文件已清理为函数与类型注解。

## 数据从哪里来

| 文件 | 内容 | 是否可改 |
|---|---|---|
| `day57_cases.json` | Day57 的 8 道题、检索编号；`day58_support` 会按编号切出原文 | 不改 |
| `day57_answers_v2.json` | 要被裁判读的 8 份回答 | 不改 |
| `day58_human_labels.json` | 你自己的人工判读，8 题 | 只填这里 |
| `notes/python-notes.md` | 原文；证据按行号切片后交给裁判 | 不改 |

裁判能看到问题、回答、原文证据；**不能看到** `must_include` / `must_not_include`，
否则等于把预期答案泄漏给它。

## A：`build_judge_messages(case, answer)`

调用点：检查器与 live 入口都调用 `build_judge_messages(case, answer)`；
live 再把返回的消息交给 `judge_once`。

证据从 `case["evidence"]` 取：运行环境按 `case["retrieved_ids"]` 从
`notes/python-notes.md` 切出 `[{"id": str, "text": str}]`。
`answer["cited_ids"]` 只是回答声称引用了哪些编号，没有正文，不能当证据。
两条消息的 `content` 都必须是 `str`（消息接口不收 dict）。

| # | 检查项 | 期望 |
|---|---|---|
| 1 | 返回两条消息 | `[{"role": "system", ...}, {"role": "user", ...}]`，内容为字符串 |
| 2 | `answer_ok` | system 或 user 里出现这个字段名与含义 |
| 3 | `citation_ok` | 同上，并说明没有引用时填 `null` |
| 4 | 输出格式 | 明确要求只输出一个 JSON 对象 |
| 5 | 问题 | user 消息包含 `case["question"]` 原文 |
| 6 | 回答 | user 消息包含 `answer["answer"]` 原文 |
| 7 | 证据 | user 消息包含 `case["evidence"]` 每一项的 `id` 与 `text` |
| 8 | 不泄漏预期 | 两个字段 `must_include` / `must_not_include` 不出现 |
| 9 | 无引用场景 | 用 `cited_ids=[]` 的回答也能生成两条消息 |
| 10 | 不改输入 | 调用前后 `case` 与 `answer` 不变 |

提示：system 负责评分标准，user 负责材料；把「原文没写就不要补」写进 system。

## B：`parse_judge_verdict(raw)`

调用点：`verdict = parse_judge_verdict(call["raw_text"])`；live 入口每题调用一次。

| # | 输入 | 期望 |
|---|---|---|
| 1 | 纯 JSON，三个键齐全 | 返回字典，`citation_ok` 可为 `None` |
| 2 | ```json 代码块包住 | 去掉围栏后按 1 处理 |
| 3 | JSON 前后有解释文字 | `ValueError`（不做正则抠取） |
| 4 | 缺少 `reason` | `ValueError` |
| 5 | 多出 `confidence` | `ValueError` |
| 6 | `answer_ok` 为字符串 `"true"` | `ValueError` |
| 7 | `reason` 为整数 | `ValueError` |
| 8 | `citation_ok` 为 `false` | 合法，返回 `False` |
| 9 | 输入不是字符串（`None`） | `TypeError` |
| 10 | 空字符串或只有空白 | `ValueError` |

返回：`{"answer_ok": bool, "citation_ok": bool | None, "reason": str}`，
键恰好三个，`reason` 保留原字符串。

## 现场运行与预算

1. 先填 [人工标签](day58_human_labels.json)：8 题都填 `answer_ok`；
   有引用时 `citation_ok` 填 `true`/`false`，没有引用填 `null`；`reason` 写一两句。
   **先填人工标签，再跑裁判**，避免被裁判结论带着走。
2. 离线检查：`--part a` 应为 10/10，`--part b` 应为 10/10。
3. 先单题试一次：`--part live --limit 1`（1 次调用），看原始返回与解析。
4. 全量跑：`--part live`（8 次调用）。失败不自动重试，原始文本保留在结果里。
5. 比较：`--part compare`，读逐题表与分歧清单，再写记录里的观察。

预算：单题试跑 1 次 + 全量 8 次 = **9 次调用**，在 8～12 次的计划内；
不自动重试。费用按实际用量，记录里抄结果目录打印的 token，不估算成账单。

## 跑完看什么

`--part a`：10 组结构检查，不一致应为 0。
`--part b`：10 组解析检查，不一致应为 0。
`--part live`：每题打印原始返回、解析结果、用量与耗时；解析失败单独列出。
`--part compare`：人工/裁判逐题对照，答案一致数与引用一致数，分歧题号与字段。

一开始就一致不等于裁判可信，8 题也不足以报「准确率」；重点看分歧。
观察写在 [记录](day58_record.md)；每次运行在 `outputs/` 下新建目录，失败也保留。
