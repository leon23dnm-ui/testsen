import numpy as np
import torch

from iski.core.state import OmegaState
from iski.dynamics.noise import make_rng
from iski.graph.topology import GraphCOO
from iski.memory.formation import create_memory, formation_decision
from iski.memory.item import MemoryItem
from iski.prediction.buffer import RingBufferH
from iski.prediction.heads import PredHead
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks


class _Cfg:
    Dmax = 0
    sigma = 0.5
    theta_form = 0.5
    w_mem_init = 0.3
    M_max = 3
    theta_gws = 0.0
    beta_g = 0.0
    T_A = 1.0
    lam_N = 1.0
    lam_E = 1.0
    Lambda = 0.5
    kappa = 1.0
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
    w_max = 1.0
    w_min = 0.1
    theta_forget = 0.9
    theta_I = 0.1
    T_archive = 100
    x_min = -10.0
    x_max = 10.0
    W_max = 2.0
    E_max = 10.0
    mu_star = 0.1
    beta_h = 0.05
    eta_theta = 0.01
    eta_g = 0.05
    g_min = 0.5
    g_max = 5.0


def _item(e, x=None, w=0.3):
    return MemoryItem(
        e=np.asarray(e, dtype=float),
        x=np.zeros(4) if x is None else np.asarray(x, dtype=float),
        rho=np.array([0.3, 0.5, 0.1, 0.2, w, 0.0, 0.0, 0.0, 0.0]),
        status=0,
        t_create=0,
        last_access=0,
    )


def test_formation_forms_on_empty_memory():
    e_in = np.ones(8)
    decision, k = formation_decision(e_in, [], theta_form=0.5, sigma=0.5, m_max=3)
    assert decision == "form"
    assert k == -1


def test_formation_forms_on_novelty():
    M = [_item(np.array([1.0, 0.0, 0.0, 0.0]))]
    e_in = np.array([0.0, 0.0, 0.0, 1.0])  # ортогональный вход -> sim ~ 0
    decision, _ = formation_decision(e_in, M, theta_form=0.5, sigma=0.5, m_max=3)
    assert decision == "form"


def test_formation_reinforces_on_repeat():
    e = np.array([0.5, 0.5, 0.5, 0.5])
    M = [_item(e)]
    decision, k = formation_decision(e, M, theta_form=0.5, sigma=0.5, m_max=3)
    assert decision == "reinforce"
    assert k == 0


def test_formation_cap_at_m_max():
    M = [_item(np.eye(4)[i]) for i in range(3)]
    e_in = np.array([0.0, 0.0, 0.0, 1.0])
    decision, _ = formation_decision(e_in, M, theta_form=0.5, sigma=0.5, m_max=3)
    assert decision == "reinforce"  # cap: новизна есть, но |M| == m_max


def test_create_memory_canonical_fields():
    cfg = _Cfg()
    e_in = np.linspace(0.0, 1.0, 8)
    X_t = np.arange(16, dtype=float).reshape(4, 4)
    item = create_memory(e_in, X_t, cfg, t=7)
    assert (item.e == e_in).all()
    assert (item.x == X_t.mean(axis=0)).all()
    assert item.w == cfg.w_mem_init
    assert item.status == 0
    assert item.t_create == 7
    assert item.last_access == 7
    X_t[0, 0] = 999.0
    assert item.x[0] != 999.0  # копия, не ссылка


def _pipeline_with_memory():
    cfg = _Cfg()
    torch.manual_seed(0)
    N, K, D = 4, 4, 8
    graph = GraphCOO(
        np.array([[0], [1]]),
        np.array([0.2]),
        np.zeros(1),
        np.zeros(1, dtype=int),
        np.zeros(1),
    )
    E = np.eye(D, N)[:, :N].T  # [N=4, D=8]
    S = np.tile([0.1, 0.0, 1.0], (N, 1))
    state = OmegaState(cfg, E, np.zeros((N, K)), graph, S, store=[], tick=0)
    pipeline = Pipeline(
        state, Clocks(1, 1, 1), cfg, PredHead(N, K, 3), RingBufferH(5), make_rng(0)
    )
    return pipeline


def test_fmem_nonzero_after_formation():
    pipeline = _pipeline_with_memory()
    e_in = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    out = pipeline.tick(e_in, 1.0)
    assert len(pipeline.state.store) == 1  # novelty -> form
    out = pipeline.tick(None, 0.0)  # авто-фаза: F_mem из store
    assert out["metrics"]["mem_fro"] > 0.0


def test_formation_none_without_input():
    pipeline = _pipeline_with_memory()
    pipeline.tick(None, 0.0)
    assert len(pipeline.state.store) == 0
