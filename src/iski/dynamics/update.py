import torch


def field_update(
    X, I_src, Lam: float, kappa: float, L, xi, g=None, theta=None
) -> torch.Tensor:
    """Обновление поля X: X + Lam*(-X + tanh(g*(I_src - kappa*(L@X) - theta))) + xi.

    Форма v3.0 (Phase 8b): Phi(g(z - theta)), z = I_src - kappa*(L@X).
    """
    X_t = torch.as_tensor(X, dtype=torch.float64)
    I_t = torch.as_tensor(I_src, dtype=torch.float64)
    L_t = torch.as_tensor(L, dtype=torch.float64)
    xi_t = torch.as_tensor(xi, dtype=torch.float64)

    n = X_t.shape[0]
    g_t = (
        torch.ones(n, dtype=torch.float64)
        if g is None
        else torch.as_tensor(g, dtype=torch.float64)
    )
    th_t = (
        torch.zeros(n, dtype=torch.float64)
        if theta is None
        else torch.as_tensor(theta, dtype=torch.float64)
    )

    diffusion = L_t @ X_t
    Z = g_t.unsqueeze(1) * (I_t - kappa * diffusion - th_t.unsqueeze(1))
    activation = torch.tanh(Z)
    return X_t + Lam * (-X_t + activation) + xi_t
