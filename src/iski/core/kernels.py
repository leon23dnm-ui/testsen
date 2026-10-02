import numpy as np
import torch


def kernel_similarity(
    E: np.ndarray | torch.Tensor, e: np.ndarray | torch.Tensor, sigma: float
):
    """RBF-ядро сходства: K(e_i, e) = exp(-||E_i - e||^2 / (2 sigma^2)).

    Поддерживает numpy и torch.
    """
    if isinstance(E, torch.Tensor):
        diff = E - e
        sq_dist = torch.sum(diff * diff, dim=1)
        return torch.exp(-sq_dist / (2.0 * sigma * sigma))

    if E.ndim != 2:
        raise ValueError("E must be a 2D array (N, D)")
    diff = E - e
    sq_dist = np.sum(diff * diff, axis=1)
    return np.exp(-sq_dist / (2.0 * sigma * sigma))
