"""命令行参数入门：一次讲清 argparse 和各种参数写法。

自己动手试这些命令，看输出有什么不同：
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py --verbose
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py --count 3
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py --name 小明
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py -q
    .venv\\Scripts\\python.exe weeks\\week00_python\\argparse_demo.py --help
"""

import argparse
import contextlib
import io
import sys


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


# ============================================================
section("第 1 步：命令行参数最原始的形态")
# ============================================================

print("你敲的每条命令，Python 都原封不动记在 sys.argv 里。")
print(f"  本次运行收到的参数：{sys.argv}")
print(f"  一共 {len(sys.argv)} 个")
print()
print("sys.argv[0] 永远是脚本自己的路径，[1] 之后才是你输入的参数。")
print("所以要手工处理就得写 argv[1]、argv[2]……还得自己判断有没有、")
print("是不是数字、顺序对不对。参数一多就变成一团乱麻。")
print()
print("argparse 就是来解决这件事的：你声明『我有哪些参数』，")
print("它负责解析、校验、报错，还顺手生成帮助文档。")


# ============================================================
section("第 2 步：声明参数（这一段就是 argparse 的全部核心）")
# ============================================================

parser = argparse.ArgumentParser(
    description="演示各种命令行参数的写法",
)

# 写法一：开关型参数。出现就是 True，不出现就是 False，后面不跟值
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help="打印详细信息",
)

# 写法二：带值的参数。用户必须（或可以）跟一个值
parser.add_argument(
    "--count",
    type=int,
    default=1,
    help="重复次数，默认 1",
)

# 写法三：带值的参数，值是文本
parser.add_argument(
    "--name",
    default="访客",
    help="称呼，默认是「访客」",
)

# 这是练习 3 要加的那个参数
parser.add_argument(
    "--quiet",
    "-q",
    action="store_true",
    help="只输出最后结论，不打印过程",
)

args = parser.parse_args()


# ============================================================
section("第 3 步：取到的值长什么样")
# ============================================================

print("parse_args() 返回的是一个对象，每个参数变成一个属性：")
print(f"  args.verbose = {args.verbose!r}")
print(f"  args.count   = {args.count!r}")
print(f"  args.name    = {args.name!r}")
print(f"  args.quiet   = {args.quiet!r}")
print()
print("注意两个细节：")
print("  1. 参数名里的横线在属性名里变成下划线（--dry-run → args.dry_run）")
print("  2. 开关型参数是 True/False，带值参数就是你给的值")


# ============================================================
section("第 4 步：根据参数决定行为")
# ============================================================

for index in range(args.count):
    if args.verbose:
        print(f"  第 {index + 1} 次：你好，{args.name}（详细信息已开启）")
    else:
        print(f"  第 {index + 1} 次：你好，{args.name}")


# ============================================================
section("第 5 步：怎么让 --quiet 真的少打印东西")
# ============================================================


def run_checks(verbose: bool) -> bool:
    """模拟 check_env.py 里那些检查函数，边跑边打印。"""
    print("  [v] 检查 Python 版本")
    print("  [v] 检查依赖包")
    if verbose:
        print("      openai 3.19.2")
        print("      httpx 0.28.1")
    print("  [v] 检查密钥")
    return True


print("问题来了：检查函数都是自己 print 的，")
print("quiet 之后要想『不要中间过程』，怎么做到？\n")

print("方案 A：把 quiet 一层层传进去，每个 print 都加判断")
print("        → 要改四十多处 print，不现实\n")

print("方案 B：把整个过程的标准输出临时重定向到一个『黑洞』")
print("        → 只改一处，检查函数完全不用动\n")

print("方案 B 的实际效果：")

# contextlib.redirect_stdout 会临时把 print 的目标换掉
# io.StringIO() 是一个只存在内存里的假文件，写进去的内容直接丢掉
sink = io.StringIO() if args.quiet else sys.stdout

with contextlib.redirect_stdout(sink):
    all_ok = run_checks(args.verbose)

print("  " + "=" * 30)
print("  环境就绪" if all_ok else "  还有项目没通过")

print()
print("上面这块如果用 -q 运行，中间那几行就消失了，只剩结论。")
print("试试对比这两个命令：")
print(f"  python {sys.argv[0]}")
print(f"  python {sys.argv[0]} -q")


# ============================================================
section("第 6 步：--help 是自动生成的")
# ============================================================

print("你没有写任何帮助文档，但 argparse 根据 add_argument 里的")
print("help 文字自动生成了 -h/--help 的内容。跑一下：")
print()
print(f"  python {sys.argv[0]} --help")
print()
print("这是 argparse 最值的地方之一：参数、类型、默认值、说明")
print("写在一处，代码、帮助、报错三件事同时都有了。")


section("小结")
print("1. 用 argparse.ArgumentParser() 创建解析器")
print("2. 用 add_argument 声明每个参数")
print("3. 用 parse_args() 取值，之后当普通变量用")
print()
print("三种最常用的参数写法：")
print('  --flag              action="store_true"   出现即 True')
print("  --count 5           type=int, default=1    带值并可指定类型")
print('  --name 小明         default="访客"         带值的文本参数')
print()
print("配合 -q / -v 这种单字母短名，就是你在命令行工具里见到的样子。")
