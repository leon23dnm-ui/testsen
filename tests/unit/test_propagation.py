import numpy as np
import torch

from iski.core.state import OmegaState
from iski.dynamics.propagation import propagate
from iski.graph.topology import GraphCOO


class _Cfg:
    Dmax = 1


def _make_state_with_delay():
    old = np.array([[1.0, 2.0], [3.0, 4.0]])
    new = np.array([[5.0, 6.0], [7.0, 8.0]])

    state = OmegaState(
        _Cfg(),
        E=np.zeros(2),
        X=old,
        graph=None,
        S=np.zeros(2),
        store=[],
        tick=0,
    )
    state.advance_ring()  # ptr=1, hist[1]=old
    state.X = new
    state.advance_ring()  # ptr=0, hist[0]=new, hist[1]=old
    return state


def test_propagation_manual_two_nodes():
    state = _make_state_with_delay()
    edge_index = np.array([[0], [1]], dtype=int)
    w_plus = np.array([0.5])
    w_minus = np.array([0.0])
    delays = np.array([1], dtype=int)
    graph = GraphCOO(edge_index, w_plus, w_minus, delays, np.zeros(1))

    out = propagate(graph, state, n=2, k=2)
    expected = torch.zeros(2, 2, dtype=torch.float64)
    expected[1] = 0.5 * torch.tensor([1.0, 2.0], dtype=torch.float64)

    assert torch.allclose(out, expected)
