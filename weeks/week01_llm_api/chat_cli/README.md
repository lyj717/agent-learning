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

## 这个目录里有什么

```
chat_cli/
├── chat_cli.py            命令行入口（你要写）——REPL 与命令处理
├── conversation.py        对话历史（你要写）——多轮的地基
├── llm.py                 和模型打交道（已给）——发请求、返回文本与 usage
├── cost.py                价格表与成本估算（你要写）——从 Day 9 搬过来
├── tests/                 验收测试（已给）
└── pytest.ini             测试配置
```

## 还没做的（TODO）

- **流式打印**（Day 11）：现在是一次性输出，等模型把话说完才显示；要改成打字机效果
- **出错容错**（Day 12）：`main` 里还没包 `try/except`——断网、限流、密钥错都会把程序打断，
  而且失败的问句会留在历史里。代码里留了 `TODO(Day 12)` 的书签
- **上下文裁剪**（Day 12）：历史会一直涨，聊得越久每次发的 token 越多，需要「超过 N 轮就丢最早的」
