import numpy as np
import torch

from iski.core.state import OmegaState
from iski.dynamics.noise import make_rng
from iski.graph.topology import GraphCOO
from iski.prediction.buffer import RingBufferH
from iski.prediction.heads import PredHead
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks


class _Cfg:
    Dmax = 0
    sigma = 1.0
    theta_gws = 0.0
    beta_g = 0.0
    T_A = 1.0
    lam_N = 1.0
    lam_E = 1.0
    kappa = 1.0
    Lambda = 0.5
    xi_max = 0.0
    lam_elig = 0.1
    gate_thr = 0.0
    q_max = 1.0
    eta = [0.1] * 9
    eta_plast = 0.01
    lam_w = 0.0
    theta_align = 0.0
    eta_E = 0.01
    tau1 = 1
    M_max = 5
    w_max = 1.0
    w_min = 0.1
    theta_forget = 0.9
    theta_I = 0.1
    T_archive = 100
    x_min = -10.0
    x_max = 10.0
    W_max = 100.0
    E_max = 10.0
    mu_star = 0.1
    beta_h = 0.05
    eta_theta = 0.01
    eta_g = 0.05
    g_min = 0.5
    g_max = 5.0


def _make_state():
    edge_index = np.array([[0], [1]], dtype=int)
    graph = GraphCOO(
        edge_index,
        w_plus=np.zeros(1),
        w_minus=np.zeros(1),
        delays=np.zeros(1, dtype=int),
        q_elig=np.zeros(1),
    )
    E = np.eye(2, dtype=float)
    X = np.zeros((2, 2), dtype=float)
    S = np.array([[0.1, 0.0, 1.0], [0.1, 0.0, 1.0]])
    return OmegaState(_Cfg(), E, X, graph, S, store=[], tick=0)


def _make_head(seed):
    torch.manual_seed(seed)
    return PredHead(2, 2, 3)


def test_tick_determinism():
    base = _make_state()

    head1 = _make_head(42)
    head2 = _make_head(42)
    hbuf1 = RingBufferH(5)
    hbuf2 = RingBufferH(5)
    rng1 = make_rng(7)
    rng2 = make_rng(7)
    clocks = Clocks(2, 4, 8)

    p1 = Pipeline(base, clocks, _Cfg(), head1, hbuf1, rng1)
    p2 = Pipeline(base.clone_for_candidate(), clocks, _Cfg(), head2, hbuf2, rng2)

    for _ in range(3):
        p1.tick(np.array([1.0, 0.0]), 0.5)
        p2.tick(np.array([1.0, 0.0]), 0.5)

    assert np.allclose(p1.state.X, p2.state.X, atol=1e-9)
