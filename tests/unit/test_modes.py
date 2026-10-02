import numpy as np

from iski.memory.modes import update_modes


def _base_rho():
    return np.array([[0.8, 0.5, 0.5, 0.5, 0.5], [0.7, 0.4, 0.4, 0.6, 0.6]])


def test_reuse_one_decreases_d():
    rho = _base_rho()
    eta = [0.5] * 9
    d0 = update_modes(
        rho, reuse=0.0, imp=0.0, surprise=0.0, pg=0.0, eta=eta, dt=0.1, w_max=2.0
    )[:, 0]
    d1 = update_modes(
        rho, reuse=1.0, imp=0.0, surprise=0.0, pg=0.0, eta=eta, dt=0.1, w_max=2.0
    )[:, 0]
    assert np.all(d1 < d0)


def test_surprise_one_decreases_f():
    rho = _base_rho()
    eta = [0.1] * 9
    f0 = update_modes(
        rho, reuse=0.0, imp=0.0, surprise=0.0, pg=0.0, eta=eta, dt=0.1, w_max=2.0
    )[:, 3]
    f1 = update_modes(
        rho, reuse=0.0, imp=0.0, surprise=1.0, pg=0.0, eta=eta, dt=0.1, w_max=2.0
    )[:, 3]
    assert np.all(f1 < f0)


def test_w_within_bounds():
    rho = _base_rho()
    eta = [0.1] * 9
    w = update_modes(
        rho, reuse=0.5, imp=0.5, surprise=0.0, pg=0.0, eta=eta, dt=0.1, w_max=1.5
    )[:, 4]
    assert np.all(w >= 0.0)
    assert np.all(w <= 1.5)


def test_components_except_w_within_zero_one():
    rho = _base_rho()
    eta = [0.5] * 9
    rho_next = update_modes(
        rho, reuse=0.5, imp=0.5, surprise=0.5, pg=0.5, eta=eta, dt=0.1, w_max=2.0
    )
    dacf = rho_next[:, :4]
    assert np.all(dacf >= 0.0)
    assert np.all(dacf <= 1.0)
