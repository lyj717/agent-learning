"""Day 41 的运行与留证环境：资料展示、真实请求入口和独立输出目录。

这里只调用学员传入的建库与问答函数，不实现加载到入库或检索到回答的整合逻辑。
生成模型沿用 Day 40 请求层；问题、期望、候选判断与观察由学员完成。
"""

import hashlib
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from fastembed import TextEmbedding
from langchain_core.documents import Document
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week05_rag.demos.day38.day38_embedding_support import (
    MODEL_NAME,
    VECTOR_SIZE,
    create_embedding_model,
)
from weeks.week05_rag.demos.day39.day39_support import prepare_collection
from weeks.week05_rag.demos.day40.day40_model_io import request_grounded_json

DAY41 = Path(__file__).resolve().parent
MATERIALS = DAY41 / "materials"
OUTPUTS = DAY41 / "outputs"
COLLECTION_NAME = "chunks"
DEFAULT_SOURCE_ROOT = ROOT
DEFAULT_PATHS = ["notes/python-notes.md"]
BASELINE_PATH = DAY41.parent / "day39" / "day39_retrieval_记录.md"
CHUNK_LINES = 8
OVERLAP_LINES = 2
DEFAULT_LIMIT = 3

RequestFunction = Callable[[list[dict[str, str]]], dict]
BuildFunction = Callable[
    [Path, list[str], QdrantClient, str, TextEmbedding, int, int], dict[str, Document]
]
AnswerFunction = Callable[
    [str, dict[str, Document], QdrantClient, str, TextEmbedding, RequestFunction, int],
    dict,
]


def resolve_from_root(path: Path) -> Path:
    """相对路径按仓库根目录解释，绝对路径保留其位置。"""
    return (path if path.is_absolute() else ROOT / path).resolve()


def run_sources(source_root: Path, paths: list[str]) -> None:
    """只读出 UTF-8 全文和行号，不运行 Day 41 的两道练习或模型。"""
    source_root = resolve_from_root(source_root)
    if not paths:
        raise ValueError("请通过 --paths 提供至少一个相对 UTF-8 文本路径")
    print(f"资料根目录：{source_root}")
    print(f"相对路径列表：{paths}")
    print("这里只显示当前磁盘原文；尚未创建数据库或调用模型。")
    for relative_path in paths:
        candidate = Path(relative_path)
        absolute_path = (source_root / candidate).resolve()
        # is_relative_to(目录)：检查解析后的路径是否仍在该目录内，防止把根目录用错。
        if candidate.is_absolute() or not absolute_path.is_relative_to(source_root):
            raise ValueError(f"需要资料根目录内的相对路径：{relative_path}")
        text = absolute_path.read_text(encoding="utf-8")
        print(f"\n来源={relative_path}；全文行数={len(text.splitlines())}")
        for line_number, line in enumerate(text.splitlines(), start=1):
            print(f"  {line_number}: {line}")


def _markdown_cells(line: str) -> list[str]:
    """拆开一行 Markdown 表格，把转义的竖线保留在单元格内。"""
    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(line):
        character = line[index]
        if character == "\\" and index + 1 < len(line) and line[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current).strip())
    if cells and not cells[0]:
        cells = cells[1:]
    if cells and not cells[-1]:
        cells = cells[:-1]
    return cells


