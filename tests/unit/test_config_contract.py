import types

import numpy as np
import pytest
import torch

from iski.core.state import OmegaState
from iski.dynamics.noise import make_rng
from iski.graph.topology import GraphCOO
from iski.prediction.buffer import RingBufferH
from iski.prediction.heads import PredHead
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks

FULL = {
    "sigma": 1.0,
    "theta_gws": 0.0,
    "beta_g": 0.0,
    "T_A": 1.0,
    "lam_N": 1.0,
    "lam_E": 1.0,
    "Lambda": 0.5,
    "kappa": 1.0,
    "xi_max": 0.0,
    "lam_elig": 0.1,
    "gate_thr": 0.0,
    "q_max": 1.0,
    "eta": [0.1] * 9,
    "eta_plast": 0.01,
    "lam_w": 0.0,
    "theta_align": 0.0,
    "eta_E": 0.01,
    "w_max": 1.0,
    "w_min": 0.1,
    "theta_forget": 0.9,
    "theta_I": 0.1,
    "T_archive": 100,
    "tau1": 1,
    "M_max": 5,
    "mu_star": 0.1,
    "beta_h": 0.05,
    "eta_theta": 0.01,
    "eta_g": 0.05,
    "g_min": 0.5,
    "g_max": 5.0,
    "Dmax": 0,
}


def _pipeline(cfg):
    torch.manual_seed(0)
    graph = GraphCOO(
        np.array([[0], [1]]),
        np.zeros(1),
        np.zeros(1),
        np.zeros(1, dtype=int),
        np.zeros(1),
    )
    state = OmegaState(
        cfg,
        np.eye(2),
        np.zeros((2, 2)),
        graph,
        np.array([[0.1, 0.0, 1.0], [0.1, 0.0, 1.0]]),
        store=[],
        tick=0,
    )
    return Pipeline(
        state, Clocks(2, 4, 8), cfg, PredHead(2, 2, 3), RingBufferH(5), make_rng(0)
    )


def test_pipeline_fails_on_missing_key():
    for key in ("eta_plast", "Lambda", "mu_star", "theta_gws"):
        params = dict(FULL)
        params.pop(key)
        with pytest.raises(KeyError, match=key):
            _pipeline(types.SimpleNamespace(**params))


def test_pipeline_accepts_full_cfg():
    _pipeline(types.SimpleNamespace(**FULL))
