"""环境自检脚本。

作用：确认虚拟环境、依赖、密钥配置都正常。每次换机器或换项目都先跑一遍。

用法：
    .venv\\Scripts\\python.exe check_env.py          # 只检查环境
    .venv\\Scripts\\python.exe check_env.py --live   # 额外发一次真实 API 请求

读这个文件时可以留意几个 Python 特有的写法：
- 三引号字符串做文档注释
- `import os` / `from pathlib import Path`：模块导入
- `if __name__ == "__main__":`：只在直接运行时执行的入口
- 类型注解 `-> None`、`list[str]`
"""

import argparse
import os
import sys
from pathlib import Path

# 仓库根目录（这个文件所在的位置）
ROOT = Path(__file__).parent

# 每一项：要检查的包名 -> 在代码里 import 的名字
REQUIRED_PACKAGES = {
    "openai": "openai",
    "httpx": "httpx",
    "python-dotenv": "dotenv",
    "pydantic": "pydantic",
    "rich": "rich",
    "pytest": "pytest",
}

# 主流服务商的密钥都远长于这个数，明显更短基本是没复制完整
MIN_KEY_LEN = 20


def check_python() -> bool:
    """检查 Python 版本。Agent 开发建议 3.11 以上。"""
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"

    if version < (3, 11):
        print(f"  [x] Python {version_text}：版本偏低，建议升级到 3.11 以上")
        return False

    # sys.prefix 会指向虚拟环境目录；如果它等于基础环境，说明没激活 venv
    in_venv = sys.prefix != sys.base_prefix
    venv_text = "已启用虚拟环境" if in_venv else "未启用虚拟环境（建议激活 .venv）"

    print(f"  [v] Python {version_text}：{venv_text}")
    print(f"      解释器路径：{sys.executable}")
    print(f"      当前工作目录：{Path.cwd()}")
    return in_venv


def check_packages() -> bool:
    """逐个尝试导入依赖，报告缺哪个。"""
    missing = []

    for package_name, import_name in REQUIRED_PACKAGES.items():
        try:
            module = __import__(import_name)
            # 模块不一定有 __version__，取不到就显示 unknown
            version = getattr(module, "__version__", "unknown")
            print(f"  [v] {package_name} {version}")
        except ImportError:
            missing.append(package_name)
            print(f"  [x] {package_name}：未安装")

    if missing:
        print(
            f"\n  修复：.venv\\Scripts\\python.exe -m pip install {' '.join(missing)}"
        )

    return not missing


# 中文标点出现在配置值里通常说明是手误（比如把 = 打成了 ＝）
SUSPICIOUS_PUNCTUATION = "，。；：（）＝“”‘’【】、《》"


def inspect_env_format(env_path: Path) -> bool:
    """体检 .env 的书写格式。

    记事本保存的文件可能带 BOM，或者混入中文标点，这些都会导致配置读不出来，
    但报错信息往往很隐晦，所以这里主动检查一次。
    """
    raw = env_path.read_bytes()
    problems: list[str] = []

    # Windows 记事本另存为「UTF-8 带 BOM」时，文件头会多出三个字节
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("文件开头有 BOM 标记，第一个配置项会读不出来")
        problems.append(
            "  修复：记事本里「另存为」，编码选「UTF-8」（不要选带 BOM 的那个）"
        )

    text = raw.decode("utf-8-sig", errors="replace")

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            problems.append(f"第 {line_number} 行没有等号，这一行会被忽略")
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        found = [char for char in SUSPICIOUS_PUNCTUATION if char in value]
        if found:
            problems.append(
                f"第 {line_number} 行 {key} 的值里有中文标点：{' '.join(found)}"
            )

        if " " in value:
            problems.append(f"第 {line_number} 行 {key} 的值里有空格，可能多了空格")

        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            problems.append(f"第 {line_number} 行 {key} 的值被引号包着，建议去掉引号")

    expected_keys = {"LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "DEBUG"}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.partition("=")[0].strip()
        if key not in expected_keys:
            problems.append(f"出现未知配置项 {key}，代码不会读它（不影响运行）")

    if problems:
        for problem in problems:
            print(f"  [!] {problem}")
        return False

    print("  [v] .env 格式正常（无 BOM、无多余空格、无中文标点）")
    return True


def check_env_file() -> tuple[bool, str]:
    """检查 .env 文件与密钥。返回（是否就绪, 密钥）。"""
    env_path = ROOT / ".env"

    if not env_path.exists():
        print("  [x] 没有找到 .env 文件")
        print("      修复：copy .env.example .env，然后填入你的密钥")
        return False, ""

    print("  [v] .env 文件存在")

    # 记事本等编辑器可能存出带 BOM 或带中文标点的文件，先做一次格式体检
    if not inspect_env_format(env_path):
        print("      格式有问题会读不到配置，建议按上面的提示改一下")

    # load_dotenv 会把 .env 里的内容塞进环境变量
    from dotenv import load_dotenv

    load_dotenv(env_path)
    api_key = os.environ.get("LLM_API_KEY", "")

    if not api_key or "填入" in api_key:
        print("  [!] 密钥还没填（.env 里仍然是示例内容）")
        return False, api_key

    if len(api_key) < MIN_KEY_LEN:
        print("  [!] 密钥看起来太短，确认有没有复制完整")
        return False, api_key

    # 只显示前后几位，不要把完整密钥打印出来或写进日志
    masked = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"  [v] 密钥已配置：{masked}")
    return True, api_key


