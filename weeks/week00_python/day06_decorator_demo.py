"""装饰器：给函数「套一层」，而不改函数本身。

每一节都是同一个顺序：
    这是什么 → 为什么需要它 → 一个具体场景 → 代码 → 要注意什么

运行：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day06_decorator_demo.py

清单里的要求是「会读、会用现成的就够」，所以这份演示重点在「看懂」，
不追求自己写出复杂装饰器。最后一个能自己写出来的目标：计时器。
"""

import functools
import time


def section(title: str) -> None:
    print(f"\n{'=' * 56}\n{title}\n{'=' * 56}")


def say(*lines: str) -> None:
    for line in lines:
        print(line)


# ============================================================
section("1. 前提：Python 里函数也是「值」")
# ============================================================

say(
    "这是什么：函数可以被赋值给变量、当参数传给别人、也可以被当成返回值返回。",
    "为什么先说它：装饰器就是用这三种能力拼出来的，不理解这一节就会觉得 @ 很玄。",
    "场景：想知道「哪一步慢」——写一个通用的计时器，套在任何函数上用。",
)
print()


def greet(name: str) -> str:
    return f"你好，{name}"


shout = greet  # 注意：这里不写括号，是把函数本身赋给另一个名字
say(
    f"  shout = greet 之后，shout('小明') = {shout('小明')!r}",
    f"  greet 这个名字指向的对象：{greet}",
    "  两个名字指向同一个函数对象，谁都能调用。",
)


def apply_twice(func, value: str) -> str:
    """把传进来的函数连着用两次——func 就是一个普通参数。"""
    # func 收到的是一个「函数」（比如下面的 exclaim），所以 func(value) 就是在调用它
    # func(func(value)) 从里往外读：先用 value 算一次，再把结果算第二次
    return func(func(value))


def exclaim(text: str) -> str:
    """在末尾加一个感叹号——拿它来看清「用了两次」。"""
    return text + "!"


say(
    f"  函数当参数传：apply_twice(exclaim, '好') = {apply_twice(exclaim, '好')!r}",
    "    从里往外读：exclaim('好') 先得到 '好!'，再 exclaim('好!') 得到 '好!!'",
    f"  换个函数当然也行：apply_twice(str.upper, 'hi') = {apply_twice(str.upper, 'hi')!r}",
    "    这个例子看不出用了两次（大写再大写还是大写），",
    "    正好说明「怎么用」是由传进来的那个函数决定的，apply_twice 自己不管。",
    "",
    "  既然函数能当参数、能当返回值，那就能写出「吃一个函数、吐一个函数」的东西——",
    "  那个东西就是装饰器。",
)


# ============================================================
section("2. 闭包：内层函数记住了外层的变量")
# ============================================================

say(
    "这是什么：在一个函数里定义另一个函数，里面的函数能一直记着外面的变量。",
    "为什么需要：装饰器要在「包装」的时候记住原函数，靠的就是这个机制。",
)
print()


def make_counter():
    """造一个计数器函数，每次调用加一。"""
    count = 0

    def bump() -> int:
        nonlocal count  # 声明：我要改的是外面那个 count
        count += 1
        return count

    return bump


counter = make_counter()
say(
    f"  每次调用都加一：{counter()}, {counter()}, {counter()}",
    "",
    "  有意思的地方：make_counter() 早就执行完返回了，可 count 还活着——",
    "  它被里面的 bump 函数「记」住了。这就是闭包。",
)


# ============================================================
section("3. 装饰器本体：吃一个函数，吐一个函数")
# ============================================================

say(
    "这是什么：一个函数，收一个函数当参数，返回一个新的函数。",
    "为什么需要：有些事每个函数都要做（计时、记日志、重试、检查权限），",
    "           但不该混进业务代码里。装饰器把它们「套」在外面。",
    "场景：想看看哪个函数慢——加一行 @timed 就行，函数体一个字都不用改。",
)
print()


def timed(func):
    """包一层计时，返回包装后的函数。"""

    # wraps(原函数)：把原函数的名字、文档字符串、注解都复制到 wrapper 上，
    # 不加的话，被装饰后的函数就「改名」成 wrapper 了
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()  # perf_counter()：高精度计时器，专门用来量耗时
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"      [{func.__name__}] 耗时 {elapsed * 1000:.0f} 毫秒")
        return result

    return wrapper


def slow_add(a: int, b: int) -> int:
    time.sleep(0.2)
    return a + b


say("  先看不用 @ 的写法——这才是装饰器的本体：")
timed_add = timed(slow_add)
say(f"    结果是 {timed_add(1, 2)}")
print()

say("  再看 @ 的写法，效果完全一样：")


