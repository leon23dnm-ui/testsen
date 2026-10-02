import numpy as np

from iski.core.state import OmegaState
from iski.graph.topology import GraphCOO
from iski.safety.invariants import check, project


class _Cfg:
    Dmax = 0
    x_min = -1.0
    x_max = 1.0
    W_max = 10.0
    E_max = 2.0
    M_max = 5
    q_max = 1.0


def _make_state():
    edge_index = np.array([[0], [1]], dtype=int)
    w_plus = np.array([15.0])
    w_minus = np.array([-2.0])
    delays = np.zeros(1, dtype=int)
    q_elig = np.array([2.0])
    graph = GraphCOO(edge_index, w_plus, w_minus, delays, q_elig)

    E = np.array([[3.0, 0.0], [0.0, 0.0]])
    X = np.array([[0.0, 5.0]])
    S = np.zeros(1)
    return OmegaState(_Cfg(), E, X, graph, S, store=[], tick=0)


def test_project_removes_violations():
    state = _make_state()
    assert len(check(state, _Cfg())) > 0
    project(state, _Cfg())
    assert check(state, _Cfg()) == []


def test_e_norms_bounded_after_project():
    state = _make_state()
    project(state, _Cfg())
    norms = np.linalg.norm(state.E, axis=1)
    assert np.all(norms <= _Cfg.E_max + 1e-9)
