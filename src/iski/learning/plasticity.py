import numpy as np

from iski.core.delta import Delta


def plasticity_delta(graph, eps, eta: float, lam_w: float) -> Delta:
    """Delta пластичности по prediction error eps и eligibility Q_elig."""
    eps_node = eps.mean(axis=-1)
    dst = graph.edge_index[1]

    dw = eta * graph.q_elig * eps_node[dst]
    dW_plus = np.maximum(dw, 0.0) - lam_w * graph.w_plus
    dW_minus = np.maximum(-dw, 0.0) - lam_w * graph.w_minus

    return Delta(dW_plus=dW_plus, dW_minus=dW_minus)
