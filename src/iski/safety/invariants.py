import numpy as np


def check(st, cfg) -> list[str]:
    """Проверить hard-инварианты состояния и вернуть список нарушений."""
    violations: list[str] = []

    if np.any(st.X < cfg.x_min) or np.any(st.X > cfg.x_max):
        violations.append("X out of [x_min, x_max]")

    if np.any(st.graph.w_plus < 0.0) or np.any(st.graph.w_plus > cfg.W_max):
        violations.append("w_plus out of [0, W_max]")
    if np.any(st.graph.w_minus < 0.0) or np.any(st.graph.w_minus > cfg.W_max):
        violations.append("w_minus out of [0, W_max]")

    e_norms = np.linalg.norm(st.E, axis=1)
    if np.any(e_norms > cfg.E_max):
        violations.append("||e_i|| > E_max")

    if len(st.store) > cfg.M_max:
        violations.append("|M| > M_max")

    if np.any(st.graph.q_elig < -cfg.q_max) or np.any(st.graph.q_elig > cfg.q_max):
        violations.append("q_elig out of [-q_max, q_max]")

    return violations


def project(st, cfg) -> None:
    """Спроецировать состояние на допустимое множество инвариантов."""
    st.X = np.clip(st.X, cfg.x_min, cfg.x_max)

    st.graph.w_plus = np.clip(st.graph.w_plus, 0.0, cfg.W_max)
    st.graph.w_minus = np.clip(st.graph.w_minus, 0.0, cfg.W_max)

    norms = np.linalg.norm(st.E, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    scale = np.where(norms > cfg.E_max, cfg.E_max / norms, 1.0)
    st.E = st.E * scale

    st.graph.q_elig = np.clip(st.graph.q_elig, -cfg.q_max, cfg.q_max)
