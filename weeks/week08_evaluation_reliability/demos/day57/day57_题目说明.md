# Day57 题目说明：规则判分与基线回归

本页是 [练习](day57_eval_exercises.py) 的完整题面补充：调用点、全部判分情形与提示。
完整判定规则、参数和返回结构在下面 A、B 两节；练习文件已清理为函数实现与类型注解。

## 数据从哪里来

| 文件 | 内容 | 是否可改 |
|---|---|---|
| `day57_cases.json` | 8 道笔记问答的题面、必含要点、禁词、本次检索到的片段编号 | 不改；这是本轮评测集 |
| `day57_answers_v1.json` | 上一版系统对这 8 题的回答（status、answer、cited_ids） | 不改；用来复现基线 |
| `day57_answers_v2.json` | 这一版系统对同样 8 题的回答 | 不改；本轮被评测对象 |
| `day57_baseline.json` | 上一版逐题判定结果（含已知失败），已冻结 | 不改；`--part regression` 的对照物 |

数据是教学样本，不请求模型。q01～q08 的问题对应 `notes/python-notes.md` 的速查表；
引用编号只用于检查「有没有编造编号」，不判断片段是否支持结论。

## A：`judge_answer(case, answer)`

调用点：`--part a` 的检查器逐组调用 `judge_answer(case, answer)`，每组另查输入未被改动。
返回 `{"id": str, "passed": bool, "failed": list[str]}`；`failed` 只能取
`empty_answer`、`not_answered`、`missing_points`、`forbidden_text`、`no_citation`、
`citation_not_retrieved` 这六个名字，出现其他名字算错。

`failed` 是**列表**，不是单个字符串；通过时是空列表 `[]`，不是 `None`、空字符串，
也不能省略这个键。每种失败项最多出现一次，顺序按上面的判定顺序。

参数 `case` 的字段（判分只用后三个）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | `str` | 题号，原样写进返回值 |
| `question` | `str` | 问题原文，判分不使用 |
| `must_include` | `list[str]` | 回答里必须逐项出现的要点 |
| `must_not_include` | `list[str]` | 回答里一旦出现就记 `forbidden_text` |
| `retrieved_ids` | `list[str]` | 本次检索到的片段编号 |

参数 `answer` 的字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `status` | `str` | 正常回答为 `"answered"`，其他值记 `not_answered` |
| `answer` | `str` | 回答正文；去掉首尾空白后为空记 `empty_answer` |
| `cited_ids` | `list[str]` | 回答引用的片段编号，顺序不参与判定 |

每题的实际规则字段（`--part a` 的检查器也会逐题打印）：

| 题号 | `must_include` | `must_not_include` |
|---|---|---|
| q01 | `["sorted(", "key=", "reverse=True"]` | `[]` |
| q02 | `["d.get"]` | `[]` |
| q03 | `["None", "is None"]` | `["def f(x=[])"]` |
| q04 | `["join"]` | `[]` |
| q05 | `["def ", "->", "list[str]"]` | `[]` |
| q06 | `["Field", "default_factory"]` | `[]` |
| q07 | `["*args", "**kwargs"]` | `[]` |
| q08 | `["key=lambda", "x[field]"]` | `[]` |

| 情况 | 返回值 |
|---|---|
| 通过 | `{"id": "q01", "passed": True, "failed": []}` |
| 失败 | `{"id": "q03", "passed": False, "failed": ["missing_points", "forbidden_text"]}` |

