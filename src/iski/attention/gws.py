import numpy as np
import torch

from iski.core.kernels import kernel_similarity


def gws_broadcast(E, X, sal, theta: float, sigma: float, beta: float):
    """GWS broadcast: порог Sal>theta + мягкие alpha (TopK запрещён).

    Returns:
        X_bcast: X + beta * B
        S: булевый маска Sal > theta
    """
    was_numpy = isinstance(X, np.ndarray)
    E_t = torch.as_tensor(E, dtype=torch.float64)
    X_t = torch.as_tensor(X, dtype=torch.float64)
    sal_t = torch.as_tensor(sal, dtype=torch.float64)

    S = sal_t > theta
    if not torch.any(S):
        if was_numpy:
            return X_t.numpy(), S.numpy()
        return X_t, S

    idx = torch.nonzero(S, as_tuple=True)[0]
    alpha = sal_t[idx] / sal_t[idx].sum()

    B = torch.zeros_like(X_t, dtype=torch.float64)
    for pos, i in enumerate(idx.tolist()):
        K = torch.as_tensor(
            kernel_similarity(E_t, E_t[i], sigma), dtype=torch.float64
        ).unsqueeze(1)
        contrib = alpha[pos] * K * X_t[i].unsqueeze(0)
        B = B + contrib

    X_bcast_t = X_t + beta * B
    if was_numpy:
        return X_bcast_t.numpy(), S.numpy()
    return X_bcast_t, S
