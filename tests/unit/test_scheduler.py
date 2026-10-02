import pytest

from iski.runtime.scheduler import Clocks


def test_clocks_invalid_order_raises():
    with pytest.raises(AssertionError):
        Clocks(50, 10, 200)


def test_clocks_medium_active():
    clocks = Clocks(10, 20, 100)
    assert clocks.active(50, "medium") is True
    assert clocks.active(51, "medium") is False
