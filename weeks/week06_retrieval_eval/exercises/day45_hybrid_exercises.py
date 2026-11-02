"""Day45：新增关键词候选，再按名次融合；单题探查后由学员写观察。

--part a/b 运行函数对照；--part probe --case q07 使用固定资料和旧向量排名比较三路指标。
运行日志自动保存到 demos/day45/outputs；学员观察保留在 demos/day45/day45_记录.md。
"""

import argparse
import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.day44.day44_support import (
    LABELS,
    SNAPSHOT_SHA256,
)
from weeks.week06_retrieval_eval.demos.day45.day45_checks import (
    run_fusion_checks,
    run_keyword_checks,
)
from weeks.week06_retrieval_eval.demos.day45.day45_support import (
    TOKENIZER_VERSION,
    probe_case,
    tokenize_text,
)
from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def rank_keywords(query: str, chunks: list[Document], limit: int = 3) -> list[str]:
    """按固定词项规则计算 BM25，返回正分片段的有序编号。"""
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
    """按 RRF 累加两路名次贡献，返回融合后的有序编号。"""
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


def main() -> None:
    """AI 运行环境：选择人工对照或旧开发题探查，自动保存配置、输出和异常。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=["a", "b", "probe"], default="a")
    parser.add_argument(
        "--case", choices=[f"q{i:02d}" for i in range(1, 11)], default="q07"
    )
    args = parser.parse_args()
    day = ROOT / "weeks/week06_retrieval_eval/demos/day45"
    config = {
        "part": args.part,
        "case": args.case,
        "source_snapshot_sha256": SNAPSHOT_SHA256,
        "labels_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "chunk_lines": 8,
        "overlap_lines": 2,
        "channel_limit": 3,
        "final_k": 3,
        "rank_constant": 60,
        "tokenizer": TOKENIZER_VERSION,
        # version(安装包名)：读取本机实际安装版本，只记录公开环境信息。
        "rank_bm25_version": version("rank-bm25"),
    }

    def execute(run_dir: Path) -> None:
        """执行所选入口；只有探查成功才写结构化排名结果。"""
        if args.part == "a":
            run_keyword_checks(rank_keywords)
        elif args.part == "b":
            run_fusion_checks(fuse_rankings)
        else:
            report = probe_case(args.case, rank_keywords, fuse_rankings)
            (run_dir / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    run_logged(
        args.part,
        execute,
        config,
        Path(__file__),
        day / "outputs",
        origin_env="DAY45_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
