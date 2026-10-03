# chat_cli

一个命令行小工具：**把一个问题交给它，它调用模型，把回答一个字一个字打印出来。**

---

## 怎么跑起来（换台机器也照这个来）

> 验收标准：别人照着这一节，五分钟内能把工具跑起来。

### 1. 环境

需要 Python 3.11 以上（开发时用的是 3.13.9）。在**仓库根目录**执行：

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

这个工具只用到四个包——`openai`、`httpx`、`python-dotenv`、`pydantic`，
`requirements.txt` 里都已经包含。

### 2. 密钥

在仓库根目录执行：

```bash
copy .env.example .env
```

然后打开生成的 `.env`，把三个值换成真实的：

| 变量 | 填什么 |
|---|---|
| `LLM_API_KEY` | 服务商给你的密钥（OpenAI / DeepSeek / 通义千问 任选其一） |
| `LLM_BASE_URL` | 该服务商的接口地址，比如 `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名，比如 `deepseek-v4-flash` |

`.env` 已经被 `.gitignore` 屏蔽，**不会**被提交到仓库。

### 3. 运行

在**仓库根目录**执行：

```bash
.venv\Scripts\python.exe weeks\week00_python\chat_cli\chat_cli.py "用一句话说明什么是 RAG"
```

真实输出（边生成边打印，所以你会看到字一个个冒出来）：

```
RAG（检索增强生成）是一种让大模型在回答前先检索外部知识库的相关信息，
再基于检索结果生成更准确、可溯源回答的技术。
```

常用开关：

```bash
... chat_cli.py "介绍一下你自己" --system "你只说一句话"   # 换人设
... chat_cli.py "1+1 等于几" --no-stream                  # 不要打字机效果
... chat_cli.py "你好" --model deepseek-chat              # 换模型
... chat_cli.py "你好" --verbose                          # 打 DEBUG 日志，看请求细节
... chat_cli.py --help                                    # 看全部参数
```

### 4. 测试

测试要在 `chat_cli` 目录里跑（那里有自己的 `pytest.ini`，负责让测试能 import 到 `llm.py`）：

```bash
cd weeks\week00_python\chat_cli
..\..\..\.venv\Scripts\python.exe -m pytest -v
```

预期结果：**3 passed**。

---

## 它由哪几块组成

```
chat_cli/
├── chat_cli.py       命令行入口：接参数、配日志、把各块串起来
├── llm.py            和模型打交道：拼请求、发请求、解析回复
├── tests/test_llm.py 测试（测 llm.py 里的纯逻辑）
└── pytest.ini        测试配置（让测试能 import 到 llm.py）
```

分成两个文件是有意的：`llm.py` 不碰命令行、不打印任何东西，
所以它容易被测；`chat_cli.py` 只管和「人」打交道。

---

## 用到了前面学的哪些东西

> 这一节是「对着代码讲三分钟」的提纲。

| 用到的知识 | 在这个项目里体现在哪 | 学了第几天 |
|---|---|---|
| argparse 命令行参数 | `chat_cli.parse_args()` | Day 7 前置（`argparse_demo.py`） |
| Pydantic 请求结构 | `llm.build_request()` | Day 4 |
| dotenv 读密钥 | `llm.require_api_key()` | Day 5 |
| logging 打日志 | `chat_cli.setup_logging()` | Day 5 |
| 生成器 / 流式输出 | `llm.stream_chat()` | Day 6 |
| pytest 测试 | `tests/test_llm.py` | Day 7 前置 |

---

## 已知的不足与下一步

> 诚实列出做不到的事，比假装完美更像工程。

- 只支持单轮问答，不支持多轮对话（每次提问都是独立的一次请求）
- 网络超时没有重试，失败了就直接报错退出
- 日志只打在屏幕上，没有写进文件
- 只能在终端里跑，还没做成 Web 服务
