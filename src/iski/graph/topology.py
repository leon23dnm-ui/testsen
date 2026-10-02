from dataclasses import dataclass

import numpy as np


@dataclass
class GraphCOO:
    """Разреженный адаптивный граф в COO-представлении.

    edge_index: (2, E) — [src, dst] для каждого ребра
    w_plus, w_minus: (E,) — веса W+ и W-
    delays: (E,) int — задержки d_{ji}
    q_elig: (E,) — eligibility traces
    """

    edge_index: np.ndarray
    w_plus: np.ndarray
    w_minus: np.ndarray
    delays: np.ndarray
    q_elig: np.ndarray

    def w_eff(self) -> np.ndarray:
        """Эффективный вес: W_eff = W+ - W-."""
        return self.w_plus - self.w_minus

    def clone(self) -> "GraphCOO":
        """Глубокая копия графа."""
        return GraphCOO(
            edge_index=self.edge_index.copy(),
            w_plus=self.w_plus.copy(),
            w_minus=self.w_minus.copy(),
            delays=self.delays.copy(),
            q_elig=self.q_elig.copy(),
        )

    def dense_abs(self, n: int) -> np.ndarray:
        """Плотная матрица A[dst, src] += |W_eff| размера (n, n)."""
        A = np.zeros((n, n), dtype=float)
        src = self.edge_index[0]
        dst = self.edge_index[1]
        A[dst, src] += np.abs(self.w_eff())
        return A

    def laplacian(self, n: int) -> np.ndarray:
        """L = D_g - |W_eff|, где D_g = diag(sum_j A_ij)."""
        A = self.dense_abs(n)
        row_sum = A.sum(axis=1)
        D = np.diag(row_sum)
        return D - A
