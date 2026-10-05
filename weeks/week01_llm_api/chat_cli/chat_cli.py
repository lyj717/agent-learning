"""命令行入口：一个能连续聊天的机器人。

流程就是一句话：读一行 → 是命令就处理 → 不是就发给模型 → 把回答存回历史。

要写的三个函数：
    parse_args()      接 --system / --model 两个参数
    handle_command()  处理 /clear 和 /cost
    main()            REPL 主循环，把上面这些和 llm、conversation 串起来

用法：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe chat_cli.py
"""

import argparse
import logging

from conversation import Conversation


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """定义并解析命令行参数。
    要做的：
        --system   system 人设，默认 None（不给 system）
        --model    模型名，默认 None（用 .env 里的）
    期望结果：
        parse_args(["--system", "只说一句话"]).system == "只说一句话"
        parse_args([]).model is None
    提示：argv 做成参数是为了能测试——测试时传列表，真实运行时传 None。
    """
    raise NotImplementedError("parse_args 还没写")


def handle_command(
    line: str, conversation: Conversation, usage_log: list[tuple[int, int]]
) -> bool:
    """这一行如果是命令就处理掉，返回 True；不是命令返回 False（交给模型）。

    要支持两个命令：
        /clear   清空历史（system 留着），并说一句清掉了几条
        /cost    打印本次会话累计的调用次数、token 和估算花费

    其他以 / 开头的，提示「未知命令」，也算处理掉了（返回 True）。

    usage_log 是每次调用记下来的 (输入 token, 输出 token)，
    /cost 时把它拆成两个列表交给 cost.session_cost() 算总账。

    期望结果：
        handle_command("你好", conversation, []) is False
        handle_command("/cost", conversation, []) is True    # 并打印一行账
        handle_command("/clear", conversation, []) is True   # 之后 messages 只剩 system
    """
    raise NotImplementedError("handle_command 还没写")


def main(argv: list[str] | None = None) -> int:
    """把一切串起来，返回退出码。
    要做的：
        1. args = parse_args(argv)，建 conversation = Conversation(args.system)
        2. usage_log = []，打印欢迎和命令说明
        3. 循环读入一行：
             空行 → 跳过
             /exit 或 /quit → 跳出循环
             handle_command(...) 返回 True → 继续下一轮
             否则 → 拼出这次要发的 messages，调 llm.chat()，把回答和用量收好，
                    再把这轮问答存进历史，最后打印回答
        4. 中途出错：用 logger.exception 记下来，别让程序崩掉，
           而且**不要把这条问句留在历史里**（留着的话下一轮会带着一条没人回答的问题）

    提示：
        - 想避免污染历史，可以先拼 payload = conversation.messages() + [问句]，
          成功了再 conversation.add_user() / add_assistant()
        - 用量记成 (usage.prompt_tokens, usage.completion_tokens) 追加进 usage_log
        - 用 input("你> ") 读一行；Ctrl+C 也要能干净退出
    """
    raise NotImplementedError("main 还没写")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
