import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "m0"))

import run_m0


def _graph():
    cfg = run_m0.make_cfg(ROOT, fast=True)
    pipeline = run_m0.bootstrap(cfg)
    return cfg, pipeline.state.graph


def test_bootstrap_creates_edges():
    _, graph = _graph()
    assert graph.edge_index.shape[1] > 0


def test_bootstrap_weights_bounded_by_w_init_max():
    cfg, graph = _graph()
    assert graph.w_plus.max() <= cfg.w_init_max
    assert (graph.w_plus >= 0.0).all()
    assert graph.w_minus.max() <= cfg.w_minus_init_max
    assert (graph.w_minus >= 0.0).all()
    assert (graph.w_minus > 0.0).any()


def test_bootstrap_inhibitory_fraction():
    cfg, graph = _graph()
    n_pairs = cfg.N * (cfg.N - 1)
    frac = float((graph.w_minus > 0).sum()) / n_pairs
    assert abs(frac - cfg.rho_I * cfg.p0) <= 0.10


def test_bootstrap_delays_in_range():
    cfg, graph = _graph()
    assert (graph.delays >= 0).all()
    assert (graph.delays < cfg.Dmax).all()


def test_bootstrap_no_self_loops():
    _, graph = _graph()
    assert (graph.edge_index[0] != graph.edge_index[1]).all()
