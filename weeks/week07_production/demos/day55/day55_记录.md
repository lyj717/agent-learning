# Day55｜安全失败路径与交付记录

2026-11-10 开工。Day55 整体重估为约 1～1.5 个自然日，先做 A1（错误映射与信息暴露，约 1～1.5 小时）。
本机没有 Docker，容器段只准备配置，不伪报验证通过。

## A1：错误映射与信息暴露

先读 [错误暴露演示](day55_error_leak_demo.py)（从 demonstrate 读起），
再在 [A1 练习](../../exercises/day55_error_exercises.py) 实现 `error_response`；
五组情形与期望正文都写在函数题面里，不需要打开检查器。

### 客观运行数据（确认亲跑后由 AI 转录）

| 入口 | 本轮目录 | 完成结果 | 来源确认 |
|---|---|---|---|
| 错误暴露演示 | `outputs/error_leak_demo_20261110_210845_466733_40630709` | completed | 未确认（unconfirmed） |
| A1 练习 | `outputs/error_exercise_20261110_211824_817641_d1c4747b` | 5/5 通过 | 学员亲跑（按日志转录） |

| 情形 | 传入异常 | 期望状态码 | 实际状态码 | 实际正文 | 通过 |
|---|---|---|---|---|---|
| timeout | TimeoutError | 504 | 504 | 上游超时 + request_id | True |
| connection | ConnectionError | 502 | 502 | 上游连接失败 + request_id | True |
| bad_value | ValueError | 400 | 400 | 请求不合法 + request_id | True |
| unknown | KeyError | 500 | 500 | 内部错误 + request_id | True |
| runtime | RuntimeError | 500 | 500 | 内部错误 + request_id | True |

五组正文都只有 `detail` 和 `request_id` 两个键，异常消息里的密钥、路径与堆栈均未出现。

状态码取 status，正文取 body，异常取 error；逐组 JSON 与 error_checks.json 都在本轮目录里。

### 观察与判断（学员填写）

1. 为什么 500 的正文不能直接放 `str(exc)`？举一个你在这道题里见过的泄露内容。

   作答：异常信息中可能存在敏感信息。演示中泄露了密钥

2. 超时映射成 504、连接失败映射成 502，如果两者都写成 500，对调用方排查会有什么影响？

   作答：排查更加困难，更难定位问题所在

## 后续状态

A1 已验收（五组 5/5，两道观察核对通过）。A2 权限与注入边界、B 容器配置、C 最简页面
尚未交付；容器验证受本机 Docker 缺失限制，届时如实记录“未验证”。
