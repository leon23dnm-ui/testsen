import subprocess
import sys
from pathlib import Path


def test_run_m0_fast_creates_report():
    root = Path(__file__).resolve().parents[2]
    report = root / "REPORT.md"
    if report.exists():
        report.unlink()

    result = subprocess.run(
        [sys.executable, str(root / "experiments" / "m0" / "run_m0.py"), "--fast"],
        cwd=str(root),
        timeout=60,
        check=False,
    )
    assert report.exists()
    assert result.returncode in (0, 1)
    text = report.read_text(encoding="utf-8")
    assert "Вердикт" in text
