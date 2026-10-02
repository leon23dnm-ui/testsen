import numpy as np


def update_eligibility(graph, state, lam: float, gate_thr: float, qmax: float):
    """Обновление eligibility traces Q_elig по edges.

    q_new = clip((1-lam)*q + gate*psi, -qmax, qmax)
    gate = |a_dst * a_src| > gate_thr
    psi = (a_dst - a_mean) * (a_src - a_mean)
    """
    X = state.X
    a = X.mean(axis=-1)
    a_mean = a.mean()
    q_old = graph.q_elig

    q_new = np.empty_like(q_old, dtype=float)
    edges = graph.edge_index.shape[1]

    for e in range(edges):
        src = graph.edge_index[0, e]
        dst = graph.edge_index[1, e]
        d = int(graph.delays[e])

        delayed_X = state.delayed(d)
        a_src = delayed_X.mean(axis=-1)[src]
        a_dst = a[dst]

        psi = (a_dst - a_mean) * (a_src - a_mean)
        gate = abs(a_dst * a_src) > gate_thr

        q_new[e] = np.clip((1.0 - lam) * q_old[e] + gate * psi, -qmax, qmax)

    return q_new
