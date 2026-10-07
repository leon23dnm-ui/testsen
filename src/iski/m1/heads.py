"""PredHead с padding до N_max: вход N*K дополняется нулями до N_max*K,
predict возвращает только активные N строк. Рост N не ломает голову.

Runner обязан вызывать head.sync(state) перед каждым тиком пайплайна —
predict отдаёт ровно N*K элементов под текущее число узлов.
"""

import numpy as np

from iski.prediction.heads import PredHead


class PaddedPredHead:
    def __init__(self, n_max: int, K: int, H: int, lr: float = 0.01):
        self.n_max = n_max
        self.K = K
        self._n = None
        self.inner = PredHead(n_max, K, H, lr=lr)

    def sync(self, state) -> None:
        self._n = int(state.X.shape[0])

    def _pad(self, X):
        X = np.asarray(X, dtype=float)
        out = np.zeros((self.n_max, self.K), dtype=float)
        out[: X.shape[0]] = X
        return out

    def encode(self, X):
        return self.inner.encode(self._pad(X))

    def predict(self, h):
        if self._n is None:
            raise RuntimeError("PaddedPredHead: predict до sync(state)")
        full = self.inner.predict(h).reshape(self.n_max, self.K)
        return full[: self._n]

    def train_step(self, h_old, x_obs):
        return self.inner.train_step(h_old, self._pad(x_obs))
