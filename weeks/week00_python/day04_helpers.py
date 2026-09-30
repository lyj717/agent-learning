"""一个极小的模块，专门用来演示「模块与导入」。

它自己可以直接运行，也可以被别的文件 import：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day04_helpers.py

被 day04_more_demo.py 导入时，下面 if __name__ == "__main__": 里的代码不会执行。
"""

from pydantic import BaseModel


class ToolSpec(BaseModel):
    """一个工具的名字和说明。"""

    name: str
    description: str


# 模块级常量：别的文件 import 之后可以直接用
SEARCH_TOOL = ToolSpec(name="search_docs", description="在文档库里检索相关内容")


def format_tool(tool: ToolSpec) -> str:
    """把工具格式化成一行给人看的文字。"""
    return f"{tool.name}：{tool.description}"


def make_tool(name: str, description: str) -> ToolSpec:
    """造一个工具。Week 02 里这种「工厂函数」会很常见。"""
    return ToolSpec(name=name, description=description)


if __name__ == "__main__":
    # 只有「直接运行这个文件」时才会走到这里。
    # 被 import 的时候，__name__ 是 "day04_helpers" 而不是 "__main__"。
    print("我是 day04_helpers.py，现在是被直接运行的")
    print("  __name__ =", __name__)
    print("  格式化一个工具：", format_tool(SEARCH_TOOL))
    print("  顺手自测一下 make_tool：", make_tool("get_time", "取当前时间"))
