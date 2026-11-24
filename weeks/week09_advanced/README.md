# Week 09｜进阶方向 A：MCP Server

**阶段交付物**：一个别人可以安装、配置、真正用起来的 MCP Server——把本地 Markdown 笔记
做成带行号出处的全文检索，配上工具、资源与提示词模板，带 README、测试和 CI。

## 当前接续：Week08 已验收（2026-11-21），本周选 A｜MCP Server

Week08 的评测三件套、CI 与阶段验收见
[Week08 HANDOFF](../week08_evaluation_reliability/HANDOFF.md)。按该交接，本周不重做评测，
也不为了「多做一个方向」铺开 B/C/D；B/C/D 只作了解。

本周要回答的是三个问题，答案写进 Day64 记录，后面每天都拿它自查：

1. **给谁用**：谁会在自己的模型应用里装这个 server？
2. **解决什么问题**：不装它，这个人现在怎么干活、哪里麻烦？
3. **最小可用接口**：第一版只暴露哪几个工具/资源，为什么是这几个。

## 复用已有能力，不另起一套业务

| 已有资产 | 本周怎么用 |
|---|---|
| `notes/` 下 4 份真实学习笔记（约 52 KB） | 检索语料，不新造假数据 |
| Day 24 的 `search_notes`、Day45 的关键词检索 | 检索思路与「带出处的命中」返回结构 |
| Day 25 的路径白名单与权限边界 | 拒绝目录穿越、拒绝绝对路径的判据 |
| Week06 的 `run_logged` | 每次运行的 `console.log` / `run_info.json` |
| Week08 Day62 的 `.github/workflows/ci.yml` | 第 68 天往里加 MCP 的离线检查 |

不重做 RAG，不接向量库：本周的检索就是关键词 + 行号，够用、可解释、别人的机器上
不用下载模型。

## 本周排期：7 个自然日

按 3～5 小时/天估，本周约 **4.5～5.5 天**学习工作量，铺在 7 天里，留 **1.5～2.5 天**
缓冲（复习、排错、真实宿主联调、发布返工）。数字是排期估计，不是实测耗时。

| 单元 | 主要任务 | 主机制 | 预计自然日 |
|---|---|---|---|
| Day64 | 三角色与三原语；最小 server + 客户端两种连法；手写 JSON-RPC 帧；实现第一批工具 | MCP 的 server/client 分离与工具注册 | 约 3/4～1 天 |
| Day65 | 文件检索工具：多目录、行号出处、路径边界、编码与空文件 | 检索业务 + 路径安全 | 约 1 天 |
| Day66 | 资源与提示词：把笔记暴露成 `note://`，再加一个可复用提示词；错误语义 | 三原语中的 resources / prompts | 约 3/4 天 |
| Day67 | 打包成可安装项目：pyproject、入口命令、宿主配置、README | 可交付性 | 约 1/2～3/4 天 |
| Day68 | pytest：进程内 client + stdio 冒烟；接进 GitHub Actions | 测试与 CI | 约 1/2～3/4 天 |
| Day69 | 真实宿主（Inspector / 自建 host + 真实模型）跑通一次问答，留轨迹 | 端到端集成 | 约 1/2～3/4 天 |
| Day70 | 阶段变式、口头解释、HANDOFF | 阶段验收 | 约 1/2 天 |

只做一个方向、一个 server；B/C/D 不排任务。每天仍按 3～5 小时，不靠延长学时补进度。

## 官方文档去哪看（先读这几节）

- **MCP 官方站**：<https://modelcontextprotocol.io/>。先读「Get started」与
  「Architecture」两页：它讲清 host / client / server 三个角色、三种原语和 JSON-RPC 2.0
  这条消息层。这是本周唯一权威来源。
- **Python SDK v2 文档**：<https://py.sdk.modelcontextprotocol.io/v2/>。按顺序读
  **First steps**（三原语与 `MCPServer`）、**The Client**（`Client` 的四种连法、
  `list_tools` / `call_tool` 的返回结构）。
- **迁移页**：<https://py.sdk.modelcontextprotocol.io/v2/migration/>。只读
  「FastMCP renamed to MCPServer」一节，知道网上大量 1.x 教程为什么直接报
  `ModuleNotFoundError`。
- **测试页**：<https://py.sdk.modelcontextprotocol.io/v2/get-started/testing/>，
  第 68 天写测试前读。

本周装的是 `mcp==2.3.0`（2.x）。2.x 把 `FastMCP` 改名为 `MCPServer`，协议新增
2026-07-28 这一代（`server/discover`），旧的 2025 握手时代仍由同一个 server 兼容。
读到 1.x 教程（`from mcp.server.fastmcp import FastMCP`）时先换算，不要照抄。

## Day64：三角色、工具注册与两条连法（2026-11-21 开工，11-22 验收）

