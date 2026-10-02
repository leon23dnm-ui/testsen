from dataclasses import FrozenInstanceError

import pytest

from iski.core.delta import Delta, SingleWriterViolation


def test_delta_is_frozen():
    d = Delta(dX=1.0)
    with pytest.raises(FrozenInstanceError):
        d.dX = 2.0


def test_merge_conflict_on_same_channel():
    d1 = Delta(dX=1.0)
    d2 = Delta(dX=2.0)
    with pytest.raises(SingleWriterViolation) as exc:
        d1.merge(d2)
    assert exc.value.args[0] == "dX"


def test_merge_disjoint_channels_ok():
    d1 = Delta(dX=1.0)
    d2 = Delta(dE=2.0)
    merged = d1.merge(d2)
    assert merged.dX == 1.0
    assert merged.dE == 2.0
    assert merged.is_empty() is False


def test_delta_empty_by_default():
    assert Delta().is_empty() is True
