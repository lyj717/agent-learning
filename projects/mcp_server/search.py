"""纯文本检索：按行找关键词，保留行号与原文。

这一层不碰文件、不碰 MCP，只做「给定一段文本，找出命中行」。好处是能单独测：
不用起 server、不用建语料。第 65 天会在它上面加文件层。
"""


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
