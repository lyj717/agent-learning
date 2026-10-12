"""Day 24 小练习 A：把单文件检索扩展为多文件检索，并限制总结果数。"""

from day24_retrieval_demo import NOTES_DIR, find_in_text


def search_notes(keyword: str, limit: int = 3) -> list[dict]:
    """从固定资料目录找关键词，返回带出处的前 limit 条命中。"""
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("关键词必须是非空字符串！")
    if type(limit) != int or limit < 1:
        raise ValueError("结果数必须是正整数！")
    count = 0
    results: list[dict] = []
    for path in sorted(NOTES_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        hits = find_in_text(text, keyword.strip(), path.name)
        results.extend(hits)
        if len(hits):
            count += len(hits)
        if count >= limit:
            break
    return results[: min(count, limit)]


def main() -> None:
    """打印成功、无命中和非法参数的对照结果。"""
    print(f"固定资料目录：{NOTES_DIR}")
    cases = [
        ("跨文件命中", "青禾笔记本", 3, "两条：products.txt:2、stock.txt:2"),
        ("总数上限", "青禾笔记本", 1, "一条：products.txt:2"),
        (
            "同一文件多条命中时也不能超过上限",
            "单价",
            1,
            "一条：products.txt:2；第 3 行也命中，但应被 limit 截掉",
        ),
        (
            "去掉关键词首尾空白",
            "  星野签字笔  ",
            3,
            "两条：products.txt:3、stock.txt:3",
        ),
        ("无命中", "不存在的商品", 3, "[]"),
        ("空关键词", "  ", 3, "ValueError"),
        ("零上限", "单价", 0, "ValueError"),
        ("bool 上限", "单价", True, "ValueError"),
    ]
    for label, keyword, limit, expected in cases:
        print(f"\n{label}；期望：{expected}")
        try:
            hits = search_notes(keyword, limit)
        except ValueError as error:
            print(f"实际：ValueError: {error}")
        else:
            print(f"实际：{hits}")


if __name__ == "__main__":
    main()


# 现象与原因（学员运行后填写）
# 1. 同样检索青禾笔记本，limit=3 和 limit=1 的输出有什么差别？
#    为什么 limit 不能在每个文件中重新计数？
# 答：limit=3时有两条记录，limit=1时只有一条
#   limit在每个文件中重新计数相当于每个文件单独判断limit，最后输出的条数很可能与limit要求的不同
# 2. 从输出选一条命中，打开 source 对应的文件，核对 line 和 text。
#    为什么要保留这两个出处字段，而不是只给模型一个价格数字？
# 答：[{'source': 'products.txt', 'line': 2, 'text': '青禾笔记本：单价 18 元/本，规格 A5。'}]
#   青禾笔记本：单价 18 元/本，规格 A5。
#   给模型带出处的原文，它才能区分“搜到了商品名”和“找到了价格”，给出line和source方便自己核对
#   如果仍只问乘法，数字就够；需要核对单位、含义或出处时，才需要更多信息。
