# Week 02｜结构化输出与工具调用

**目标**：吃透工具调用的完整回合。这一周是整个计划的分水岭。

**交付物**：会调用 3 个工具的结构化信息抽取器（含错误自纠）。

分工还是老规矩：**演示和讲解由 AI 搭好，实验、记录、练习题由学员自己完成。**

## 本周材料

| 天 | 材料 | 谁做 | 是什么 |
|---|---|---|---|
| Day 15 | `day15_structured_output_demo.py` | AI 搭・学员跑 | 结构化输出：JSON 模式管什么、不管什么；含 3 个真实踩过的坑（离线，`--live` 真跑 3 次对照） |
| Day 15 | `day15_structured_output_exercises.py` | **学员做** | 三题：拼提示词 → 安全解析 → 串起来真抽 10 条（留了空，会大声报 `NotImplementedError`） |
| Day 15 | `day15_抽取成功率记录.md` | **学员填** | Day 15 交付物：10 条的逐条结果 + 两个成功率 + 你的结论 |
| — | `llm_client.py` | AI 搭 | 共用的请求层：建客户端 + 发一次 JSON 模式请求（`chat_json` 会把原始文本和 `finish_reason` 一起给你）。Day 15 里这段是写在练习里的，从 Day 16 起收进这个文件 |
| Day 16 | `day16_pydantic_demo.py` | AI 搭・学员跑 | Pydantic 校验：空串归一、格式校验、报错怎么读；「校验失败 → 把错误回填 → 模型改对」的完整回合（离线，`--live` 真跑一轮对照） |
| Day 16 | `day16_validator_decorator_demo.py` | AI 搭・学员跑 | 加餐：`@field_validator` + `@classmethod` 到底干嘛用——5 个小实验（不加装饰器 / 不加 classmethod / before vs after / 装饰器展开 / 一器多字段），完全离线 |
| Day 16 | `day16_regex_demo.py` | AI 搭・学员跑 | 加餐：`re.fullmatch` 是什么、`\d{11}` 怎么读、`search`/`match`/`fullmatch` 的区别，以及「全角数字能绕过 11 位数字校验」这个真坑，完全离线 |
| Day 16 | `day16_model_validate_demo.py` | AI 搭・学员跑 | 加餐：`PersonExtract.model_validate_json(raw)` 到底做了什么——把黑盒拆成三步（解析 → 逐字段校验 → 造实例），每步都打印出来；含「字段缺失 / 多余字段」为什么不算错，完全离线 |
| Day 16 | `day16_retry_probe.py` | AI 搭・学员跑 | 工具：**零成本**验证「重试有没有真的重发请求」——把 `chat_json` 换成假函数，数它被调用了几次。写完第 3 题后跑它自测，不用花一分钱 |
| Day 16 | `day16_pydantic_exercises.py` | **学员做** | 三题：把规矩写成模型 → 把报错变成给模型看的话 → 带重试地抽一次（留了空，会大声报 `NotImplementedError`） |
| Day 16 | `day16_脏数据处理记录.md` | **学员填** | Day 16 交付物：四条脏数据的处理结果 + 三条难抽文本的「第一次 vs 重试后」对照 + 你的结论 |

跑法（在仓库根目录）：

