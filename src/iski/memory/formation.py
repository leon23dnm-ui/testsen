import numpy as np

from iski.core.kernels import kernel_similarity
from iski.memory.item import MemoryItem


def formation_decision(e_in, M, theta_form: float, sigma: float, m_max: int):
    """Novelty = 1 - max_k sim(e_in, e_k^mem). M пусто => Novelty = 1.

    form: Novelty > theta_form и |M| < m_max; иначе reinforce.
    Возвращает (decision, best_idx): best_idx — индекс ближайшего элемента
    (для reinforce: last_access=t), при пустом M — -1.
    """
    best, best_sim = -1, 0.0
    e_row = np.asarray(e_in, dtype=float).reshape(1, -1)
    for k, item in enumerate(M):
        sim = float(kernel_similarity(e_row, item.e, sigma)[0])
        if sim > best_sim:
            best, best_sim = k, sim
    novelty = 1.0 - best_sim
    if novelty > theta_form and len(M) < m_max:
        return "form", best
    return "reinforce", best


def create_memory(e_in, X_t, cfg, t: int) -> MemoryItem:
    """Новый элемент памяти: e = e_in; x = паттерн опыта; rho канонический.

    F_mem = Sum w_k K(E,e_k) x_k требует x_k из R^K — паттерн опыта
    берём как mean_N(X_t) (усреднение поля по узлам).
    """
    rho = np.array(
        [0.3, 0.5, 0.1, 0.2, cfg.w_mem_init, 0.0, 0.0, 0.0, 0.0], dtype=float
    )
    return MemoryItem(
        e=np.asarray(e_in, dtype=float).copy(),
        x=np.asarray(X_t, dtype=float).mean(axis=0).copy(),
        rho=rho,
        status=0,
        t_create=t,
        last_access=t,
    )
