# Week 07｜工程化与可观测性

**交付物**：用 FastAPI 包装、带完整 trace 的 Agent 服务。

## 当前接续：Day51A 已验收，下一步 Day51B（2026-11-06）

Day51A 于 11 月 5 日开工、11 月 6 日完成本次经答疑订正的验收：严格请求模型、
HTTP 路由登记与调用、框架校验和业务拒绝。学员已确认亲跑 A 11/11、B 12/12，
客观数据见 [Day51A 记录](demos/day51/day51a_记录.md)；原始日志和学员作答保留。

开工时按 Day50 的反馈将 **Day51 整体暂估为两个自然日，每天 3～5 小时**：
A 约一天、B 暂估另一天；这是排期估计，未记录实际学习小时，替代历史表中的 3/4 天。
下一步在 Day51B 开工时细化已有 RAG、日志、会话边界与真实端口启动的整合，B 尚未开工。

- [x] Day46/47 到期短复验完成（11 月 6 日；第 1 题经术语答疑，第 2 题计数与分母正确，已提醒小数舍入）
- [x] HTTP 请求、框架调用与校验边界经代码和观察核对
- [x] A 11 组、B 12 组对照通过并确认亲跑，AI 转录客观数据
- [x] 三道观察经答疑订正验收，清理练习长题干；收尾检查见下文

回看入口：[学习路线与接口速查](demos/day51/day51_学习路线.md)、
[完成的练习](exercises/day51_http_exercises.py)。四份独立演示与全部运行命令保留在学习路线。
本阶段用 add_api_route 显式登记函数；路由演示经补讲后展示双方代码及
“发送→函数执行→收到响应”的实际顺序。题干已清理，接口说明留在学习路线。

环境已装 FastAPI 0.162.0、Starlette 1.10.0，沿用 httpx 0.28.1 与 Pydantic 2.13.5；
新增依赖在根 requirements.txt 固定。TestClient 在进程内经过实际框架处理，不监听端口；
本阶段没有检索或模型请求，也不据此声称会话隔离和真实网络服务已完成。

11 月 6 日收尾证据：清题干后从仓库根和练习目录复查四个 A/B 入口，两次均为
A 11/11、B 12/12；Week07 Ruff 与格式检查通过，现有离线测试 12 passed（2.57 秒）。
练习执行逻辑、已启用导入、学员记录和原始日志保持；只清本轮 AI 验证与测试临时数据。

开工时的脚手架、错误变体和依赖验证，以及路由讲解缺口与订正经过，见根
[FAILURES.md](../../FAILURES.md)；不把 AI 试跑当作学员实验。

## Day50 验收记录

Day50 于 2026-11-04 开工，11 月 5 日完成经答疑订正的验收。按
[Week06 交接](../week06_retrieval_eval/HANDOFF.md)，先给已有 RAG 路径补请求 ID、
结构化阶段日志和失败定位，再包装 HTTP 服务；本日未提前算作服务或标准 trace 已完成。

**原开工预计约半个自然日、2～3 小时**，包含前置复习、演示、独立实现、排错与观察；
这是当时的排期估计，未记录实际学习小时。

**2026-11-05 学员反馈订正：半天明显低估。** Day50 还需要适应从工具使用者转为工具
作者，理解可调用对象、函数与结果、参数固定，以及调用双方的职责；这些此前较少独立
使用，不能按“代码短、复用旧 RAG”略去。若重排，应先为这一前置安排约一个自然日的
独立学习与练习，再另估日志应用和整合；这不是补记实际耗时，也不要求重做 Day50。
Day51 现已按上述两步重估；会话边界仍留待 Day51B 的整合验收。

- [x] Day45 到期短复验完成：Precision@2 分母经答疑订正，不记独立闭卷首答通过
- [x] A 5/5、B 8/8 代码对照通过，裸 raise 与校验阶段边界经订正验收
- [x] 学员亲跑 A 5/5、B 8/8，客观数据已从对应日志转录
- [x] 三道观察通过；异常消息泄露路径经答疑补充，原答与学员订正保留
- [x] AI 清理练习长题干、保留一行 docstring；Ruff、格式与现有测试检查通过

11 月 5 日收尾证据：清理后 A 5/5、B 8/8；Week07 Ruff 与格式检查通过；
现有离线测试 12 passed（1.76 秒）。学员函数执行 AST、启用的导入、观察与原日志保持。
开工的旧残留清理、前置教学缺口、首轮检查及订正过程见根
[FAILURES.md](../../FAILURES.md)，此处以当前验收结果为准。

## Day50 回看入口

- [JSONL 演示](demos/day50/day50_jsonl_demo.py)：字典→JSON 字符串→追加成行→逐行解析。
- [请求 ID 演示](demos/day50/day50_request_id_demo.py)：同一次请求关联阶段事件与失败类型。
- [action 演示](demos/day50/day50_action_demo.py)：函数赋值、传参、调用与固定参数。
- [raise 对照](demos/day50/day50_reraise_demo.py)：捕获后继续抛出时的回溯差异。
- [完成的练习](exercises/day50_trace_exercises.py)：A 包装动作，B 接通四阶段与空候选短路。
- [接口与阶段边界](demos/day50/day50_接口.md)、[学员记录](demos/day50/day50_记录.md)。
- [公共旧函数](demos/shared/rag_functions.py)：原样集中已验收的消息组装与回复校验实现。