def read_baseline_questions(path: Path = BASELINE_PATH) -> list[tuple[int, str]]:
    """只从 Day 39 自有资料基线表读编号和问题，不读取期望或自动判分。"""
    path = resolve_from_root(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    in_table = False
    questions: list[tuple[int, str]] = []
    numbers: set[int] = set()
    for line in lines:
        stripped = line.strip()
        if not in_section:
            if stripped.startswith("## 自有资料基线"):
                in_section = True
            continue
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        cells = _markdown_cells(stripped)
        if not in_table:
            if len(cells) == 5 and cells[0] == "编号":
                in_table = True
            continue
        if cells and all(not cell.strip("-: ") for cell in cells):
            continue
        if len(cells) != 5:
            raise ValueError("自有资料基线表应有五列；单元格中的竖线请写成 \\|")
        try:
            number = int(cells[0])
        except ValueError as error:
            raise ValueError(f"基线编号应为正整数：{cells[0]!r}") from error
        if number < 1:
            raise ValueError(f"基线编号应为正整数：{number}")
        if number in numbers:
            raise ValueError(f"基线表有重复编号：{number}")
        numbers.add(number)
        if cells[1].strip():
            questions.append((number, cells[1].strip()))
    if not questions:
        raise ValueError(
            "自有资料基线没有已填写的问题；请先读原文，在 Day 39 表中填写问题与期望来源，"
            "再运行 batch。运行层只读取编号和问题，不替你填写或判分。"
        )
    print(f"基线文件：{path}")
    print(f"读到 {len(questions)} 个已填写的问题；目标约 10 个，不硬性要求恰好 10 个。")
    print("只读取编号与问题；期望来源和你的判断不会送给模型。")
    return questions


def _json_document(value: object) -> dict:
    """把 Document 的原文与出处转成普通字典，不保存向量。"""
    if isinstance(value, Document):
        return {
            "id": value.id,
            "page_content": value.page_content,
            "metadata": value.metadata,
        }
    raise TypeError(f"不能保存为 JSON 的类型：{type(value).__name__}")


def _write_json(path: Path, value: object) -> None:
    """把原始运行数据写到本次目录，中文可直接阅读。"""
    # dumps(default=函数)：遇到 Document 时才调用转换函数；不改动运行中的对象。
    text = json.dumps(value, ensure_ascii=False, indent=2, default=_json_document)
    path.write_text(text + "\n", encoding="utf-8")


def _show_snapshot(originals: dict[str, Document], version: str) -> None:
    """展示 A 返回的本次全文快照，后续引用核对必须使用同一个版本。"""
    print(f"\n本次原文版本：sources_snapshot.json 的 SHA256={version}")
    print("下面是本次建库函数返回的全文快照；问答期间不会重新读取磁盘替换它。")
    for source, document in originals.items():
        print(f"\n来源={source}；全文行数={len(document.page_content.splitlines())}")
        for line_number, line in enumerate(document.page_content.splitlines(), start=1):
            print(f"  {line_number}: {line}")


def _show_result(number: int, question: str, result: dict, path: Path) -> None:
    """逐项打印检索、原始响应、校验结果和错误，便于学员核对保存数据。"""
    print(f"\n问题 {number}：{question}")
    candidates = result["candidates"]
    print(f"实际候选数={len(candidates)}；生成请求数={result['request_count']}")
    for rank, (document, score) in enumerate(candidates, start=1):
        print(f"  候选 {rank}：原片段 id={document.id}；余弦分数={score:.6f}")
        print(
            f"    来源={document.metadata['source']}；"
            f"原行={document.metadata['line_start']}～{document.metadata['line_end']}"
        )
        print(f"    正文={document.page_content!r}")
    response = result["response"]
    if response is None:
        print("response=None：本次没有保存到模型响应。")
    else:
        print(f"响应模型={response['model']}")
        print("模型原始回复：")
        print(response["raw_text"])
        print(f"finish_reason={response['finish_reason']}")
        print(f"usage={response['usage']}")
    checked = result["checked"]
    print("校验结果 checked：")
    print(json.dumps(checked, ensure_ascii=False, indent=2))
    if checked is not None:
        by_id = {document.id: document for document, _score in candidates}
        for cited_id in checked["cited_ids"]:
            document = by_id.get(cited_id)
            if document is None:
                print(f"  引用 {cited_id} 不在候选中，请检查本次校验结果。")
                continue
            print(f"  引用原文 {cited_id}：{document.page_content!r}")
    print(f"error={result['error']!r}")
    if not candidates and result["error"] is None:
        print("空候选：程序没有发起生成请求；这不能证明整个资料库没有答案。")
    print(f"本题原始记录：{path}")


def run_questions(
    build_fn: BuildFunction,
    answer_fn: AnswerFunction,
    source_root: Path,
    paths: list[str],
    questions: list[tuple[int, str]],
    chunk_lines: int = CHUNK_LINES,
    overlap_lines: int = OVERLAP_LINES,
    limit: int = DEFAULT_LIMIT,
) -> None:
    """只建一次独立库，调用学员函数逐题问答，并保留真实输入与响应。"""
    if not questions or any(not question.strip() for _number, question in questions):
        raise ValueError("至少提供一个非空问题；尚未建库，也未调用模型")
    numbers = [number for number, _question in questions]
    if any(type(number) is not int or number < 1 for number in numbers):
        raise ValueError("问题编号必须是正整数")
    if len(set(numbers)) != len(numbers):
        raise ValueError("问题编号重复，会覆盖本次记录，请先订正编号")
    if not paths:
        raise ValueError("请提供至少一个相对资料路径")
    if limit < 1:
        raise ValueError("limit 必须至少为 1")
    if chunk_lines < 1 or overlap_lines < 0 or overlap_lines >= chunk_lines:
        raise ValueError("需要 chunk_lines >= 1 且 0 <= overlap_lines < chunk_lines")

    source_root = resolve_from_root(source_root)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    # mkdtemp(prefix=名前缀, dir=父目录)：创建唯一目录；这里不使用系统 TEMP 或旧库。
    output_path = Path(tempfile.mkdtemp(prefix="run_", dir=OUTPUTS))
    database_path = output_path / "db"
    run_info = {
        "source_root": str(source_root),
        "relative_paths": list(paths),
        "embedding_model": MODEL_NAME,
        "vector_size": VECTOR_SIZE,
        "chunk_lines": chunk_lines,
        "overlap_lines": overlap_lines,
        "limit": limit,
        "collection_name": COLLECTION_NAME,
        "database_path": str(database_path),
        "question_numbers": numbers,
        "point_count": None,
        "source_snapshot_sha256": None,
        "state": "starting",
    }
    info_path = output_path / "run_info.json"
    _write_json(info_path, run_info)
    print(f"本次独立目录：{output_path}")
    print(f"资料根目录：{source_root}")
    print(f"相对路径列表：{paths}")
    print(f"向量模型={MODEL_NAME}；维度={VECTOR_SIZE}；只读已有模型缓存")
    print(f"窗口行数={chunk_lines}；重叠行数={overlap_lines}；limit={limit}")
    print("本入口使用 Day 40 的真实生成请求；每题无 SDK 重试，回答和人工判分分开记录。")

    model = create_embedding_model()
    # QdrantClient(path=路径)：打开本次本地库；finally 负责在正常结束或异常时关闭它。
    client = QdrantClient(path=str(database_path))
    try:
        prepare_collection(client, COLLECTION_NAME)
        originals = build_fn(
            source_root,
            list(paths),
            client,
            COLLECTION_NAME,
            model,
            chunk_lines,
            overlap_lines,
        )
        snapshot_path = output_path / "sources_snapshot.json"
        _write_json(snapshot_path, originals)
        # sha256(字节).hexdigest()：计算已保存快照的摘要，标识本次原文版本。
        version = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
        run_info["source_snapshot_sha256"] = version
        run_info["point_count"] = client.count(collection_name=COLLECTION_NAME).count
        run_info["state"] = "ready"
        _write_json(info_path, run_info)
        print(f"本次库记录数={run_info['point_count']}")
        _show_snapshot(originals, version)
        for number, question in questions:
            result = answer_fn(
                question,
                originals,
                client,
                COLLECTION_NAME,
                model,
                request_grounded_json,
                limit,
            )
            question_path = output_path / f"question_{number:02d}.json"
            # 先保存再打印：即使 B 返回 error，也保留已经收到的 response 原文与用量。
            _write_json(
                question_path,
                {"number": number, "question": question, "result": result},
            )
            _show_result(number, question, result, question_path)
        run_info["state"] = "completed"
        _write_json(info_path, run_info)
    except Exception as error:
        run_info["state"] = "failed"
        run_info["runtime_error"] = f"{type(error).__name__}: {error}"
        _write_json(info_path, run_info)
        raise
    finally:
        client.close()
    print(f"\n配置记录：{info_path}")
    print("请用原文和事先填写的期望判断回答；运行层不会自动填写你的观察或判分。")
