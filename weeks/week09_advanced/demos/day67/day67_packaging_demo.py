"""Day67 演示：把一个目录变成「别人装得上、配得进宿主」的项目。

前几天的 server 只能在这个仓库里跑：靠 `python -m projects.mcp_server.server` 和仓库根
的 sys.path。今天看的是交付层——元数据、依赖、入口点、宿主配置，让别人不用知道目录结构。

学完应能回答：`[project.scripts]` 里的「模块:函数」是什么、三个宿主的配置键差在哪、
NOTES_ROOT 由谁传、为什么入口函数不能带参数。演示只读文件与打印配置，不安装、不联网。
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PROJECT = REPO_ROOT / "projects/mcp_server"


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def show_pyproject() -> None:
    """打印今天要写的 pyproject 结构与每段的作用；返回 None。"""
    say("\n三、pyproject 的五段")
    say("  [build-system]  用什么后端构建（setuptools）")
    say("  [project]       名字、版本、Python 要求、依赖")
    say("  [project.scripts] 命令名 = 模块:函数（这就是入口点）")
    say("  [tool.setuptools] 告诉构建工具打包哪些包")
    say("")
    say("  [project.scripts]")
    say('  notes-mcp-server = "projects.mcp_server.server:main"')
    say("  左边是装好后的命令名，右边是「哪个模块的哪个函数」。")
    say("  所以 main() 不能带参数，也不能在 import 时就跑起来。")


def show_host_configs() -> None:
    """打印三种宿主的配置片段与差异；返回 None。"""
    say("\n四、三个宿主的配置（键名不一样，内容一样）")
    claude = {
        "mcpServers": {
            "notes": {
                "command": "C:\\path\\to\\python.exe",
                "args": ["-m", "projects.mcp_server.server"],
                "env": {"NOTES_ROOT": "C:\\path\\to\\notes"},
            }
        }
    }
    say("\n  Claude Desktop：%APPDATA%\\Claude\\claude_desktop_config.json")
    say(json.dumps(claude, ensure_ascii=False, indent=2))

    cursor = {
        "mcpServers": {
            "notes": {
                "command": "C:\\path\\to\\notes-mcp-server.exe",
                "args": [],
                "env": {"NOTES_ROOT": "C:\\path\\to\\notes"},
            }
        }
    }
    say("\n  Cursor：项目根 .cursor/mcp.json（外层键也是 mcpServers）")
    say(json.dumps(cursor, ensure_ascii=False, indent=2))

    vscode = {
        "servers": {
            "notes": {
                "type": "stdio",
                "command": "C:\\path\\to\\notes-mcp-server.exe",
                "args": [],
                "env": {"NOTES_ROOT": "C:\\path\\to\\notes"},
            }
        }
    }
    say("\n  VS Code：项目根 .vscode/mcp.json（外层键是 servers，且要 type）")
    say(json.dumps(vscode, ensure_ascii=False, indent=2))


def show_current_state() -> None:
    """看仓库里现在有什么、还缺什么；返回 None。"""
    say("\n五、仓库现在的状态")
    say(f"  项目目录：{PROJECT}")
    say(f"  有 pyproject.toml：{(REPO_ROOT / 'pyproject.toml').exists()}")
    say(f"  有 projects/__init__.py：{(REPO_ROOT / 'projects/__init__.py').exists()}")
    say(f"  有项目 README：{(PROJECT / 'README.md').exists()}")
    say(
        f"  有 LICENSE：{any((REPO_ROOT / name).exists() for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt'))}"
    )
    version_file = PROJECT / "__init__.py"
    if version_file.exists():
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("__version__"):
                say(f"  当前版本：{line}")


def main() -> None:
    """按「是什么、为什么、场景、配置、注意」讲一遍打包与宿主配置。"""
    say("Day67 把前六天的 server 变成「别人能装、能配进宿主」的项目。")
    say("学完应能说清：入口点是什么、三个宿主配置差在哪、NOTES_ROOT 谁来传。")

    say("\n一、这是什么")
    say(
        "打包 = 元数据（名字/版本/依赖）+ 入口点（命令 → 函数）+ 包发现（哪些目录算代码）。"
    )
    say("装好之后，用户不需要知道 `projects/mcp_server/server.py` 在哪，只认命令名。")

    say("\n二、为什么需要它")
    say("没有入口点，每个宿主都得写一长串 python + 绝对路径 + 模块名；")
    say("换个目录就失效，也没法在 README 里写「装完直接用」。")

    show_pyproject()
    show_host_configs()
    show_current_state()

    say("\n六、注意什么")
    say("1. 入口函数无参、不在 import 时执行：宿主只负责调用它，参数走环境变量与协议。")
    say("2. 命令与模块名区分：装好后是 notes-mcp-server；仓库里调试仍是 python -m。")
    say(
        "3. 三个宿主键不同：Claude/Cursor 用 mcpServers，VS Code 用 servers 且要 type。"
    )
    say("4. 路径写绝对路径：宿主从自己的目录启动，相对路径会找不到。")
    say("5. NOTES_ROOT 由宿主 env 传；不写死，换一套笔记不用改代码。")
    say(
        "6. 版本号只认 pyproject；__init__.py 里的 __version__ 要与它一致，否则两个来源会漂。"
    )


if __name__ == "__main__":
    main()
