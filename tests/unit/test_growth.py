"""M1: нейрогенез — should_grow, grow_node, PaddedPredHead."""

import numpy as np

from iski.m1.bootstrap import bootstrap_m1
from iski.m1.growth import grow_node, novelty_score, should_grow
from iski.memory.item import MemoryItem


def _cfg(root):
    import types
    from pathlib import Path

    import yaml

    r = Path(root)
    cfg = {}
    for rel in (
        "config/model_m1.yaml",
        "config/runtime.yaml",
        "config/bootstrap.yaml",
        "config/experiments/m1.yaml",
    ):
        cfg.update(yaml.safe_load((r / rel).read_text(encoding="utf-8")))
    return types.SimpleNamespace(**cfg)


ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
CFG = _cfg(ROOT)


def _full_store(n=5, D=64):
    rng = np.random.default_rng(0)
    return [
        MemoryItem(e=rng.standard_normal(D), x=np.zeros(8), rho=np.ones(9) * 0.3)
        for _ in range(n)
    ]


def test_bootstrap_m1_starts_small():
    pipe = bootstrap_m1(CFG)
    assert pipe.state.X.shape == (4, 8)
    assert pipe.head.n_max == 32


def test_novelty_and_should_grow():
    pipe = bootstrap_m1(CFG)
    st = pipe.state
    e = np.random.default_rng(1).standard_normal(CFG.D)
    # пустой store — рост запрещён (память не полна)
    assert not should_grow(st, CFG, e)
    # полный store + новый вход -> разрешён
    st.store = _full_store()
    assert should_grow(st, CFG, e)
    # похожий вход (низкая новизна) — не растим
    st2 = pipe.state
    st2.store = [MemoryItem(e=e.copy(), x=np.zeros(8), rho=np.ones(9) * 0.3)] * 5
    assert novelty_score(e, st2.store, CFG.sigma) <= CFG.theta_form


def test_grow_node_appends_everything():
    pipe = bootstrap_m1(CFG)
    st = pipe.state
    st.store = _full_store()
    e = np.random.default_rng(2).standard_normal(CFG.D)
    edges0 = len(st.graph.w_plus)
    out = grow_node(st, CFG, e, t=100, last_grow=-(10**9), cooldown=50)
    assert out == 100
    assert st.X.shape == (5, 8)
    assert st.E.shape == (5, 64)
    assert st.S.shape == (5, 3)
    assert st.X_hist.shape == (st.L, 5, 8)
    assert len(st.graph.w_plus) > edges0
    # ring buffer читается корректно
    d0 = st.delayed(0)
    assert d0.shape == (5, 8)
    # cooldown блокирует повторный рост
    assert grow_node(st, CFG, e, t=120, last_grow=100, cooldown=50) == 100


def test_pipeline_tick_after_growth():
    pipe = bootstrap_m1(CFG)
    st = pipe.state
    st.store = _full_store()
    e = np.random.default_rng(3).standard_normal(CFG.D)
    grow_node(st, CFG, e, t=50, last_grow=-(10**9), cooldown=1, pipe=pipe)
    pipe.head.sync(st)
    out = pipe.tick(None, 0.0)
    assert out["metrics"]["activity"] is not None
    assert st.X.shape[0] == 5


def test_n_max_cap():
    pipe = bootstrap_m1(CFG)
    st = pipe.state
    st.store = _full_store()
    e = np.random.default_rng(4).standard_normal(CFG.D)
    while st.X.shape[0] < CFG.N_max:
        st.X = np.vstack([st.X, np.zeros((1, CFG.K))])
        st.E = np.vstack([st.E, np.zeros((1, CFG.D))])
        st.S = np.vstack([st.S, np.zeros((1, 3))])
    assert not should_grow(st, CFG, e)
