"""Bootstrap M1: как канонический, но с PaddedPredHead(N_max) —
голова допускает рост N вплоть до N_max без переинициализации."""

import numpy as np
import torch

from iski.core.state import OmegaState
from iski.dynamics.homeostasis import init_S
from iski.dynamics.noise import make_rng
from iski.graph.topology import GraphCOO
from iski.m1.heads import PaddedPredHead
from iski.prediction.buffer import RingBufferH
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks


def bootstrap_m1(cfg) -> Pipeline:
    """Та же инициализация, что bootstrap(); head на N_max слотов."""
    torch.manual_seed(cfg.seeds["boot"])
    rng = np.random.default_rng(cfg.seeds["boot"])
    N, D, K = cfg.N, cfg.D, cfg.K

    E = rng.standard_normal((N, D))
    norms = np.linalg.norm(E, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    E = E / norms

    src, dst, w_plus, w_minus = [], [], [], []
    p_i = cfg.rho_I * cfg.p0
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            exc = rng.random() < cfg.p0
            inh = rng.random() < p_i
            if not (exc or inh):
                continue
            src.append(i)
            dst.append(j)
            w_plus.append(rng.uniform(0.0, cfg.w_init_max) if exc else 0.0)
            w_minus.append(rng.uniform(0.0, cfg.w_minus_init_max) if inh else 0.0)

    M = len(src)
    edge_index = np.array([src, dst], dtype=int) if M else np.empty((2, 0), dtype=int)
    w_plus = np.array(w_plus) if M else np.zeros(0)
    w_minus = np.array(w_minus) if M else np.zeros(0)
    delays = rng.integers(0, cfg.Dmax, M) if M else np.zeros(0, dtype=int)
    q_elig = np.zeros(M)
    graph = GraphCOO(edge_index, w_plus, w_minus, delays, q_elig)

    X = np.zeros((N, K))
    S = init_S(N, cfg.mu_star)
    state = OmegaState(cfg, E, X, graph, S, store=[], tick=0)
    clocks = Clocks(cfg.clocks["m"], cfg.clocks["s"], cfg.clocks["q"])
    head = PaddedPredHead(cfg.N_max, K, cfg.H_head)
    head.sync(state)
    hbuf = RingBufferH(cfg.tau1 + 2)
    rng_noise = make_rng(cfg.seeds["noise"])
    return Pipeline(state, clocks, cfg, head, hbuf, rng_noise)
