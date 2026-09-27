"""演示 pytest 的 tmp_path 夹具：它是什么、为什么需要它。

运行：
    .venv\\Scripts\\python.exe -m pytest tests/test_tmp_path_demo.py -v -s
"""

from pathlib import Path


def test_tmp_path_is_a_directory(tmp_path):
    """tmp_path 是一个目录，类型是前面学过的 Path。"""
    print(f"\n  第 1 个测试拿到的临时目录：{tmp_path}")

    assert isinstance(tmp_path, Path)
    assert tmp_path.exists()


def test_each_test_gets_its_own_directory(tmp_path):
    """每个测试拿到的是不同的目录，互不干扰。"""
    print(f"  第 2 个测试拿到的临时目录：{tmp_path}")

    assert tmp_path.exists()


def test_write_and_read_a_file(tmp_path):
    """在临时目录里造一个文件，写进去再读回来。"""
    fake_env = tmp_path / ".env"
    fake_env.write_text("LLM_MODEL=test-model\n", encoding="utf-8")

    print(f"  写好的文件路径：{fake_env}")

    assert fake_env.exists()
    assert fake_env.read_text(encoding="utf-8") == "LLM_MODEL=test-model\n"


def test_leftovers_do_not_leak_between_tests(tmp_path):
    """上一个测试写的文件不会出现在这个测试的目录里。"""
    files = list(tmp_path.iterdir())

    print(f"  第 4 个测试的目录里有 {len(files)} 个文件")

    assert files == []
