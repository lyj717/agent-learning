"""Day 33 知识点：幂等，只用普通 Python 观察重复请求。

这份没有 LangGraph、interrupt 或 resume。先把「一次动作怎样算重复」看清，
整合演示再把这个小函数放到人工确认之后。
阅读顺序：main → record_once。
"""


def main() -> None:
    """用同编号与新编号对照，观察动作是否新增。"""
    print("=== 1. 这是什么 ===")
    print("本例修改一个列表，模拟已经执行过的动作记录。")
    print("幂等：同一个动作重复请求，实际效果与只做一次相同。")

    print("\n=== 2. 为什么需要它 ===")
    print("网络重试可能把同一次操作提交两遍；业务编号让系统识别同一个动作。")

    print("\n=== 3. 场景与函数接口 ===")
    print("收件记录 receipt-18 重试一次；另一条记录 receipt-19 应当正常新增。")
    print("record_once(action_id, recorded_ids)")
    print("action_id：本次动作的业务编号；recorded_ids：已经执行过的编号列表。")
    print("返回 bool：True 表示这次新增了记录，False 表示重复请求被跳过。")

    print("\n=== 4. 代码与真实输出 ===")
    recorded_ids: list[str] = []
    for action_id in ["receipt-18", "receipt-18", "receipt-19"]:
        added = record_once(action_id, recorded_ids)
        print(
            f"请求 {action_id}：新增={added}；"
            f"实际动作数={len(recorded_ids)}；记录={recorded_ids}"
        )

    print("\n=== 5. 注意什么 ===")
    print("用稳定的业务编号判断重复，不能每次重试都换一个新编号。")
    print("本例列表只在当前进程有效，真实系统要持久保存编号并防止并发重复写入。")
    print("这里先掌握输入、去重与效果；人工确认流程留在整合演示里连接。")


def record_once(action_id: str, recorded_ids: list[str]) -> bool:
    """同一业务编号只新增一次；通过返回值说明本次是否真正新增。"""
    if action_id in recorded_ids:
        return False
    recorded_ids.append(action_id)
    return True


if __name__ == "__main__":
    main()
