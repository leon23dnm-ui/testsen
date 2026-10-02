import numpy as np

from iski.graph.topology import GraphCOO


def test_w_eff_sign():
    edge_index = np.array([[0, 1], [1, 0]], dtype=int)
    w_plus = np.array([1.0, -0.5])
    w_minus = np.array([0.5, -0.2])
    g = GraphCOO(edge_index, w_plus, w_minus, np.zeros(2, dtype=int), np.zeros(2))
    expected = np.array([0.5, -0.3])
    assert np.allclose(g.w_eff(), expected)


def test_laplacian_row_sums_zero():
    edge_index = np.array([[0, 1, 2], [1, 2, 0]], dtype=int)
    w_plus = np.array([1.0, 1.0, 1.0])
    w_minus = np.array([0.0, 0.0, 0.0])
    g = GraphCOO(edge_index, w_plus, w_minus, np.zeros(3, dtype=int), np.zeros(3))
    L = g.laplacian(n=3)
    assert np.allclose(L.sum(axis=1), 0.0)
