"""Day 41 的独立离线检查环境，不实现学员的建库或问答函数。

A 使用真实缓存模型和磁盘教学原文，B 使用独立的手工 point 与请求接口替身。
本模块不发回答模型请求；从练习入口运行 --part a / --part b。
"""

import argparse
import json
from collections.abc import Callable
from copy import deepcopy

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day41.day41_support import MATERIALS


def show_check(label: str, actual: object, expected: object) -> None:
    """打印实际值和固定期望，避免把教学检查写成学员结论。"""
    print(f"{label}：实际={actual!r}，期望={expected!r}；一致={actual == expected}")


def prepare_collection(client: QdrantClient, name: str) -> None:
    """仅提供已讲过的空 512 维 COSINE 集合。"""
    # create_collection(集合名, vectors_config=配置)：只建空集合，不读取或编码资料。
    client.create_collection(
        name, vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )


def run_a(build_fn: Callable[..., dict[str, Document]]) -> None:
    """独立检查 A 的全文快照、四条片段、空清单和参数错误。"""
    print("A｜AI 教学原文与真实缓存 embedding；不调用回答模型。")
    paths = ["notes/museum.md", "archive/museum.md"]
    before_paths = paths.copy()
    expected_texts = {}
    for source in paths:
        text = (MATERIALS / source).read_text(encoding="utf-8")
        expected_texts[source] = text
        print(f"\n来源={source}；磁盘资料={MATERIALS / source}")
        for number, line in enumerate(text.splitlines(), start=1):
            print(f"  {number}: {line}")

    model = create_embedding_model()
    # 本地内存库在 finally 中关闭；所有集合由检查环境创建后交给 A。
    client = QdrantClient(":memory:")
    try:
        prepare_collection(client, "build_demo")
        originals = build_fn(
            MATERIALS,
            paths,
            client,
            "build_demo",
            model,
            chunk_lines=3,
            overlap_lines=1,
        )
        show_check("全文返回类型", isinstance(originals, dict), True)
        show_check("全文 source 键", set(originals), set(paths))
        for source in paths:
            original = originals.get(source)
            valid = isinstance(original, Document)
            if valid:
                valid = (
                    original.id == source
                    and original.page_content == expected_texts[source]
                    and original.metadata == {"source": source, "line_count": 5}
                )
            show_check(f"{source} 的全文、id 与 metadata", valid, True)
        show_check("路径清单未改动", paths, before_paths)

        # count(..., exact=True).count：取得准确记录数；scroll 只查看已经写入的数据。
        count = client.count("build_demo", exact=True).count
        show_check("库记录数", count, 4)
        records, _ = client.scroll(
            "build_demo", limit=10, with_payload=True, with_vectors=False
        )
        actual_locations = set()
        for record in records:
            payload = record.payload or {}
            print(f"\n读回 point id={record.id}；payload={payload}")
            source = payload.get("source")
            start = payload.get("line_start")
            end = payload.get("line_end")
            actual_locations.add((payload.get("chunk_id"), source, start, end))
            text_matches = (
                source in expected_texts
                and isinstance(start, int)
                and isinstance(end, int)
                and 1 <= start <= end <= 5
                and payload.get("text")
                == "\n".join(expected_texts[source].splitlines()[start - 1 : end])
            )
            show_check("读回正文与原行对应", text_matches, True)
            show_check("embedding 模型名", payload.get("embedding_model"), MODEL_NAME)
            show_check(
                "payload 六键",
                set(payload),
                {
                    "chunk_id",
                    "text",
                    "source",
                    "line_start",
                    "line_end",
                    "embedding_model",
                },
            )
        expected_locations = {
            ("notes/museum.md#L1-L3", "notes/museum.md", 1, 3),
            ("notes/museum.md#L3-L5", "notes/museum.md", 3, 5),
            ("archive/museum.md#L1-L3", "archive/museum.md", 1, 3),
            ("archive/museum.md#L3-L5", "archive/museum.md", 3, 5),
        }
        show_check("四条编号、来源和范围", actual_locations, expected_locations)
        show_check(
            "同正文两个来源均保留",
            len(records) == 4 and actual_locations == expected_locations,
            True,
        )

        prepare_collection(client, "empty_build")
        empty = build_fn(
            MATERIALS,
            [],
            client,
            "empty_build",
            model,
            chunk_lines=3,
            overlap_lines=1,
        )
        show_check("合法参数下空清单返回", empty, {})
        show_check("空清单的库记录数", client.count("empty_build", exact=True).count, 0)

        for index, (chunk_lines, overlap_lines) in enumerate([(0, 0), (3, -1), (3, 3)]):
            name = f"invalid_build_{index}"
            prepare_collection(client, name)
            print(f"\n空清单也要校验参数：窗口={chunk_lines}，重叠={overlap_lines}")
            try:
                build_fn(
                    MATERIALS,
                    [],
                    client,
                    name,
                    model,
                    chunk_lines=chunk_lines,
                    overlap_lines=overlap_lines,
                )
            except NotImplementedError:
                raise
            except ValueError as error:
                print(f"实际=ValueError，期望=ValueError；完整信息={error!s}")
            else:
                print("实际=未抛异常，期望=ValueError")
            show_check("错误参数后库记录数", client.count(name, exact=True).count, 0)
    finally:
        client.close()


