"""本周旧函数集中入口：实际实现沿用学员已验收代码。

函数索引：
chunk_documents：Week05 Day37，全文按行切块，供 Day44 查看固定版本片段。
score_query：Week06 Day43 A，单题编号级指标，供 Day44 旧基线回放。
evaluate_queries：Week06 Day43 B，有答案题逐题平均，供后续整批比较。
project_relevance：Week06 Day44 A，原文依据映射到当前全库编号，供 Day45 探查。
Day45 的关键词排名和融合函数由学员在本次练习实现。
"""

from langchain_core.documents import Document


def project_relevance(evidence: list[dict], chunks: list[Document]) -> set[str]:
    """把原文依据映射为同源、行范围相交的片段编号集合（原 Day44 A）。

    evidence（list[dict]，必填）：每项含 source:str、line_start:int、line_end:int，
    表示固定原文的来源与闭区间行号，不是检索结果或片段编号。
    chunks（list[Document]，必填）：待核对的全部片段，id 为编号，metadata 含上述三键。
    输入字段由调用环境预先校验；不在此重复校验，也不改变输入。
    返回 set[str]：同源且至少共享一行的片段 id，重复命中去重；空输入或无相交返回空集合。
    相交允许只覆盖部分依据，不代表必要事实全部找齐；缺字段等异常原样抛出。
    """
    set_id = set()
    for e in evidence:
        for chunk in chunks:
            if e["source"] == chunk.metadata["source"] and max(
                e["line_start"], chunk.metadata["line_start"]
            ) <= min(e["line_end"], chunk.metadata["line_end"]):
                set_id.add(chunk.id)
    return set_id


def chunk_documents(
    documents: list[Document], chunk_lines: int = 3, overlap_lines: int = 1
) -> list[Document]:
    """按固定行窗口切分全文，保留片段编号和原行范围（原 Day 37 A）。

    输入参数：
        documents（list[Document]）：全文列表，每项 metadata 须有 source。
        chunk_lines（int，默认 3）：每个窗口最多包含的原文行数，必须 >= 1。
        overlap_lines（int，默认 1）：相邻窗口重叠的行数，须满足
            0 <= overlap_lines < chunk_lines；每次前进两者之差的行数。

    返回值（list[Document]）：按全文及窗口顺序返回片段；空输入返回 []。
        id 为 source#L起行-L末行；metadata 恰有 source、line_start、line_end，
        行号从 1 开始且包含两端；page_content 用换行连接这些原行。
        当前窗口到达文末即停止，不再补一个完全被覆盖的尾部窗口。

    注意：无效窗口或重叠抛 ValueError，即使 documents 为空也检查。
        空白全文跳过；不修改传入的全文，不按相同正文去重。
    """
    chunks = []
    step = chunk_lines - overlap_lines
    if chunk_lines < 1 or overlap_lines >= chunk_lines or overlap_lines < 0:
        raise ValueError
    for document in documents:
        text = document.page_content
        lines = text.splitlines()
        source = document.metadata["source"]
        if text.strip():
            for start in range(1, len(lines) + 1, step):
                stop = min(start - 1 + chunk_lines, len(lines))
                if len(lines) == 1:
                    window = lines[0]
                    chunk_text = window
                else:
                    window = lines[start - 1 : stop]
                    chunk_text = "\n".join(window)
                chunk = Document(
                    page_content=chunk_text,
                    metadata={"source": source, "line_start": start, "line_end": stop},
                    id=f"{source}#L{start}-L{stop}",
                )
                chunks.append(chunk)
                if stop == len(lines):
                    break
    return chunks


def score_query(
    ranked_ids: list[str], relevant_ids: set[str], k: int = 3
) -> dict[str, int | float | None]:
    """按编号计算单题指标（原 Week06 Day43 A，沿用已验收实现）。

    ranked_ids:list[str] 为按排名排列的候选编号；relevant_ids:set[str] 是
    事先标好的全库相关编号，两项必填。k:int 默认 3，必须为正整数，bool 不算。
    返回 dict：retrieved_count 为前 k 条实际数量，relevant_count 为全部相关数，
    matched_count 为前 k 条的相关数；hit 为 0/1，recall 为相关数/全部相关数，
    precision 为相关数/k。三个计数是 int，后两项是 float。
    已确认无答案时 relevant_ids 为空，hit/recall/precision 都返回 None。
    非法 k 或整份排名中有重复编号时抛 ValueError；不修改输入，不检查标注语义。
    """
    if type(k) is not int or k < 1:
        raise ValueError("K必须为正整数！")
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("id不能有重复编号！")
    retrieved = ranked_ids[:k]
    retrieved_count = len(retrieved)
    relevant_count = len(relevant_ids)
    matched = set(retrieved) & relevant_ids
    matched_count = len(matched)
    if not relevant_ids:
        return {
            "retrieved_count": retrieved_count,
            "relevant_count": relevant_count,
            "matched_count": matched_count,
            "hit": None,
            "recall": None,
            "precision": None,
        }
    hit = int(bool(matched))
    recall = matched_count / relevant_count
    precision = matched_count / k
    return {
        "retrieved_count": retrieved_count,
        "relevant_count": relevant_count,
        "matched_count": matched_count,
        "hit": hit,
        "recall": recall,
        "precision": precision,
    }


def evaluate_queries(
    samples: list[dict[str, list[str] | set[str]]], k: int = 3
) -> dict[str, int | float | None]:
    """按有答案题平均指标（原 Week06 Day43 B，沿用已验收实现）。

    samples:list[dict] 必填，各项含 ranked_ids:list[str]、relevant_ids:set[str]。
    k:int 默认 3，逐题转交 score_query；空 samples 仍检查 k。
    返回 dict：total/answerable_count/no_answer_count 为总题数、有答案题数、
    已确认无答案题数，类型 int；mean_hit/mean_recall/mean_precision 为先逐题
    计算再对有答案题平均的 float，没有有答案题时均为 None。
    no_answer_with_candidates:int 计无答案却返回至少一条片段的题，每题最多计 1。
    非法 k、重复编号继续抛 ValueError；不修改输入，不拿未标注题冒充无答案题。
    """
    if type(k) is not int or k < 1:
        raise ValueError("K必须为正整数！")
    answerable_count = 0
    no_answer_count = 0
    no_answer_with_candidates = 0
    hits = []
    recalls = []
    precisions = []
    for sample in samples:
        ranked_ids = sample["ranked_ids"]
        relevant_ids = sample["relevant_ids"]
        answer = score_query(ranked_ids=ranked_ids, relevant_ids=relevant_ids, k=k)
        if answer["relevant_count"] == 0:
            no_answer_count += 1
            if answer["retrieved_count"] > 0:
                no_answer_with_candidates += 1
        else:
            answerable_count += 1
            hits.append(answer["hit"])
            recalls.append(answer["recall"])
            precisions.append(answer["precision"])
    if answerable_count == 0:
        return {
            "total": len(samples),
            "answerable_count": answerable_count,
            "no_answer_count": no_answer_count,
            "mean_hit": None,
            "mean_recall": None,
            "mean_precision": None,
            "no_answer_with_candidates": no_answer_with_candidates,
        }
    mean_hit = sum(hits) / len(hits)
    mean_recall = sum(recalls) / len(recalls)
    mean_precision = sum(precisions) / len(precisions)
    return {
        "total": len(samples),
        "answerable_count": answerable_count,
        "no_answer_count": no_answer_count,
        "mean_hit": mean_hit,
        "mean_recall": mean_recall,
        "mean_precision": mean_precision,
        "no_answer_with_candidates": no_answer_with_candidates,
    }
