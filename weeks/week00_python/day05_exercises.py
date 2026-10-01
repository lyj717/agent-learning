"""Day 5 练习：文件、JSON、异常、环境变量。

写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day05_exercises.py

本日考点（想不起来去查 docs/python-7天补齐清单.md 的 Day 5，
或翻今天的三份演示脚本 day05_file_json_demo.py、day05_exception_demo.py、
day05_env_logging_demo.py）：
  - 文件读写：with open(...) as f:，以及为什么一定要写 encoding="utf-8"
  - pathlib：Path(__file__).parent、p.exists()、p.mkdir(exist_ok=True)
  - JSON：带 s 的 json.loads/json.dumps 吃字符串，不带的吃文件对象
  - 异常：try/except 写具体类型、raise 主动抛、自定义异常类
  - 环境变量：os.environ、load_dotenv、密钥只放 .env 且永不提交

前两题在这个文件里写；第三题是动手操作，步骤在文件末尾。
卡住就按 notes/卡住了怎么办.md 里的六招走，还不行再问我。
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).parent
ROOT = HERE.parent.parent  # 仓库根目录
SAMPLE = HERE / "day05_sample.json"
OUTPUT_DIR = HERE / "outputs"

# 环境变量的名字和 .env.example 里保持一致
API_KEY_ENV = "LLM_API_KEY"

# 主流服务商的密钥都远长于这个数，明显更短基本是没复制完整
MIN_KEY_LEN = 20


class MissingConfigError(Exception):
    """缺少必需的配置时抛这个（第 2 题要用）。"""


def review_dataset(source: Path, target: Path) -> dict:
    """读一份 JSON，改两个地方，写到新路径，返回改好的那份数据。
    要做的（六步）：
        1. 用 with 打开 source 读进来，得到 Python 字典
        2. 把 dataset["version"] 加 1
        3. 给 dataset["documents"] 里每一条加上 "reviewed": True
        4. 确认 target 所在的目录存在（不存在就建）
        5. 把改好的字典写到 target
        6. 返回这个字典（调用方就不用再读一遍文件了）
    期望结果：
        review_dataset(SAMPLE, OUTPUT_DIR / "day05_reviewed.json")
        -> 返回值的 version 是 2，每条文档都有 reviewed: True
        -> 新文件是一段缩进好的 JSON，中文没有被转义成 \\uXXXX
    """
    with source.open(encoding="utf-8") as s_file:
        dataset = json.load(s_file)
    dataset["version"] += 1
    for data in dataset["documents"]:
        data["reviewed"] = True
    target.parent.mkdir(exist_ok=True)
    with target.open("w", encoding="utf-8") as t_file:
        json.dump(dataset, t_file, ensure_ascii=False, indent=2)
    return dataset


def require_api_key(env_name: str = API_KEY_ENV) -> str:
    """拿到 API Key；拿不到就大声报错，不要返回一个假值。
    要做的（四步）：
        1. 调用 load_dotenv(ROOT / ".env")，把 .env 里的值读进环境变量
        2. 从环境变量里取 env_name 对应的值
        3. 取到了、而且长度合理，就返回它
        4. 取不到（或者明显太短），raise MissingConfigError，
           报错信息里写清两件事：缺的是哪个变量、该怎么办
    期望结果：
        环境里有值   -> 返回字符串（注意：不要把这个值打印出来）
        环境里没有   -> 抛 MissingConfigError，信息可以直接念给人听
    """
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get(env_name)
    if not api_key or len(api_key) < MIN_KEY_LEN:
        raise MissingConfigError(
            f"缺少配置 {env_name}：请在仓库根目录复制 .env.example 为 .env，并填入真实值"
            f"（当前长度 {len(api_key) if api_key else 0}，疑似没复制完整）"
        )
    return api_key


if __name__ == "__main__":
    print("=== 第 1 题：读 JSON、改字段、写回新文件 ===")
    target = OUTPUT_DIR / "day05_reviewed.json"
    result = review_dataset(SAMPLE, target)
    print(f"  version = {result['version']}（原始是 1）")
    print(f"  每条都有 reviewed 吗：{all(d['reviewed'] for d in result['documents'])}")
    print(f"  写到：{target}")
    print(f"  它存在吗：{target.exists()}")

    print("\n=== 第 2 题：读 API Key ===")
    try:
        key = require_api_key()
        print(f"  拿到了：{len(key)} 个字符的字符串（内容不打印）")
    except MissingConfigError as error:
        print(f"  按预期报错：{error}")

    print("\n=== 第三题不在这里写代码 ===")
    print("  看文件末尾「动手：建一个干净的虚拟环境」那一节")


# ============================================================
# 现象与原因（做完之后填）
# ============================================================
#
# 1. 第 1 题里读文件和写文件，你分别用了哪个 json 方法？
#    为什么不能把带 s 的那个直接用在文件对象上？
#    读文件：load 写文件：dump
#    s的含义是string，带s的方法是给字符串对象用的
# 2. 如果读写文件时忘了写 encoding="utf-8"，在你这台机器上会发生什么？
#    报错：UnicodeDecodeError: 'gbk' codec can't decode byte 0xad in position 2: illegal multibyte sequence
#    关键就是开头那个 'gbk'——python 拿系统默认编码去解 utf-8 的文件了
#
# 3. require_api_key 里为什么不能写成
#    os.environ.get(env_name, "test") 这种带默认值的做法？
#    带默认值会导致如果api_key不合法程序依然会带着默认值的假密钥运行
#
# 4. 动手：建一个干净的虚拟环境
#
#    一行一行敲下面的命令，注意看每一步的输出：
#
#      python -m venv .tmp_env
#      .tmp_env\Scripts\python.exe -m pip install httpx pydantic python-dotenv
#      .tmp_env\Scripts\python.exe -m pip list
#      .tmp_env\Scripts\python.exe -c "import httpx, pydantic, dotenv; print('三个包都能导入')"
#      Remove-Item .tmp_env -Recurse -Force
#
#    要观察的三件事：
#      a. 刚建好的环境里 pip list 有几行？为什么这么少？
#      只有一行，因为只新建了一个环境，什么包都没装，只有pip
#      b. 装完三个包之后多出多少行？哪些是被连带装上的？
#      多出了13行，10个被连带装上的
#      c. 这个临时环境和仓库里的 .venv 有关系吗？
#      没有关系，是一个独立的虚拟环境
