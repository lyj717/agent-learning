# Week07 交接（2026-11-13）

## 1. 一句话状态

Week07 的服务化主线已完成：FastAPI 接口与会话、SSE 读取、标准 trace、并发/窗口限额、重试、
错误映射、容器打包、最简页面都做过独立验收；Day56 把它们接成了一个可跑的离线服务，
并留下 1/5/10 并发梯度与失败 trace 的证据。**但业务仍是人工教具**：真实模型、真实 RAG、
SSE 服务端组合与真实服务商负载都还没接入。

## 2. 现在能跑什么

```powershell
# 整合练习：5 组（success / retry / exhausted / fatal / concurrency）
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day56_integration_exercises.py
# 预期：本次 5/5

# 端到端梯度：自动起服务，跑 1/5/10 档 + 一次 504 失败 trace
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day56\day56_gradient.py
# 预期（本机实测）：1 档约 60ms；5 档约 800ms；10 档约 2.3s；失败 504，4 个 span（1 根 + 3 次尝试）

# 容器（B 段产物）
docker run -d --name week07 -p 8000:8000 week07-service:v1
Invoke-RestMethod http://127.0.0.1:8000/health
docker rm -f week07
```

测试：2026-11-13 复跑 **12 passed**（1.67 秒），命令如下；本轮用独立 basetemp，
跑完已清理，未留下 `.pytest_cache` 或临时目录。

```powershell
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest_tmp_day56 tests
```

## 3. 环境要点

- Python 3.13，虚拟环境 `.venv`；FastAPI 0.162 / uvicorn 0.54 / OpenTelemetry SDK 1.45.2。
- Docker Desktop 4.99 已安装并可运行；Docker Hub 网络不稳，构建前先确认代理/镜像加速；
  `docker` 的命令行输出只有英文。
- 所有运行输出落在各单元 `outputs/`，已被 `.gitignore` 排除；失败日志保留，不覆盖。
- Windows 上 `.pytest_tmp` 有跨账号 ACL 问题（`[WinError 5]`），必要时用管理员删除后重建。
- 演示与练习默认不请求模型、不读密钥；`model_calls=0`。

## 4. 留的尾巴

1. **真实链路未接**：Day56 服务用人工 retrieve/request 回调，没有接真实模型与真实 RAG；
   SSE 服务端也没有和这套服务组合。
2. **工具授权未接入 HTTP**：Day55 A2 的 `authorize` 只是独立函数，Day56 的 `/ask` 没调用它。
3. **502/504**：A1 做了映射并在 Day56 服务里使用，但真实上游（模型/检索）的细分与验证未做。
4. **真实服务商负载**：1/5/10 梯度只证明本机服务行为，额度、429、费用需单独小预算验证。
5. **B/C 是了解级**：Dockerfile 与页面主体由 AI 搭，学员只做验证与修改；不按掌握计。
6. **口头解释**：`day56_口头问答.md` 已写，但 Q1 的“如何区分三层”与 Q2/Q3 的细节仍偏薄，
   建议面试前重写一版。
7. **页面未容器化**：页面在本地 uvicorn 下验证，没有打进镜像。

## 5. 下一周目标与建议第一步

Week08 是评测、回归与成本：评测方法（规则匹配、LLM-as-judge、人工标注取舍）、回归测试、
成本与延迟优化、失败模式清单，最后把评测接进 CI。

建议第一步（约半天）：先读 `docs/ai-agent-12周学习计划.md` 的第 8 周，整理 Week06 已有的
评测样本、指标与脚本，确认哪些能复用、哪些要新做；先定一个 baseline 与留出集，再决定优化项。
不要先上 CI，也不要先换模型。

## 延迟复验状态

- Day51B/Day52：11 月 9 日经提示与订正核对通过，不记独立闭卷首答。
- Day53：11 月 10 日闭卷复验，经三处措辞订正通过。
- Day54～56 的机制（限额、重试、整合）尚未做跨天闭卷变式，下一周安排 10～15 分钟复现。
