"""Нейрогенез M1: рост узла из неудержанной новизны.

Триггер (в runner, после тика): вход e_in, |M| == M_max, Novelty > theta_form,
cooldown прошёл и N < N_max. Новый узел:
  E_new = normalized e_in (специализация на новизне),
  X_new = 0 (нет истории), S_new = (mu*, 0, 1) канон-инициализация,
  рёбра к/от всех узлов по bootstrap-статистике (p0 возб., rho_I*p0 торм.,
  веса U(0,w_init_max)/U(0,w_minus_init_max), задержки U(0,Dmax)),
  ring-buffer X_hist расширяется нулями (прошлое узла — нули; delayed(0)=X_new).
Весь рандом seeded (RULES 9).
"""

import numpy as np

from iski.core.kernels import kernel_similarity


def novelty_score(e_in, store, sigma: float) -> float:
    """Novelty = 1 - max_k sim(e_in, e_k); пустой store => 1."""
    e_row = np.asarray(e_in, dtype=float).reshape(1, -1)
    best = 0.0
    for item in store:
        sim = float(kernel_similarity(e_row, item.e, sigma)[0])
        best = max(best, sim)
    return 1.0 - best


def should_grow(state, cfg, e_in) -> bool:
    """Рост разрешён, если вход не удержан памятью: |M|=M_max и Novelty>theta_form."""
    if e_in is None or state.X.shape[0] >= cfg.N_max:
        return False
    if len(state.store) < cfg.M_max:
        return False
    return novelty_score(e_in, state.store, cfg.sigma) > cfg.theta_form


def grow_node(
    state, cfg, e_in, t: int, last_grow: int, cooldown: int, pipe=None
) -> int:
    """Добавить узел в state. Возвращает t роста или last_grow без изменений."""
    if t - last_grow < cooldown or not should_grow(state, cfg, e_in):
        return last_grow

    st = state
    N, K = st.X.shape
    rng = np.random.default_rng(cfg.seeds["boot"] + 50_000 + t)

    e_new = np.asarray(e_in, dtype=float).copy()
    norm = np.linalg.norm(e_new)
    e_new = e_new / norm if norm > 0 else e_new
    st.E = np.vstack([st.E, e_new[None, :]])
    st.X = np.vstack([st.X, np.zeros((1, K), dtype=st.X.dtype)])
    st.S = np.vstack([st.S, np.array([[cfg.mu_star, 0.0, 1.0]])])

    hist = np.zeros((st.L, N + 1, K), dtype=st.X_hist.dtype)
    hist[:, :N] = st.X_hist
    hist[st.ptr, N] = st.X[N]
    st.X_hist = hist

    g = st.graph
    src, dst, wp, wm, dl, qe = [], [], [], [], [], []
    for i in range(N + 1):
        for j in range(N + 1):
            if i == j or (i != N and j != N):
                continue
            exc = rng.random() < cfg.p0
            inh = rng.random() < cfg.rho_I * cfg.p0
            if not (exc or inh):
                continue
            src.append(i)
            dst.append(j)
            wp.append(rng.uniform(0.0, cfg.w_init_max) if exc else 0.0)
            wm.append(rng.uniform(0.0, cfg.w_minus_init_max) if inh else 0.0)
            dl.append(int(rng.integers(0, cfg.Dmax)))
            qe.append(0.0)
    if src:
        g.edge_index = np.hstack(
            [g.edge_index, np.array([src, dst], dtype=g.edge_index.dtype)]
        )
        g.w_plus = np.concatenate([g.w_plus, np.array(wp)])
        g.w_minus = np.concatenate([g.w_minus, np.array(wm)])
        g.delays = np.concatenate([g.delays, np.array(dl, dtype=g.delays.dtype)])
        g.q_elig = np.concatenate([g.q_elig, np.array(qe)])

    # pipeline.last_eps имеет размер (N_old, K) — падим новым узлом-нулём
    if pipe is not None and hasattr(pipe, "last_eps"):
        K_ = st.X.shape[1]
        pipe.last_eps = np.vstack([pipe.last_eps, np.zeros((1, K_))])
    return t
