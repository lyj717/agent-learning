"""一段对话的状态：多轮对话真正住的地方。

模型那边是无状态的，「多轮」全靠你在本地把历史攒起来、每次整段发过去。
这个文件就是那个「攒历史」的地方：不碰网络、不打印，纯状态管理，所以好测。
"""


class Conversation:
    """一段对话：一条可选的 system 人设，加上按时间顺序排的历史。"""

    system: dict[str, str] | None

    def __init__(self, system_prompt: str | None = None) -> None:
        """建一段新对话；system_prompt 传 None 表示不要 system。"""
        if system_prompt is None:
            self.system = None
        else:
            self.system = {"role": "system", "content": system_prompt}
        self.history: list[dict[str, str]] = []

    def add_user(self, text: str) -> None:
        """把用户说的这句话记进历史。"""
        self.history.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        """把模型刚给的这个回答记进历史。"""
        self.history.append({"role": "assistant", "content": text})

    def messages(self) -> list[dict[str, str]]:
        """返回这次要发给模型的完整 messages：system 在前，历史在后。"""
        if self.system is not None:
            messages = [self.system]
            messages.extend(self.history)
        else:
            messages = self.history.copy()
        return messages

    def clear(self) -> None:
        """清空对话历史，但保留 system 人设。"""
        self.history = []

    def turns(self) -> int:
        """已经聊了几轮——也就是历史里用户说过几句。"""
        return sum(1 for m in self.history if m["role"] == "user")
