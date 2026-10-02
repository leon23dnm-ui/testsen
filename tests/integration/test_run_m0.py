import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments" / "m0"))
import run_m0


def test_run_m0_creates_report(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    report = root / "REPORT.md"

    orig = run_m0.make_cfg

    def _tiny(r):
        cfg = orig(r)
        cfg.warm_ticks = 3
        cfg.auto_ticks = 3
        cfg.T_maint = 1
        cfg.sweep = {"eta_plast": [0.01], "Lambda": [0.3], "eta_g": [0.0]}
        return cfg

    monkeypatch.setattr(run_m0, "make_cfg", _tiny)
    monkeypatch.setattr(sys, "argv", ["run_m0.py"])
    try:
        run_m0.main()
    except SystemExit:
        pass

    assert report.exists()
    assert "Вердикт" in report.read_text(encoding="utf-8")
