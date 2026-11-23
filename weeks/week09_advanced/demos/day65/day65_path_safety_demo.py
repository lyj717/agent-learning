"""Day65 演示二：folder 参数为什么不能直接拼路径，正确判据是什么。

server 如果允许调用方指定「在哪个子目录搜」，就等于把一部分路径控制权交给了
模型。本演示用几个真实目录跑给你看：哪些字符串会逃出语料目录、字符串里有没有
`..` 为什么不能当判据、以及 resolve + relative_to 这套判据怎么用。

学完应能回答：绝对路径和 `..` 分别怎么逃出去、为什么 `notes/../notes` 是合法的、
判据为什么要在 resolve() 之后做。只读本目录的 corpus/ 与 outside/。
"""

from pathlib import Path

BASE = Path(__file__).with_name("corpus")
OUTSIDE = Path(__file__).with_name("outside")

CASES = ["", "notes", "notes/../notes", "..", "../outside", "C:\\Windows", "missing"]


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def is_inside(path: Path, base: Path) -> bool:
    """判断 path 解析后是否仍在 base 里面；返回 bool。

    不用字符串前缀比较：C:\\repo\\corpus2 会以 C:\\repo\\corpus 开头。
    relative_to 只认真正的父子关系，逃出去会抛 ValueError。
    """
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def naive_checks(folder: str) -> tuple[bool, bool]:
    """两种常见的错误判据，返回 (字符串里含两点, 以斜杠开头)。"""
    return (".." in folder, folder.startswith(("/", "\\")))


def main() -> None:
    """按「为什么危险、错误判据、正确判据、逐例对照、注意」讲一遍。"""
    say("Day64 的 server 只收关键词，路径是固定的；一旦允许 folder 参数，就得防越界。")
    say(
        "学完应能说清：绝对路径和 .. 怎么逃、为什么不能查字符串、判据为什么在 resolve 之后做。"
    )

    say("\n一、这是什么")
    say("路径边界 = 调用方给的相对目录，解析之后必须还在语料根里面。")
    say("不是「看起来像相对路径」，而是「拼出来、解析完，确实在根下面」。")

    say("\n二、为什么需要它")
    say(
        "folder 来自模型（最终来自用户），可能是 ../outside、C:\\Windows、甚至 ..\\..\\..。"
    )
    say("不检查就拼路径，等于把整台机器的文件读权限交给对话内容。")

    say("\n三、两种常见但不够用的判据")
    for folder in ("notes/../notes", "../outside", "C:\\Windows"):
        has_dots, starts_slash = naive_checks(folder)
        say(f"  folder={folder!r}  含两点={has_dots}  以斜杠开头={starts_slash}")
    say("  只查两点：会误杀 notes/../notes（解析后仍在根内，合法）。")
    say("  只查斜杠：C:\\Windows 不以斜杠开头，照样逃出去。")

    say("\n四、正确判据：先 resolve，再 relative_to")
    say("  target = (base / folder).resolve()")
    say("  target.relative_to(base.resolve())  # 抛 ValueError 就是越界")
    say("resolve 会消掉 ..、也会把绝对路径整个替换掉；relative_to 只认真父子关系。")

    say(f"\n五、逐例跑一遍（语料根={BASE}）")
    for folder in CASES:
        target = (BASE / folder).resolve() if folder else BASE.resolve()
        inside = is_inside(target, BASE)
        kind = "目录" if target.is_dir() else ("文件" if target.is_file() else "不存在")
        verdict = "允许" if inside and target.is_dir() else "拒绝"
        say(f"  folder={folder!r}")
        say(f"    解析到：{target}")
        say(f"    在根内：{inside}；类型：{kind}；结论：{verdict}")

    say("\n六、越界会读到什么")
    secret = (OUTSIDE / "secret.md").resolve()
    say(f"  ../outside 解析到：{secret}")
    say(f"  那里的文件写着：{secret.read_text(encoding='utf-8').splitlines()[0]}")
    say("  检查通过后，这个文件永远不会出现在检索结果里。")

    say("\n七、注意什么")
    say("1. 判据要作用在 resolve() 之后；直接比较字符串拼出来的路径会被 .. 绕过。")
    say(
        "2. 用 relative_to 判断父子，不要用 startswith：corpus2 会骗过 corpus 前缀检查。"
    )
    say("3. folder 指向一个文件也要拒绝——工具只接受目录。")
    say("4. 语料根本身不存在时，先说清是根的问题，而不是「folder 不存在」。")
    say("5. resolve 会跟随符号链接与 junction；本演示不展开，知道有这回事即可。")
    say("6. 拒绝时抛 ValueError，让工具层统一转成 is_error，模型看得到原因。")


if __name__ == "__main__":
    main()
