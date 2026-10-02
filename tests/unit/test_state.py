import numpy as np

from iski.core.delta import Delta
from iski.core.state import OmegaState


class _Cfg:
    Dmax = 2


class _Graph:
    def __init__(self):
        self.W_plus = np.zeros((3, 3), dtype=np.float64)
        self.W_minus = np.zeros((3, 3), dtype=np.float64)


def _make_state(X=None, store=None):
    cfg = _Cfg()
    E = np.array([1.0, 2.0, 3.0])
    X = X if X is not None else np.array([[1.0, 2.0], [3.0, 4.0]])
    graph = _Graph()
    S = np.array([0.5, 0.5])
    store = store if store is not None else []
    return OmegaState(cfg, E, X, graph, S, store, tick=0)


def test_clone_is_independent():
    state = _make_state()
    clone = state.clone_for_candidate()

    state.X += 100.0
    state.graph.W_plus += 1.0
    state.advance_ring()

    assert not np.array_equal(clone.X, state.X)
    assert not np.array_equal(clone.graph.W_plus, state.graph.W_plus)
    assert not np.array_equal(clone.X_hist, state.X_hist)
    assert clone.ptr == 0
    assert clone.tick == state.tick == 0


def test_delayed_zero_after_advance():
    state = _make_state(X=np.array([[1.0, 2.0], [3.0, 4.0]]))
    state.advance_ring()
    assert np.array_equal(state.delayed(0), state.X)


def test_apply_delta_dX_adds():
    state = _make_state(X=np.array([[1.0, 2.0], [3.0, 4.0]]))
    delta = Delta(dX=np.array([[0.5, 1.0], [1.0, 0.5]]))
    state.apply_delta(delta)
    expected = np.array([[1.5, 3.0], [4.0, 4.5]])
    assert np.allclose(state.X, expected)


def test_apply_delta_dM_add_increases_store():
    state = _make_state(store=[])
    item = {"id": 7, "rho": 0.1}
    delta = Delta(dM=("add", item))
    state.apply_delta(delta)
    assert len(state.store) == 1
    assert state.store[0] is item
