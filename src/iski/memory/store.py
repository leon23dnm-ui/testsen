import numpy as np

from iski.core.kernels import kernel_similarity


class MemoryStore:
    """Ограниченное хранилище элементов памяти и проекция F^mem."""

    def __init__(self, items: list, m_max: int):
        self.items = list(items)
        self.m_max = m_max

    def clone(self) -> "MemoryStore":
        return MemoryStore([item.clone() for item in self.items], self.m_max)

    def projection(self, E: np.ndarray, sigma: float, K: int) -> np.ndarray:
        """F^mem = Sum_{status==0} w_k * K(E, e_k)[:,None] * x_k[None,:]."""
        N = E.shape[0]
        out = np.zeros((N, K), dtype=float)

        for item in self.items:
            if item.status != 0:
                continue
            K_col = kernel_similarity(E, item.e, sigma)[:, np.newaxis]
            x_row = item.x[np.newaxis, :]
            out += item.w * K_col * x_row

        return out
