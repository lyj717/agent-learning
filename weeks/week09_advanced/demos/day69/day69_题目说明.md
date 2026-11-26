# Day69 题目：把 server 接到真实模型上跑一次问答

前八天做的是 server 本身。今天换到**宿主**视角：启动 server、把工具给模型、让模型自己调、
再把工具结果拼回对话，最后核对回答里的引用是否真的被原文支持。

宿主脚本已经由 AI 提供：[day69_host.py](../day69_host.py)。你不重写宿主，负责跑、核对、记录。

## 三步

### 1. 离线自检（不花钱）

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day69\day69_host.py --fake
```

它会用脚本化假模型走一遍「宿主 → MCP server → 工具 → 回填」的链路，轨迹存到
`demos/day69/outputs/fake_<时间>.json`。看到 `tool_calls` 里有一次 `search_notes` 就算通。

### 2. 真实模型跑一次

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day69\day69_host.py --live --question "我的笔记里怎么处理流式块？"
```

- 读 `.env` 里的 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`；
- 最多 4 轮模型调用（宿主有 `MAX_ROUNDS`）；
- 轨迹存到 `outputs/live_<时间>.json`，控制台同时打印每一步。

问题可以换成你想问的，但要是 `notes/` 里真有的内容。

### 3. 核对引用

从轨迹里找到最终回答，把里面引用的「文件名 + 行号」逐条打开原文核对：

| 引用 | 原文那一行 | 是否支持回答 | 备注 |
|---|---|---|---|
| 例：`流式块解剖.md:12` | 打开文件看第 12 行 | 是 / 否 | 引了但只支持半句也算「否」 |

这一步是今天的主要学习点：**回答看起来对，不等于引用支持它**。

## 检查器

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day69_host_exercises.py
```

10 组：A 5（宿主结构）、B 2（离线自检与假轨迹）、C 3（真实轨迹、调用过工具、回答与用量）。
C 组要求 `outputs/` 里有 `live_*.json`，且里面至少一次工具调用、`prompt_tokens > 0`。

## 预算与边界

- 离线自检 **0 次模型调用**；真实运行一次最多 **5 次**（4 轮工具循环 + 1 次收尾），失败重跑一次，最多 10 次。
- 只用 `notes/` 和 `day65/corpus` 的内容，不接外部检索；不追求回答质量，追求**链路与引用可核对**。
- 收尾兜底：模型在 4 轮内不肯结束时，宿主会把已检索结果收拢，改用非 thinking 模型（`deepseek-chat`）生成最终回答；这个模型不可用时会报错并写进轨迹。
- 真实调用失败（网络、额度、超时）就把报错和 `run_info` 记进记录，不伪造轨迹。
- 检查器不会联网；它只看你留下的文件。

## 交付物

- `outputs/live_*.json`：真实轨迹（至少一份成功的）。
- [Day69 记录](day69_记录.md)：运行数据表、引用核对表、四道观察。


