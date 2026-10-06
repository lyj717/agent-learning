"""验收测试：简易长期记忆。跑红了就是还没写对。

跑法（要先 cd 到 chat_cli 目录）：
    cd weeks\\week01_llm_api\\chat_cli
    ..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -v tests\\test_memory.py
"""

from pathlib import Path

import memory


def test_load_facts_returns_empty_when_file_missing(tmp_path: Path):
    """第一次用的时候文件还不存在——那不是错误，就是「还没有记忆」。"""
    assert memory.load_facts(tmp_path / "facts.json") == []


def test_add_then_load_round_trip(tmp_path: Path):
    """存两条、读回来，顺序不变。"""
    path = tmp_path / "facts.json"
    memory.add_fact(path, "我叫刘小明")
    memory.add_fact(path, "我在学 Agent")
    assert memory.load_facts(path) == ["我叫刘小明", "我在学 Agent"]


def test_facts_are_saved_as_readable_chinese(tmp_path: Path):
    """文件里得是中文原样，不能是 \\u5218 那种转义——不然打开没法看。"""
    path = tmp_path / "facts.json"
    memory.add_fact(path, "我叫刘小明")
    assert "刘小明" in path.read_text(encoding="utf-8")


def test_load_facts_survives_broken_file(tmp_path: Path):
    """文件被写坏了（不是 JSON）也不该崩，当成「还没有记忆」。"""
    path = tmp_path / "facts.json"
    path.write_text("这不是 JSON", encoding="utf-8")
    assert memory.load_facts(path) == []


def test_compose_system_without_facts_returns_base():
    """没有事实时原样返回人设（None 也原样）。"""
    assert memory.compose_system(None, []) is None
    assert memory.compose_system("人设", []) == "人设"


def test_compose_system_includes_facts():
    """有事实时，人设和事实都要在，而且是「- 内容」这种清单格式。"""
    composed = memory.compose_system("人设", ["我叫刘小明"])
    assert composed is not None
    assert "人设" in composed
    assert "刘小明" in composed
    assert "- 我叫刘小明" in composed


def test_compose_system_without_base_still_works():
    """只有事实、没有人设，也要能拼出来。"""
    composed = memory.compose_system(None, ["我叫刘小明"])
    assert composed is not None
    assert "刘小明" in composed
