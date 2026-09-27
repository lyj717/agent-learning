import check_env


def test_correct_return_true(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_MODEL=deepseek-v4-flash", encoding="utf-8")

    assert check_env.inspect_env_format(env_file) is True


def test_Chinese_mark_return_false(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_MODEL=】deepseek-v4-flash", encoding="utf-8")

    assert check_env.inspect_env_format(env_file) is False
