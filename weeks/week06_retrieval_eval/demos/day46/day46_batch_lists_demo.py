"""Day46 补充：用工具耗时说明循环内的一次结果与循环外的整批收集列表。"""


def main() -> None:
    """观察列表创建位置如何影响保留的数据，不实现检索整合练习。"""
    print("Week6 要保存整批评测结果。Day46 需要同时处理一题的数据和整批的数据。")
    print("本演示只补一个 Python 用法：列表放在哪创建，才能保留每一次结果。")
    print("下方两次工具耗时为 AI 人工数据，没有发请求，不是学员实验。")
    observations = [("查天气", 12), ("查日程", 20)]

    print("\n一、每次循环都创建列表，会丢掉前面收集的数据。")
    print("场景：想把两次工具调用的耗时都收集起来，最后再统计。")
    for tool_name, elapsed_ms in observations:
        durations = []
        durations.append(elapsed_ms)
        print(f"当前工具={tool_name}；当前一次耗时={elapsed_ms}；列表={durations}")
    print(f"循环结束只剩={durations}；第二次 durations=[] 清掉了第一次的内容。")

    print("\n二、循环前创建一次列表，循环里逐次追加，才能保留整批数据。")
    durations = []
    for tool_name, elapsed_ms in observations:
        durations.append(elapsed_ms)
        print(f"当前工具={tool_name}；当前一次耗时={elapsed_ms}；累计列表={durations}")
    print(f"循环结束保留={durations}；整批总耗时={sum(durations)} 毫秒。")

    print("\n三、注意：变量分别负责什么。")
    print("elapsed_ms 每次装一次调用的耗时；durations 装全部调用的耗时。")
    print("sum(durations) 等两次都收集完再调用，得到整批统计。")
    print("空批次也应提前创建 durations=[]；循环零次后，这个列表仍然存在。")
    print("回到 A：单题 metrics、逐题 rows、用于整批汇总的 samples 有不同用途。")
    print("先分清你要保存一次结果还是累计全部结果，再决定列表的创建位置。")


if __name__ == "__main__":
    main()
