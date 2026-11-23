"""检索：纯文本按行匹配，以及在一整个笔记目录里找带出处的命中。

find_matches 只处理一段文本；safe_subdir 与 search_files 把它接到文件系统上，
并保证调用方给的子目录不会逃出语料根。三层都能单独测，不需要起 server。
"""

from pathlib import Path

DEFAULT_NOTES_ROOT = Path(__file__).resolve().parents[2] / "notes"
"""默认语料目录：仓库根下的 notes/；可用环境变量 NOTES_ROOT 覆盖。"""


def find_matches(text: str, keyword: str, limit: int = 5) -> list[dict[str, int | str]]:
    """按行查找关键词，返回命中的行号与原文。

    参数：
        text（str，必填）：要检索的全文；按 splitlines() 切行，行号从 1 开始。
        keyword（str，必填）：关键词。先去掉首尾空白；空字符串不接受。
            匹配时不区分大小写（中文不受影响，英文 NOTE 能命中 note）。
        limit（int，默认 5）：最多返回几条命中，按出现顺序取前 limit 条。
            必须是大于等于 1 的整数；0 和负数要拒绝。

    返回：
        list[dict[str, int | str]]：每个元素形如
            {"line": 2, "text": "第二行：关键词 在这里"}
        text 保留该行原文（不 strip、不改大小写）。没有命中返回 []，不是错误。

    抛出：
        ValueError：keyword 去空白后为空，或 limit 小于 1。
            消息里要指明是哪个参数不合法，方便调用方（和模型）看懂。
    """
    if not keyword.strip():
        raise ValueError("关键词为空！")
    if limit <= 0:
        raise ValueError("limit不是正整数！")
    matches: list[dict[str, int | str]] = []
    key = keyword.strip()
    for line_num, line in enumerate(text.splitlines(), start=1):
        if key.casefold() in line.casefold():
            matches.append(
                {
                    "line": line_num,
                    "text": line,
                }
            )
    return matches[:limit]


def safe_subdir(root: Path, folder: str) -> Path:
    """把相对子目录解析成绝对目录，保证不逃出语料根。

    参数：
        root（Path，必填）：语料根目录。
        folder（str，必填）：相对子目录，"" 表示根本身；可以写成 notes 或
            notes/../notes 这种解析后仍在根内的形式。

    返回：
        Path：解析后的绝对目录（resolve 之后），且一定在 root 里面。

    抛出：
        ValueError：root 不存在或不是目录；folder 解析后逃出 root（绝对路径、
            .. 越界都算）；folder 指向不存在的路径，或指向一个文件。
            消息里要说明是哪种情况。
    """
    if not root.exists():
        raise ValueError("root不存在")
    if not root.is_dir():
        raise ValueError("root不是目录")
    path = (root / folder).resolve()
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError("不在root内")
    if not path.exists():
        raise ValueError("指向不存在路径")
    if not path.is_dir():
        raise ValueError("没有指向目录")
    return path


def search_files(
    root: Path,
    keyword: str,
    limit: int = 5,
    folder: str = "",
) -> list[dict[str, int | str]]:
    """在 root 下的 Markdown 里检索关键词，返回带出处的命中。

    参数：
        root（Path，必填）：语料根目录。
        keyword（str，必填）：关键词，规则与 find_matches 相同（去首尾空白、
            大小写不敏感、空字符串拒绝）。
        limit（int，默认 5）：**全局**上限，按文件顺序累计，凑够就停；
            不是每个文件各拿 limit 条。小于 1 拒绝。
        folder（str，默认 ""）：先经 safe_subdir 解析的相对子目录；空串表示整个根。

    返回：
        list[dict[str, int | str]]：按文件顺序（相对路径的 POSIX 形式升序）、
        再按行号升序；每项恰好三个键：
            {"source": "notes/agent-notes.md", "line": 3, "text": "关键词：描述写清用途。"}
        source 是相对 root 的 POSIX 路径，不写绝对路径；text 保留原文。
        没有命中返回 []。

    边界：
        - 只扫 *.md，递归进子目录；
        - 跳过只有空白的文件；
        - 读不成 UTF-8 的文件跳过（不要用 errors=ignore，坏字节会被悄悄吞掉）；
        - 参数不合法要在扫描前就抛 ValueError——即使目录里一个 .md 都没有。
    """
    if not keyword.strip():
        raise ValueError("关键词为空！")
    if limit <= 0:
        raise ValueError("limit不是正整数！")
    if not root.is_dir():
        raise ValueError(f"语料目录不存在：{root}")
    dir = safe_subdir(root, folder)
    results: list[dict[str, int | str]] = []
    files = sorted(
        dir.rglob("*.md"), key=lambda path: path.relative_to(root.resolve()).as_posix()
    )
    for path in files:
        source = path.relative_to(root.resolve()).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not text.strip():
            continue
        for match in find_matches(text, keyword, limit):
            results.append(
                {"source": source, "line": match["line"], "text": match["text"]}
            )
            if len(results) >= limit:
                return results
    return results
