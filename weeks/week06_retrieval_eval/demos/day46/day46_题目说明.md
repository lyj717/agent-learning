# Day46 A｜把单题检索比较扩展到一批题

本题已于 2026-11-03 完成当次验收，以下保留原需求与接口说明；实现见练习文件。

你已经写过单题评分、整批汇总、关键词排序和 RRF。今天只写 `compare_retrievals`：
接收一批题目，对其中每一道开发题比较“仅向量”和“融合”，返回逐题结果及两份整批汇总。
评分规则沿用 Day43，关键词与融合沿用 Day45。

## 要做的：看清输入是什么

| 参数 | 类型与来源 | 代表什么 |
|---|---|---|
| `cases` | 环境传入的 `list[dict]` | 一批已经标好的题，可能同时包含 dev 与 holdout |
| `chunks` | 环境传入的 `list[Document]` | 固定资料的**全部片段**，用于关键词检索和相关标注映射 |
| `vector_search` | 环境传入的函数 | 调用 `vector_search(问题文字, k)`，取得该问题的向量候选编号列表 |
| `k` | `int`，默认 `3` | 每路最多取几条，以及最终按前几条评分；人工检查也会传其他值 |
| `rank_constant` | `int`，默认 `60` | 传给旧 RRF 函数的分母常量；人工检查也会传其他值 |

`cases` 中的一道题长这样：

```python
{
    "id": "demo01",  # 这道题的编号
    "split": "dev",  # dev 要评测，holdout 跳过
    "question": "在哪里登记？",  # 传给检索函数的问题文字
    "answerable": True,  # 已经根据原文确认有答案
    "evidence": [  # 答案依据在原文的什么位置
        {"source": "guide.md", "line_start": 1, "line_end": 1}
    ],
}
```

**按 `split` 判断是否为开发题。** `id` 的值是 `demo01`、`q01` 这样的题号。
原文已确认没有答案的题，`answerable=False`、`evidence=[]`；它仍可能属于 dev，仍需要检索和记录。

`vector_search` 已经由环境准备好，你不需要定义它，也不需要自己加载模型或建库。
例如 `vector_search("在哪里登记？", 3)` 可能返回 `["parking.md#L1-L1"]`。
它返回的是**已按向量相似度排好序的片段编号列表**。每道 dev 调用一次，
这一份列表同时用于仅向量组的评分和融合组的 RRF 输入。

## 提示：要复用哪些函数

六个名字已在练习文件中预留导入，实际实现集中在
[evaluation_functions.py](../shared/evaluation_functions.py)。详细异常与参数类型见各函数 docstring。

| 旧函数 | 本题中用来做什么 |
|---|---|
| `project_relevance(evidence, chunks)` | 用本题原文依据和全库片段，取得全部相关编号，返回 `set[str]` |
| `rank_keywords(question, chunks, limit=k)` | 对同一全库做关键词检索，返回关键词排名 `list[str]` |
| `fuse_rankings(vector_ids, keyword_ids, limit=k, rank_constant=rank_constant)` | 合并两份编号榜，返回融合排名 `list[str]` |
| `score_query(ranked_ids, relevant_ids, k=k)` | 计算一种排名在本题的指标，返回单题指标字典 |
| `evaluate_queries(samples, k=k)` | 汇总一种方案在全部开发题上的表现，返回整批指标字典 |
| `check_ranked_ids(value, allowed, limit=k)` | 检查向量回调的列表类型、数量、重复与未知编号；`allowed` 传全库片段 id 的集合，成功返回 `None` |

`evaluate_queries` 的 `samples` 是一个列表，其中每项都要有这两键：

```python
{"ranked_ids": ["parking.md#L1-L1"], "relevant_ids": {"guide.md#L1-L1"}}
```

两份汇总分别针对**同一批开发题的向量排名**和**同一批开发题的融合排名**。
无答案题也放进这两批样本，由旧函数负责单列计数、排除出有答案题均值。

## 期望结果：返回的三层结构

最外层是一个字典，恰好三个键，**三者处于同一层**：

| 顶层键 | 类型 | 内容 |
|---|---|---|
| `rows` | `list[dict]` | 每道 dev 一条结果，按输入中的原顺序排列 |
| `vector_summary` | `dict` | 仅向量方案的整批汇总，沿用 `evaluate_queries` 返回结构 |
| `fused_summary` | `dict` | 融合方案的整批汇总，沿用 `evaluate_queries` 返回结构 |

