"""Day65 演示一：把检索从「一段文本」扩到「一整个目录」。

Week09 的 server 早晚要搜真实笔记，而模型手里只有关键词与语料目录。
本演示只解决文件层：怎么列出 Markdown、怎么读出 UTF-8、哪些文件要跳过、
命中记录里的出处怎么写。

学完应能回答：为什么要排序、为什么要 as_posix、非 UTF-8 与空文件怎么处理、
全局 limit 和每文件 limit 差在哪。全部离线，只读本目录的 corpus/。
"""

from pathlib import Path

CORPUS = Path(__file__).with_name("corpus")


def say(text: str = "") -> None:
    """打印一行；不传参数时只输出一个空行。"""
    print(text)


def find_lines(text: str, keyword: str) -> list[tuple[int, str]]:
    """按行找关键词，返回 (行号, 原文) 列表；行号从 1 开始，不区分大小写。

    这里用本地小函数，不 import 练习里的 find_matches：演示要能单独跑，
    不依赖学员当天写没写、写对没写对。
    """
    needle = keyword.casefold()
    hits: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if needle in line.casefold():
            hits.append((number, line))
    return hits


def scan(
    root: Path, keyword: str, limit: int = 5, *, verbose: bool = False
) -> list[dict[str, int | str]]:
    """扫描 root 下的 Markdown，返回带出处的命中，最多 limit 条。

    跳过读不成 UTF-8 的文件和只有空白的文件；出处是相对 root 的 POSIX 路径。
    verbose=True 时打印每个被跳过的文件和原因。
    """
    if not root.is_dir():
        raise ValueError(f"语料目录不存在：{root}")
    results: list[dict[str, int | str]] = []
    files = sorted(
        root.rglob("*.md"), key=lambda path: path.relative_to(root).as_posix()
    )
    for path in files:
        source = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            if verbose:
                say(f"  跳过 {source}：不是 UTF-8")
            continue
        if not text.strip():
            if verbose:
                say(f"  跳过 {source}：只有空白")
            continue
        for number, line in find_lines(text, keyword):
            results.append({"source": source, "line": number, "text": line})
            if len(results) >= limit:
                return results
    return results


def main() -> None:
    """按「是什么、为什么、场景、代码、注意」讲一遍文件层，再跑语料目录。"""
    say(
        "Week09 要交付一个能检索笔记的 MCP Server。Day64 的 find_matches 只认一段文本，"
    )
    say(
        "今天把它接到一整个目录上。学完应能说清：排序、出处、编码、limit 各自解决什么问题。"
    )

    say("\n一、这是什么")
    say("文件层 = 找到候选文件 + 读出文本 + 把命中拼回出处。")
    say(
        "它不做匹配（Day64 的 find_matches 做），只负责「从哪些文件、按什么顺序、出错怎么办」。"
    )

    say("\n二、为什么需要它")
    say("模型给的只有关键词，它不知道笔记在哪个文件夹、第几行。")
    say(
        "没有出处，回答就没法核对；顺序不稳定，同样的查询两次结果不一样，也没法写测试。"
    )

    say("\n三、具体场景")
    say(f"语料目录：{CORPUS}")
    say("里面有 notes/ 与 archive/ 两个子目录、一个空文件、一个不是 UTF-8 的文件。")
    say("用户问「关键词在哪出现」，server 要回「哪个文件、第几行、原文是什么」。")

    say("\n四、先看目录里有什么")
    files = sorted(
        CORPUS.rglob("*.md"), key=lambda path: path.relative_to(CORPUS).as_posix()
    )
    for path in files:
        say(f"  {path.relative_to(CORPUS).as_posix():24} {path.stat().st_size:>4} 字节")

    say("\n五、跑一次检索（关键词=关键词，limit=5）")
    hits = scan(CORPUS, "关键词", limit=5, verbose=True)
    say(f"\n共 {len(hits)} 条：")
    for hit in hits:
        say(f"  {hit['source']}:{hit['line']} | {hit['text']}")

    say("\n六、limit 是全局的")
    say("limit=2 时只拿前两条——不是每个文件各拿两条。")
    say("按文件顺序累计，凑够就停；否则 5 个文件每个返回 5 条，模型会被塞爆。")
    shown = scan(CORPUS, "关键词", limit=2)
    for hit in shown:
        say(f"  {hit['source']}:{hit['line']} | {hit['text']}")

    say("\n七、注意什么")
    say(
        "1. 排序：用相对路径的 POSIX 形式排序，Windows 和 Linux 结果才一致，测试才可重复。"
    )
    say("2. 出处：存相对路径（notes/a.md），不存绝对路径——绝对路径换台机器就失效，")
    say("   也会把本机目录结构泄露给模型。")
    say("3. 编码：read_text(encoding=utf-8) 遇到坏文件抛 UnicodeDecodeError；")
    say("   要么跳过并说一声，要么让整个查询失败。别用 errors=ignore——字节被悄悄吃掉，")
    say("   坏文件甚至会「命中」关键词。")
    say("4. 空文件：读完 strip 一下再判断，避免把空文件也列进结果。")
    say("5. rglob 会进子目录；如果只想搜当前层，用 glob。")
    say("6. 路径边界下一份演示讲：folder 参数不能直接拼。")


if __name__ == "__main__":
    main()