def check_gitignore() -> bool:
    """确认 .env 不会被提交。这个检查比看起来重要。"""
    gitignore = ROOT / ".gitignore"

    if not gitignore.exists():
        print("  [x] 没有 .gitignore，密钥有泄露风险")
        return False

    content = gitignore.read_text(encoding="utf-8")
    if ".env" in content:
        print("  [v] .gitignore 已屏蔽 .env")
        return True

    print("  [x] .gitignore 里没有屏蔽 .env")
    return False


def live_test(api_key: str) -> bool:
    """发一次真实请求，验证密钥和网络都通。"""
    from openai import OpenAI

    base_url = os.environ.get("LLM_BASE_URL") or None
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    print(f"  使用模型：{model}")
    print(f"  接口地址：{base_url or '默认'}")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回答一个字：好"}],
            # 推理类模型会先花掉一部分额度做内部推理，给太小会导致正文为空
            max_tokens=200,
        )

        choice = response.choices[0]
        content = choice.message.content or ""
        print(f"  [v] 调用成功，模型回复：{content.strip() or '(空)'}")
        print(f"      结束原因：{choice.finish_reason}")

        # usage 里是本次消耗的 token 数，Day 9 会用它算成本
        if response.usage:
            print(
                f"      token 用量：输入 {response.usage.prompt_tokens}，"
                f"输出 {response.usage.completion_tokens}"
            )

        if not content.strip():
            print(
                "  [!] 回复为空。常见原因：额度给得太小，或该模型把内容放在推理字段里"
            )
            return False

        return True
    # 这里故意捕获所有异常：网络、密钥、模型名都可能出错，统一提示即可。
    # 行尾的忽略标记表示「我知道检查工具会警告，这里是刻意为之」。
    except Exception as error:  # noqa: BLE001
        print(f"  [x] 调用失败：{type(error).__name__}: {error}")
        print("      常见原因：密钥错、模型名不对、base_url 不匹配、网络不通")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="环境自检")
    parser.add_argument("--live", action="store_true", help="额外发一次真实 API 请求")
    args = parser.parse_args()

    print("\n=== 环境自检 ===\n")

    print("[1/4] Python 与虚拟环境")
    python_ok = check_python()

    print("\n[2/4] 依赖包")
    packages_ok = check_packages()

    print("\n[3/4] 密钥配置")
    env_ok, api_key = check_env_file()

    print("\n[4/4] 密钥安全")
    security_ok = check_gitignore()

    live_ok = True
    if args.live:
        print("\n[额外] 真实 API 调用")
        if not env_ok:
            print("  跳过：密钥没配好")
        else:
            live_ok = live_test(api_key)

    all_ok = python_ok and packages_ok and env_ok and security_ok and live_ok
    print("\n" + "=" * 30)
    if all_ok:
        print("环境就绪，可以开始 Day 1 了。")
    else:
        print("还有项目没通过，按上面的提示修一下再跑一次。")
    print()


if __name__ == "__main__":
    main()