class TeachingRequest:
    """计数并留存消息的 AI 接口替身，既不联网也不生成内容。"""

    def __init__(self, response: dict, fail: bool = False) -> None:
        """保存预先写明的响应，每次调用记录一份消息快照。"""
        self.response = response
        self.fail = fail
        self.messages: list[list[dict[str, str]]] = []

    def __call__(self, messages: list[dict[str, str]]) -> dict:
        """模拟一次接口返回或连接异常，不执行任何真实请求。"""
        self.messages.append(deepcopy(messages))
        if self.fail:
            raise RuntimeError("AI 接口替身：教学连接失败")
        return deepcopy(self.response)


def show_b_result(
    result: object,
    request: TeachingRequest,
    expected_calls: int,
    expected_payload: dict | None,
    expected_response: dict | None,
    expected_checked: dict | None,
    expect_error: bool,
    question: str,
) -> None:
    """只核对 B 的外部返回值，不提供 B 内部组合算法。"""
    show_check("返回为字典", isinstance(result, dict), True)
    show_check("接口实际调用数", len(request.messages), expected_calls)
    if not isinstance(result, dict):
        print(f"完整返回={result!r}")
        return
    show_check(
        "返回五键",
        set(result),
        {"candidates", "response", "checked", "request_count", "error"},
    )
    show_check("内部请求计数", result.get("request_count"), expected_calls)
    candidates = result.get("candidates")
    expected_count = 0 if expected_payload is None else 1
    valid_candidates = (
        isinstance(candidates, list) and len(candidates) == expected_count
    )
    if valid_candidates and expected_count:
        pair = candidates[0]
        valid_candidates = isinstance(pair, tuple) and len(pair) == 2
        if valid_candidates:
            document, score = pair
            valid_candidates = (
                isinstance(document, Document)
                and isinstance(score, float)
                and document.id == expected_payload["chunk_id"]
                and document.page_content == expected_payload["text"]
                and document.metadata
                == {
                    "source": expected_payload["source"],
                    "line_start": expected_payload["line_start"],
                    "line_end": expected_payload["line_end"],
                }
            )
    show_check("保留本次候选、分数类型与全部出处", valid_candidates, True)
    print(f"实际候选={candidates!r}")
    show_check("完整响应保留", result.get("response"), expected_response)
    show_check("checked", result.get("checked"), expected_checked)
    error = result.get("error")
    error_valid = (
        isinstance(error, str) and bool(error.strip())
        if expect_error
        else error is None
    )
    show_check("error 符合预期", error_valid, True)
    print(f"完整 error={error!s}")
    if request.fail:
        show_check(
            "异常类型和信息均保留",
            isinstance(error, str)
            and "RuntimeError" in error
            and "AI 接口替身：教学连接失败" in error,
            True,
        )
    if expected_calls == 1 and len(request.messages) == 1:
        messages = request.messages[0]
        valid_messages = len(messages) == 2 and [
            message.get("role") for message in messages
        ] == ["system", "user"]
        if valid_messages:
            try:
                user_data = json.loads(messages[1]["content"])
            except (ValueError, KeyError, TypeError):
                valid_messages = False
            else:
                valid_messages = user_data == {
                    "question": question,
                    "evidence": [
                        {
                            "id": expected_payload["chunk_id"],
                            "source": expected_payload["source"],
                            "line_start": expected_payload["line_start"],
                            "line_end": expected_payload["line_end"],
                            "text": expected_payload["text"],
                        }
                    ],
                }
        show_check("实际问题和本批原文进入消息", valid_messages, True)


