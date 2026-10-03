"""命令行入口：把参数、配置、模型调用串成一个能用的工具。

用法（README 里有完整说明）：
    .venv\\Scripts\\python.exe weeks\\week00_python\\chat_cli\\chat_cli.py "用一句话说明什么是异步"
    ... --no-stream                一次性输出，不要打字机效果
    ... --system "你只答一句话"      换人设
    ... --model deepseek-chat      换模型
    ... --verbose                  打出 DEBUG 日志

要写三个函数：
    parse_args()     第 1 条要求：用 argparse 接参数
    setup_logging()  第 3 条要求：用 logging 打日志
    main()           把上面两块和 llm 里的函数串起来
"""

import argparse
import logging

from llm import build_request, chat, stream_chat


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """定义并解析命令行参数。
    要做的（照着 weeks/week00_python/argparse_demo.py 第 2 步写）：
        question     位置参数，要问的问题（必填）
        --system     system 提示词，默认 None
        --model      模型名，默认 None（不传就用 .env 里的）
        --no-stream  开关，加上就一次性输出
        --verbose    开关，加上就打 DEBUG 日志
    期望结果：
        parse_args(["你好"]).question            == "你好"
        parse_args(["你好", "--no-stream"]).no_stream is True
        parse_args([]) 会打印用法并退出（argparse 自动做这件事）
    提示：为什么要把 argv 做成参数？为了能测试——测试时传一个列表进去，
         真实运行时传 None（表示读真正的命令行）。
    """
    parser = argparse.ArgumentParser(description="把一个问句交给模型，流式打印回答")
    parser.add_argument("question", help="用户问题")
    parser.add_argument("--system", default=None, help="系统提示词")
    parser.add_argument("--model", default=None, help="模型名")
    parser.add_argument("--no-stream", action="store_true", help="关闭流式输出")
    parser.add_argument("--verbose", action="store_true", help="打开DEBUG日志")
    return parser.parse_args(argv)


def setup_logging(verbose: bool) -> None:
    """按 --verbose 决定日志级别。
    要做的：
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
    注意：basicConfig 只生效一次（Day 5 踩过的坑），所以这个函数只在入口调一次。
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
    # 第三方库会打「请求流水账」（每发一次请求就打一行 HTTP Request ... 200 OK），
    # 那不是要给用户看的信息，会把工具的输出来刷花。
    # 平时把它们压到 WARNING，只留我们自己的日志；加 --verbose 才放开看细节。
    # 注意：这个环境里的 openai 实际用的是 httpx2（被改名过的 httpx），两个都要压。
    if not verbose:
        for noisy in ("httpx", "httpx2"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    """把一切串起来，返回退出码（0 表示成功，非 0 表示失败）。
    要做的：
        1. args = parse_args(argv)
        2. setup_logging(args.verbose)
        3. request = build_request(args.question, model=args.model,
                                  system_prompt=args.system, stream=not args.no_stream)
        4. 流式：for piece in stream_chat(request): print(piece, end="", flush=True)
           非流式：print(chat(request))
        5. 中途出错：用 logger.exception 记下来，返回 1
        6. 正常结束返回 0
    提示：
        - 用 logger = logging.getLogger(__name__) 打日志（Day 5 学的惯例）
        - 别用 sys.exit()，把退出码 return 出去——这样 main 才好测
        - 最后末尾那句 SystemExit(main()) 负责把退出码交给操作系统
        - 流式打印完记得再 print() 一次换行（Day 6 学的）
    """
    logger = logging.getLogger(__name__)
    try:
        args = parse_args(argv)
        setup_logging(args.verbose)
        request = build_request(
            args.question,
            model=args.model,
            system_prompt=args.system,
            stream=not args.no_stream,
        )
        if request.stream:
            for piece in stream_chat(request):
                print(piece, end="", flush=True)
            print()
        else:
            print(chat(request))
    except Exception as error:
        logger.exception(f"调用失败：{type(error).__name__}")
        return 1
    else:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
