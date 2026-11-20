# Day62 记录：GitHub Actions 离线 CI + 手动 live

只填客观运行结果与自己的判断；要求见 [题目说明](day62_题目说明.md)。
远端结果以 GitHub Actions 页面为准，没看到之前不写「已通过」。

## 1. 本地结果

| 入口 | 结果 | 输出目录 / 说明 |
|---|---|---|
| workflow 检查器 | 10/10 | `outputs/` |
| `ruff check` | 通过 | 本地 |
| `ruff format --check` | 通过 | 本地 |
| `pytest` | 17 passed | 本地 |
| 本地 live 冒烟（可选） | 未跑 | 未消耗调用 |

## 2. 远端运行

| 项目 | 结果 |
|---|---|
| Actions 运行 URL（手动） | https://github.com/lyj717/agent-learning/actions/runs/44701577259 |
| `offline` job | success（手动运行 21 秒；push 那次 33 秒） |
| `live` job（push 时） | skipped（push 运行 44336006843） |
| `live` job（手动 Run workflow） | success（16 秒，冒烟步骤通过） |
| 运行时长 | push 33 秒；手动 offline 21 秒、live 16 秒 |
| live 实际用量 / 费用 | 1 次调用；35+18=53 token；回答「收到」；耗时 1019ms；按未命中价约 0.000214 元 |

## 3. 观察与原因

1. 为什么 push 只跑离线，真实模型要手动触发？
   如果 live 也挂 push，会发生什么？从费用、密钥、失败影响三方面说。

   答：push跑离线更方便，不需要主动触发；如果 live 也自动触发，
   每次提交都花钱，额度不可控，并且每次 push 都自动使用密钥，风险面变大，
   并且live 一红，日常 CI 也红，反而掩盖真正的离线问题



2. 哪些检查必须留在离线 job，哪些只能放到 live？
   各举一条，并说明判据。

   答：格式检查，测试等留在离线job，不需要网络、密钥、模型，能确定复现的用离线job，如ruff
   真实模型调用只能放到live，需要 secrets 或真实模型才能验证的用live，如smoke



3. 第一次远端运行有没有暴露本地没发现的问题？
   例如依赖、路径、Python 版本、YAML 解析、权限。没有就写「未发现」，并说明
   本地已经预演了哪些命令。

   答：远端只出现 Node 20 / ubuntu-latest 两条警告，没有失败。
   已经预演了如下命令：
   workflow 检查器（10/10）；
   ruff check weeks/week08_evaluation_reliability tests；
   ruff format --check ...；
   pytest -p no:cacheprovider tests（17 passed）。



4. 这份 workflow 用哪几道闸限制预算？至少列四条，并指出哪一条最关键。

   答：
   最关键的一条：手动设置live触发
   max_tokens=32；
   max_retries=0，只调用 1 次；
   仅在live里调用真实模型
   设置timeout-minutes: 10
   


