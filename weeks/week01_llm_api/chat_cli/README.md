# chat_cli（Week 01 交付物）

一个能**连续聊天**的命令行机器人。跟 Week 00 那个单轮小工具比，它多了三样：

- 多轮对话：自己维护 messages 历史，每次请求整段发过去
- `/clear`：清空上下文，但保留 system 人设
- `/cost`：随时看本次会话累计的 token 和花费

流式打印（Day 11）和上下文裁剪 / 失败重试（Day 12）还没接，README 会跟着更新。

## 怎么跑

在**仓库根目录**执行：

```bash
cd weeks\week01_llm_api\chat_cli
..\..\..\.venv\Scripts\python.exe chat_cli.py
```

启动后直接打字提问；打 `/` 开头的看命令：

| 命令 | 作用 |
|---|---|
| `/remember 我叫刘小明` | 把这条事实存进本地文件，以后每次请求都带着它（长期记忆） |
| `/clear` | 清空对话历史（system 人设留着） |
| `/cost` | 打印本次会话累计的 token 与估算花费 |
| `/exit` | 退出 |

想换人设或模型：

```bash
..\..\..\.venv\Scripts\python.exe chat_cli.py --system "你只说一句话" --model deepseek-flash
```

## 自测

```bash
cd weeks\week01_llm_api\chat_cli
..\..\..\.venv\Scripts\python.exe -m pytest -v
```

测试是我（AI）写好的验收标准，红了就是还没写对。

### PyCharm 报「未解析的引用」怎么办

如果在 PyCharm 里看到 `from conversation import Conversation` 标红（未解析的引用），
**那不是代码错**。`import conversation` 要求 chat_cli 在模块搜索路径上，命令行跑测试
时是 `pytest.ini` 里那行 `pythonpath = .` 在起作用——但 PyCharm 的静态检查不看这一行，
只认「源码根」，所以找不到模块名，就标红。

修法：右键 `chat_cli` 目录 → `Mark Directory as` → `Sources Root`（目录会变蓝）。
之后 `conversation`、`llm`、`cost` 都能被认出来。

要留意的是：这个标记只存在 `.idea/` 里，而 `.idea/` 已被 `.gitignore` 屏蔽——
换台机器要重新点一次。运行时（`pytest` 和 `python chat_cli.py`）不受影响。

## 架构说明

> 写给人看的：这个工具由哪几块组成、一次请求从哪走到哪。
> 下面是引导问题，用你自己的话填（可以画箭头，比段落更清楚）。

**一次提问，数据是怎么流动的？**（命令行 → 程序 → 模型 → 屏幕）

- `chat_cli.py`：接命令、分流、循环
- `conversation.py`：拼 messages、裁剪、换人设
- `llm.py`：发请求、重试、流式；对外只给文字片段
- `cost.py`：把 token 数换成钱
- `memory.py`：事实存哪、怎么拼回 system

**为什么要拆成这几个文件？**

- `conversation.py`、`cost.py`、`memory.py` 都不碰网络、不读命令行、不打印，所以能脱离网络单独测
- 分工明确，出问题时容易定位到是哪一层

## 使用方法

见上面「怎么跑」。注意：**退出程序后就是新对话**（历史不落盘），要让它长期记住什么，用 `/remember`。

## 已知限制

> 诚实列出做不到的事，比假装完美更像工程。参考问题：

- 上下文裁剪是「丢最早的」——用户问「一开始说的那件事」时，模型会不记得。
- 记忆是「全塞进 system」——事实攒到几百条同样会导致越来越贵，越来越慢
- 重试只包了「拿到流对象」那一步——已经吐出半截文字时网络断了，用户的历史和模型的对话都会丢失
- 模型写的回答没有留痕（没有日志文件），出问题很难溯源


## 讲解提纲

> 录视频前先在这里写 3~5 行提示词，照着讲，别念代码。参考结构：

1. 一句话说清这个工具干什么（10 秒）
2. 演示：连续问三句、`/cost` 看一眼、`/clear` 之后再问（60 秒）
3. 讲一个设计决定 + 为什么（比如「为什么要 trim」「为什么记忆拼进 system」）（60 秒）
4. 讲一个踩过的坑 + 怎么发现的（30 秒，`FAILURES.md` 里挑一条）
5. 已知限制 + 下一步（20 秒）

## 这个目录里有什么

```
chat_cli/
├── chat_cli.py            命令行入口（你要写）——REPL 与命令处理
├── conversation.py        对话历史（你要写）——多轮的地基
├── llm.py                 和模型打交道（已给）——发请求、返回文本与 usage
├── cost.py                价格表与成本估算（你要写）——从 Day 9 搬过来
├── memory.py              简易长期记忆（你要写）——事实存本地文件、拼进 system
├── tests/                 验收测试（已给）
└── pytest.ini             测试配置
```

## 还没做的（TODO）

- ✅ **流式打印**（Day 11 已完成）：回答现在是边收边打的
- ✅ **出错容错**（Day 12）：断网、限流、超长输入都不崩；Ctrl+C 干净退出；失败那轮不进历史
- ✅ **上下文裁剪**（Day 12）：`conversation.trim(MAX_TURNS)`，超过 8 轮丢最早的
- ✅ **简易长期记忆**（Day 13）：`memory.py` + `/remember`，事实存 `facts.json`、每轮拼进 system
