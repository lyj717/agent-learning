"""Day 34 答疑：收到响应但缺用量，与请求超时没有拿到响应的区别。

直接运行；只调用已讲过的离线模型入口，不联网、不执行工具、不运行学员的节点。
阅读顺序：main。两种情境各发一次独立请求，不需要先运行其他演示。
"""

import sys
from pathlib import Path

# __file__ 定位仓库根目录，运行不依赖当前终端目录。
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weeks.week04_frameworks.demos.day34 import day34_support as support


def main() -> None:
    """用两次独立调用，区分响应字典中的 None 字段与抛异常没有返回字典。"""
    print("=== 1. 这是什么 ===")
    print("响应是模型这次交回的一份数据；usage 只是其中记录用量的一个字段。")
    print("usage=None 表示没有提供用量，不等于整个响应是 None。")

    print("\n=== 2. 为什么要分开 ===")
    print("拿到了响应，才能读取其中的 message；拿到了用量，才能统计已知 token。")
    print("响应可以是一条工具点单，不一定已经是最终答复。")

    print("\n=== 3. 具体场景 ===")
    print("沿用 support.request_model：传原生消息字典列表、情境名与单次超时秒数。")
    print("第一种情境正常返回点单但不提供用量；第二种情境直接抛 TimeoutError。")
    print("都是固定教学情境，不是网络实测；第二种也不是真的等待到超时。")

    print("\n=== 4.1 收到了响应，但 response['usage'] 是 None ===")
    # request_model(原生消息列表, scenario=情境, timeout_seconds=秒数)：一次离线响应。
    response = support.request_model(
        [{"role": "user", "content": support.QUESTION}],
        scenario="usage_unknown",
        timeout_seconds=1.0,
    )
    print("调用正常返回，response 变量已经拿到一份字典。")
    print(f"response 的类型：{type(response).__name__}")
    print(f"response['message']['role']：{response['message']['role']}")
    print(f"response['finish_reason']：{response['finish_reason']}")
    print(f"assistant 点单数量：{len(response['message']['tool_calls'])}")
    print(f"response['usage']：{response['usage']}")
    print("消息已经有了，可以处理点单；只有 token 用量没有给出。")
    print("本课记账约定：usages 加一项 None，表示这份已收到的响应缺少用量。")

    print("\n=== 4.2 请求超时，没有拿到这次响应 ===")
    try:
        timed_response = support.request_model(
            [{"role": "user", "content": support.QUESTION}],
            scenario="slow_model",
            timeout_seconds=0.05,
        )
    except TimeoutError as error:
        # TimeoutError 是 Python 内置异常；跳到这里时，上面的赋值没有完成。
        print(f"进入 except：{type(error).__name__}；{error}")
        print("这次调用没有正常返回字典，timed_response 的赋值没有完成。")
        print("没有本次响应的 message、finish_reason 或 usage 可以读取。")
        print("本课记账约定：usages 保持原样；steps 仍记一次已尝试的请求。")
    else:
        # else 只在 try 没有抛异常时运行；这里防止教具变化后还打印错误的解释。
        raise AssertionError(f"教具预期超时，却返回了：{timed_response}")

    print("\n=== 5. 注意什么 ===")
    print("收到响应但缺用量：正常返回字典，只是 usage 字段为 None。")
    print("超时未拿到响应：调用抛出异常，没有这次的返回字典。")
    print("两种情况都不能解释为实际消耗为 0。")
    print("usages 在本课只保存已收到响应的用量记录；steps 另记所有请求尝试。")
    print("是否继续请求由练习里的停止规则决定，本文件只观察两种接口结果。")


if __name__ == "__main__":
    main()