| # | 情形 | 输入要点 | 期望 `failed` |
|---|---|---|---|
| 1 | q01 的 v2 回答 | 三个要点齐全，引用合法 | `[]` |
| 2 | q02 的 v2 回答 | 用 `d.get`，引用合法 | `[]` |
| 3 | q03 的 v2 回答 | 缺 `None`/`is None`，且踩 `def f(x=[])` | `["missing_points", "forbidden_text"]` |
| 4 | q04 的 v2 回答 | 含 `join`，引用合法 | `[]` |
| 5 | q05 的 v2 回答 | `def `、`->`、`list[str]` 齐全 | `[]` |
| 6 | q06 的 v2 回答 | `Field` 与 `default_factory` 齐全 | `[]` |
| 7 | q07 的 v2 回答 | `*args` 与 `**kwargs` 齐全 | `[]` |
| 8 | q08 的 v2 回答 | 要点齐全但 `cited_ids` 为空 | `["no_citation"]` |
| 9 | status 为 `insufficient` | 引用为空 | `["not_answered"]` |
| 10 | 回答只有三个空格 | 引用合法 | `["empty_answer"]` |
| 11 | 引用 `notes/python-notes.md#L99-L100` | 该编号不在检索结果，其余合格 | `["citation_not_retrieved"]` |
| 12 | q03 回答 `def f(x=[]) 就行。` | 同时缺要点、踩禁词 | `["missing_points", "forbidden_text"]` |
| 13 | q01 正确回答但 `cited_ids=[]` | 其余合格 | `["no_citation"]` |
| 14 | 同一编号引用两次 | 编号都在检索结果里 | `[]`（重复不算失败） |

提示：

- 先把两个短路条件（status、空白回答）处理掉，再按固定顺序追加失败项；
  不要用 `if/elif` 把多个失败项吞成一个。
- 判断「不在检索结果里」时，先把 `retrieved_ids` 转成 set。
- 只比较字面子串，不要改写回答、不要做同义词匹配。

## B：`compare_baseline(baseline, current)`

调用点：`--part b` 的检查器逐组调用；`--part regression` 还会用真实两版结果调用。
返回 `{"regressed": list[str], "fixed": list[str], "still_failing": list[str],
"unchanged_pass": list[str]}`，每个列表按题号升序。

参数 `baseline` / `current`：都是 `dict[str, dict]`，键是题号；内层至少含
`"passed": bool`，可带 `"id": str`、`"failed": list[str]` 等附加键，本题只读 `passed`。

| 返回字段 | 类型 | 含义 |
|---|---|---|
| `regressed` | `list[str]` | 上次通过、这次失败 |
| `fixed` | `list[str]` | 上次失败、这次通过 |
| `still_failing` | `list[str]` | 两次都失败 |
| `unchanged_pass` | `list[str]` | 两次都通过 |

| # | 情形 | 输入要点 | 期望 |
|---|---|---|---|
| 1 | 两版相同 | 八题都 `passed=True` | 前三个列表空，`unchanged_pass` 为八题 |
| 2 | 只修好 q02 | baseline 的 q02 为 False | `fixed=["q02"]` |
| 3 | 只改坏 q03 | current 的 q03 为 False | `regressed=["q03"]` |
| 4 | 一修好一改坏 | baseline q02=False，current q03=False | `fixed=["q02"]`、`regressed=["q03"]` |
| 5 | 两次都失败 | 两版 q08 都为 False | `still_failing=["q08"]` |
| 6 | 输入顺序打乱 | baseline 按 q03、q01、q02、q04 插入，current 另一种顺序 | `still_failing=["q02", "q04"]`、`unchanged_pass=["q01", "q03"]`，均升序 |
| 7 | 题号集合不同 | baseline 两题，current 一题 | `ValueError` |
| 8 | passed 是字符串 `"yes"` | baseline 的 q01 | `TypeError` |
| 9 | 两版都是空字典 | `{}` 与 `{}` | 四个列表都为空 |

提示：

- 先校验两个参数的类型、题号集合和内层 `passed`，通过后再分类；
  不要分类到一半才发现类型不对。
- 用 `type(value) is bool` 判断，`1` 不能当 `True`。
- 四个列表返回前都 `sorted()`；空输入返回四个空列表。

## 跑完看什么

`--part a`：14 组结果 + 14 组输入检查，不一致应为 0。
`--part b`：9 组结果 + 9 组输入检查，不一致应为 0。
`--part regression`：先看「基线自检」的 regressed/fixed 是否为空，
以及 still_failing 是否正好是基线里的已知失败；再看「本次变化」。

观察写在 [记录](day57_记录.md)；运行日志在每次新建的 `outputs/` 目录，
失败也保留，不覆盖历史。