def run_b(answer_fn: Callable[..., dict]) -> None:
    """用独立单 point 和人工请求返回检查 B，不调用 A。"""
    print("B｜真实缓存 embedding ＋独立手工 point。")
    print(
        "所有 request_fn 都是 AI 接口替身，不是模型实际回复；本检查没有回答模型联网。"
    )
    text = "借用台灯需登记借阅卡号。"
    original = Document(
        id="teaching/lamp.md",
        page_content=f"台灯借用说明\n{text}",
        metadata={"source": "teaching/lamp.md", "line_count": 2},
    )
    print("来源名 teaching/lamp.md 仅表示内存教学原文，不声称存在同名磁盘文件。")
    for number, line in enumerate(original.page_content.splitlines(), start=1):
        print(f"  {number}: {line}")
    payload = {
        "chunk_id": "teaching/lamp.md#L2-L2",
        "source": "teaching/lamp.md",
        "line_start": 2,
        "line_end": 2,
        "text": text,
        "embedding_model": MODEL_NAME,
    }
    payloads = {
        "lamp": payload,
        "bad_line": {
            **payload,
            "line_start": 1,
            "line_end": 1,
            "chunk_id": "teaching/lamp.md#L1-L1",
        },
        "bad_source": {
            **payload,
            "source": "teaching/missing.md",
            "chunk_id": "teaching/missing.md#L2-L2",
        },
        "bad_id": {**payload, "chunk_id": "teaching/lamp.md#L9-L9"},
    }
    model = create_embedding_model()
    # embed(单条文本) 仍返回生成器；这里只给这一条手工记录准备真实 512 维向量。
    vector = next(iter(model.embed(text))).tolist()
    show_check("手工 point 的真实向量维度", len(vector), VECTOR_SIZE)
    client = QdrantClient(":memory:")
    try:
        for name, sample_payload in payloads.items():
            prepare_collection(client, name)
            # 固定一条教学 point；这里没有实现任意资料的加载、切分或批量存储流程。
            client.upsert(
                name,
                points=[PointStruct(id=901, vector=vector, payload=sample_payload)],
                wait=True,
            )
        prepare_collection(client, "empty")

        answered = {
            "status": "answered",
            "answer": "需登记借阅卡号。",
            "cited_ids": ["teaching/lamp.md#L2-L2"],
        }
        insufficient = {
            "status": "insufficient",
            "answer": "这份资料没有提供台灯功率。",
            "cited_ids": [],
        }
        unknown = {
            "status": "answered",
            "answer": "需登记借阅卡号。",
            "cited_ids": ["teaching/lamp.md#L8-L8"],
        }
        # 三键回复文字和四键接口响应都由 AI 手写；usage=None，不能充当真实用量。
        good_response = {
            "raw_text": json.dumps(answered, ensure_ascii=False),
            "finish_reason": "stop",
            "usage": None,
            "model": "AI接口替身",
        }
        cases = [
            (
                "正常回答",
                "lamp",
                "借用台灯需要登记什么？",
                good_response,
                answered,
                False,
                False,
            ),
            (
                "有候选但资料不足",
                "lamp",
                "这盏台灯的功率是多少瓦？",
                {
                    **good_response,
                    "raw_text": json.dumps(insufficient, ensure_ascii=False),
                },
                insufficient,
                False,
                False,
            ),
            (
                "空集合不请求",
                "empty",
                "借用台灯需要登记什么？",
                good_response,
                None,
                False,
                False,
            ),
            (
                "未知引用保留原始回复后拒绝",
                "lamp",
                "借用台灯需要登记什么？",
                {**good_response, "raw_text": json.dumps(unknown, ensure_ascii=False)},
                None,
                True,
                False,
            ),
            (
                "length 即使 JSON 合法仍拒绝",
                "lamp",
                "借用台灯需要登记什么？",
                {**good_response, "finish_reason": "length"},
                None,
                True,
                False,
            ),
            (
                "坏 JSON 保留原始回复后拒绝",
                "lamp",
                "借用台灯需要登记什么？",
                {**good_response, "raw_text": "这不是 JSON"},
                None,
                True,
                False,
            ),
            (
                "错原行在请求前拒绝",
                "bad_line",
                "借用台灯需要登记什么？",
                good_response,
                None,
                True,
                False,
            ),
            (
                "错来源在请求前拒绝",
                "bad_source",
                "借用台灯需要登记什么？",
                good_response,
                None,
                True,
                False,
            ),
            (
                "id 与正确范围不符也拒绝",
                "bad_id",
                "借用台灯需要登记什么？",
                good_response,
                None,
                True,
                False,
            ),
            (
                "请求异常保留候选与计数",
                "lamp",
                "借用台灯需要登记什么？",
                good_response,
                None,
                True,
                True,
            ),
        ]
        for label, name, question, response, checked, expect_error, fail in cases:
            print(f"\n情境：{label}")
            originals = {"teaching/lamp.md": deepcopy(original)}
            before = deepcopy(originals)
            request = TeachingRequest(response, fail=fail)
            expected_calls = int(name == "lamp")
            expected_response = response if expected_calls and not fail else None
            result = answer_fn(
                question, originals, client, name, model, request, limit=3
            )
            show_b_result(
                result,
                request,
                expected_calls,
                payloads.get(name),
                expected_response,
                checked,
                expect_error,
                question,
            )
            show_check("输入全文快照未改动", originals == before, True)

        for question, limit in [("  \n", 3), ("借用台灯需要登记什么？", 0)]:
            print(f"\n参数情境：question={question!r}，limit={limit}")
            originals = {"teaching/lamp.md": deepcopy(original)}
            before = deepcopy(originals)
            request = TeachingRequest(good_response)
            try:
                answer_fn(
                    question, originals, client, "lamp", model, request, limit=limit
                )
            except NotImplementedError:
                raise
            except ValueError as error:
                print(f"实际=ValueError，期望=ValueError；完整信息={error!s}")
            else:
                print("实际=未抛异常，期望=ValueError")
            show_check("参数错误时接口调用数", len(request.messages), 0)
            show_check("输入全文快照未改动", originals == before, True)
    finally:
        client.close()

    run_mixed_check(answer_fn)


