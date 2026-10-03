# Week 00｜Python 补齐（7 天）

**目标**：具备读懂并改写真实 Agent 项目代码的能力。
**周期**：2026-09-24 → 2026-10-03

---

## 本周交付物

**一个能跑、有 README 的 CLI 小工具** → [`chat_cli/`](chat_cli/README.md)

命令行参数 + 真实 API 调用 + 流式打印 + pytest 测试。
那份 README 里写了环境准备、密钥配置、运行命令、测试命令，以及真实的输出示例——
照着做，换台机器也能在 5 分钟内跑起来。

## 每日清单

| 天 | 主题 | 那天的代码 |
|---|---|---|
| ✅ Day 1 | 缩进语法、动态类型、f-string、真值判断 | `day01_*.py` |
| ✅ Day 2 | list/dict/tuple/set、切片、推导式、解包、深浅拷贝 | `day02_*.py` |
| ✅ Day 3 | 函数、可变默认参数陷阱、类型注解、lambda | `day03_exercises.py` |
| ✅ Day 4 | 类与 `self`、模块导入、Pydantic、Enum、`@property`、`__len__` | `day04_*.py` |
| ✅ Day 5 | 文件与 JSON、异常、虚拟环境、`.env`、logging | `day05_*.py` |
| ✅ Day 6 | 生成器、装饰器、`async/await`、`asyncio.gather` | `day06_*.py` |
| ✅ Day 7 | 串烧实战：把前六天拼成一个工具 | `day07_api_demo.py`、`chat_cli/` |

> 唯一没专门练过的是 `*args` / `**kwargs`——只在 `day04_class_demo.py` 的
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