**完成情况**：检查器 **13/13**（学员亲跑，AI 复跑一致）；三份演示均亲跑，记录里的
`2026-07-28`、`2025-11-25`、工具名与日志目录已转录。三问与六道观察第一次批改后
订正通过（观察 3、4、6 与三问 2 各改一处）。工具层用 `ToolError` 转出参数错误，
第 9～11 组客户端能看到具体原因。练习骨架里的「第 64 题」提示已清理，`ruff` 与格式
检查通过。留两点：观察 4 对「schema 由谁生成」的表述仍偏「读了参数名」，Day66 讲
schema 时再收一次；记录里写的宿主是 DeepSeek Harness，是否支持接 MCP 要到 Day69 验证。

**今天只引入一个机制**：MCP 的 server 与 client 是两个进程/两个角色，中间说 JSON-RPC；
工具由 server 声明、由模型（通过 host）调用。工具怎么设计、资源与提示词、打包与发布
都排到后面几天。

**预计 3/4～1 天**，工作量主要在：读两页文档、跑三份演示、按接口写两个函数并注册成工具。
第一次接触协议，读文档和对照「客户端看到什么」的时间要算进去，不按 AI 写代码的速度估。

顺序：

1. 打开 [Day64 记录](demos/day64/day64_记录.md) 顶部的「开始之前」：只读 SDK 的
   First steps 一页（约 10 分钟，看哪三个小标题那里写了），再写三问；每题 1～2 句，
   记录里给了一个别的题目的示例。
2. 跑 [概念与工具演示](demos/day64/day64_mcp_hello_demo.py)：进程内连一个 server，
   看 `tools/list` 里的 `inputSchema` 是怎么从函数签名长出来的，以及工具报错为什么
   不抛异常、而是变成 `is_error=True` 的结果。
   前四节是背景；赶时间只看第五～七节（工具定义、一次调用、三种失败）。
3. 跑 [stdio 演示](demos/day64/day64_mcp_stdio_demo.py)：客户端拉起一个**子进程** server，
   走真实的 stdio 传输。注意 server 的 stdout 就是协议通道。
4. 跑 [协议帧演示](demos/day64/day64_mcp_wire_demo.py)：不用 SDK 客户端，手写
   `initialize` / `tools/list` / `tools/call` 的 JSON，看清楚 SDK 替你做了什么。
   同一个 server，SDK 客户端拿到 `2026-07-28`，手写帧拿到 `2025-11-25`，把原因写进记录。
5. 打开 [题目说明](demos/day64/day64_题目说明.md)，在
   `projects/mcp_server/` 的骨架里实现 `find_matches` 并注册 `search_text` 工具。
   先单独测函数，再跑检查器；两条命令都在题目说明的「跑法」里。
6. 跑检查器，13 组应全过：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day64\day64_mcp_hello_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day64\day64_mcp_stdio_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day64\day64_mcp_wire_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day64_mcp_exercises.py
```

预期：三份演示各自打印协议版本、工具清单与调用结果；检查器打印 13 组逐项结果与合计，
最后一行为「全过 13/13」。

预算：**0 次模型调用**，全部离线。每次运行在 `demos/day64/outputs/` 下新建目录，
保存 `console.log`、`run_info.json`；`DAY64_RUN_ORIGIN` 默认 `unconfirmed`，
AI 验证标记 `ai_validation`，不冒充分学员亲跑。

## Day65：文件检索工具与路径边界（2026-11-22 开工，11-23 验收）

**完成情况**：A 8/8、B 10/10、C 4/4，合计 **22/22**（学员亲跑三份日志，AI 全量复跑一致）。
`safe_subdir` 用 resolve 后 relative_to 判父子；`search_files` 全局 limit、跳过坏编码与空文件、
先校验后扫描；`search_notes` 每次调用读 `NOTES_ROOT`。五道观察经一轮订正通过：第 3 题原先
想用 print 告知跳过文件，改为「必须走返回值」；第 4 题补上 limit 契约。练习提示与「第 65 题」
标记已清理，`ruff` 与格式检查通过。

**预计约 1 天**：两件新东西——文件层（遍历、编码、出处）与路径边界（resolve +
relative_to），再把它注册成工具。读演示与跑检查器的时间要算进去。

顺序：

1. **先做 10～15 分钟 [Week08 复验](demos/shared/week08_review.md)**（闭卷，三件套）。
2. 读 [文件层演示](demos/day65/day65_scan_demo.py)：排序、`source` 为什么用相对 POSIX 路径、
   空文件与坏编码怎么处理、`limit` 为什么是全局的。
3. 读 [路径边界演示](demos/day65/day65_path_safety_demo.py)：`..` 与绝对路径分别怎么逃出去、
   为什么字符串查两点不够、判据为什么在 `resolve()` 之后。
4. 打开 [题目说明](demos/day65/day65_题目说明.md)，实现 `safe_subdir`（A）→ 跑 `--part a`；
   再实现 `search_files`（B）→ 跑 `--part b`；最后注册 `search_notes`（C）→ 跑 `--part c`。
5. 三部分一起跑一遍，22/22；把结果与日志目录抄进 [Day65 记录](demos/day65/day65_记录.md)，
   再答五道观察题。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day65\day65_scan_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day65\day65_path_safety_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part b
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py --part c
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day65_file_search_exercises.py
```

