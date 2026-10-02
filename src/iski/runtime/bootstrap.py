import numpy as np
import torch

from iski.core.state import OmegaState
from iski.dynamics.homeostasis import init_S
from iski.dynamics.noise import make_rng
from iski.graph.topology import GraphCOO
from iski.prediction.buffer import RingBufferH
from iski.prediction.heads import PredHead
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks


def bootstrap(cfg) -> Pipeline:
    """Bootstrap M0: E нормированные randn; два независимых набора рёбер.

    Возбуждающие: w_plus ~ U(0, w_init_max) с вероятностью p0 на пару i!=j;
    тормозящие: w_minus ~ U(0, w_minus_init_max) (знак q=-1) с вероятностью
    p_I = rho_I*p0 (разреженнее). Наборы независимы; ребро существует, если
    выпала хотя бы одна популяция. Весь рандом seeded.
    """
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
    head = PredHead(N, K, cfg.H_head)
    hbuf = RingBufferH(cfg.tau1 + 2)
    rng_noise = make_rng(cfg.seeds["noise"])
    return Pipeline(state, clocks, cfg, head, hbuf, rng_noise)
