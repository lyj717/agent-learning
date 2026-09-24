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


def check_env_file() -> tuple[bool, str]:
    """检查 .env 文件与密钥。返回（是否就绪, 密钥）。"""
    env_path = ROOT / ".env"

    if not env_path.exists():
        print("  [x] 没有找到 .env 文件")
        print("      修复：copy .env.example .env，然后填入你的密钥")
        return False, ""

    print("  [v] .env 文件存在")

    # load_dotenv 会把 .env 里的内容塞进环境变量
    from dotenv import load_dotenv

    load_dotenv(env_path)
    api_key = os.environ.get("LLM_API_KEY", "")

    if not api_key or "填入" in api_key:
        print("  [!] 密钥还没填（.env 里仍然是示例内容）")
        return False, api_key

    # 只显示前后几位，不要把完整密钥打印出来或写进日志
    masked = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
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
            max_tokens=10,
        )
        content = response.choices[0].message.content
        print(f"  [v] 调用成功，模型回复：{content}")
        return True
    # 这里故意捕获所有异常：网络、密钥、模型名都可能出错，统一提示即可。
    # noqa 表示「我知道 ruff 会警告，但这里是有意为之」。
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

    if args.live:
        print("\n[额外] 真实 API 调用")
        if not env_ok:
            print("  跳过：密钥没配好")
        else:
            live_test(api_key)

    all_ok = python_ok and packages_ok and env_ok and security_ok
    print("\n" + "=" * 30)
    if all_ok:
        print("环境就绪，可以开始 Day 1 了。")
    else:
        print("还有项目没通过，按上面的提示修一下再跑一次。")
    print()


if __name__ == "__main__":
    main()