预期：A 8/8、B 10/10、C 4/4，合计 22/22。

数据：检查器用 `demos/day65/corpus/` 的固定语料（含一个空文件、一个坏编码文件、一个空目录）；
第 22 组用仓库真实的 `notes/`，只要求至少一条、出处是相对 `.md`。预算 **0 次模型调用**。
每次运行在 `demos/day65/outputs/` 下新建目录，保存 `console.log`、`run_info.json` 与
`results.json`；`DAY65_RUN_ORIGIN` 默认 `unconfirmed`，AI 自验标 `ai_validation`。

## Day66：资源、提示词与错误语义（2026-11-23 开工，11-24 验收）

**完成情况**：A 11/11、B 10/10，合计 **21/21**（学员全量运行，AI 复跑一致）。
`note://index` + `note://{+path}` 两个资源、`review_note` 提示词、`read_note` 工具都已注册；
错误形态分清：工具失败是 `is_error` 结果，资源/提示词失败是 `MCPError`（未知 URI `-32602`、
处理器异常 `-32603`）。五道观察经一轮改写通过（第 4、5 题问法先改清楚，第 2 题把「异常给谁看」
改准）。收尾发现并修正：说明写成行尾注释时 description 为空，已改回 docstring；脚手架已清，
`ruff` 与格式检查通过。

**预计约 3/4 天**：两件新东西——资源（具体资源 vs 模板、`{+path}`）与提示词（用户在宿主里挑），
外加把三种原语的失败形态归位。读三份演示的时间要算进去。

顺序：

1. **先做 10～15 分钟 [Day64 复验](demos/shared/day64_review.md)**（闭卷）。
2. 读 [资源演示](demos/day66/day66_resources_demo.py)：清单与模板为什么分开、`{+path}` 的作用、
   读不到时客户端拿什么。
3. 读 [资源怎么被用掉](demos/day66/day66_resource_flow_demo.py)：宿主先读资源、把正文拼进消息
   与模型自己调工具，两条路径并排看。
4. 读 [提示词演示](demos/day66/day66_prompts_demo.py)：参数表、渲染成的消息、失败形态。
5. 读 [错误形态演示](demos/day66/day66_error_shapes_demo.py)：同一个「读笔记」走工具/资源/提示词，
   三者的结果与异常并排看。
6. 打开 [题目说明](demos/day66/day66_题目说明.md)，实现 A 的三个文件函数 → `--part a`；
   再注册资源、提示词、工具 → `--part b`；最后全量 21/21。
7. 把结果与日志目录抄进 [Day66 记录](demos/day66/day66_记录.md)，答五道观察题。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day66\day66_resources_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day66\day66_resource_flow_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day66\day66_prompts_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day66\day66_error_shapes_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py --part b
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day66_resources_exercises.py
```

预期：A 11/11、B 10/10，合计 21/21。

数据：沿用 Day65 的固定语料 `demos/day65/corpus/`（含子目录、坏编码与空文件）。
预算 **0 次模型调用**；每次运行在 `demos/day66/outputs/` 下新建目录，
保存 `console.log`、`run_info.json`、`results.json`。
`DAY66_RUN_ORIGIN` 默认 `unconfirmed`，AI 自验标 `ai_validation`。

## Day67：打包与宿主配置（2026-11-24 开工，11-24 验收）

**完成情况**：检查器 **18/18**（A 8、B 8、C 2；学员全量运行，AI 复跑一致）。
仓库根 `pyproject.toml`（入口点 `notes-mcp-server = "projects.mcp_server.server:main"`、
`packages = ["projects", "projects.mcp_server"]`）、`projects/__init__.py`、
README 的三份宿主配置与 MIT `LICENSE` 都已就位。四道观察经一轮订正通过：第 1 题从
「环境变量找入口」改为「包已装进 site-packages、import 按模块路径找到」；第 3 题把
`notes_root()` 从「传递者」改回「读取者」。收尾去掉骨架注释并修正 BOM；`ruff`、格式与
`pytest 17 passed` 通过。

**预计 1/2～3/4 天**：不写新的 MCP 机制，做交付层。主要时间在 pyproject 的字段对齐、
README 的三份宿主配置和许可证选择；检查器不安装，18 组都是静态检查 + 一次模块冒烟。

顺序：

1. 读 [打包演示](demos/day67/day67_packaging_demo.py)：元数据/入口点/包发现、三份宿主配置的差别、
   `NOTES_ROOT` 由谁传，以及仓库现在还缺什么。
2. 打开 [题目说明](demos/day67/day67_题目说明.md)，按字段表写 `pyproject.toml` 和
   `projects/__init__.py` → `--part a` 8/8。
3. 填 `projects/mcp_server/README.md` 模板、选许可证并放 `LICENSE` → `--part b` 8/8。
4. 跑全量 18/18；想亲眼看入口命令的话按题目说明里的可选安装步骤试一次，失败也记录。
5. 把结果与日志目录抄进 [Day67 记录](demos/day67/day67_记录.md)，答四道观察题。

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\demos\day67\day67_packaging_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week09_advanced\exercises\day67_packaging_exercises.py
```

