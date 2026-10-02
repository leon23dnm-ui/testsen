import numpy as np

from iski.core.state import OmegaState
from iski.graph.topology import GraphCOO
from iski.learning.eligibility import update_eligibility


class _Cfg:
    Dmax = 0


def _make_graph(q_init):
    edge_index = np.array([[0, 1], [1, 0]], dtype=int)
    w = np.zeros(2)
    delays = np.zeros(2, dtype=int)
    return GraphCOO(edge_index, w, w, delays, np.array(q_init))


def test_eligibility_coactivation_grows():
    X = np.array([[3.0, 3.0], [1.0, 1.0]])  # a=[3,1], a_mean=2
    state = OmegaState(_Cfg(), np.zeros(2), X, None, np.zeros(2), [], 0)
    state.advance_ring()
    graph = _make_graph([0.0, 0.0])

    q_new = update_eligibility(graph, state, lam=0.1, gate_thr=0.5, qmax=5.0)
    assert abs(q_new[0]) > abs(graph.q_elig[0])


def test_eligibility_rest_decays():
    X = np.zeros((2, 2))
    state = OmegaState(_Cfg(), np.zeros(2), X, None, np.zeros(2), [], 0)
    state.advance_ring()
    graph = _make_graph([1.0, -1.0])

    q_new = update_eligibility(graph, state, lam=0.2, gate_thr=0.5, qmax=5.0)
    assert abs(q_new[0]) < abs(graph.q_elig[0])
    assert abs(q_new[1]) < abs(graph.q_elig[1])
