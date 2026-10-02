import numpy as np
import pytest

from iski.core.delta import Delta, SingleWriterViolation
from iski.core.state import OmegaState
from iski.graph.topology import GraphCOO
from iski.runtime.candidate import assemble


class _Cfg:
    Dmax = 0


def _make_state():
    edge_index = np.array([[0], [1]], dtype=int)
    graph = GraphCOO(
        edge_index,
        w_plus=np.zeros(1),
        w_minus=np.zeros(1),
        delays=np.zeros(1, dtype=int),
        q_elig=np.zeros(1),
    )
    return OmegaState(
        _Cfg(),
        E=np.zeros((2, 2)),
        X=np.zeros((2, 2)),
        graph=graph,
        S=np.zeros(2),
        store=[],
        tick=0,
    )


def test_assemble_applies_non_overlapping_deltas():
    state = _make_state()
    d1 = Delta(dX=np.ones((2, 2)))
    d2 = Delta(dW_plus=np.array([0.5]))
    cand = assemble(state, [d1, d2])
    assert np.allclose(cand.X, np.ones((2, 2)))
    assert np.allclose(cand.graph.w_plus, np.array([0.5]))


def test_assemble_conflict_raises():
    state = _make_state()
    d1 = Delta(dX=np.ones((2, 2)))
    d2 = Delta(dX=np.ones((2, 2)) * 2)
    with pytest.raises(SingleWriterViolation):
        assemble(state, [d1, d2])