命令从仓库根目录运行，全部离线，无新增依赖：

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day50\day50_jsonl_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day50\day50_request_id_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day50\day50_action_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day50\day50_reraise_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day50_trace_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day50_trace_exercises.py --part b
```

每次运行新建 `demos/day50/outputs/模式_时间_后缀/`，保存 console.log、run_info.json，
A/B 另存 events.jsonl、checks.json。失败与旧轮次保留；输出目录不提交 Git。
默认 origin=unconfirmed，亲跑由学员确认；AI 试跑显式标 ai_validation，不当学员实验。
本课回调为人工教具，model_calls=0；阶段 ok 与 JSON/引用编号通过不证明语义正确。
题干已清理，完整接口保留在独立说明中；学员已经启用的导入保持启用。

配套阅读：[Python 3.13 json](https://docs.python.org/3.13/library/json.html) 看 dumps/loads
与 JSON 分帧说明；[uuid4](https://docs.python.org/3.13/library/uuid.html#uuid.uuid4) 看 UUID
和 hex；[perf_counter](https://docs.python.org/3.13/library/time.html#time.perf_counter)
看秒数差值；[OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
只读 trace/span 关系，对照后续标准追踪，本日不安装 SDK。

## 本阶段预算与后续安排

Week07 以约四个自然日为协调目标，每天仍按 3～5 小时。下表保留**开工时初版估计**：
11 月 5 日 Day50 低估反馈后，整版不能继续作为当前工期承诺；Day51～56 须在开工前按
真实掌握程度重估。必要前置、角色适应、复习、排错与订正都计入，先合并重复与非核心，
仍超量则如实调整跨度，不能硬挤进原先四天。
复用已验收 RAG 与旧重试/超时机制；HTTP/SSE/追踪各自先拆开学，再由学员接入。

| 单元 | 主要任务 | 初版估计（历史值，待重估） |
|---|---|---|
| Day50 | 请求关联与结构化阶段日志；Day45 短复验 | 原估约 1/2，已确认低估 |
| Day51 | FastAPI 请求/响应与会话边界；复用一条已有问答路径 | 约 3/4 |
| Day52 | SSE 流式、断开与部分输出；到期短复验 | 约 1/2 |
| Day53 | 接一种标准 trace 工具，复用字段定位失败 | 约 1/2 |
| Day54 | 并发上限、限流与旧重试组合；按实测梯度找瓶颈 | 约 1/2 |
| Day55 | 安全失败路径、容器打包与最简页面交付 | 约 3/4 |
| Day56 | 新情境整合验收、口头解释与交接 | 约 1/2 |

初版合计约四个自然日，未计足 Day50 的陌生前置，不能据此认定只剩三天半的工作；
后续以开工时的新估计为准。每推进 3～4 个新单元的复习时间原分配在 Day53/56，
不以重复抄写、额外界面打磨或多追踪工具凑任务。
若容器条件尚未具备，先准备并核对配置，真实构建/启动验证如实留待完成，不伪报通过。

复验接续（11 月 6 日更新）：Day45 已于 11 月 5 日经答疑订正完成，Day46/47 于
11 月 6 日核对完成；均保留实际首答与答疑边界。Day48 在 11 月 6～7 日窗口内，
拟接在 Day51B 开工前做 10～15 分钟新情境判断，未完成不打勾。
Day50 于 11 月 5 日验收，11 月 7～8 日安排 10～15 分钟闭卷复现成功/失败事件与请求关联，
阶段末再做变式；延迟复验尚未发生，不提前勾选。
Day51A 于 11 月 6 日验收，11 月 8～9 日安排 10～15 分钟闭卷复现路由登记、
请求模型与 422/400 边界，阶段末再做变式；本项尚未发生。
Week06 的权限约束尾项并入本周会话与检索边界检查，JD、简历、正式视频沿用延后安排。

## 必做顺序

- [x] 请求 ID、结构化阶段日志与失败定位（Day50，11 月 5 日经答疑订正验收）
- [ ] 先做 FastAPI 接口、请求校验与会话隔离
- [ ] 再接流式返回（SSE），核对断开、超时和部分输出的处理
- [ ] 接一种 trace 工具，复用已有轨迹字段，每次调用都能查到链路
- [ ] 限流、重试与并发上限；从单请求逐步增加负载
- [ ] 安全：提示词注入、工具越权、密钥管理、输出过滤
- [ ] 准备容器环境、打包并验证安装与启动说明
- [ ] 最简前端：能对话、能看引用、能看耗时即可

## 选修与范围

界面打磨、语义缓存、多种追踪工具对比暂不必做。成本与延迟优化留到 Week 08 依据瓶颈选择。真实服务商测试先核对额度与限流；假模型压测只能说明本地服务表现。

## 验收标准

- [ ] 给出实际测试的并发梯度、样本量与瓶颈分析，不强行追求 50 并发
- [ ] 从一次失败请求找到对应 trace，检查会话隔离和日志脱敏
- [ ] 在干净环境验证 README；尚未完成的部署或环境验证如实标记
