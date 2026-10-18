# Week 00｜Python 补齐（7 天）

**目标**：具备读懂并改写真实 Agent 项目代码的能力。
**周期**：2026-09-24 → 2026-10-03

> 这一周的完整交接见 [`HANDOFF.md`](HANDOFF.md)——下一个对话从这里读起。

---

## 本周交付物

**一个能跑、有 README 的 CLI 小工具** → [`chat_cli/`](chat_cli/README.md)

命令行参数 + 真实 API 调用 + 流式打印 + pytest 测试。
那份 README 里写了环境准备、密钥配置、运行命令、测试命令，以及真实的输出示例——
照着做，换台机器也能在 5 分钟内跑起来。

## 每日清单

| 天 | 主题 | 那天的代码 |
|---|---|---|
| ✅ Day 1 | 缩进语法、动态类型、f-string、真值判断 | `demos/day01/`、`exercises/day01_exercises.py` |
| ✅ Day 2 | list/dict/tuple/set、切片、推导式、解包、深浅拷贝 | `demos/day02/`、`exercises/day02_exercises.py` |
| ✅ Day 3 | 函数、可变默认参数陷阱、类型注解、lambda | `exercises/day03_exercises.py` |
| ✅ Day 4 | 类与 `self`、模块导入、Pydantic、Enum、`@property`、`__len__` | `demos/day04/`、`exercises/day04_*.py` |
| ✅ Day 5 | 文件与 JSON、异常、虚拟环境、`.env`、logging | `demos/day05/`、`exercises/day05_exercises.py` |
| ✅ Day 6 | 生成器、装饰器、`async/await`、`asyncio.gather` | `demos/day06/`、`exercises/day06_exercises.py` |
| ✅ Day 7 | 串烧实战：把前六天拼成一个工具 | `demos/day07/day07_api_demo.py`、`chat_cli/` |

2026-10-18 目录整理：演示按天放在 `demos/dayNN/`，练习集中在 `exercises/`；
命令行参数演示位于 `demos/argparse/argparse_demo.py`。Day 5 的 JSON 样例和输出
位于 `demos/day05/`，完整项目 `chat_cli/` 保留原目录结构。

> 唯一没专门练过的是 `*args` / `**kwargs`——只在 `demos/day04/day04_class_demo.py` 的
> 装饰器那一节露过一次。记在这儿，等 Week 04 读框架源码时补上。

## 顺手沉淀下来的两份东西

它们不属于哪一天，但这一周用得最多：

- [`notes/python-notes.md`](../../notes/python-notes.md) 里的「我要干什么 → 用什么」速查表
  ——按需求查写法，不按术语查
- [`notes/卡住了怎么办.md`](../../notes/卡住了怎么办.md) 的六招排查法
  ——卡住时照着走，别在原地空转

## 验收标准

- [ ] 换台机器照 README 能在 5 分钟内跑起来
- [ ] 能对着自己的代码连续讲 3 分钟不卡壳
- [x] 密钥没有进过仓库

第三条已经自查过：

```
git log -p --all | findstr API_KEY
```

历史里只有占位符（`sk-xxxx`）和测试用的假数据（`sk-abc123`），没有真实密钥。

---

详细知识点见 `docs/python-7天补齐清单.md`。
