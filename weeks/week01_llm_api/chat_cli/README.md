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
