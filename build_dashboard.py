"""Генератор дашборда качества ISKI M0.

Собирает данные из pytest (junit.xml), coverage.py (coverage.json) и ruff,
пересчитывает тесты и пишет единый HTML-дашборд в dashboard/index.html.

Запуск: python build_dashboard.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASH = ROOT / "dashboard"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)


def collect_tests() -> dict:
    """Перезапуск pytest с junit-отчётом; возврат сводки и пофайловой статистики."""
    DASH.mkdir(exist_ok=True)
    proc = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=src/iski",
            "--cov-report=json:dashboard/coverage.json",
            f"--junitxml={DASH / 'junit.xml'}",
            "-q",
        ]
    )
    data = {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.strip().splitlines()[-1:],
    }
    root = ET.parse(DASH / "junit.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    data.update(
        total=int(suite.get("tests", 0)),
        failures=int(suite.get("failures", 0)),
        errors=int(suite.get("errors", 0)),
        skipped=int(suite.get("skipped", 0)),
        duration=float(suite.get("time", 0.0)),
    )
    files = []
    for tc in suite.iter("testcase"):
        cls = tc.get("classname", "")
        fname = cls.split(".")[0] if cls else "?"
        status = (
            "failed"
            if tc.find("failure") is not None or tc.find("error") is not None
            else "skipped"
            if tc.find("skipped") is not None
            else "passed"
        )
        files.append(
            {
                "file": fname,
                "name": tc.get("name", ""),
                "status": status,
                "time": float(tc.get("time", 0.0)),
            }
        )
    per_file: dict[str, dict] = {}
    for t in files:
        s = per_file.setdefault(
            t["file"],
            {"file": t["file"], "passed": 0, "failed": 0, "skipped": 0, "time": 0.0},
        )
        s[t["status"]] += 1
        s["time"] += t["time"]
    data["files"] = sorted(per_file.values(), key=lambda x: x["file"])
    return data


def collect_coverage() -> dict:
    cov = json.loads((DASH / "coverage.json").read_text())
    summary = cov["totals"]
    modules = []
    for fname, d in cov.get("files", {}).items():
        s = d["summary"]
        modules.append(
            {
                "file": fname.replace("src/iski/", ""),
                "stmts": s["num_statements"],
                "missed": s["missing_lines"],
                "pct": s["percent_covered"],
            }
        )
    modules.sort(key=lambda m: m["pct"])
    return {
        "total_pct": summary["percent_covered"],
        "stmts": summary["num_statements"],
        "missed": summary["missing_lines"],
        "modules": modules,
    }


def collect_ruff() -> dict:
    check = run(["ruff", "check", "src", "tests"])
    fmt = run(["ruff", "format", "--check", "src", "tests"])
    return {
        "lint_ok": check.returncode == 0,
        "lint_output": check.stdout.strip() or check.stderr.strip(),
        "format_ok": fmt.returncode == 0,
        "format_output": fmt.stdout.strip() or fmt.stderr.strip(),
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>ISKI M0 — Dashboard</title>
<style>
 body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; background:#0f1117; color:#e6e6e6; }}
 h1 {{ font-size:1.5rem; }} .muted {{ color:#8b93a7; font-size:.85rem; }}
 .cards {{ display:flex; gap:1rem; flex-wrap:wrap; margin:1.2rem 0; }}
 .card {{ background:#1a1f2e; border-radius:10px; padding:1rem 1.4rem; min-width:150px; }}
 .card .v {{ font-size:1.8rem; font-weight:700; }} .card .l {{ color:#8b93a7; font-size:.8rem; }}
 .ok {{ color:#4ade80; }} .bad {{ color:#f87171; }}
 table {{ border-collapse:collapse; width:100%; margin-top:1rem; background:#1a1f2e; border-radius:10px; overflow:hidden; }}
 th, td {{ padding:.5rem .9rem; text-align:left; font-size:.88rem; border-bottom:1px solid #262c3d; }}
 th {{ background:#232a3b; color:#8b93a7; text-transform:uppercase; font-size:.75rem; }}
 .bar {{ background:#262c3d; border-radius:4px; height:10px; width:220px; display:inline-block; vertical-align:middle; }}
 .bar > div {{ background:linear-gradient(90deg,#38bdf8,#4ade80); height:10px; border-radius:4px; }}
 .badge {{ padding:.15rem .5rem; border-radius:6px; font-size:.75rem; font-weight:600; }}
 .badge.pass {{ background:#14351f; color:#4ade80; }} .badge.fail {{ background:#3b1a1a; color:#f87171; }}
 footer {{ margin-top:2rem; }}
</style>
</head>
<body>
<h1>🛰 ISKI M0 v3.0 — Quality Dashboard</h1>
<div class="muted">Сгенерирован: {generated} · Python <code>python -m build_dashboard.py</code></div>
<div class="cards">
  <div class="card"><div class="v {tests_cls}">{tests_total}</div><div class="l">Тестов: passed {tests_passed} / failed {tests_failed} / skipped {tests_skipped}</div></div>
  <div class="card"><div class="v">{tests_duration:.1f}s</div><div class="l">Время прогона</div></div>
  <div class="card"><div class="v {cov_cls}">{coverage:.1f}%</div><div class="l">Покрытие кода ({cov_missed} строк не покрыто)</div></div>
  <div class="card"><div class="v">Ruff lint: <span class="{ruff_cls}">{ruff_label}</span></div><div class="l">Формат: {fmt_label}</div></div>
</div>
<h2>Покрытие по модулям</h2>
<table>
<tr><th>Модуль</th><th>Строк</th><th>Не покрыто</th><th>Покрытие</th></tr>
{cov_rows}
</table>
<h2>Тесты по файлам</h2>
<table>
<tr><th>Файл</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Время, с</th></tr>
{test_rows}
</table>
<footer class="muted">{verdict}</footer>
</body>
</html>
"""


