"""Day 2 练习：容器、切片、推导式、字典操作、排序、解包。

三道题的函数体是空的，需要你自己写。写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day02_exercises.py

本日考点（想不起来怎么写时，去 docs/python-7天补齐清单.md 的 Day 2 那一段查，
或者翻 weeks/week00_python/day02_for_loop_demo.py、day02_partition_demo.py）：
  - 列表推导式：一行生成一个新列表
  - 字典取值：d["k"] 取不到会报错，d.get("k", 默认值) 不会
  - 字典计数：counts.get(word, 0) + 1 这个固定套路
  - 排序：sorted(..., key=lambda item: item[1], reverse=True)
  - 切片：items[:5] 取前五个
  - 字符串拼接："\\n".join(列表)

做题规矩和 Day 1 一样：先自己想 20 分钟；每写完一题单独跑一次；
卡住就把报错原文和你的猜测一起发我。
"""


def join_user_messages(messages: list[dict]) -> str:
    """把所有 role 是 "user" 的消息内容拼成一个字符串，用换行分隔。

    输入长这样（这就是 Agent 开发里对话历史的标准结构）：
        [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮你"},
            {"role": "user", "content": "帮我查天气"},
        ]

    期望结果："你好\\n帮我查天气"

    考点：列表推导式 + 字典取值 + join。
    如果列表里一条 user 消息都没有，应返回空字符串。
    """
    contents = []
    for message in messages:
        if message["role"] == "user":
            contents.append(message["content"])
    return "\n".join(contents)


def top_words(text: str, limit: int = 5) -> list[tuple[str, int]]:
    """统计每个词出现的次数，返回次数最多的前 limit 个。
    期望结果：
        top_words("the cat and the dog and the bird", 2)
            -> [("the", 3), ("and", 2)]
        top_words("a a b", 5)
            -> [("a", 2), ("b", 1)]
        top_words("", 3)
            -> []

    考点：字典做计数器 + sorted 配 key=lambda + 切片取前几个。
    提示：用 text.split() 把句子切成单词列表。
    注意：统计时用 counts.get(word, 0) + 1，这是字典计数的固定写法。
    """

    counts = {}
    words = text.split(" ")
    tops = []
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    tops = list(counts.items())
    sorted(tops, key=lambda x: x[1])

    return tops


def flatten_orders(orders: list[dict]) -> list[tuple[str, str, int]]:
    """把嵌套的订单结构拍平成 (订单号, 商品名, 数量) 的列表。

    输入长这样：
        [
            {
                "order_id": "A1",
                "items": [
                    {"name": "键盘", "qty": 2},
                    {"name": "鼠标", "qty": 1},
                ],
            },
            {
                "order_id": "A2",
                "items": [{"name": "显示器", "qty": 1}],
            },
        ]

    期望结果：
        [("A1", "键盘", 2), ("A1", "鼠标", 1), ("A2", "显示器", 1)]

    考点：嵌套遍历（外层订单、内层商品）+ 每层取字典的值 + 组装元组。
    这个「拍平」动作在你以后解析模型返回的嵌套 JSON 时天天用到。
    """
    raise NotImplementedError("第 3 题还没写")


if __name__ == "__main__":
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你"},
        {"role": "user", "content": "帮我查天气"},
    ]

    print("=== 第 1 题：拼接 user 消息 ===")
    print(join_user_messages(history))
    print(f"（只有 assistant 时：{join_user_messages([history[1]])!r}）")

    print("\n=== 第 2 题：词频前 N ===")
    for text, limit in [
        ("the cat and the dog and the bird", 2),
        ("a a b", 5),
        ("", 3),
    ]:
        print(f"  {text!r} 前 {limit} 个 -> {top_words(text, limit)}")

    print("\n=== 第 3 题：拍平订单 ===")
    orders = [
        {
            "order_id": "A1",
            "items": [
                {"name": "键盘", "qty": 2},
                {"name": "鼠标", "qty": 1},
            ],
        },
        {"order_id": "A2", "items": [{"name": "显示器", "qty": 1}]},
    ]
    for row in flatten_orders(orders):
        print(f"  {row}")
