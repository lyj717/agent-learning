"""验收测试：成本估算。数字来自官方价格页（deepseek-flash，空闲时段）。"""

import pytest
from cost import PRICE_IDLE, PRICE_PEAK, cost_of_call, session_cost


def test_cost_of_call_input_only():
    assert cost_of_call(1_000_000, 0) == 1.0


def test_cost_of_call_output_only():
    assert cost_of_call(0, 1_000_000) == 4.0


def test_cost_of_call_all_cached():
    assert cost_of_call(1_000_000, 0, cached_tokens=1_000_000) == 0.02


def test_cost_of_call_peak_price():
    assert cost_of_call(1_000_000, 0, price=PRICE_PEAK) == 2.0


def test_session_cost_single_turn():
    assert session_cost([1_000_000], [0], PRICE_IDLE) == 1.0


def test_session_cost_input_and_output():
    assert session_cost([1_000_000], [1_000_000], PRICE_IDLE) == 5.0


def test_session_cost_peak():
    assert session_cost([1_000_000], [0], PRICE_PEAK) == 2.0


@pytest.mark.parametrize("turns", [3, 10])
def test_session_cost_scales_with_turns(turns):
    """每轮 100 万输入，总账就是轮数那么多钱——不长在写死的表上。"""
    inputs = [1_000_000] * turns
    outputs = [0] * turns
    assert session_cost(inputs, outputs, PRICE_IDLE) == float(turns)
