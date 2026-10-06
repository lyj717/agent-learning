"""简易长期记忆：把你告诉它的事实存到本地文件，下次启动还记得。

为什么要单独一个文件：模型自己不留任何东西，所谓「记忆」是你存在外面、每次重新
喂回去的东西。这一层只管「存 / 取 / 拼成提示词」——不碰网络、不打印，所以好测。
"""

import json
from pathlib import Path


def load_facts(path: Path) -> list[str]:
    """从文件里读回事实列表。"""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as facts:
        try:
            fact = json.load(facts)
        except json.JSONDecodeError:
            return []
        return fact


def add_fact(path: Path, text: str) -> None:
    """把一条新事实追加进文件（文件不存在就新建）。"""
    facts = load_facts(path)
    text = text.strip()
    if not text or text in facts:
        return
    facts.append(text)
    with path.open("w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)


def compose_system(base_system: str | None, facts: list[str]) -> str | None:
    """把「人设 + 记得的事实」拼成一条 system 提示词。"""
    if not facts:
        return base_system
    head = base_system + "\n" if base_system else ""
    return (
        head
        + "\n你记得关于用户的这些事实：\n"
        + "\n".join(f"- {fact}" for fact in facts)
    )
