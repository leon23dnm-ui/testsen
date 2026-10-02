import numpy as np


def compute_metrics(st, eps, e_in, cfg) -> dict:
    """Вычислить activity, энтропию H, s_ed, rho(J), норму eps."""
    X = st.X
    E = st.E
    N = X.shape[0]

    activity = float(np.mean(np.abs(X)))

    abs_x = np.abs(X)
    total = abs_x.sum()
    if total > 0:
        p = abs_x.flatten() / total
        p = p[p > 0]
        H = float(-np.sum(p * np.log(p)))
    else:
        H = 0.0

    rn = np.linalg.norm(X, axis=1)
    if rn.sum() > 0:
        alpha = rn / rn.sum()
    else:
        alpha = np.full(N, 1.0 / N)
    ebar = alpha @ E

    if e_in is not None and np.linalg.norm(e_in) > 0 and np.linalg.norm(ebar) > 0:
        s_ed = float(np.dot(ebar, e_in) / (np.linalg.norm(ebar) * np.linalg.norm(e_in)))
    else:
        s_ed = float(np.nan)

    if st.graph is not None:
        A = st.graph.dense_abs(N)
        Lambda = getattr(cfg, "Lambda", 0.0)
        J = (1.0 - Lambda) * np.eye(N) + Lambda * A
        rho_j = float(np.max(np.sum(np.abs(J), axis=1)))
    else:
        rho_j = float(np.nan)

    eps_norm = float(np.linalg.norm(eps))

    return {
        "activity": activity,
        "H": H,
        "s_ed": s_ed,
        "rho_j": rho_j,
        "eps_norm": eps_norm,
    }


def gate_fraction(state, graph, gate_thr: float) -> float:
    """Readout: доля рёбер с активным гейтом eligibility |a_dst*a_src| > gate_thr."""
    n_edges = graph.edge_index.shape[1]
    if n_edges == 0:
        return 0.0

    a = np.asarray(state.X, dtype=float).mean(axis=-1)
    count = 0
    for e in range(n_edges):
        src = graph.edge_index[0, e]
        dst = graph.edge_index[1, e]
        a_src = state.delayed(int(graph.delays[e])).mean(axis=-1)[src]
        count += abs(a[dst] * a_src) > gate_thr
    return count / n_edges


def tick_metrics(F_ext, gws_mask, gate_frac: float, graph, S) -> dict:
    """Расширенный лог тика: gate_frac, mean_F_ext, mask_frac, ||W||_F, mean_g."""
    return {
        "gate_frac": float(gate_frac),
        "mean_F_ext": float(np.mean(F_ext)),
        "mask_frac": float(np.mean(gws_mask)),
        "w_fro": float(np.linalg.norm(graph.w_eff())),
        "mean_g": float(np.mean(np.asarray(S, dtype=float)[:, 2])),
    }
