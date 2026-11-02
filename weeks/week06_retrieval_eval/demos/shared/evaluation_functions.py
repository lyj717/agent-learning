"""本周旧函数集中入口：实际实现沿用学员已验收代码。

函数索引：
chunk_documents：Week05 Day37，全文按行切块，供 Day44 查看固定版本片段。
score_query：Week06 Day43 A，单题编号级指标，供 Day44 旧基线回放。
evaluate_queries：Week06 Day43 B，有答案题逐题平均，供后续整批比较。
project_relevance：Week06 Day44 A，原文依据映射到当前全库编号。
tokenize_text：Day45 提供的辅助，固定词项规则，供 rank_keywords 内部使用。
rank_keywords：Week06 Day45 A，关键词排名。
fuse_rankings：Week06 Day45 B，两路名次融合。
check_ranked_ids：Day45 提供的辅助，核对回调返回的编号是否合法。

Day46 compare_retrievals 需要 project_relevance、rank_keywords、fuse_rankings、
score_query、evaluate_queries、check_ranked_ids；直接从本文件导入这六个函数。
vector_search 是运行环境传入的回调，不在这里实现；本题批量整合仍由学员写。
导入不加载向量模型、不创建数据库、不运行检索。原练习保留为学习记录。
"""

import re

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


def tokenize_text(text: str) -> list[str]:
    """按固定规则生成词项（原 Day45 提供的辅助，不是新的学员练习）。

    text:str 必填，为问题或片段正文；返回 list[str]，保留顺序和重复词项。
    统一大小写，保留英文标识符、整数与中文单字；空白或纯标点返回 []。
    不改输入，不扩展同义词，不去停用词；非字符串导致的异常原样抛出。
    """
    # re.findall(模式, 文本)：取出全部匹配，casefold() 统一大小写。
    return re.findall(r"[a-z_][a-z_0-9]*|[0-9]+|[\u4e00-\u9fff]", text.casefold())


def rank_keywords(query: str, chunks: list[Document], limit: int = 3) -> list[str]:
    """计算 BM25 并返回正分片段的有序编号（原 Day45 A，保留学员逻辑）。

    query:str 必填，非空白问题；chunks:list[Document] 必填，id 为唯一片段编号，
    page_content 为正文。limit:int 默认 3，必须为正整数，bool 不算。
    返回 list[str]：按分数降序、完整编号升序排列，最多 limit 条。
    同步过滤无词项片段及对应编号；空语料、无正分返回 []，不改变输入。
    非法问题或 limit 抛 ValueError；匹配后零分也会被过滤，分数不是正确概率。
    """
    if type(limit) is not int or limit < 1:
        raise ValueError("limit必须是正整数！")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query是非空字符串！")
    corpus = []
    id_list = []
    token_query = tokenize_text(query)
    if not chunks:
        return []
    for chunk in chunks:
        token_chunk = tokenize_text(chunk.page_content)
        if token_chunk:
            corpus.append(token_chunk)
            id_list.append(chunk.id)
    if not corpus:
        return []
    # BM25Okapi(corpus)：每个子列表是一块词项；get_scores 返回与 corpus 对应的分数。
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query=token_query)
    scores_id_dict = {}
    for index in range(len(corpus)):
        score = float(scores[index])
        if score > 0:
            scores_id_dict[id_list[index]] = score
    ordered = sorted(scores_id_dict.keys(), key=lambda d: (-scores_id_dict[d], d))
    return ordered[:limit]


def fuse_rankings(
    vector_ids: list[str],
    keyword_ids: list[str],
    limit: int = 3,
    rank_constant: int = 60,
) -> list[str]:
    """累加两路 RRF 名次贡献并返回编号（原 Day45 B，保留学员双重循环）。

    vector_ids、keyword_ids:list[str] 必填，分别为已排好的两路编号。
    limit:int 默认 3，为最终上限；rank_constant:int 默认 60，为分母常量。
    两个数都必须为正整数，bool 不算。返回 list[str]，按总分降序、完整编号升序。
    单路为空仍处理另一路，两路空返回 []；跨路同号累加，同路重复抛 ValueError，
    包括截取范围外的重复。非法参数也抛 ValueError；不改变两路输入。
    """
    if type(limit) is not int or limit < 1:
        raise ValueError("limit必须是正整数！")
    if type(rank_constant) is not int or rank_constant < 1:
        raise ValueError("rank_constant必须是正整数！")
    vector_pairs = []
    keyword_pairs = []
    for index, vector_id in enumerate(vector_ids, start=1):
        vector_score = 1 / (index + rank_constant)
        vector_pair = (vector_id, vector_score)
        vector_pairs.append(vector_pair)
    for index, keyword_id in enumerate(keyword_ids, start=1):
        keyword_score = 1 / (index + rank_constant)
        keyword_pair = (keyword_id, keyword_score)
        keyword_pairs.append(keyword_pair)
    if len(vector_ids) != len(set(vector_ids)):
        raise ValueError
    if len(keyword_ids) != len(set(keyword_ids)):
        raise ValueError
    pairs = []
    for vector in vector_pairs:
        score = vector[1]
        for keyword in keyword_pairs:
            if vector[0] == keyword[0]:
                score += keyword[1]
                break
        pairs.append((vector[0], score))
    for keyword in keyword_pairs:
        if not any(keyword[0] == pair[0] for pair in pairs):
            pairs.append(keyword)
    ordered = sorted(pairs, key=lambda pair: (-pair[1], pair[0]))
    ids = []
    for id, score in ordered:
        ids.append(id)
    return ids[:limit]


def check_ranked_ids(value: list[str], allowed: set[str], limit: int) -> None:
    """核对排名返回值（原 Day45 提供的辅助；不是新的学员练习）。

    value:list[str] 必填，为待检查排名；allowed:set[str] 必填，为允许的全库编号；
    limit:int 必填，传当前 k。类型错误抛 TypeError，超过上限、重复或未知编号
    抛 ValueError；成功返回 None，不修改输入，不判断是否相关。limit 由调用方先校验。
    """
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TypeError("排名应返回 list[str]")
    if len(value) > limit or len(value) != len(set(value)):
        raise ValueError("排名不能超过 limit，也不能重复编号")
    if not set(value) <= allowed:
        raise ValueError("排名中含有不属于本批输入的编号")


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