预期：18/18（A 8、B 8、C 2）。

数据：检查器只读文件、跑一次 `python -m projects.mcp_server.server` 冒烟；**0 次模型调用**。
每次运行在 `demos/day67/outputs/` 下新建目录，保存 `console.log`、`run_info.json`、
`results.json`；`DAY67_RUN_ORIGIN` 默认 `unconfirmed`。

## Day68：测试与 CI（待开工）

pytest：进程内 `Client(mcp)` 的确定性检查 + 一条 stdio 冒烟（带超时，防止挂死）；
把 MCP 的检查接进 `.github/workflows/ci.yml` 的 offline job。预计约 1/2～3/4 天。

## Day69：真实宿主跑通（待开工）

用 MCP Inspector（`npx @modelcontextprotocol/inspector`）或自建 host + 真实模型，
就 `notes/` 里的内容问一个真问题，留下面板截图/轨迹、工具调用参数与最终回答。
**没看到真实宿主里工具被调用之前，不写「别人可以用」。** 预计约 1/2～3/4 天。

## Day70：阶段变式与交接（待开工）

MCP 协议闭卷复验、三件套口头解释（给谁用/怎么用/出问题怎么办）、写 HANDOFF。
预计约 1/2 天。

## 复验安排

| 时间 | 内容 | 时长 | 状态 |
|---|---|---|---|
| Day65 开工前 | Week08 闭卷复现：规则/裁判/测量三件套，题目见 [Week08 复验](demos/shared/week08_review.md) | 10～15 分钟 | [ ] |
| Day66 开工前 | Day64 闭卷复现：三角色、schema、失败形态、两条传输，题目见 [Day64 复验](demos/shared/day64_review.md) | 10～15 分钟 | [ ] |
| Day69 开工前 | MCP 阶段变式：换一个真实问题走一遍工具选择与调用（题目当天给） | 10～15 分钟 | [ ] |

到期未做先补或改期，写进下面的「计划校准」，**没发生的不勾**。

## 计划校准

| 日期 | 计划 | 实际 | 偏差与动作 |
|---|---|---|---|
| | | | |

## 必做顺序

- [x] Day64：协议与工具注册，13 组检查
- [ ] 复习：Day65 前 Week08 闭卷复现（10～15 分钟）
- [x] Day65：文件检索与路径边界
- [ ] 复习：Day66 前 Day64 闭卷复现（10～15 分钟）
- [x] Day66：资源、提示词与错误语义
- [x] Day67：打包与宿主配置
- [ ] Day68：测试与 CI
- [ ] Day69：真实宿主跑通并留证
- [ ] Day70：阶段变式与口头解释

## 验收标准

- 能说清 host / client / server 各是谁、谁发起调用、JSON-RPC 在中间干什么
- 能解释 `tools/list` 里的 `inputSchema` 从哪来，以及「工具描述写得含糊」会让模型怎么错
- 能说清工具失败为什么返回 `is_error=True` 而不是抛异常；协议错误和工具错误不是一回事
- 能说清 stdio 与 Streamable HTTP 各自的适用场景，以及为什么 stdio 下不能往 stdout 打印
- 别人按 README 能装上并配置进一个真实宿主，工具在宿主里真的被调用过（有轨迹）
- 有测试、有 CI、有失败路径；说明覆盖不到的风险，不承诺「测过就绝不出错」
- 阶段末能对「MCP 解决什么问题、不解决什么问题」做 3 分钟口头解释

## 范围与暂不做

- 不做 OAuth / 多租户 / 远程部署；本地 stdio 为主，HTTP 只做了解与一次本地验证。
- 不接向量检索、不重做 RAG；语料就是 `notes/` 的 4 份 Markdown。
- 不为了「看起来完整」堆工具；工具数量按真实用途定，宁少勿滥。
- B/C/D 三个方向只作了解，不排任务、不计入验收。
- 发布到 GitHub 的 push 由学员执行；AI 不 push，只报本地领先几个提交。



