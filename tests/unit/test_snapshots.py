import numpy as np

from iski.core.snapshots import export_snapshot
from iski.core.state import OmegaState


class _Cfg:
    Dmax = 2


class _Graph:
    def __init__(self):
        self.w_plus = np.ones((3, 3), dtype=np.float64)
        self.w_minus = np.zeros((3, 3), dtype=np.float64)


def _make_state():
    cfg = _Cfg()
    E = np.array([1.0, 2.0, 3.0])
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    graph = _Graph()
    S = np.array([0.5, 0.5])
    return OmegaState(cfg, E, X, graph, S, [], tick=0)


def test_snapshot_is_independent_of_state():
    state = _make_state()
    metrics = {"tick": 0}
    gamma = export_snapshot(state, metrics)

    assert gamma["frozen"] is True
    assert np.array_equal(gamma["X"], state.X)
    assert np.array_equal(gamma["W_eff"], state.graph.w_plus - state.graph.w_minus)

    state.X += 100.0
    state.graph.w_plus += 50.0

    assert not np.array_equal(gamma["X"], state.X)
    assert not np.array_equal(gamma["W_eff"], state.graph.w_plus - state.graph.w_minus)
