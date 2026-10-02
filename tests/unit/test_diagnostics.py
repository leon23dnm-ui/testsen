import numpy as np

from iski.core.state import OmegaState
from iski.graph.topology import GraphCOO
from iski.runtime.diagnostics import compute_metrics


class _Cfg:
    Dmax = 0
    Lambda = 0.5


def _make_state():
    edge_index = np.array([[0], [1]], dtype=int)
    graph = GraphCOO(
        edge_index,
        w_plus=np.ones(1),
        w_minus=np.zeros(1),
        delays=np.zeros(1, dtype=int),
        q_elig=np.zeros(1),
    )
    E = np.array([[1.0, 0.0], [0.0, 1.0]])
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    S = np.zeros(2)
    return OmegaState(_Cfg(), E, X, graph, S, store=[], tick=0)


def test_entropy_bounds():
    state = _make_state()
    metrics = compute_metrics(state, np.zeros_like(state.X), e_in=None, cfg=_Cfg())
    M = state.X.size
    assert 0.0 <= metrics["H"] <= np.log(M) + 1e-9


def test_s_ed_is_one_for_equal_e_in():
    state = _make_state()
    X = np.array([[1.0, 0.0], [0.0, 0.0]])
    state.X = X
    metrics = compute_metrics(
        state, np.zeros_like(state.X), e_in=state.E[0], cfg=_Cfg()
    )
    assert np.isclose(metrics["s_ed"], 1.0, atol=1e-5)


def test_rho_j_lower_bound():
    state = _make_state()
    metrics = compute_metrics(state, np.zeros_like(state.X), e_in=None, cfg=_Cfg())
    assert metrics["rho_j"] >= 1.0 - _Cfg().Lambda - 1e-9
