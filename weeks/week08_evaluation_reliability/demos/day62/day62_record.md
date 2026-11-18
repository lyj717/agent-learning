# Day62 记录：GitHub Actions 离线 CI + 手动 live

只填客观运行结果与自己的判断；要求见 [题目说明](day62_题目说明.md)。
远端结果以 GitHub Actions 页面为准，没看到之前不写「已通过」。

## 1. 本地结果

| 入口 | 结果 | 输出目录 / 说明 |
|---|---|---|
| workflow 检查器 | __/10 | `outputs/` |
| `ruff check` | | |
| `ruff format --check` | | |
| `pytest` | __ passed | |
| 本地 live 冒烟（可选） | __ 次调用；用量 __ | 不跑就写「未跑」 |

## 2. 远端运行

| 项目 | 结果 |
|---|---|
| Actions 运行 URL | |
| `offline` job | |
| `live` job（push 时） | |
| `live` job（手动 Run workflow） | |
| 运行时长 | |
| live 实际用量 / 费用 | |

## 3. 观察与原因

1. 为什么 push 只跑离线，真实模型要手动触发？
   如果 live 也挂 push，会发生什么？从费用、密钥、失败影响三方面说。

   答：



2. 哪些检查必须留在离线 job，哪些只能放到 live？
   各举一条，并说明判据。

   答：



3. 第一次远端运行有没有暴露本地没发现的问题？
   例如依赖、路径、Python 版本、YAML 解析、权限。没有就写「未发现」，并说明
   本地已经预演了哪些命令。

   答：



4. 这份 workflow 用哪几道闸限制预算？至少列四条，并指出哪一条最关键。

   答：


