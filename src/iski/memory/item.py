from dataclasses import dataclass

import numpy as np


@dataclass
class MemoryItem:
    """Элемент долговременной памяти M0."""

    e: np.ndarray
    x: np.ndarray
    rho: np.ndarray
    status: int = 0
    t_create: int = 0
    last_access: int = 0

    @property
    def w(self) -> float:
        """Скалярный вес = rho[4], без дублирования поля."""
        return float(self.rho[4])

    def clone(self) -> "MemoryItem":
        """Независимая копия item."""
        return MemoryItem(
            e=self.e.copy(),
            x=self.x.copy(),
            rho=self.rho.copy(),
            status=self.status,
            t_create=self.t_create,
            last_access=self.last_access,
        )
