# Day47｜先判内容，再汇总

本日问题固定为 dev 的 q01、q03、q06、q08，各比较 vector 和 fused，共 8 份回答。
它们分别用于观察 Day46 的退化、不变、无答案和改善情境，属于有目的的小样本，不能代表整批正确率。

## 两项人工判断看什么

| 字段 | 对照什么证据 | 何时填 true / false / null |
|---|---|---|
| answer_ok | 问题、预先的 expected、固定全文、实际回答 | 有答案题：全部必要要点都答到且没有事实错误，才填 true；漏答、答错、拒答或运行失败填 false。无答案题：明确资料不足且未编造具体答案，才填 true，否则 false |
| citation_ok | 回答里的每项实质说法、实际 cited_ids 对应的原片段与原文 | 所有实质说法都被实际引用合起来支持填 true；有任一说法缺依据、引用矛盾或只沾主题填 false；纯拒答且没有实质答案、运行失败或无可解析回答填 null |

“实质说法”指问题所问的具体操作、数值、事实等；“资料没有提供这些信息”这种拒答不单独算一项实质答案。
有答案但纯拒答：answer_ok=false、citation_ok=null。无答案且正确拒答：answer_ok=true、citation_ok=null。
回答若自称 insufficient 却又猜出一个金额，仍要按实际内容判错，不能因为状态名就放过。

回答正确和引用支持是两条独立判断：正确内容也可能没有被实际引用支持；
不完整回答里已经说出的那部分，则可能都有引用支持。
只做 JSON/编号合法性检查、或确认片段来自原文，仍不能代替这两项人工判断。

## 在哪里填

生成命令会打印新的 outputs/generate_... 目录。打开其中：

- `review_pack.md`：只读材料，逐项列出问题、expected、全文依据、候选、原始响应和被引用片段。
- `reviews.json`：你的作答区。每项只填 reviewed、answer_ok、citation_ok、reason；id/group 保留。
- `responses.json`：客观数据与原始响应，保留不改；report 会核对其摘要。

每项读完后将 reviewed 改为 true；answer_ok 填 true/false，citation_ok 填 true/false/null。
reason 用一两句话写“回答哪点对或缺了什么，实际引用能支持哪句话”，不要只写“看着没问题”。
初始 reviewed=false 表示还没判；此时 null 不能当成“引用不适用”。全 8 项完成后才能出正式汇总。

## A 的输入和返回

本题只写 `summarize_reviews(reviews)`；没有要导入的旧函数、模型调用或检索回调。
运行环境已复用的旧函数在 [answer_functions.py](../shared/answer_functions.py)，不需要再实现。

返回值顶层是 `vector`（仅向量方案）和 `fused`（融合方案），两组各自统计下面六个字段。
输入的 `group` 也是这两个值；`dev/holdout` 是题目的 `split`，不是本题的方案名称。
下面所有计数的单位都是“一份回答”，不是片段数、引用编号数或回答里的句子数。

| 返回字段 | 类型 | 具体含义与计算口径 |
|---|---|---|
| total | int | 这组有多少份已经完成人工判分的回答；无答案题和运行失败也算一份。本题遇到未评阅输入应拒绝整批汇总，不能偷偷跳过 |
| answer_correct | int | 这组 answer_ok=True 的回答有多少份；有答案题须正确答全，无答案题正确拒答也算通过 |
| answer_accuracy | float 或 None | answer_correct / total；这组没有回答时为 None |
| citation_applicable | int | 这组 citation_ok 为 True 或 False 的回答有多少份，即能够评价引用支持的回答数；None 不计入 |
| citation_supported | int | 这组 citation_ok=True 的回答有多少份；一份回答的全部实质说法都被实际引用支持，才算一份通过 |
| citation_support_rate | float 或 None | citation_supported / citation_applicable；没有可评价引用的回答时为 None |

即使一份回答引用了三个片段，citation_applicable 最多也只加 1，citation_supported 最多也只加 1。
空组仍保留全部字段：四个计数为 0，两项比率为 None。

人工数据形状示例（不是实际模型结果）：

```python
reviews = [
    {
        "id": "demo01",
        "group": "vector",
        "reviewed": True,
        "answer_ok": False,
        "citation_ok": True,
    },
    {
        "id": "demo02",
        "group": "vector",
        "reviewed": True,
        "answer_ok": True,
        "citation_ok": None,
    },
]
```

上例 vector 有两份回答，一份正确；只有一份引用可评价，且它通过。
fused 没有样本，但返回字段仍全部保留：

```python
{
    "vector": {
        "total": 2,
        "answer_correct": 1,
        "answer_accuracy": 0.5,
        "citation_applicable": 1,
        "citation_supported": 1,
        "citation_support_rate": 1.0,
    },
    "fused": {
        "total": 0,
        "answer_correct": 0,
        "answer_accuracy": None,
        "citation_applicable": 0,
        "citation_supported": 0,
        "citation_support_rate": None,
    },
}
```

回答正确率的分母是该组所有已评阅回答，包括无答案题和运行失败。
引用支持率的分母只包括 citation_ok 为 true 或 false 的回答；null 不算通过，也不进这个分母。
这是回答级的“所有实质说法均被支持”比例，不是引用编号命中率或逐条引用的准确率。

## 用量与耗时怎样读

运行环境自动记录生成请求数、失败数、usage 已记录条数、输入/输出 token、生成调用耗时。
没有 usage 不等于用了 0 token；汇总会同时显示已记录条数，不把部分已知合计叫整批总费用。
沿用旧请求层，不保留缓存命中拆分，因此用旧 cost_of_call 分别按全命中和全未命中算范围。

价格版本：2026-11-03 核对 [DeepSeek 官方价格页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)，
统一用 Flash 高峰价折算：输入缓存命中 0.04、未命中 2、输出 8 元/百万 token。
这是便于两组比较的同价换算范围，不是实际账单；模型不匹配或 usage 缺失时费用留 null。
本地检索成本没有计入。耗时仅包住一次生成调用，含网络等待；不含检索、建库、人工评阅。
Day46 未记录检索耗时，因此不会补成 0，也不能称为完整 RAG 端到端延迟。

官方资料只需对照上述价格表，以及 [响应 usage 字段](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)
中的 prompt_tokens/completion_tokens；计时 API 可查 [perf_counter](https://docs.python.org/3.13/library/time.html#time.perf_counter)。
本日演示会解释用法，不要求从头阅读整页。
