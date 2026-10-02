import numpy as np

from iski.graph.topology import GraphCOO
from iski.learning.plasticity import plasticity_delta


def _make_graph(q_elig):
    edge_index = np.array([[0, 1], [1, 0]], dtype=int)
    w_plus = np.zeros(2)
    w_minus = np.zeros(2)
    delays = np.zeros(2, dtype=int)
    return GraphCOO(edge_index, w_plus, w_minus, delays, np.array(q_elig))


def test_plasticity_positive_dw_only_plus():
    graph = _make_graph([1.0, -1.0])
    eps = np.zeros((2, 2))
    eps[1] = 1.0  # eps_node[1] = 1.0 -> positive dw for edge 0->1

    delta = plasticity_delta(graph, eps, eta=0.5, lam_w=0.0)
    assert delta.dW_plus[0] > 0.0
    assert np.all(delta.dW_minus == 0.0)


def test_plasticity_zero_eps_decay():
    graph = _make_graph([0.5, -0.5])
    graph.w_plus[:] = 1.0
    graph.w_minus[:] = 1.0
    eps = np.zeros((2, 2))

    delta = plasticity_delta(graph, eps, eta=0.5, lam_w=0.1)
    assert np.allclose(delta.dW_plus, -0.1 * graph.w_plus)
    assert np.allclose(delta.dW_minus, -0.1 * graph.w_minus)