@timed
def slow_mul(a: int, b: int) -> int:
    """两个数相乘（顺便用来说明 wraps 保住了这段说明）。"""
    time.sleep(0.2)
    return a * b


say(f"    结果是 {slow_mul(3, 4)}")
print()

say(
    "  所以 @timed 这一行的意思就是：slow_mul = timed(slow_mul)",
    "  ——把原函数包一层，再把包好的结果重新叫回原来的名字。",
)


# ============================================================
section("4. functools.wraps：一行代码，救回函数的名字")
# ============================================================

say(
    "  上面 timed 里那行 @functools.wraps(func) 看着像废话，其实很关键。",
    "  去掉它会怎样？看这个：",
)


def without_wraps(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@without_wraps
def original() -> int:
    """我是原始函数的说明。"""
    return 1


say(
    f"    没加 wraps：函数名成了 {original.__name__!r}，说明是 {original.__doc__!r}",
    f"    加了 wraps：slow_mul 的函数名还是 {slow_mul.__name__!r}，说明是 {slow_mul.__doc__!r}",
    "",
    "  名字丢了会有什么后果：日志里全记成「wrapper」、调试器里看不出是哪个函数、",
    "  测试框架的报错也认不出它。所以写装饰器时记得加上 @functools.wraps(func)。",
)


# ============================================================
section('5. @app.get("/chat") 背后是什么')
# ============================================================

say(
    "这是什么：带参数的装饰器——外面再套一层函数，先收参数，再返回真正的装饰器。",
    "为什么需要：Web 框架要记住「哪个 URL 交给哪个函数」，这件事就发生在装饰器里。",
    "场景：你写的每个接口，都是被这样一个装饰器「登记」进路由表的。",
)
print()

ROUTES: dict[str, object] = {}


def route(path: str):
    """先收路径参数，返回一个装饰器。"""

    def decorator(func):
        ROUTES[path] = func  # 登记：把路径和函数记到一张表里
        return func  # 原函数原样还回去，所以它照样能直接调用

    return decorator


@route("/chat")
def chat_handler() -> str:
    return "（这里是聊天的处理逻辑）"


@route("/health")
def health_handler() -> str:
    return "ok"


say(
    f"  这个模块被导入时，注册表就被填好了：{list(ROUTES)}",
    f"  被装饰的函数自己也能调用：chat_handler() = {chat_handler()!r}",
    f"  请求进来时框架查表：ROUTES['/chat']() = {ROUTES['/chat']()!r}",
    "",
    "  FastAPI 的 @app.get('/chat') 就是这个套路：登记 + 原样返回。",
    "  区别只是它顺手把参数类型、返回类型也记下来，用来做校验和生成接口文档。",
)


# ============================================================
section("6. 需要会用的几个现成装饰器")
# ============================================================

say(
    "  @property            把方法当属性用（Day 4 学过）",
    "  @functools.lru_cache 缓存函数结果，同样的参数第二次直接返回上次的",
    "  @pytest.fixture      测试前准备数据；@pytest.mark.parametrize 参数化测试",
    "  @app.get / @app.post Web 框架的路由",
    "  @staticmethod / @classmethod  类里的两种方法（见到不慌就行）",
    "",
    "  清单对这一天只要求「会读、会用现成的」，所以上面 timed 的内部细节",
    "  一时写不出来完全不影响往下走——真正需要自己动手写的时候再回来补十分钟就够。",
    "  唯一值得顺手记住的是 wrapper(*args, **kwargs) 那一行：",
    "  装饰器不知道原函数有几个参数，就靠它把所有参数原样转发过去。",
)


# ============================================================
section("7. 要注意什么")
# ============================================================

say(
    "  1. 装饰器在「定义被装饰函数的那一刻」就执行了。",
    "     也就是说，import 这个模块的时候第 5 节的 ROUTES 就被填好了——",
    "     这既是路由能生效的原因，也是「有些副作用发生在导入时」的来源。",
    "  2. 忘了 @functools.wraps，函数名和文档会丢，日志和调试都会变难。",
    "  3. 别把装饰器套太多层。三层以上的装饰器，读代码的人要花很久才能想明白",
    "     一次调用到底经过了几层。",
    "  4. 装饰器不该偷偷改函数的行为。名字叫 timed 就该只做计时，",
    "     顺手改返回值、吞异常，是给人埋坑。",
)


section("总结")
say(
    "1. 函数是值：能赋值、能当参数、能当返回值",
    "2. 闭包让内层函数记住外层变量，装饰器靠它记住原函数",
    "3. @deco 就是 f = deco(f) 的语法糖",
    "4. 写装饰器要加 @functools.wraps(func)，否则名字和说明会丢",
    "5. @app.get('/chat') = 带参数的装饰器 + 注册，框架靠它知道哪个 URL 找哪个函数",
)
