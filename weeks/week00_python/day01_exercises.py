"""Day 1 练习：缩进、条件判断、循环、f-string、真值判断。

三道题的函数体是空的，需要你自己写。写完跑一遍看结果：
    .venv\\Scripts\\python.exe weeks\\week00_python\\day01_exercises.py

做题规矩：
1. 先自己想 20 分钟，别急着看之前的演示文件。
2. 每写完一题就单独跑一次，看输出对不对——别三题一起写完再跑。
3. 卡住了就把报错原文和你的猜测发给我。
"""


def describe_parity(number: int) -> str:
    """判断奇偶，返回「奇数」或「偶数」。

    期望结果：
        describe_parity(7)  -> "奇数"
        describe_parity(8)  -> "偶数"
        describe_parity(0)  -> "偶数"

    """
    if number % 2 == 0:
        answer = "偶数"
    else:
        answer = "奇数"
    return answer


def fibonacci(count: int) -> list[int]:
    """返回菲波那契数列的前 count 项，从 0 和 1 开始。

    期望结果：
        fibonacci(6)  -> [0, 1, 1, 2, 3, 5]
        fibonacci(1)  -> [0]
        fibonacci(0)  -> []

    """
    answers = []
    if count <= 0:
        return answers
    if count == 1:
        answers.append(0)
        return answers
    answers.append(0)
    answers.append(1)
    while len(answers) < count:
        answers.append(answers[-1] + answers[-2])
    return answers


def longest(words: list[str]) -> str:
    """返回列表里最长的那个字符串；列表为空时返回空字符串。

    期望结果：
        longest(["python", "agent", "ai"])  -> "python"
        longest(["a", "abc", "ab"])         -> "abc"
        longest([])                         -> ""

    """
    longest_str = ""
    if not words:
        return longest_str
    for word in words:
        if len(word) > len(longest_str):
            longest_str = word
    return longest_str


if __name__ == "__main__":
    print("=== 第 1 题：奇偶判断 ===")
    for value in (7, 8, 0):
        print(f"  {value} -> {describe_parity(value)}")

    print("\n=== 第 2 题：菲波那契 ===")
    for count in (6, 10, 20):
        print(f"  前 {count} 项：{fibonacci(count)}")

    print("\n=== 第 3 题：最长的字符串 ===")
    for words in (
        ["python", "agent", "ai"],
        ["a", "abc", "ab"],
        [],
    ):
        print(f"  {words} -> {longest(words)!r}")
