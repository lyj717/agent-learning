# Day64 复验（Day66 开工前，10～15 分钟，闭卷）

闭卷：不翻演示、不翻记录。写完告诉 AI 即可，不用抄到聊天里。

### 1. host、client、server 分别是谁？一个「模型决定调用工具」的请求，从模型到工具执行要经过哪几方？

答：host是主机是使用大模型的应用，如claude code，client是客户端，在 host 内部负责说 MCP，server是服务端，是我们需要写的服务
一个「模型决定调用工具」的请求，模型给出工具调用 → host 里的 client 发 tools/call → server 执行工具函数 → 结果回到 client → 交给模型

### 2. `tools/list` 返回的 `inputSchema` 是从哪来的？如果工具描述写得很含糊，会在哪一步出问题？

答：从工具的类型注解和默认值里读来的，会在模型选工具和填参数那一步出错

### 3. 工具里 `raise ToolError("参数不对")` 之后，客户端拿到的是 Python 异常还是别的？它和 JSON-RPC 的 `error` 有什么区别？

答：拿到的是mcp的CallToolResult，里面 is_error=True、content 带原因，JSON-RPC 的 `error` 是请求本身不合法，两者区别是结果和协议错误
### 4. stdio 和 Streamable HTTP 各适合什么场景？为什么 stdio 模式下 server 不能往 stdout 打印调试信息？

答：stdio适合：本机、单用户。Streamable HTTP 适合：远程、多客户端、部署在服务器上，客户端用 HTTP 访问
stdout 是协议通道，不能当日志；服务前写一定坏，服务期间写了会丢。要输出就用 logging（默认写 stderr）。

