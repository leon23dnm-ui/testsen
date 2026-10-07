"""Smoke-тест движка визуализации: шаги, снапшот, инъекция, reset."""

from scripts.viz_server import Engine, make_cfg


def test_cfg_and_bootstrap():
    eng = Engine()
    assert eng.cfg.N == 4
    assert eng.pipe.state.X.shape == (4, 4)


def test_step_and_snapshot():
    eng = Engine()
    snap = eng.step(3)
    assert snap["t"] == 3
    assert snap["phase"] == "warm"
    assert len(snap["x"]) == 4 and len(snap["xk"]) == 4
    n_edges = len(snap["edges"])
    assert len(snap["w"]) == n_edges == len(snap["flux"]) == len(snap["delay"])
    assert "activity" in snap["metrics"]


def test_inject_and_reset():
    eng = Engine()
    eng.inject("two", dur=5)
    assert eng.inject_vec is not None
    snap = eng.step(2)
    assert snap["inject_left"] > 0
    eng.reset(eta_plast=0.1, Lambda=0.5, eta_g=0.0)
    assert eng.cfg.eta_plast == 0.1 and eng.cfg.Lambda == 0.5
    assert eng.pipe.state.tick == 0


def test_edge_flux_shape_matches_propagate():
    eng = Engine()
    eng.step(1)
    g = eng.pipe.state.graph
    assert eng.last_flux.shape == g.w_eff().shape


def test_make_cfg_keys():
    cfg = make_cfg()
    for k in ("N", "D", "K", "warm_ticks", "auto_ticks", "M_max", "theta_form"):
        assert hasattr(cfg, k)
