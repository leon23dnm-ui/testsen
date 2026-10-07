import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments" / "m1"))
import run_m1


def test_run_m1_creates_report(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    report = root / "experiments" / "m1" / "REPORT_M1.md"
    backup = report.read_bytes() if report.exists() else None

    orig = run_m1.make_cfg

    def _tiny(r):
        cfg = orig(r)
        cfg.warm_ticks = 3
        cfg.auto_ticks = 3
        cfg.T_maint = 1
        cfg.sweep = {"eta_plast": [0.01], "Lambda": [0.3], "eta_g": [0.0]}
        return cfg

    monkeypatch.setattr(run_m1, "make_cfg", _tiny)
    monkeypatch.setattr(sys, "argv", ["run_m1.py"])
    try:
        run_m1.main()
    except SystemExit:
        pass

    assert report.exists()
    assert "Вердикт" in report.read_text(encoding="utf-8")

    if backup is not None:
        report.write_bytes(backup)
    else:
        report.unlink()


def test_m1_cfg_scaled_dims():
    root = Path(__file__).resolve().parents[2]
    cfg = run_m1.make_cfg(root)
    assert (cfg.N, cfg.K, cfg.D) == (16, 8, 64)
    assert cfg.M_max == 5
    assert cfg.theta_ed_warm == 0.15
    assert cfg.H_max == 2.5 and cfg.rho_max == 1.5 and cfg.mu_star == 0.1


def test_m1_pipeline_runs_scaled():
    from iski.runtime.bootstrap import bootstrap

    root = Path(__file__).resolve().parents[2]
    cfg = run_m1.make_cfg(root)
    pipe = bootstrap(cfg)
    assert pipe.state.X.shape == (16, 8)
    out = pipe.tick(None, 0.0)
    assert "metrics" in out