`rows` 是**列表**：没有开发题就为 `[]`，有一道就装一个字典，有多道就装多个字典。
每个字典恰好八个键：

| 每题字段 | 类型 | 放什么 |
|---|---|---|
| `id` | `str` | 输入题目的 id |
| `question` | `str` | 输入题目的 question |
| `relevant_ids` | `list[str]` | 全部相关编号；把映射得到的集合按编号升序保存 |
| `vector_ids` | `list[str]` | 本题那一次向量检索得到的有序编号 |
| `keyword_ids` | `list[str]` | 旧关键词函数得到的有序编号 |
| `fused_ids` | `list[str]` | 旧 RRF 函数得到的有序编号 |
| `vector_metrics` | `dict` | 对本题向量排名调用 `score_query` 的完整结果 |
| `fused_metrics` | `dict` | 对本题融合排名调用 `score_query` 的完整结果 |

注意类型区别：`project_relevance` 返回集合，`score_query` 和 `evaluate_queries` 接收相关编号集合；
报告中的 `relevant_ids` 则按要求保存为有序列表，便于写入 JSON。

### 一道题时的完整返回示例

以下是 **AI 人工说明数据**，只展示返回结构，不是本次开发集结果。
假设只有上面的 `demo01`，k=3，相关片段为 guide；向量榜仅有 parking，关键词榜仅有 guide，
融合榜为 guide、parking。片段都属于假设的全库，文件名不指向仓库真实文件。

```json
{
  "rows": [
    {
      "id": "demo01",
      "question": "在哪里登记？",
      "relevant_ids": ["guide.md#L1-L1"],
      "vector_ids": ["parking.md#L1-L1"],
      "keyword_ids": ["guide.md#L1-L1"],
      "fused_ids": ["guide.md#L1-L1", "parking.md#L1-L1"],
      "vector_metrics": {
        "retrieved_count": 1, "relevant_count": 1, "matched_count": 0,
        "hit": 0, "recall": 0.0, "precision": 0.0
      },
      "fused_metrics": {
        "retrieved_count": 2, "relevant_count": 1, "matched_count": 1,
        "hit": 1, "recall": 1.0, "precision": 0.3333333333333333
      }
    }
  ],
  "vector_summary": {
    "total": 1, "answerable_count": 1, "no_answer_count": 0,
    "mean_hit": 0.0, "mean_recall": 0.0, "mean_precision": 0.0,
    "no_answer_with_candidates": 0
  },
  "fused_summary": {
    "total": 1, "answerable_count": 1, "no_answer_count": 0,
    "mean_hit": 1.0, "mean_recall": 1.0, "mean_precision": 0.3333333333333333,
    "no_answer_with_candidates": 0
  }
}
```

两份 summary 描述整批题，放在 `rows` 列表外面。有多道题时，`rows` 增加元素，顶层仍是这三个键。

## 还要满足的验收条件

- **参数先检查**：`k` 和 `rank_constant` 都是正整数，`bool` 不算。非法时抛 `ValueError`，空批次也检查。
- **整批开发题先检查**：重复的 dev **题目 id**，或有答案却无法映射到任何全库片段，均抛 `ValueError`。
  任一道 dev 有这两类问题时，本次向量回调调用次数应为 0，不能先处理完前面的正常题才发现。
- **留出题跳过**：holdout 不检索、不评分、不放进 `rows` 或任何汇总。
- **无答案开发题保留**：相关集合为空，仍运行检索，记录候选与旧指标函数的结果。
- **回调结果检查**：调用给定的 `check_ranked_ids`。错误类型抛 `TypeError`；重复、超量或未知编号抛 `ValueError`。
  检索自身抛出的其他异常原样向外抛，由日志环境保存失败现场。
- **空批次返回完整结构**：`rows=[]`，两份 summary 都保留旧汇总函数的完整字段；没有有答案题时均值为 `None`。
- **使用传入的值**：两路候选上限、融合最终上限与评分都用当前 `k`，RRF 用当前 `rank_constant`；不改输入数据。

实现后先运行练习 `--part a` 核对人工场景；通过后运行 `--part batch`，再写本日记录的三道观察。
