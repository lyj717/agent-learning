"""一段对话的状态：多轮对话真正住的地方。

模型那边是无状态的，「多轮」全靠你在本地把历史攒起来、每次整段发过去。
这个文件就是那个「攒历史」的地方：不碰网络、不打印，纯状态管理，所以好测。

要写的六个东西：
    __init__         建一段对话，可以带一条 system 人设
    add_user         记下用户说的话
    add_assistant    记下模型的回答
    messages         每次请求要发出去的东西（system + 全部历史，按时间排）
    clear            清空历史，但**保留 system 人设**
    turns            已经聊了几轮（用户说过几句）
"""


class Conversation:
    def __init__(self, system_prompt: str | None = None) -> None:
        """建一段新对话。
        要做的：
            1. 用一个列表存历史（空列表）
            2. 把 system_prompt 记下来（可能是 None，表示不要 system）
        提示：system 不放在历史列表里也行——只要你保证 messages() 每次都先给
              它、clear() 之后它还在。
        """
        raise NotImplementedError("__init__ 还没写")

    def add_user(self, text: str) -> None:
        """把用户说的这句话记进历史。
        要做的：往历史末尾追加 {"role": "user", "content": text}
        """
        raise NotImplementedError("add_user 还没写")

    def add_assistant(self, text: str) -> None:
        """把模型刚给的这个回答记进历史。
        要做的：往历史末尾追加 {"role": "assistant", "content": text}
        提示：这一步最容易忘。忘了它，下一轮模型就不知道它自己刚说过什么，
              会答得前言不搭后语（串味）。
        """
        raise NotImplementedError("add_assistant 还没写")

    def messages(self) -> list[dict[str, str]]:
        """返回这次要发给模型的完整 messages。
        期望结果：
            有 system 时，第一条是 {"role": "system", "content": ...}；
            后面按时间顺序跟着历史里的每一条。
        提示：返回**新列表**（用 copy 或者重新拼一个），别把内部列表直接交出去——
              调用方一改就串了。
        """
        raise NotImplementedError("messages 还没写")

    def clear(self) -> None:
        """清空对话历史，但保留 system 人设。
        期望结果：调用之后 messages() 里只剩那条 system（没 system 就是空列表）
        提示：人设是配置，不是对话内容，所以不清。
        """
        raise NotImplementedError("clear 还没写")

    def turns(self) -> int:
        """已经聊了几轮——也就是历史里用户说过几句。"""
        raise NotImplementedError("turns 还没写")