def run_mixed_check(answer_fn: Callable[..., dict]) -> None:
    """独立检查正常与坏编号并存时是否在任何请求前拒绝整批候选。"""
    print("\nB 混合候选｜两条同向量记录，正常编号与错误编号交换数据库位置。")
    print("不要求同分候选的先后顺序；两次都必须核对全部候选，保留两条并且不请求。")
    print("request_fn 是 AI 接口替身，不是模型实际回复。")
    text = "借用台灯需登记借阅卡号。"
    original = Document(
        id="teaching/lamp.md",
        page_content=f"台灯借用说明\n{text}",
        metadata={"source": "teaching/lamp.md", "line_count": 2},
    )
    payload = {
        "chunk_id": "teaching/lamp.md#L2-L2",
        "source": "teaching/lamp.md",
        "line_start": 2,
        "line_end": 2,
        "text": text,
        "embedding_model": MODEL_NAME,
    }
    wrong_payload = {**payload, "chunk_id": "teaching/lamp.md#L9-L9"}
    response = {
        "raw_text": json.dumps(
            {
                "status": "answered",
                "answer": "需登记借阅卡号。",
                "cited_ids": ["teaching/lamp.md#L2-L2"],
            },
            ensure_ascii=False,
        ),
        "finish_reason": "stop",
        "usage": None,
        "model": "AI接口替身",
    }
    model = create_embedding_model()
    vector = next(iter(model.embed(text))).tolist()
    client = QdrantClient(":memory:")
    try:
        for index, pair in enumerate(
            [(payload, wrong_payload), (wrong_payload, payload)]
        ):
            name = f"mixed_{index}"
            prepare_collection(client, name)
            client.upsert(
                name,
                points=[
                    PointStruct(id=901, vector=vector, payload=pair[0]),
                    PointStruct(id=902, vector=vector, payload=pair[1]),
                ],
                wait=True,
            )
            print(
                f"\n布置 {index + 1}：point 901 的片段 id={pair[0]['chunk_id']}；"
                f"point 902 的片段 id={pair[1]['chunk_id']}"
            )
            originals = {"teaching/lamp.md": deepcopy(original)}
            before = deepcopy(originals)
            request = TeachingRequest(response)
            result = answer_fn(
                "借用台灯需要登记什么？",
                originals,
                client,
                name,
                model,
                request,
                limit=3,
            )
            show_check(
                "混合候选返回五键",
                set(result),
                {"candidates", "response", "checked", "request_count", "error"},
            )
            candidates = result.get("candidates")
            valid = isinstance(candidates, list) and len(candidates) == 2
            actual_rows = set()
            if valid:
                for candidate in candidates:
                    if not (
                        isinstance(candidate, tuple)
                        and len(candidate) == 2
                        and isinstance(candidate[0], Document)
                        and isinstance(candidate[1], float)
                    ):
                        valid = False
                        break
                    document, _ = candidate
                    actual_rows.add(
                        (
                            document.id,
                            document.page_content,
                            document.metadata.get("source"),
                            document.metadata.get("line_start"),
                            document.metadata.get("line_end"),
                        )
                    )
                    valid = valid and set(document.metadata) == {
                        "source",
                        "line_start",
                        "line_end",
                    }
            expected_rows = {
                ("teaching/lamp.md#L2-L2", text, "teaching/lamp.md", 2, 2),
                ("teaching/lamp.md#L9-L9", text, "teaching/lamp.md", 2, 2),
            }
            show_check(
                "两条实际候选与分数完整保留，不依赖顺序",
                valid and actual_rows == expected_rows,
                True,
            )
            print(f"实际混合候选={candidates!r}")
            show_check("混合候选实际接口调用数", len(request.messages), 0)
            show_check("混合候选内部请求计数", result.get("request_count"), 0)
            show_check("混合候选 response", result.get("response"), None)
            show_check("混合候选 checked", result.get("checked"), None)
            error = result.get("error")
            show_check(
                "混合候选 error 非空",
                isinstance(error, str) and bool(error.strip()),
                True,
            )
            print(f"混合候选完整 error={error!s}")
            show_check("输入全文快照未改动", originals == before, True)
    finally:
        client.close()


def main() -> None:
    """本模块只提供检查函数；实际作答从练习入口开始。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print("请运行 exercises/day41_rag_exercises.py --part a 或 --part b。")


if __name__ == "__main__":
    main()
