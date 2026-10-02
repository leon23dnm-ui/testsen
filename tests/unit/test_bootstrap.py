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
    assert (graph.w_minus == 0.0).all()


def test_bootstrap_delays_in_range():
    cfg, graph = _graph()
    assert (graph.delays >= 0).all()
    assert (graph.delays < cfg.Dmax).all()


def test_bootstrap_no_self_loops():
    _, graph = _graph()
    assert (graph.edge_index[0] != graph.edge_index[1]).all()
