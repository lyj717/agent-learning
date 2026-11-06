# Day51 学习路线

Day51 整体先估约两个自然日（每天 3～5 小时），按 Day50 的反馈重新估计，
包含角色适应、读报文、独立实现、排错、复验和观察。这次只布置 Day51A，约一个自然日。
Day51B 暂估另一天；待 A 验收后再细化已有 RAG、日志、会话隔离与真正端口启动的范围。

2026-11-06 接续：Day51A 的 A/B 与三道观察已经答疑订正验收，练习长题干已清理；
下方保留原学习顺序供回看，成品接口见“完成后的接口速查”。下一步为尚未开工的 Day51B。

## 这一次以什么身份写代码

你写服务端的处理函数，客户端发 HTTP 请求，FastAPI 找到登记的函数并调用。
自己调用函数，与客户端通过接口请求函数，是两种入口。
先看“谁提交数据、谁校验、谁调用、谁返回”这条关系；不预先假定看过装饰器就已熟练。

本次主要新机制是 **框架把 HTTP 请求交给已登记的函数**。
用 add_api_route 显式展示 endpoint 接收哪个函数；@ 装饰器的等价写法后续按需补。
Pydantic 沿用旧知识，新增的是它在请求进入函数前进行校验的位置。

## 阅读与操作顺序

1. 在 [记录](day51a_记录.md) 写两道 Day46/47 到期短复验，先不翻旧答案。
2. 运行 [HTTP 报文](day51_http_demo.py)：只构造人工请求/响应，不发网络。
3. 运行 [路由登记](day51_route_demo.py)：登记不执行，匹配请求才由框架调用。
   本文件也明确说明 TestClient(app) 和 client.get/post 的最小用法。
4. 运行 [请求体](day51_body_demo.py)：JSON → 模型实例 → 处理函数；422 在函数之前。
5. 运行 [HTTPException](day51_http_exception_demo.py)：主动抛出怎样变成错误响应。
6. 到 [练习文件](../../exercises/day51_http_exercises.py) 先完成 A 请求模型，再完成 B 小接口。
   原题旁曾列全输入、输出与状态边界；验收后集中保留在下方接口速查，无需读验收器。
7. 告知已运行，AI 读取日志转录客观数据；三道观察由你写在记录中。

第一段建议先做到“能说明路由函数由谁、何时调用”，再进入请求体和 A/B。
不要求一次读完四份。每份演示自己的最小应用独立运行，不导入下一份的业务实现。

11 月 6 日路由答疑时曾先停在第 3 步：按重排后的输出对照双方代码，
看清 app.add_api_route 建立规则、client.get 提交请求，以及 ①发送、②函数执行、③收到响应。
HTTP 是通信规则，FastAPI 是服务端框架，TestClient 是本地测试客户端；先理清这三个角色。
随后学员完成请求模型、小接口和观察，并订正调用者及空字符串的长度约束解释。

## 完成后的接口速查

从练习模块取得 QuestionRequest、create_app，所需 FastAPI/Pydantic 名字已在模块中导入。

- QuestionRequest.model_validate(字典) 返回 QuestionRequest 实例，校验不合格抛
  pydantic.ValidationError。question 必填、严格 str、最少 1 字符，模型层不 strip；
  top_k 为严格 int、默认 2、范围 1～4；不接收额外字段。
  实例用 .question/.top_k 取值，.model_dump() 返回含这两个字段的字典。
- create_app() 无参数，每次返回一份新 FastAPI 应用。处理函数由学员定义和登记，
  FastAPI 在请求匹配且校验通过后调用；测试客户端只需取得应用并提交请求。

| 方法与路径 | 客户端输入 | 成功响应正文 |
|---|---|---|
| GET /health | 无业务数据 | {"status": "ok", "mode": "offline"} |
| POST /inspect | JSON 顶层为 question 与可选 top_k | 清理首尾空白后的 question、top_k、character_count |

POST /inspect 的最小输入 {"question":" 地点 "} 对应成功正文
{"question":"地点","top_k":2,"character_count":2}，状态码 200。
模型校验失败为 422；字符串通过模型但 strip 后为空，由业务函数抛 HTTPException，
状态码 400、detail="question 不能只有空白"；错误方法为 405，未知路径为 404。
HTTPException 从 fastapi 导入。上述输入均为人工数据，不运行检索或模型。

## 命令（仓库根目录）

```powershell
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51\day51_http_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51\day51_route_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51\day51_body_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\demos\day51\day51_http_exception_demo.py
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day51_http_exercises.py --part a
.venv\Scripts\python.exe -B -X utf8 weeks\week07_production\exercises\day51_http_exercises.py --part b
```

## 输出与数据从哪里来

每次在本目录 outputs/ 下新建目录，保存 console.log、run_info.json；A/B 另存 checks.json，
B 的逐请求方法、路径、提交 JSON、状态码和响应体在 requests.jsonl。
默认来源 unconfirmed；告知亲跑后由 AI 核对，AI 试跑标为 ai_validation。
原始失败和旧轮次保留。记录中的两格结果来自 checks.json；观察 1/3 来自对应演示 console，
观察 2 来自 B 的 requests.jsonl 与你自己的源码，均有可运行的数据来源。
全部案例是人工数据，TestClient 在进程内执行真实框架处理，不建立实际 HTTP/socket 连接；
本阶段没有模型请求，也未据此验收真正网络服务或会话隔离。

## 官方文档读哪几节

- [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)：
  只读 path、operation、path operation function 和返回内容，理解路径/方法/函数的关系。
  官方示例用 @app.get，先看作用，本课显式登记的代码更便于看清函数从哪里传入。
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/)：
  只读 Using TestClient，以及 get/post、json 参数；对应本课本地发送器。
- [Request Body](https://fastapi.tiangolo.com/tutorial/body/)：
  只读 Create your data model、Declare it as a parameter、Results，
  对应 JSON 怎样变成处理函数参数。
- [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)：
  只读 Use HTTPException 和 resulting response，对应主动拒绝与状态码。
