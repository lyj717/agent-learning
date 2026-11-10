# Day54 前置｜异步调度预测（先写判断，再运行核对）

2026-11-10。配合三份演示：`day54_task_order_demo.py`、`day54_await_states_demo.py`、
`day54_suspend_points_demo.py`。每题大约 10 分钟。

规则：先在“作答”处写出你**预测**的输出，再运行核对；不要先跑再抄输出。
写不出精确顺序就写“不确定 + 卡在哪一步”，比猜一个答案有用。
三题写完告诉 AI，批改在聊天里给，原答保留。

## 第 1 题：两个任务的打印顺序

```python
import asyncio


async def job(name: str) -> None:
    print(name, "起")
    await asyncio.sleep(0)
    print(name, "中")
    await asyncio.sleep(0)
    print(name, "止")


async def main() -> None:
    await asyncio.gather(job("甲"), job("乙"))


asyncio.run(main())
```

写出六行打印的完整顺序；并说明“中”和“止”为什么不是甲全部做完才轮到乙。

作答："甲","起" "乙","起" "甲","中" "乙","中" "甲","止" "乙","止"
因为在每个打印阶段后都有一个await asyncio.sleep(0)，此时会从甲切换到乙，乙打印完遇到await再切换回甲

## 第 2 题：只调用、不 await

```python
import asyncio


async def hello() -> None:
    print("hello")


async def main() -> None:
    hello()
    print("after")


asyncio.run(main())
```

写出实际输出。再回答：`hello()` 的函数体执行了吗？如果没执行，为什么 Python
还会在程序结束时报一条 `RuntimeWarning`？

作答：没有执行，只打印了一行 after，因为协程对象 hello() 被创建了，但从来没被驱动
等它被垃圾回收时，Python 报 coroutine 'hello' was never awaited

## 第 3 题：一个会挂起、一个不会

```python
import asyncio


async def quick() -> None:
    print("quick 完成")


async def other() -> None:
    print("other 前半")
    await asyncio.sleep(0)
    print("other 后半")


async def main() -> None:
    await asyncio.gather(quick(), other())


asyncio.run(main())
```

写出三行打印的顺序，并解释为什么 `quick` 没有在中间被 `other` 插进来。

再预测一个变式（不用运行）：如果给 `quick` 加一行 `await asyncio.sleep(0)`，
打印顺序会变成什么？为什么？

作答："quick 完成" "other 前半" "other 后半"
因为quick()中没有要挂起的地方，直接一次全部执行完
如果加在之前就变成"other 前半" "quick 完成" "other 后半"，如果加在后面就不会改变顺序

## 自查

- 是否每一题都先写了预测，再去运行？
- 有没有哪一步是“凭感觉”跳过的？把它写下来，批改时先讲那一步。