def main() -> int:
    print("[1/3] Запуск pytest + coverage…")
    tests = collect_tests()
    print("[2/3] Чтение coverage.json…")
    cov = collect_coverage()
    print("[3/3] Проверка ruff…")
    ruff = collect_ruff()

    passed = tests["total"] - tests["failures"] - tests["errors"] - tests["skipped"]
    all_green = tests["failures"] == 0 and tests["errors"] == 0 and ruff["lint_ok"]
    cov_rows = "\n".join(
        f"<tr><td><code>{m['file']}</code></td><td>{m['stmts']}</td><td>{m['missed']}</td>"
        f"<td><span class='bar'><div style='width:{m['pct']:.0f}%'></div></span> {m['pct']:.1f}%</td></tr>"
        for m in cov["modules"]
    )
    test_rows = "\n".join(
        f"<tr><td><code>{f['file']}</code></td><td>{f['passed']}</td>"
        f'<td class="{"bad" if f["failed"] else ""}">{f["failed"]}</td>'
        f"<td>{f['skipped']}</td><td>{f['time']:.2f}</td></tr>"
        for f in tests["files"]
    )
    html = HTML_TEMPLATE.format(
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        tests_total=tests["total"],
        tests_passed=passed,
        tests_failed=tests["failures"] + tests["errors"],
        tests_skipped=tests["skipped"],
        tests_duration=tests["duration"],
        tests_cls="ok" if all_green else "bad",
        coverage=cov["total_pct"],
        cov_missed=cov["missed"],
        cov_cls="ok" if cov["total_pct"] >= 80 else "bad",
        ruff_cls="ok" if ruff["lint_ok"] else "bad",
        ruff_label="OK" if ruff["lint_ok"] else "ERRORS",
        fmt_label="OK" if ruff["format_ok"] else "ERRORS",
        cov_rows=cov_rows,
        test_rows=test_rows,
        verdict=(
            "✅ Все проверки зелёные: тесты пройдены, линтер чистый."
            if all_green
            else "❌ Есть падения — см. таблицу тестов."
        ),
    )
    out = DASH / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Дашборд записан: {out}")
    print(
        f"Итог: {passed}/{tests['total']} passed, coverage {cov['total_pct']:.1f}%, "
        f"ruff {'clean' if ruff['lint_ok'] else 'FAIL'}"
    )
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
