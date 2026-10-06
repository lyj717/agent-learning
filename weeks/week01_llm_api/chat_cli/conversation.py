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

    def trim(self, keep_turns: int) -> int:
        """只保留最近 keep_turns 轮对话，system 人设留着，返回丢掉了几条消息。

        要做的：
            1. 一条 user + 一条 assistant 算一轮，从最后往前数 keep_turns 轮
            2. 更早的整个丢掉；system 不参与裁剪
            3. 返回丢掉的消息条数（一条都没丢就是 0）

        期望结果：
            conv = Conversation("人设")，然后 add 5 轮问答（共 10 条历史）
            conv.trim(2) == 6        # 只留最近 2 轮（4 条），丢掉 6 条
            conv.turns() == 2
            conv.messages()[0]["role"] == "system"      # 人设还在

            conv2 = Conversation()，只聊了 1 轮
            conv2.trim(5) == 0       # 要留的比现有的还多，什么都不该丢

        提示：
            · 先算「要保留的条数」= keep_turns * 2，再从列表尾部切
            · keep_turns 比现有轮数大时不能切出负数，直接返回 0
            · 历史里可能有「只有 user、没有 assistant」的残句（上一轮失败留下的），
              所以别假设历史长度一定是偶数——想想你的策略怎么处理它
        """
        raise NotImplementedError("trim 还没写")
