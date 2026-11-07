"""Day51B 补充：用书架认识字典中按名称保存的多个列表。

只讲分组容器的创建、追加与读取；HTTP 和历史记录仍由学员在练习中组合。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weeks.week06_retrieval_eval.demos.shared.run_logs import run_logged


def demonstrate_groups(run_dir: Path) -> None:
    """观察三个放书动作怎样进入两个列表，以及未知书架怎样读取。"""
    print("Day51B 要让不同会话各有自己的历史列表。")
    print("本例先用不同书架各有一个书名列表，补上分组容器的用法。")
    print("学完应能找到一个分组的列表，再追加、读取；之后用于练习 B 的历史保存。")
    print("\n一、是什么：字典的键是书架名称，值是这个书架上的书名列表。")
    print("为什么：只有一个列表时，Python 和 SQL 的书会混在一起。")
    print("场景：依次把《入门》《查询》《进阶》放到 Python、SQL、Python 书架。")
    print("都是人工数据，不涉及 HTTP、检索或模型。")

    print("\n二、先创建一个空字典，不预先写死有哪些书架")
    shelves: dict[str, list[str]] = {}
    print("代码：shelves: dict[str, list[str]] = {}")
    print("str 表示键是字符串；list[str] 表示每个值都是书名列表。")
    print("实际：", shelves)

    print("\n三、每次放书：没有这个书架才新建列表，然后向这个书架追加")
    print("核心代码：")
    print("  if category not in shelves:")
    print("      shelves[category] = []")
    print("  shelves[category].append(title)")
    print("category not in shelves 检查字典里有没有这个键。")
    print("shelves[category] 取出该键对应的列表；append(title) 向列表末尾加一本书。")
    for category, title in [("Python", "入门"), ("SQL", "查询"), ("Python", "进阶")]:
        print("\n本次 category =", category, "；title =", title)
        if category not in shelves:
            shelves[category] = []
            print("首次遇到这个书架，给它创建一个空列表。")
        else:
            print("书架已经存在，保留原来的列表。")
        shelves[category].append(title)
        print("追加后整个字典：", shelves)

    print("\n四、读取一个书架，而不是返回整个字典")
    print('shelves["Python"] 实际：', shelves["Python"], "；期望：['入门', '进阶']")
    # dict.get(键, 默认值)：有键时返回对应值，无键时返回默认值，不新增键。
    print('shelves.get("SQL", []) 实际：', shelves.get("SQL", []), "；期望：['查询']")
    print('shelves.get("网络", []) 实际：', shelves.get("网络", []), "；期望：[]")
    print("get(名称, [])：找到就返回该书架的列表；找不到就返回空列表。")
    print("未知名称读取后，原字典没有新增书架：", shelves)

    print("\n五、注意与练习的对应")
    print("键：本例是 category，练习是已经 strip 的 session_id。")
    print("值：本例是书名列表，练习是历史记录列表，每条记录本身是 dict。")
    print("外层字典属于整个应用；字典内每个键对应一个会话的列表。")
    print("不能每次都执行 shelves[category] = []，否则会清掉该书架已有的书。")
    print("查询时读取指定键；原样返回整个容器会把所有分组一起返回。")
    print("本例到此，练习中的 HTTP、旧问答与记录结构继续使用你已写的代码。")
    print("本轮留证目录：", run_dir)


def main() -> None:
    """保存分组容器演示的输出，保持学员练习不变。"""
    run_logged(
        "grouped_lists_demo",
        demonstrate_groups,
        {"transport": "python_only", "model_calls": 0},
        Path(__file__),
        Path(__file__).parent / "outputs",
        origin_env="DAY51B_RUN_ORIGIN",
    )


if __name__ == "__main__":
    main()
