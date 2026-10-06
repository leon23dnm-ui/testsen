import copy
from typing import Any

import numpy as np

from iski.core.delta import CHANNELS, Delta


class OmegaState:
    """Состояние Omega с ring-buffer задержек по X.

    Поля (как в задании T03):
        cfg   — конфигурация, должна содержать cfg.Dmax (максимальная задержка)
        E     — поле E (R^D)
        X     — поле X (R^{N x K})
        graph — объект графа с w_plus/w_minus (и опционально q_elig)
        S     — поле S
        store — хранилище M (список элементов)
        tick  — номер тика
        X_hist — ring-buffer истории X размера (Dmax+1, N, K)
        ptr   — текущий указатель кольца

    Чтение истории только через delayed(d); прямая мутация X_hist запрещена.
    """

    def __init__(
        self,
        cfg: Any,
        E: Any,
        X: np.ndarray,
        graph: Any,
        S: Any,
        store: list,
        tick: int = 0,
    ) -> None:
        self.cfg = cfg
        self.E = E
        self.X = X
        self.graph = graph
        self.S = S
        self.store = store
        self.tick = tick

        self.Dmax = int(cfg.Dmax)
        self.L = self.Dmax + 1
        n, k = X.shape
        self.X_hist = np.zeros((self.L, n, k), dtype=X.dtype)
        self.ptr = 0

    def delayed(self, d: int) -> np.ndarray:
        """Вернуть X с задержкой d: x[t-d] из ring-buffer."""
        if not 0 <= d <= self.Dmax:
            raise ValueError(f"delay d={d} out of [0, {self.Dmax}]")
        idx = (self.ptr - d) % self.L
        return self.X_hist[idx].copy()

    def advance_ring(self) -> None:
        """Сдвинуть кольцо и сохранить текущий X."""
        self.ptr = (self.ptr + 1) % self.L
        self.X_hist[self.ptr] = self.X.copy()

    def clone_for_candidate(self) -> "OmegaState":
        """Глубокая копия состояния для candidate-фазы."""
        clone = OmegaState(
            self.cfg,
            copy.deepcopy(self.E),
            self.X.copy(),
            copy.deepcopy(self.graph),
            copy.deepcopy(self.S),
            self.store.copy(),
            tick=self.tick,
        )
        clone.X_hist = self.X_hist.copy()
        clone.ptr = self.ptr
        return clone

    def apply_delta(self, d: Delta) -> None:
        """Применить Delta к состоянию (только из candidate/commit/maintenance)."""
        if not isinstance(d, Delta):
            raise TypeError(f"apply_delta expected Delta, got {type(d).__name__}")

        if d.dX is not None:
            self.X = self.X + d.dX
        if d.dE is not None:
            self.E = self.E + d.dE
        if d.dS is not None:
            self.S = self.S + d.dS

        if d.dW_plus is not None:
            self.graph.w_plus = self.graph.w_plus + d.dW_plus
        if d.dW_minus is not None:
            self.graph.w_minus = self.graph.w_minus + d.dW_minus
        if d.dQ_elig is not None:
            self.graph.q_elig = d.dQ_elig

        if d.dM is not None:
            self._apply_dM(d.dM)

        # dG и dTheta не разобраны в T03; при появлении — явная ошибка.
        for ch in ("dG", "dTheta"):
            if getattr(d, ch) is not None:
                raise NotImplementedError(
                    f"channel {ch} is not handled by OmegaState.apply_delta in T03"
                )

        # dX/dE/dS/etc уже применены; канал dX_hist недопустим.
        for ch in CHANNELS:
            if ch in (
                "dX",
                "dE",
                "dS",
                "dW_plus",
                "dW_minus",
                "dQ_elig",
                "dM",
                "dG",
                "dTheta",
            ):
                continue
            if getattr(d, ch) is not None:
                raise NotImplementedError(f"unknown channel {ch}")

    def _apply_dM(self, op: Any) -> None:
        """Обработать одну или несколько dM-операций."""
        if not op:
            return

        # одиночная операция: ("add", ...) и т.п.
        if isinstance(op, (list, tuple)) and op and isinstance(op[0], str):
            ops = [op]
        else:
            ops = op

        for single in ops:
            action = single[0]
            if action == "add":
                self.store.append(single[1])
            elif action == "rho":
                i, rho = single[1], single[2]
                self.store[i].rho = rho
            elif action == "status":
                i, st, t = single[1], single[2], single[3]
                self.store[i].status = st
                self.store[i].status_t = t
            elif action == "del":
                i = single[1]
                self.store.pop(i)
            else:
                raise ValueError(f"unknown dM op: {action}")
