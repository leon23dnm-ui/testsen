import numpy as np

from iski.core.delta import Delta


def init_S(n: int, mu_star: float) -> np.ndarray:
    """state.S := [N,3] = (mu, theta, g); инициализация mu=mu*, theta=0, g=1."""
    S = np.zeros((n, 3), dtype=float)
    S[:, 0] = mu_star
    S[:, 2] = 1.0
    return S


def homeostasis_update(S, X, cfg) -> Delta:
    """Гомеостаз (SPEC v3.0, Phase 8b), clock=medium.

    mu'   = (1-beta_h)*mu + beta_h*mean_K(X)
    theta'= theta + eta_theta*(mu - mu*)
    g'    = clip(g + eta_g*(mu* - mu), g_min, g_max)
    """
    mu_star = cfg.mu_star
    beta_h = cfg.beta_h
    eta_theta = cfg.eta_theta
    eta_g = cfg.eta_g
    g_min = cfg.g_min
    g_max = cfg.g_max

    S_arr = np.asarray(S, dtype=float)
    mu, theta, g = S_arr[:, 0], S_arr[:, 1], S_arr[:, 2]

    mu_new = (1.0 - beta_h) * mu + beta_h * np.asarray(X, dtype=float).mean(axis=-1)
    theta_new = theta + eta_theta * (mu - mu_star)
    g_new = np.clip(g + eta_g * (mu_star - mu), g_min, g_max)

    S_new = np.column_stack([mu_new, theta_new, g_new])
    return Delta(dS=S_new - S_arr)
