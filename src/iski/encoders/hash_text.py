import numpy as np


def encode_text(text: str, D: int, seed: int) -> np.ndarray:
    """phi_text: Raw -> R^D через 64-bin хэш и случайную проекцию."""
    v = np.zeros(64, dtype=float)
    for ch in text:
        v[ord(ch) % 64] += 1.0  # ord() — стабильный hash (RULES 9: детерминизм)

    rng = np.random.default_rng(seed)
    R = rng.standard_normal((64, D))
    e = v @ R
    norm = np.linalg.norm(e)
    if norm > 0:
        e = e / norm
    return e
