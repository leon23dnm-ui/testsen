import numpy as np


def update_modes(
    rho: np.ndarray,
    reuse: float,
    imp: float,
    surprise: float,
    pg: float,
    eta,
    dt: float,
    w_max: float,
) -> np.ndarray:
    """5 уравнений жизненного цикла элемента памяти v3.0.

    rho: (M, 5) -> [d, a, c, f, w]
    eta: 9 скаляров [eta1..eta9]
    """
    rho0 = rho[:, 0]
    rho1 = rho[:, 1]
    rho2 = rho[:, 2]
    rho3 = rho[:, 3]
    rho4 = rho[:, 4]

    d = np.clip(rho0 * np.exp(-eta[0] * reuse), 0.0, 1.0)
    a = np.clip(rho1 + eta[1] * imp - eta[2] * (1.0 - reuse), 0.0, 1.0)
    c = np.clip(rho2 + eta[3] * imp + eta[4] * pg, 0.0, 1.0)
    f = np.clip(rho3 + eta[5] * (1.0 - reuse) - eta[6] * surprise, 0.0, 1.0)
    w = np.clip(rho4 * np.exp(-rho0 * dt) + eta[7] * reuse + eta[8] * imp, 0.0, w_max)

    return np.stack([d, a, c, f, w], axis=1)
