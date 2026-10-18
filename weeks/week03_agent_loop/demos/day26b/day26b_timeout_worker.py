"""Day 26B 的固定慢工具：只等待指定秒数，再返回一条检索观察。"""

import sys
import time


def main() -> None:
    """按命令行给定的秒数模拟一次本地检索。"""
    delay_seconds = float(sys.argv[1])  # sys.argv[1] 是传给本脚本的等待秒数文本。
    # time.sleep(秒数)：暂停当前程序，用来模拟工具迟迟没有返回。
    time.sleep(delay_seconds)
    print("found 2 notes")


if __name__ == "__main__":
    main()
