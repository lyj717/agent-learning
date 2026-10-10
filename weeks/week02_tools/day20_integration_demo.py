"""Day 20 离线演示：把抽取、工具箱与命令行入口接成一个项目。"""

import argparse
import json

from day16_pydantic_exercises import PersonExtract
from day18_multi_tools_exercises import execute_tool_call
from day18_seed_db import seed_db
from day19_error_recovery_exercises import tool_result_or_error


def section_extract() -> None:
    """展示抽取路径的输入、校验和结构化输出。"""
    print("\n=== 第 1 节：抽取模式 ===")
    print("这是什么：把一段杂乱文本变成固定字段的 JSON。")
    print("为什么需要：别让调用方从自然语言回答里猜姓名、城市等字段。")
    print("场景：用户粘贴一段报名信息，要拿到 name、phone、city、job。")
    print("代码：")
    print("  person = PersonExtract.model_validate_json(raw)")
    print("  result = json.dumps(person.model_dump(), ensure_ascii=False)")
    # json.dumps(对象, ensure_ascii=False)：把 Python 对象转成 JSON 文本；
    # False 让中文原样显示，便于在终端和 README 中阅读。
    raw = json.dumps(
        {"name": "李娜", "phone": None, "city": "深圳", "job": "前端"},
        ensure_ascii=False,
    )
    # model_validate_json(JSON 文本)：解析并按 PersonExtract 的字段规则校验。
    person = PersonExtract.model_validate_json(raw)
    result = json.dumps(person.model_dump(), ensure_ascii=False)
    print(f"本地结果：{result}")
    print(
        "注意：这里喂的是固定假返回，只验证拼装形状；真实抽取要调用 extract_with_retry(text)。"
    )


def section_tools() -> None:
    """展示本地工具与错误回填的现成能力。"""
    print("\n=== 第 2 节：工具问答模式 ===")
    print("这是什么：模型从三份工具说明里选工具；本地函数执行后把结果交还给模型。")
    print("为什么需要：天气、算术和订单应由对应工具给结果，而不是让模型猜。")
    print("场景：用户问杭州有几笔已支付订单，先准备练习库，再执行本地查询。")
    print("代码：")
    print("  seed_db()")
    print('  execute_tool_call("query_orders", \'{"city": "杭州"}\')')
    print('  tool_result_or_error("calculator", \'{"expression": "12 ** 2"}\')')
    # seed_db()：重建六条固定假订单；订单工具要读这份 SQLite 数据。
    seed_db()
    # execute_tool_call(工具名, JSON 参数文本)：按名称找到 Day 18 的本地工具。
    orders = execute_tool_call("query_orders", '{"city": "杭州"}')
    # tool_result_or_error(工具名, JSON 参数文本)：本地异常会变成可回填的文字。
    error = tool_result_or_error("calculator", '{"expression": "12 ** 2"}')
    print(f"订单结果：{orders}")
    print(f"错误结果：{error}")
    print("注意：真实问答要调用 ask_with_recovery(question)；它负责模型请求和调用 ID。")


def section_entry() -> None:
    """展示同一个命令行入口如何收取两种模式。"""
    print("\n=== 第 3 节：一个入口，两种模式 ===")
    print("这是什么：用户先明确选 extract 或 ask，程序再走对应的现成函数。")
    print("为什么需要：JSON 抽取与工具调用用的是两种请求方式，入口应说清任务。")
    print("场景：同一个脚本既能处理报名信息，也能回答订单问题。")
    print("代码：")
    print('  parser.add_argument("mode", choices=["extract", "ask"])')
    print('  parser.add_argument("text")')
    print('  args = parser.parse_args(["ask", "杭州有几笔已支付订单？"])')
    # ArgumentParser(description=...)：创建命令行参数解析器，并生成 --help 说明。
    parser = argparse.ArgumentParser(description="Day 20 双模式入口示意")
    # add_argument(名字, choices=...)：声明必填位置参数及允许的取值。
    parser.add_argument("mode", choices=["extract", "ask"])
    parser.add_argument("text")
    # parse_args(参数列表)：把命令行文字拆成 args.mode 和 args.text；
    # 这里给固定列表，所以演示完全离线，也不依赖你在终端输入什么。
    args = parser.parse_args(["ask", "杭州有几笔已支付订单？"])
    print(f"解析结果：mode={args.mode!r}，text={args.text!r}")
    print("注意：这个演示只展示入口形状；项目成品在 info_toolbox/app.py。")


if __name__ == "__main__":
    section_extract()
    section_tools()
    section_entry()
