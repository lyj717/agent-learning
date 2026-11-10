# Day51B / Day52 到期短复验（先闭卷 20～30 分钟）

2026-11-09。两项各约 10～15 分钟：Day51B 的会话分组、新旧应用独立、空证据/异常边界；
Day52 的完成信号、EOF、主动停止、部分文本与读超时。

先不翻旧记录、旧源码，也不要运行代码。按题面写判断即可，考察的是换输入后还能不能
说清机制，不要求重写框架。答完告诉 AI，批改在聊天里给，原答保留。

## A｜Day51B（约 10～15 分钟）

已验收的 `create_chat_app(retrieve_fn, request_fn, emit)` 每次调用返回一份新应用，
应用内部用一个字典按 `session_id` 分组保存历史，历史只供读取，不送进模型。

### 1. 状态放在哪一层

依次做三件事：

1. 创建 `app1 = create_chat_app(...)`，用 `client1 = TestClient(app1)` 向 `session_id="甲"` 提一个问题；
2. 用 `client2 = TestClient(app1)` 再向 `session_id="甲"` 提一个问题；
3. 创建 `app2 = create_chat_app(...)`，用 `client3 = TestClient(app2)` 查询 `session_id="甲"` 的历史。

写出第 3 步之前 `client2` 查询“甲”会得到几条历史、第 3 步中 `client3` 会得到几条，
并说明历史到底存在哪一层、换客户端和换应用各有什么影响。

作答：会得到两条历史；会得到0条历史
历史存在应用层，换客户端并不会覆盖原来的历史
换应用会新建一个新的历史同时保留原来的历史

### 2. 空证据与检索失败

同一应用上有两组 `/ask` 请求，编号都用 `session_id="乙"`：

- A 组：`retrieve_fn` 正常返回空列表 `[]`；
- B 组：`retrieve_fn` 抛出 `TimeoutError`。

分别写出两组的 HTTP 状态码、是否追加历史、`request_fn` 被调用几次、
返回体里的 `checked` 是什么。再说明为什么“检索结果为空”仍算一次正常轮次，
而“检索抛异常”不算。

作答：A:200，追加历史，调用0次 checked是None B：500，不追加历史，调用0次 没有checked字段
检索结果为空是合法输出，算正常轮次，检索抛异常是在执行过程中遇到的异常，不能算正常轮次

### 3. 边界：并发与会话顺序

如果两个 `/ask` 请求几乎同时打同一个 `session_id`，历史里两条的先后顺序能严格保证吗？
本次 Day51B 的验收证据能支持“并发下会话记录仍然正确”这个说法吗？说明理由。

作答：不能严格保证。不能支持“并发下会话记录仍然正确”这个说法
day51b并没有做并发相关的限制

## B｜Day52（约 10～15 分钟）

`read_answer_stream(base_url, mode, stop_after=None)` 返回固定三键
`{"state": str, "text": str, "error_type": str | None}`，`text` 保留已经收到的文字；
客户端用 `timeout=READ_TIMEOUT`（0.5 秒）读取，先检查 HTTP 状态再逐条解析事件。

### 1. 没有 done 的 EOF

服务端依次发出 `delta`（text 为 `a`）、`delta`（text 为 `b`），随后连接正常关闭，
但始终没有发 `done` 事件；客户端读到 EOF 就结束读取。

写出返回的 `state`、`error_type`、`text`，并说明：为什么不能因为“收到了文字、
连接也是正常关闭的”就判成 `completed`？

作答："state": "incomplete", "text": "ab", "error_type": None
只有发出done才能真正说明连接正常关闭

### 2. 主动停止与空文本

`mode=normal` 会依次发 4 个非空 `delta`，最后发 `done`；调用时 `stop_after=2`。

写出返回的 `state`、`error_type`、`text`，以及客户端在第 2 个非空 `delta` 之后
应当做什么（对循环和响应）。再回答：若服务端在第 1 个和第 2 个非空 delta 之间
插入一个 `text` 为空字符串的 `delta`，停止时机会不会提前？

作答： "state": "interrupted","text"为前两个非空dalta的内容 ,"error_type": None,
客户端在第 2 个非空 `delta` 之后应当直接返回，停止时机不会提前
### 3. 三种失败不是一回事

表格里的三种情况都发生在流式读取阶段。分别填写函数是返回三键字典还是抛异常；
返回的话写出 `state`、`error_type`，并说明 `text` 会是什么。

| 情况 | 返回还是抛异常 | state                | error_type | text                 |
|---|---------|----------------------|------------|----------------------|
| ① `slow` 模式中途触发本地 `httpx.ReadTimeout` | 返回   |    error                         | type(error).__name__ | 原text |
| ② 服务端发来一个 `error` 事件 | 返回      | error                | event["data"]["error_type"] | 原text      |
| ③ 服务端直接返回 HTTP 500 | 异常      | 无                    | 无          | 无                    |

补充回答：这里的 0.5 秒限制的是什么时间？它是不是“整个请求必须在 0.5 秒内完成”？

作答：本地读取的限制，不是

## 批改前先自查

- 两道题都写完后，再回看旧记录核对一次，把“当时没想到”的点记在下面；
- 如果某题只能写出结论、说不清原因，直接写“只记得结论”，不要补猜。

补充记录（可选）：
