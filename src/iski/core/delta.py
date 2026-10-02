from dataclasses import dataclass
from typing import Any

CHANNELS: tuple[str, ...] = (
    "dX",
    "dW_plus",
    "dW_minus",
    "dE",
    "dQ_elig",
    "dM",
    "dG",
    "dS",
    "dTheta",
)


class SingleWriterViolation(RuntimeError):
    """Конфликт канала: два непустых Delta пытаются записать в один канал."""


@dataclass(frozen=True)
class Delta:
    """Неизменяемый контейнер дельт по каналам Omega.

    Каждый канал может быть либо None (отсутствие дельты), либо не-None.
    Объединение (merge) запрещено, если оба операнда содержат не-None
    значение для одного и того же канала — single-writer rule.
    """

    dX: Any = None
    dW_plus: Any = None
    dW_minus: Any = None
    dE: Any = None
    dQ_elig: Any = None
    dM: Any = None
    dG: Any = None
    dS: Any = None
    dTheta: Any = None

    def is_empty(self) -> bool:
        return all(getattr(self, ch) is None for ch in CHANNELS)

    def merge(self, other: "Delta") -> "Delta":
        if not isinstance(other, Delta):
            raise TypeError(f"merge expected Delta, got {type(other).__name__}")

        merged: dict[str, Any] = {}
        for ch in CHANNELS:
            a = getattr(self, ch)
            b = getattr(other, ch)
            if a is not None and b is not None:
                raise SingleWriterViolation(ch)
            merged[ch] = a if a is not None else b

        return Delta(**merged)
