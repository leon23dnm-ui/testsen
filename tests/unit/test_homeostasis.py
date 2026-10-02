import numpy as np

from iski.dynamics.homeostasis import homeostasis_update, init_S
from iski.dynamics.update import field_update


class _Cfg:
    mu_star = 0.1
    beta_h = 0.05
    eta_theta = 0.01
    eta_g = 0.05
    g_min = 0.5
    g_max = 5.0


def test_mu_converges_to_mean_activity():
    cfg = _Cfg()
    S = init_S(3, cfg.mu_star)
    X = np.full((3, 4), 0.4)
    for _ in range(500):
        S = S + homeostasis_update(S, X, cfg).dS
    assert np.allclose(S[:, 0], np.full(3, 0.4), atol=1e-3)


def test_g_grows_when_mu_below_target():
    cfg = _Cfg()
    S = init_S(2, cfg.mu_star)
    S[:, 0] = 0.05
    d = homeostasis_update(S, np.zeros((2, 4)), cfg).dS
    assert np.all(d[:, 2] > 0.0)


def test_g_bounded():
    cfg = _Cfg()
    S = init_S(2, cfg.mu_star)
    S[:, 0] = -100.0
    for _ in range(2000):
        S = S + homeostasis_update(S, np.full((2, 4), -100.0), cfg).dS
    assert np.all(S[:, 2] <= cfg.g_max + 1e-12)
    S[:, 0] = 100.0
    for _ in range(2000):
        S = S + homeostasis_update(S, np.full((2, 4), 100.0), cfg).dS
    assert np.all(S[:, 2] >= cfg.g_min - 1e-12)


def test_zero_input_holds_activity():
    cfg = _Cfg()
    n, k = 2, 4
    S = init_S(n, cfg.mu_star)
    X = np.zeros((n, k))
    L = np.zeros((n, n))
    for _ in range(500):
        X = field_update(
            X,
            np.zeros((n, k)),
            Lam=0.5,
            kappa=1.0,
            L=L,
            xi=np.zeros((n, k)),
            g=S[:, 2],
            theta=S[:, 1],
        ).numpy()
        S = S + homeostasis_update(S, X, cfg).dS
    assert np.abs(X).mean() > 1e-3
    assert np.all(np.isfinite(X))
