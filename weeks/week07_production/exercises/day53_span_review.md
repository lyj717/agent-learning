# Day53 追踪到期短复验（先闭卷 10～15 分钟）

2026-11-10。范围：span 的父子与 trace 关联、正常/失败状态、异常消息不落记录。
先不翻旧记录、旧源码，也不运行；答完告诉 AI，批改在聊天里给，原答保留。

## 第 1 题：三段在同一条轨迹里

已有外层 `request_work`，里面依次调用两个阶段 `retrieve`（正常返回）和 `generate`
（动作抛 `TimeoutError`），两个阶段都用本题的 `trace_stage` 包装，外层也由同一个 tracer
创建。`trace_stage` 只给本段写 `request_id`、`stage`，异常时另写 `error_type`。

1. 三段各自的 `parent_span_id` 指向谁？三段的 `trace_id` 是否相同？
2. `generate` 结束后的状态是什么？它的属性里有哪些键？会不会写入异常消息？
3. `request_work` 的状态默认是什么？它会不会因为内层 `generate` 失败而自动变成 ERROR？
4. 调用方拿到的 `TimeoutError` 对象和 span 里的记录是什么关系？

作答：
1：request_work的parent_span_id指向更外层，更外层没有就为None，另外两段parent_span_id指向request_work，三者的`trace_id`相同
2：`generate` 结束后的状态是ERROR，属性里有request_id，stage和error_type，属性里没有异常消息
3：默认是 StatusCode.UNSET，不会因为内层 `generate` 失败而自动变成 ERROR
4：span 里只记类型名 "TimeoutError"，原异常对象继续沿调用栈抛给调用方

## 第 2 题：两组对照

A 组：没有外层段，动作正常返回空正文和空引用：`{"answer": "", "citations": []}`。
B 组：没有外层段，动作抛 `ValueError("人工敏感标记")`。

两组都用 `trace_stage` 包装，`record_exception` 与 `set_status_on_exception` 保持关闭。

1. A 组返回的字典和动作给的字典是同一个对象吗？span 状态是什么？
2. B 组的状态和 `error_type` 是什么？异常消息会不会进入属性或状态描述？
3. 两组各自是根段还是子段？`parent_span_id` 是什么？

作答：
1：是同一个，span状态为OK
2：状态为ERROR，error_type为ValueError，异常信息不会进入属性或状态描述
3：都各自是根段，parent_span_id是None