```bash
# Day 15 讲解（默认离线，不花钱；里面的返回数据是真实抓下来的）
.venv\Scripts\python.exe weeks\week02_tools\day15_structured_output_demo.py

# 真想亲眼看差别（要网络，跑 3 次）
.venv\Scripts\python.exe weeks\week02_tools\day15_structured_output_demo.py --live

# Day 15 练习：前两题离线自测；第三题是 10 条真实抽取
.venv\Scripts\python.exe weeks\week02_tools\day15_structured_output_exercises.py
.venv\Scripts\python.exe weeks\week02_tools\day15_structured_output_exercises.py --live

# Day 16 讲解（默认离线，不花钱；脏数据和报错都是真跑出来的）
.venv\Scripts\python.exe weeks\week02_tools\day16_pydantic_demo.py

# 真想看「失败 → 回填 → 改对」的完整回合（要网络，2 次调用）
.venv\Scripts\python.exe weeks\week02_tools\day16_pydantic_demo.py --live

# Day 16 练习：前两题离线喂脏数据；第三题是真抽三条难抽文本
.venv\Scripts\python.exe weeks\week02_tools\day16_pydantic_exercises.py
.venv\Scripts\python.exe weeks\week02_tools\day16_pydantic_exercises.py --live

# Day 16 加餐：那两个装饰器到底是干嘛的（完全离线）
.venv\Scripts\python.exe weeks\week02_tools\day16_validator_decorator_demo.py

# Day 16 加餐：re.fullmatch 和「11 位数字」怎么校验（完全离线）
.venv\Scripts\python.exe weeks\week02_tools\day16_regex_demo.py

# Day 16 加餐：model_validate_json 到底执行了哪些工作（完全离线）
.venv\Scripts\python.exe weeks\week02_tools\day16_model_validate_demo.py

# Day 16 自测：重试到底有没有重发请求（零成本，不发真实网络请求）
.venv\Scripts\python.exe weeks\week02_tools\day16_retry_probe.py
```

学员做完练习和记录后，交给 AI 对答案、挑毛病。

## 官方文档去哪看（Day 15 ~ Day 21）

计划表里的「读官方文档」，指的是**你这家模型服务商的文档**，不是第三方教程。
你的 `.env` 指向 DeepSeek，整周只用得到这一页：
<https://api-docs.deepseek.com/zh-cn/api/create-chat-completion>

| 哪一节 | 和哪天的课有关 | 读的时候盯什么 |
|---|---|---|
| `response_format` | Day 15、Day 16 | JSON 模式怎么开；文档明确要求**同时**在 system 或 user 里写要 JSON，否则模型可能一直吐空白直到把 `max_tokens` 用光；`finish_reason=length` 时 JSON 会被截断 |
| `tools` | Day 17 ~ Day 19 | 工具怎么描述成一段 JSON schema；模型返回的不是答案，而是「请你执行这个函数」 |
| `tool_choice` | Day 18 | 怎么强制或禁止模型用工具（`auto` / `none` / 指定某个工具） |
| 函数定义里的 `strict` | Day 16、Day 19 | Beta 能力：保证输出严格符合你给的 schema——它是「JSON 模式」的加强版 |
| `finish_reason` | Day 15 ~ Day 19 | `stop` / `length` / `tool_calls` 各代表什么；`tool_calls` 就是 Agent 循环的起点 |

读法建议：Day 15 只需要看 `response_format` 一节，5 分钟够。
写完提取器再回头看 `strict`，你会发现它解决的正是你踩到的坑。

## 每日清单

- [x] Day 15｜结构化输出，从杂乱文本抽 JSON，统计成功率（实测 10 条：解析 10/10 = 100%、字段 7/10 = 70%；第 9 条另补跑 3 次，见 `day15_抽取成功率记录.md`）
- [x] Day 16｜Pydantic 校验与失败重试（把抽取结果用模型接收；四条脏数据不崩，失败自动回填重试一次——注入式验证实测走通；三条真实文本一次通过）
- [ ] Day 17｜第一个工具（计算器），跑通最小闭环，画流程图
- [ ] Day 18｜多工具与工具选择，记录选错工具的案例
- [ ] Day 19｜错误回填让模型自纠，加最大重试次数
- [ ] Day 20｜整合 + README + 演示视频
- [ ] Day 21｜白板默画工具调用回合（限时 5 分钟）

## 验收标准

- [ ] 能不看笔记画出完整调用回合，说清每一步谁在执行
- [ ] 能说出工具设计得好和差区别在哪
