# 信息抽取与三工具箱

> Week 02 的独立项目。Day 16–19 的核心逻辑已迁入本目录；Day 20 完成了 `app.py` 的整合与真实运行记录。

## 开发时怎么运行

在仓库根目录执行。使用仓库的 `.venv`，真实请求所需配置读根目录 `.env`（格式见 `.env.example`）。

```powershell
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py --help
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py extract "我叫李娜，在深圳做前端。"
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py ask "杭州有几笔已支付订单？"
```

`extract` 和 `ask` 都会调用真实模型。`app.py` 中的三道整合题已完成，可以运行上面后两条命令。

## 文件导览

| 文件 | 开发时去哪里找对应逻辑 |
|---|---|
| `app.py` | 命令行入口、抽取结果显示与模式分流 |
| `extractor.py` | Day 16 的 Pydantic 校验与抽取重试 |
| `tool_calling.py` | Day 17–19 的工具说明、分发、错误回填与轮数上限 |
| `tools.py` | Day 17–18 的计算器、模拟天气和订单查询 |
| `database.py` | Day 18 的六条模拟订单；运行时生成 `orders.sqlite` |
| `llm.py` | Week 02 共用的模型请求层，密钥从仓库根目录 `.env` 读取 |

以上文件已放在同一目录，`app.py` 可以直接从相邻模块导入；正常运行不依赖 `dayNN_*.py` 练习文件。订单数据库是运行时数据，不提交。

## 项目能做什么

一个可以分别选择 `extract` 和 `ask` 两个模式的小工具：

- `extract` 模式将文本输出成固定字段的 JSON 文本。
- `ask` 模式可以调用三个小工具回答问题。

## 实际运行与输出

### extract

```text
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py extract "我叫李娜，在深圳做前端。"
{"name": "李娜", "phone": null, "city": "深圳", "job": "前端"}
```

### ask

```text
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py ask "杭州有几笔已支付订单？"
     [第 1 轮] 它点了 query_orders
        id        = call_00_ET_00mK2K0EWjsscogDzrBp5742
        arguments = {"city": "杭州"}
        → 本地执行 = {'city': '杭州', 'paid_count': 2, 'paid_total': 200.0}
杭州有 **2 笔**已支付订单，总金额 200.0 元。
```

## 一次请求经过哪些模块

以 `app.py ask "杭州有几笔已支付订单？"` 为例：

1. `main()` 读取模式与问题，`run_project()` 进入 `answer_with_tools()`。
2. `seed_db()` 重建模拟订单库，`ask_with_recovery()` 向模型发送问题和三份工具说明。
3. 模型返回工具名、参数和调用 ID；`tool_result_or_error()` 执行本地工具。
4. `ask_with_recovery()` 把结果和相同的调用 ID 加入 `messages`；下一轮 `chat_with_tools()` 将这些消息发给模型。
5. 最终答复经 `answer_with_tools()` 和 `run_project()` 返回，由 `main()` 打印。

## 已知限制

- 计算器只支持 `+`、`-`、`*`、`/` 和括号。
- 天气工具只返回模拟快照，不能查看真实天气。
- 订单工具只查询固定的假订单。
- 最多请求模型三轮。如果第三轮仍返回工具调用，本地会执行并回填结果，但没有第四轮请求让模型据此生成答复，程序返回「达到最大轮数！」。南京天气的运行轨迹见 `../day20_演示与面试素材.md`。


## 三分钟演示视频（面试复习时补录）

本次先完成演示提纲与真实运行记录；按学员安排，视频留到面试复习时录制。
录制后把日期和文件位置或链接填进 `../day20_演示与面试素材.md`。
