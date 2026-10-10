"""Week 02 项目入口：用 extract 抽字段，用 ask 调三工具回答。

在仓库根目录运行：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\info_toolbox\\app.py --help
    .venv\\Scripts\\python.exe weeks\\week02_tools\\info_toolbox\\app.py extract "我叫李娜，在深圳做前端。"
    .venv\\Scripts\\python.exe weeks\\week02_tools\\info_toolbox\\app.py ask "杭州有几笔已支付订单？"

extract 与 ask 都会调用真实模型，会使用仓库根目录 .env 中的密钥。
订单用固定模拟数据；每次进入 ask 模式时重建六条假订单。
"""

import argparse
import json

from database import seed_db
from extractor import extract_with_retry
from tool_calling import ask_with_recovery

# database.py 的 seed_db() 重建订单练习库；
# tool_calling.py 的 ask_with_recovery(question) 返回模型最终答复。


def extract_for_display(text: str) -> str:
    """抽取文本并返回可显示的 JSON；失败时返回提示。"""
    person = extract_with_retry(text)
    if person is None:
        return "提取失败"
    raw = person.model_dump()
    return json.dumps(raw, ensure_ascii=False)


def answer_with_tools(question: str) -> str:
    """重建模拟订单库，再让模型调用三个工具回答问题。"""
    seed_db()
    return ask_with_recovery(question)


def run_project(mode: str, text: str) -> str:
    """按 extract 或 ask 模式运行，并返回结果文字。"""
    if mode == "extract":
        return extract_for_display(text)
    if mode == "ask":
        return answer_with_tools(text)
    else:
        raise ValueError("模式不支持！支持：extract / ask")


def main(argv: list[str] | None = None) -> int:
    """解析命令行的模式与文本，打印项目结果。"""
    # ArgumentParser(description=...)：生成 --help 和缺参数时的错误提示。
    parser = argparse.ArgumentParser(description="Week 02：结构化抽取与三工具问答")
    # add_argument(名字, choices=...)：声明必填的位置参数及允许值。
    parser.add_argument("mode", choices=["extract", "ask"], help="选抽取或工具问答")
    parser.add_argument("text", help="要抽取的原文，或要回答的问题；带空格时用引号包住")
    # parse_args(argv)：argv 不传时读取实际命令行；传列表时可离线检查入口。
    args = parser.parse_args(argv)
    print(run_project(args.mode, args.text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
