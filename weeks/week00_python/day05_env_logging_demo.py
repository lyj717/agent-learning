"""环境变量与日志：密钥放哪、运行痕迹记哪。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day05_env_logging_demo.py

这个脚本会读仓库根目录的 .env（如果存在）。
脚本里绝不会把密钥原文打印出来——这一点你自己写代码时也要守住。
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent  # weeks/week00_python/ → 仓库根目录


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


def mask(secret: str | None) -> str:
    """打码：只显示长度，不显示内容。日志和截图里都该这么做。"""
    if not secret:
        return "（没设置）"
    return f"已设置，共 {len(secret)} 个字符（内容不打印）"


# ============================================================
section("1. 环境变量：程序外面传进来的配置")
# ============================================================

say(
    "这是什么：一组「键 = 值」，由操作系统在启动进程时交给程序。",
    "           Python 里用 os.environ 读，它用起来像个字典。",
    "为什么需要：密钥、接口地址、模型名这些「换个环境就该变」的东西，",
    "           必须从代码里搬出去——否则密钥迟早被你提交到 GitHub 上。",
    "场景：本地用 DeepSeek、服务器上用别的服务商，代码一行都不用改，只改配置。",
)
print()

say(
    f"  读之前，LLM_MODEL = {os.environ.get('LLM_MODEL')!r}",
    f"  读之前，LLM_API_KEY = {mask(os.environ.get('LLM_API_KEY'))}",
    "",
    "  现在调用 load_dotenv()，让它去读仓库根目录的 .env 文件：",
)

loaded = load_dotenv(ROOT / ".env")
say(
    f"  .env 找到了吗：{loaded}",
    f"  读之后，LLM_MODEL = {os.environ.get('LLM_MODEL')!r}",
    f"  读之后，LLM_BASE_URL = {os.environ.get('LLM_BASE_URL')!r}",
    f"  读之后，LLM_API_KEY = {mask(os.environ.get('LLM_API_KEY'))}",
    "",
    "  load_dotenv 干的事很朴素：把文件里的键值对塞进 os.environ。",
    "  之后代码里就统一用 os.environ.get(...) 取值，不用关心它从哪来。",
)


# ============================================================
section("2. 取不到的时候怎么办")
# ============================================================

say(
    "  三种写法，对应三种态度：",
    "",
    f"    os.environ.get('LLM_MODEL')            → {os.environ.get('LLM_MODEL')!r}（取不到给 None）",
    "    os.environ.get('LLM_MODEL', 'gpt-4o-mini') → 取不到就给默认值",
    "    os.environ['LLM_MODEL']                → 取不到直接抛 KeyError",
    "",
    "  选择标准很简单：",
    "    有合理默认值的（模型名、超时秒数）→ 用 .get 给默认值",
    "    没有默认值的（API Key）         → 要么抛异常，要么明确退出并告诉人怎么补",
    "",
    "  API Key 这种千万别给默认值，比如 os.environ.get('LLM_API_KEY', 'test')——",
    "  那只会让程序带着假密钥继续跑，然后在调用接口时报一个更难懂的错。",
)


# ============================================================
section("3. .env 的规矩：谁提交、谁不提交")
# ============================================================

say(
    f"  .env.example 存在吗：{(ROOT / '.env.example').exists()}  ← 这个要提交，别人照着填",
    f"  .env 存在吗：       {(ROOT / '.env').exists()}  ← 这个绝不提交",
    "",
    "  仓库里 .gitignore 头几行就写着 .env 和 .env.*，只放行 .env.example。",
    "  新手最容易犯的错是：先提交了 .env，再删掉——但历史里还留着，",
    "  密钥一旦进过 git，就得去服务商那里吊销重发，改代码是没用的。",
    "",
    "  自查命令（README 里也写了）：",
    "    git log -p | findstr API_KEY",
)


# ============================================================
section("4. 为什么不用 print 记日志")
# ============================================================

say(
    "  print 的问题：",
    "    1. 没有级别——想只看错误时，分不出来哪句是错误、哪句是正常流程",
    "    2. 没有时间——出问题时不知道是什么时候发生的",
    "    3. 关不掉——上线了还得一行行删 print，删漏了就把内部信息打给用户看",
    "    4. 写不进文件——程序崩了，屏幕上的东西也就没了",
    "    5. 分不清来源——几十个模块都在 print，不知道是谁说的",
    "",
    "  logging 这五件事全都能解决，代价只是开头多配置两行。",
    "  你后面调试 Agent 全靠它：模型调了什么工具、参数是什么、花了多久，都要留痕。",
)


# ============================================================
section("5. 最小可用的 logging")
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

say(
    "  先看配置：",
    "    logging.basicConfig(level=logging.INFO,",
    '                        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s")',
    "",
    "  format 里那几个占位符的意思：",
    "    %(asctime)s    时间戳",
    "    %(levelname)s  级别名（INFO / WARNING / ERROR）",
    "    %(name)s       logger 的名字，这里就是本模块的名字",
    "    %(message)s    你要记的那句话",
    "",
    "  接下来这几行是真实输出，注意它们的格式：",
)

logger.debug("这条 DEBUG 不会显示，因为级别设的是 INFO")
logger.info("开始处理用户请求 user_id=42")
logger.warning("检索工具返回了 0 条结果，可能是索引没建好")
logger.error("调用模型失败：连接超时")

say(
    "",
    "  这三行日志你看得见吗？它们不在标准输出（stdout）里，而在标准错误（stderr）里。",
    "  print 走 stdout，logging 默认走 stderr——这是两股流：",
    "    用 > 重定向、或者某些工具只收集 stdout 时，日志就会「消失」。",
    "    在管道里还会错位：stdout 带缓冲、stderr 不带，日志常常跑到整个输出的最前面。",
    "",
    "  想把两股流合起来看：",
    "    命令行： .venv\\Scripts\\python.exe ... 2>&1",
    "    或让日志也走 stdout：logging.basicConfig(..., stream=sys.stdout)",
    "",
    "  想知道日志到底去哪儿了，随时问一句：",
    "    print(logging.getLogger().handlers[0].stream)",
)

say(
    "",
    "  五个级别从低到高：DEBUG < INFO < WARNING < ERROR < CRITICAL。",
    "  level= 决定「低于这个级别的都不输出」——所以调成 WARNING，",
    "  上面那两行 info 就自动消失了，一行代码都不用改。",
)


# ============================================================
section("6. getLogger(__name__) 的惯例")
# ============================================================

say(
    f"  本文件里 logger 的名字是：{logger.name}",
    "  每个模块开头都写 logger = logging.getLogger(__name__)，好处是日志里自带出处，",
    "  你能一眼看出「这条日志是哪个文件打的」——模块多了以后这点特别重要。",
    "",
    "  记日志的分工，可以先用这套：",
    "    logger.debug    变量值、循环到第几轮，调试时才看",
    "    logger.info     重要流程节点：开始处理、调用工具、拿到结果",
    "    logger.warning  不符合预期但还能继续：结果为空、重试了一次",
    "    logger.error    出错了，当前这次任务失败",
    "    logger.exception 在 except 里用，它会自动把整个调用栈也记下来",
)

try:
    1 / 0  # noqa: B018  ← 故意造一个异常
except ZeroDivisionError:
    say("  下面这段是 logger.exception 的输出，注意它带上了出错位置：")
    logger.exception("计算失败，这个异常被记下来了")


# ============================================================
section("7. 一个坑：basicConfig 只生效一次")
# ============================================================

say(
    "  现在再调一次 basicConfig，想把级别改成 DEBUG：",
)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
say(
    f"    改完了吗？根 logger 的实际级别还是：{logging.getLogger().getEffectiveLevel()}",
    "    20 就是 INFO——第二次调用被忽略了，因为根 logger 已经有 handler 了。",
    "",
    "  这是新手常见困惑：「我明明设了 DEBUG 怎么还是看不到」。",
    "  规则是：basicConfig 只在「根 logger 还没有 handler」时起作用。",
    "",
    "  需要更细的控制时，正确的做法是拿具体 logger 设置：",
    "    logger = logging.getLogger(__name__)",
    "    logger.setLevel(logging.DEBUG)      ← 这个随时可以改",
    "  或者干脆自己建 handler（写文件、按天切分都靠它），那是 Week 07 的事。",
    "",
    "  还有个更省事的做法：用环境变量控制级别，本地设 DEBUG、线上设 INFO，",
    '  代码只有一行：level=os.environ.get("LOG_LEVEL", "INFO")。',
)


section("总结")
say(
    "1. 配置从环境变量来，代码里不写死；密钥只放 .env，.env 永不提交",
    "2. 有默认值的用 os.environ.get，没有的别给默认值——宁可当场报错",
    "3. 用 logging 而不是 print：有级别、有时间、有出处、能关掉、能写文件",
    "4. 每个模块开头 getLogger(__name__)；except 里用 logger.exception",
    "5. basicConfig 只生效一次，要动态改级别就用 logger.setLevel",
)
