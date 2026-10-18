"""Day 33 知识点：客服先写通知文案，再模拟发送到客户收件箱。

customer_inbox 列表代表一位客户的收件箱，每个元素代表一条已收到的通知。
先看 main 中的完整情景，再读 make_notice_text 与 send_notice；这里没有真实发送。
"""


def main() -> None:
    """跟随客服生成、发送、重复发送一条维修通知。"""
    print("=== 1. 这是什么 ===")
    print("副作用：函数除了给调用者一个返回值，还改变了函数外面的东西。")
    print("下面具体看『客户收件箱里多了一条通知』这个改变。")

    print("\n=== 2. 为什么需要知道 ===")
    print("客服需要知道：目前只是写好了文案，还是客户已经收到通知。")
    print("函数返回了什么，以及客户收件箱变成什么，是需要分别观察的两件事。")

    print("\n=== 3. 场景与接口 ===")
    print("你是维修店客服。订单 repair-42 已经修好，现在要通知客户到店取件。")
    print("第一步：make_notice_text(order_id) 根据订单号写好一段文案，返回 str。")
    print("第二步：send_notice(text, customer_inbox) 把文案放进客户收件箱，返回 None。")
    print("本例只有一位客户；customer_inbox 是他的模拟收件箱。")
    print("列表为空表示尚未收到通知；每增加一个元素，就表示多收到一条。")
    print("所谓『发送』只由列表的 append 模拟，没有连接真实消息服务。")

    print("\n=== 4. 代码与真实输出 ===")
    customer_inbox: list[str] = []
    print(f"开始时客户收件箱：{customer_inbox}")

    text = make_notice_text("repair-42")
    print("\n4.1 客服先生成文案：")
    print(f"    函数返回给客服程序：{text}")
    print(f"    客户收件箱：{customer_inbox}，仍为 0 条，客户还没有收到通知。")

    result = send_notice(text, customer_inbox)
    print("\n4.2 客服调用发送函数：")
    print(f"    函数返回给客服程序：{result}")
    print(f"    客户收件箱：{customer_inbox}")
    print(f"    客户已收到 {len(customer_inbox)} 条通知；这个变化就是本例的副作用。")

    send_notice(text, customer_inbox)
    print("\n4.3 客服又调用了一次发送函数：")
    print(f"    客户收件箱：{customer_inbox}")
    print(f"    现在共 {len(customer_inbox)} 条，相同文案被收到两次。")

    print("\n=== 5. 注意什么 ===")
    print("返回值是函数交给调用者的东西；副作用是调用后留下的其他变化。")
    print("send_notice 返回 None，但已经改变 main 中的 customer_inbox。")
    print("副作用不是坏事；发通知本来就是目标，只是重复执行会再产生一次效果。")


def make_notice_text(order_id: str) -> str:
    """根据维修订单号生成文案，交回给客服程序。"""
    return f"您的订单 {order_id} 已维修完成，请到店取件。"


def send_notice(text: str, customer_inbox: list[str]) -> None:
    """把一条通知放进传入的模拟收件箱；没有 return 时返回 None。"""
    # 这里收到 main 里的同一份列表；append 会直接修改它，不会另建一个收件箱。
    customer_inbox.append(text)


if __name__ == "__main__":
    main()
