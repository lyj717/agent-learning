"""Day 3 练习：函数、默认参数、可变默认参数的陷阱、类型注解、lambda。

写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day03_exercises.py

本日考点（想不起来去查 docs/python-7天补齐清单.md 的 Day 3，或翻演示脚本）：
  - 默认参数：def f(a, b=5)     调用时 b 可以省略
  - 关键字参数：f(a, b=10)      调用时按名字传，顺序就不重要
  - 类型注解：def f(x: int) -> str:     给人和工具看的说明书
    要会写这几种：str / int / float / bool / list[str] / dict[str, Any] / str | None
  - lambda：sorted(..., key=lambda x: x["score"])
  - 不可变默认值 vs 可变默认值（第 4 题就是专门挖这个坑）

做题规矩照旧：先自己想 20 分钟；每写完一题单独跑一次；
卡住就按 notes/卡住了怎么办.md 里的五招走，还不行再问我。
"""

from typing import Any

# 模拟一份「检索结果」。真实场景里这是向量库返回的东西，
# 你想在 Day 5 学 RAG 时会天天见到这个结构。
MOCK_DOCS = [
    {"title": "Agent 基础概念", "score": 0.62, "tags": ["agent", "基础"]},
    {"title": "工具调用详解", "score": 0.95, "tags": ["agent", "tools"]},
    {"title": "RAG 检索入门", "score": 0.78, "tags": ["rag"]},
    {"title": "提示词工程", "score": 0.85, "tags": ["prompt"]},
    {"title": "向量数据库选型", "score": 0.71, "tags": ["rag", "vector"]},
]


# ============================================================
# 第 1 题 + 第 2 题
# ============================================================


def search(
    query: str, top_k: int = 5, filters: list[str] | None = None
) -> list[dict[str, Any]]:
    """模拟一次检索。
    参数说明：
        query    用户的问题（这一题里不用真的去搜，忽略它即可）
        top_k    最多返回几条，默认 5
        filters  可选的标签过滤，形如 ["rag"]；传多个标签时要求
                 全部命中（AND），不是「命中任意一个」；
                 不传时不过滤任何东西
    期望结果：
        search("任意问题")
            -> 五条，按 score 从高到低：
               [工具调用详解 0.95, 提示词工程 0.85, RAG 检索入门 0.78,
                向量数据库选型 0.71, Agent 基础概念 0.62]
        search("任意问题", top_k=2)
            -> 前两条
        search("任意问题", filters=["rag"])
            -> 只有 RAG 检索入门 0.78 和 向量数据库选型 0.71
        search("任意问题", filters=["rag", "vector"])
            -> 只有 向量数据库选型 0.71
               （RAG 检索入门 只带 rag 标签、缺 vector，所以落选——
                 这条能区分 AND 和 OR 两种理解）

    """
    filter_doc = []
    if not filters:
        filter_doc = sorted(MOCK_DOCS, key=lambda x: x["score"], reverse=True)[:top_k]
    else:
        for doc in MOCK_DOCS:
            tag_count = 0
            for tag in filters:
                if tag in doc["tags"]:
                    tag_count += 1
            if tag_count == len(filters):
                filter_doc.append(doc)
        filter_doc = sorted(filter_doc, key=lambda x: x["score"], reverse=True)[:top_k]
    return filter_doc


# ============================================================
# 第 3 题
# ============================================================


def sort_by(
    records: list[dict[str, Any]], field: str, reverse: bool = True
) -> list[dict[str, Any]]:
    """按指定的字段给记录排序，返回新列表。这一个函数要能应付「按分数排」「按标题排」等所有情况
    期望结果：
        sort_by(MOCK_DOCS, "score")            -> 按分数从高到低
        sort_by(MOCK_DOCS, "score", reverse=False) -> 按分数从低到高
        sort_by(MOCK_DOCS, "title")            -> 按标题排（字符串按字典序）
    """
    return sorted(records, key=lambda x: x[field], reverse=reverse)


# ============================================================
# 第 4 题：可变默认参数的陷阱
# ============================================================


# 行尾的 noqa 是给检查工具看的：这一行的写法是「故意的反面教材」。
# ruff 有一条专门的规则 B006 来抓「可变对象当默认值」，这行会被它拦下来——
# 这条规则之所以存在，正是因为踩这个坑的人太多了。
def add_to_basket_wrong(item, basket=[]):  # noqa: B006
    """故意写错的版本：默认值直接用了可变对象。"""
    basket.append(item)
    return basket


def add_to_basket_right(item, basket=None):
    # 正确做法
    if basket is None:
        basket = []
    basket.append(item)
    return basket


if __name__ == "__main__":
    print("=== 第 1、2 题：模拟检索 ===")
    for doc in search("任意问题"):
        print(f"  {doc['score']: .2f}  {doc['title']}")

    print("\n  只要前两条：")
    for doc in search("任意问题", top_k=2):
        print(f"  {doc['score']: .2f}  {doc['title']}")

    print("\n  只要带 rag 标签的：")
    for doc in search("任意问题", filters=["rag"]):
        print(f"  {doc['score']: .2f}  {doc['title']}")

    print("\n=== 第 3 题：按字段排序 ===")
    print("  按分数降序：")
    for doc in sort_by(MOCK_DOCS, "score"):
        print(f"    {doc['score']: .2f}  {doc['title']}")

    print("  按标题排序：")
    for doc in sort_by(MOCK_DOCS, "title"):
        print(f"    {doc['title']}")

    print("\n=== 第 4 题：可变默认参数 ===")
    print("  错误版连续调用两次：")
    print(f"    第一次：{add_to_basket_wrong('苹果')}")
    print(f"    第二次：{add_to_basket_wrong('香蕉')}")

    print("  正确版连续调用两次：")
    print(f"    第一次：{add_to_basket_right('苹果')}")
    print(f"    第二次：{add_to_basket_right('香蕉')}")

# ============================================================
# 现象与原因（第 4 题跑完之后，把你的观察和解释写在这里）
# ============================================================
#
# 错误版第二次调用拿到的列表是：['苹果', '香蕉']
#
# 原因是：默认值 [] 在函数定义时就求值了一次，这个列表就挂在函数对象上，
#        之后每次不传 basket 的调用用的都是同一个列表，
#        所以第二次能看到上一次留下的苹果
#
# 正确版为什么没问题：真正的新列表在函数体里创建，属于调用时执行，
#               每次调用都新建一个，所以两次互不影响。
