"""真实的流式调用示例：拿模型的回复，一个字一个字地打印。

这份材料是**预习**，不是 Day 6 的必做题。

因为它要调用模型 API，而「怎么调 API」属于 Week 01 的内容。
所以文件末尾那十个问题，今天能做六条：第 ① 条（Day 5 学过的）
加上标着【今天能答】的五条；剩下四条标着【等 Week 01】，
等你学到那一周再回来看——那时候它们会简单得多。

今天要做的两件事：
    1. 读完下面那段「调用模型 API，你现在需要知道的六条」
    2. 把今天能做的六条答掉：① 和 ⑤⑥⑧⑨⑩

默认**不会**联网，也不会消耗额度：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day06_stream_example.py

想真跑一次（会消耗一点 API 额度，密钥从仓库根目录的 .env 读，需要网络）：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day06_stream_example.py --live
"""

# ============================================================
# 先读这个：调用模型 API，你现在需要知道的六条
# ============================================================
#
# 1. 调用模型 = 发一个 HTTP 请求给服务商，请求里带上「你说过的话」，
#    服务端把「模型要说的话」装在一段 JSON 里返回。
#    这是普通的网络请求，和你 Day 5 学读写 JSON 是一回事，
#    只是数据从网线来，不是从磁盘来。
#
# 2. 下面代码里的 OpenAI(...) 是官方 SDK（工具包）的客户端对象，
#    它替你把 HTTP 请求打包好了：你不用自己拼地址、拼 JSON。
#
# 3. 请求里最重要的两样东西：
#      model     用哪个模型（不同模型的能力和价格不同）
#      messages  对话历史，一个列表，每一项形如
#                {"role": "user", "content": "你好"}
#                ——和你 Day 4 综合题里做的那个 Conversation 是一回事
#
# 4. 回复里模型说的话，位置是 choices[0].message.content。
#    choices 是「候选回复」的列表（默认只要一个），所以取第 0 个。
#
# 5. 流式模式下（stream=True），你收到的不是一整段话，而是一串小碎片，
#    每个碎片只带「新多出来的那几个字」，放在 choices[0].delta.content。
#    delta 就是「增量」的意思——跟你今天学的 yield 逐字吐是同一个东西，
#    只不过这里的「字」是从网络一块一块送来的。
#
# 6. base_url 是服务商接口的地址。换服务商（OpenAI / DeepSeek / 通义千问）时，
#    变的只是地址、密钥、模型名，代码一行都不用改——所以这三样从环境变量读。

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).parent.parent.parent


def ask_model(question: str) -> None:
    """问模型一句话，把回复逐字打印出来。"""
    load_dotenv(ROOT / ".env")  # ①

    client = OpenAI(  # ②
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL"),  # ③
    )

    stream = client.chat.completions.create(  # ④
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "你是一个简洁的助手。"},
            {"role": "user", "content": question},
        ],
        stream=True,  # ⑤
    )

    for chunk in stream:  # ⑥
        delta = chunk.choices[0].delta.content  # ⑦
        if delta:  # ⑧
            print(delta, end="", flush=True)  # ⑨
    print()  # ⑩


def main() -> None:
    question = "用一句话说明什么是流式输出。"
    print(f"提问：{question}\n")
    print("回答：", end="")
    ask_model(question)


if __name__ == "__main__":
    if "--live" in sys.argv:
        main()
    else:
        print("这是示例代码，默认不联网、不消耗额度。")
        print("通读之后请照文件末尾的编号逐行注释；想真跑一次就加 --live：")
        print(
            "  .venv\\Scripts\\python.exe weeks\\week00_python\\day06_stream_example.py --live"
        )


# ============================================================
# 逐行注释作业
# ============================================================
#
# 每条后面标了今天能不能答。先把【今天能答】的五条答掉，
# 剩下的留着——等 Week 01 学完回来看，你会发现它们已经很自然了。
#
# ① 【Day 5 学过】load_dotenv(ROOT / ".env") 为什么必须放在创建 client 之前？
#    密钥为什么不直接写在代码里？
#   否则 os.environ 读不到 .env 里的内容——load_dotenv 干的就是
#   「把文件里的键值对塞进环境变量」这件事，得先塞进去才读得到
#   密钥不能写在代码里：代码要提交到 git，写进去就等于公开；
#   而且换个环境（本地 / 服务器）不用改代码
# ② 【等 Week 01】OpenAI(...) 是在创建一个什么对象？它内部替你做了什么？
#    （提示：背景知识第 1、2 条）这个文件用的是同步版；异步版叫什么名字？
#
#
# ③ 【等 Week 01】base_url 为什么单独设这一个参数就能换服务商？
#    （提示：背景知识第 6 条；密钥和模型名也是同样的道理）
#
#
# ④ 【等 Week 01】client.chat.completions.create(...) 这个方法发出去的是一个什么请求？
#    它返回的东西在 stream=True 和 stream=False 时，是两种完全不同的类型——分别是什么？
#
#
# ⑤ 【今天能答】stream=True 这一个参数改变了什么？
#    没有它的话，第 ⑥ 行还能用 for 吗？（想想你今天学的生成器）
#   返回值从「一整段完整的回复」变成「一串小碎片」，
#   每个碎片只带新多出来的那几个字，所以要循环着一点点取。
#   没有 stream=True 时拿到的是一个完整对象，它不可迭代，for 会直接报错
# ⑥ 【今天能答】为什么这里可以用 for？（提示：可迭代对象、生成器）
#    换成异步的写法，这一行会变成什么？（提示：演示第 5 节）
#   stream是可迭代对象
#   async for chunk in stream
# ⑦ 【等 Week 01】delta 是什么？为什么不是 message？
#    为什么要有 choices[0] 这一层？（提示：背景知识第 4、5 条）
#
#
# ⑧ 【今天能答】if delta: 这一行去掉会怎样？
#    （提示：最后一块碎片里可能没有内容，那 print(None) 会打印出什么？）
#   最后一块碎片里可能没有内容,会打印出None
#
# ⑨ 【今天能答】print(delta, end="", flush=True) 里两个参数各自解决什么问题？
#    把 flush=True 去掉，会看到什么现象？
#   end=""      不换行，让下一个字接在后面
#   flush=True  立刻推出去，不要等缓冲区攒满（不加的话可能整段一起冒出来)
# ⑩ 【今天能答】print() 这一行看着多余，它解决的是什么问题？
#   在输出结束后换行，防止输出杂乱
#
# 进阶（等 Week 01 之后再想）：
#    A. 想在等模型回复的同时做别的事，这个函数该怎么改？
#    B. 想把整段回复也存下来，最小改动是什么？
