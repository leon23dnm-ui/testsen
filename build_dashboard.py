"""Генератор дашборда качества ISKI M0 (расширенный: 5 вкладок).

Собирает данные из pytest (junit.xml), coverage.py (coverage.json), ruff,
REPORT.md, config/*.yaml, iski-tasks-v3.0/CHECKLIST.md и логов эксперимента
(experiments/m0/logs/*.csv -> dashboard/logs.json), пишет dashboard/index.html.

Запуск: python build_dashboard.py
"""

from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DASH = ROOT / "dashboard"
LOGS = ROOT / "experiments" / "m0" / "logs"

CRITERIA = [
    ("warm_ok", "s_ed > theta_ed_warm в конце warm"),
    ("activity_band", "activity in (A_min, A_max) в авто-фазе"),
    ("entropy_band", "H(X) < H_max в авто-фазе"),
    ("rho_stable", "rho(J) < rho_max"),
    ("no_recovery", "0 нарушений инвариантов"),
    ("nontrivial", "std(activity) > 0.001 в авто-фазе"),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)


# ---------- сбор данных ----------


def collect_tests() -> dict:
    DASH.mkdir(exist_ok=True)
    proc = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "--cov=src/iski",
            "--cov-report=json:dashboard/coverage.json",
            f"--junitxml={DASH / 'junit.xml'}",
            "-q",
        ]
    )
    data = {"exit_code": proc.returncode}
    root = ET.parse(DASH / "junit.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    data.update(
        total=int(suite.get("tests", 0)),
        failures=int(suite.get("failures", 0)),
        errors=int(suite.get("errors", 0)),
        skipped=int(suite.get("skipped", 0)),
        duration=float(suite.get("time", 0.0)),
    )
    cases, failures = [], []
    per_file: dict[str, dict] = {}
    for tc in suite.iter("testcase"):
        cls = tc.get("classname", "")
        fname = cls.split(".")[-1] if cls else "?"
        fail_el = tc.find("failure") or tc.find("error")
        status = (
            "failed"
            if fail_el is not None
            else ("skipped" if tc.find("skipped") is not None else "passed")
        )
        name = tc.get("name", "")
        t = float(tc.get("time", 0.0))
        cases.append({"file": fname, "name": name, "status": status, "time": t})
        if fail_el is not None:
            failures.append(
                {
                    "test": f"{cls}::{name}",
                    "trace": fail_el.text or fail_el.get("message", ""),
                }
            )
        agg = per_file.setdefault(
            fname, {"file": fname, "passed": 0, "failed": 0, "skipped": 0, "time": 0.0}
        )
        agg[status] += 1
        agg["time"] += t
    data["cases"] = cases
    data["failures_detail"] = failures
    data["files"] = sorted(per_file.values(), key=lambda x: x["file"])
    return data


def collect_coverage() -> dict:
    cov = json.loads((DASH / "coverage.json").read_text(encoding="utf-8"))
    modules = []
    for fname, d in cov.get("files", {}).items():
        s = d["summary"]
        modules.append(
            {
                "file": fname.replace("src\\iski\\", "").replace("src/iski/", ""),
                "stmts": s["num_statements"],
                "missed": s["missing_lines"],
                "pct": s["percent_covered"],
                "missing": d.get("missing_lines", []),
            }
        )
    modules.sort(key=lambda m: m["pct"])
    t = cov["totals"]
    return {
        "total_pct": t["percent_covered"],
        "stmts": t["num_statements"],
        "missed": t["missing_lines"],
        "modules": modules,
    }


def collect_ruff() -> dict:
    check = run(["ruff", "check", "src", "tests"])
    fmt = run(["ruff", "format", "--check", "src", "tests"])
    return {
        "lint_ok": check.returncode == 0,
        "lint_output": (check.stdout or check.stderr).strip(),
        "format_ok": fmt.returncode == 0,
    }


def collect_report() -> dict:
    """REPORT.md: таблица критериев (combos x marks), вердикт, таблицы диагностики."""
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    verdict = "НАЙДЕН" if "**НАЙДЕН**" in text else "НЕ НАЙДЕН"
    combos = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| combo"):
            in_table = True
            continue
        if in_table:
            if line.startswith("|--"):
                continue
            if not line.startswith("| eta"):
                break
            cells = [c.strip() for c in line.strip("|").split("|")]
            marks = [("x" in c.lower()) for c in cells[1:7]]
            combos.append(
                {"name": cells[0], "marks": marks, "pass": "x" in cells[7].lower()}
            )
    # диагностика (среднее по тикам) -> таблица
    diag_rows, homeo_rows, in_sec = [], [], ""
    for line in text.splitlines():
        if line.startswith("## "):
            in_sec = line[3:].strip()
            continue
        if line.startswith("| eta"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if "Диагностика" in in_sec:
                diag_rows.append(cells)
            elif "Петля гомеостаза" in in_sec:
                homeo_rows.append(cells)
    return {
        "verdict": verdict,
        "combos": combos,
        "diag": diag_rows,
        "homeo": homeo_rows,
    }


def collect_cfg() -> dict:
    boot = yaml.safe_load(
        (ROOT / "config" / "bootstrap.yaml").read_text(encoding="utf-8")
    )
    model = yaml.safe_load((ROOT / "config" / "model.yaml").read_text(encoding="utf-8"))
    return {
        "theta_ed_warm": boot.get("theta_ed_warm"),
        "A_min": boot.get("A_min"),
        "A_max": boot.get("A_max"),
        "H_max": boot.get("H_max"),
        "rho_max": boot.get("rho_max"),
        "theta_plaus": boot.get("theta_plaus"),
        "warm_ticks": boot.get("warm_ticks"),
        "auto_ticks": boot.get("auto_ticks"),
        "model": model,
    }


def collect_logs() -> list[dict]:
    """Все CSV-логи -> даунсэмплинг ~200 точек, серии activity/H/rho_j."""
    out = []
    for f in sorted(LOGS.glob("*.csv")):
        with open(f, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        step = max(1, len(rows) // 200)
        thin = rows[::step]
        out.append(
            {
                "name": f.stem,
                "t": [int(float(r["t"])) for r in thin],
                "activity": [float(r["activity"]) for r in thin],
                "H": [float(r["H"]) for r in thin],
                "rho_j": [float(r["rho_j"]) for r in thin],
            }
        )
    return out


def collect_checklist() -> list[dict]:
    path = ROOT / "iski-tasks-v3.0" / "CHECKLIST.md"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not (line.startswith("|") and re.match(r"\|\s*\d+\s*\|", line)):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3:
            rows.append(
                {
                    "task": cells[0],
                    "name": cells[1] if len(cells) > 1 else "",
                    "status": cells[2] if len(cells) > 2 else "",
                    "note": cells[-1],
                }
            )
    return rows


# ---------- рендер ----------


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def build_html(tests, cov, ruff, report, cfg, logs_json, checklist) -> str:
    passed = tests["total"] - tests["failures"] - tests["errors"] - tests["skipped"]
    all_green = (
        tests["failures"] == 0
        and tests["errors"] == 0
        and ruff["lint_ok"]
        and ruff["format_ok"]
    )
    verdict = report["verdict"]
    n_tasks = len(checklist)
    done_tasks = sum(1 for r in checklist if "x" in r["status"].lower())

    failures_html = (
        "".join(
            f"<div class='failbox'><b>{esc(f['test'])}</b><pre>{esc(f['trace'][:3000])}</pre></div>"
            for f in tests["failures_detail"]
        )
        or "<p class='muted'>Падений нет — все тесты зелёные.</p>"
    )

    files_rows = "".join(
        f"<tr><td><code>{esc(f['file'])}</code></td><td>{f['passed']}</td>"
        f"<td class='{'bad' if f['failed'] else ''}'>{f['failed']}</td>"
        f"<td>{f['skipped']}</td><td>{f['time']:.2f}</td>"
        f"<td><span class='badge {'pass' if f['failed'] == 0 else 'fail'}'>{'OK' if f['failed'] == 0 else 'FAIL'}</span></td></tr>"
        for f in tests["files"]
    )
    cases_rows = "".join(
        f"<tr><td><code>{esc(c['file'])}</code></td><td>{esc(c['name'])}</td>"
        f"<td><span class='badge {'pass' if c['status'] == 'passed' else ('fail' if c['status'] == 'failed' else 'skip')}'>{c['status']}</span></td>"
        f"<td>{c['time']:.3f}</td></tr>"
        for c in tests["cases"]
    )

    cov_rows = "".join(
        f"<tr><td><code>{esc(m['file'])}</code></td><td>{m['stmts']}</td><td>{m['missed']}</td>"
        f"<td><span class='bar'><div style='width:{m['pct']:.0f}%'></div></span> {m['pct']:.1f}%</td>"
        f"<td><details><summary class='muted'>строки</summary><span class='muted'>{esc(', '.join(map(str, m['missing']))) or '—'}</span></details></td></tr>"
        for m in cov["modules"]
    )

    thr = [
        ("theta_ed_warm", cfg["theta_ed_warm"]),
        ("A_min", cfg["A_min"]),
        ("A_max", cfg["A_max"]),
        ("H_max", cfg["H_max"]),
        ("rho_max", cfg["rho_max"]),
        ("theta_plaus", cfg["theta_plaus"]),
        ("warm_ticks", cfg["warm_ticks"]),
        ("auto_ticks", cfg["auto_ticks"]),
        ("Lambda", cfg["model"].get("Lambda")),
        ("xi_max", cfg["model"].get("xi_max")),
        ("mu_star", cfg["model"].get("mu_star")),
        ("theta_form", cfg["model"].get("theta_form")),
        ("w_mem_init", cfg["model"].get("w_mem_init")),
    ]
    thr_rows = "".join(
        f"<tr><td><code>{k}</code></td><td>{v}</td></tr>" for k, v in thr
    )

    crit_header = "".join(f"<th title='{esc(d)}'>{esc(n)}</th>" for n, d in CRITERIA)
    crit_defs = "".join(
        f"<tr><td><code>{esc(n)}</code></td><td>{esc(d)}</td></tr>" for n, d in CRITERIA
    )
    matrix_rows = "".join(
        f"<tr><td>{esc(c['name'])}</td>"
        + "".join(
            f"<td class='{'ok' if m else 'bad'}' title='{esc(CRITERIA[i][1])}'>{'✓' if m else '✗'}</td>"
            for i, m in enumerate(c["marks"])
        )
        + f"<td><span class='badge {'pass' if c['pass'] else 'fail'}'>{'PASS' if c['pass'] else 'FAIL'}</span></td></tr>"
        for c in report["combos"]
    )

    task_rows = "".join(
        f"<tr><td>T{t['task']}</td><td>{esc(t['name'])}</td><td>{esc(t['status'])}</td><td class='muted'>{esc(t['note'])}</td></tr>"
        for t in checklist
    )

    combo_opts = "".join(f"<option>{esc(l['name'])}</option>" for l in logs_json)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>ISKI M0 — Dashboard</title>
<style>
 body {{ font-family:-apple-system,Segoe UI,Roboto,sans-serif; margin:0; background:#0f1117; color:#e6e6e6; }}
 header {{ padding:1.2rem 2rem; background:#161b28; border-bottom:1px solid #262c3d; }}
 h1 {{ font-size:1.4rem; margin:0 0 .3rem; }}
 .muted {{ color:#8b93a7; font-size:.85rem; }}
 .cards {{ display:flex; gap:1rem; flex-wrap:wrap; padding:1rem 2rem; }}
 .card {{ background:#1a1f2e; border-radius:10px; padding:.9rem 1.3rem; min-width:140px; }}
 .card .v {{ font-size:1.7rem; font-weight:700; }} .card .l {{ color:#8b93a7; font-size:.78rem; }}
 .ok {{ color:#4ade80; }} .bad {{ color:#f87171; }}
 .tabs {{ display:flex; gap:.4rem; padding:0 2rem; border-bottom:1px solid #262c3d; }}
 .tab {{ padding:.6rem 1.2rem; cursor:pointer; border:none; background:none; color:#8b93a7; font-size:.9rem; border-bottom:2px solid transparent; }}
 .tab.active {{ color:#e6e6e6; border-bottom:2px solid #38bdf8; }}
 .pane {{ display:none; padding:1.2rem 2rem; }} .pane.active {{ display:block; }}
 table {{ border-collapse:collapse; width:100%; margin-top:.8rem; background:#1a1f2e; border-radius:10px; overflow:hidden; }}
 th, td {{ padding:.45rem .8rem; text-align:left; font-size:.86rem; border-bottom:1px solid #262c3d; }}
 th {{ background:#232a3b; color:#8b93a7; text-transform:uppercase; font-size:.72rem; }}
 .bar {{ background:#262c3d; border-radius:4px; height:10px; width:200px; display:inline-block; vertical-align:middle; }}
 .bar>div {{ background:linear-gradient(90deg,#38bdf8,#4ade80); height:10px; border-radius:4px; }}
 .badge {{ padding:.12rem .5rem; border-radius:6px; font-size:.72rem; font-weight:600; }}
 .badge.pass {{ background:#14351f; color:#4ade80; }} .badge.fail {{ background:#3b1a1a; color:#f87171; }} .badge.skip {{ background:#2a2f1a; color:#eab308; }}
 .failbox {{ background:#3b1a1a; border-radius:8px; padding:.8rem 1rem; margin:.6rem 0; }}
 .failbox pre {{ white-space:pre-wrap; font-size:.78rem; color:#fca5a5; }}
 select {{ background:#1a1f2e; color:#e6e6e6; border:1px solid #262c3d; border-radius:6px; padding:.4rem .7rem; }}
 canvas {{ background:#1a1f2e; border-radius:10px; max-width:100%; }}
 .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:1.4rem; }}
 footer {{ padding:1.2rem 2rem; }}
</style>
</head>
<body>
<header>
 <h1>ISKI M0 v3.0 — Quality Dashboard</h1>
 <div class="muted">Сгенерирован: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} · <code>python build_dashboard.py</code></div>
</header>
<div class="cards">
 <div class="card"><div class="v {"ok" if all_green else "bad"}">{tests["total"]}</div><div class="l">Тестов: passed {passed} / failed {tests["failures"] + tests["errors"]} / skipped {tests["skipped"]}</div></div>
 <div class="card"><div class="v">{tests["duration"]:.1f}s</div><div class="l">Время прогона pytest</div></div>
 <div class="card"><div class="v {"ok" if cov["total_pct"] >= 80 else "bad"}">{cov["total_pct"]:.1f}%</div><div class="l">Покрытие ({cov["missed"]} строк не покрыто)</div></div>
 <div class="card"><div class="v"><span class="{"ok" if ruff["lint_ok"] else "bad"}">lint {"OK" if ruff["lint_ok"] else "FAIL"}</span></div><div class="l">Ruff format: {"OK" if ruff["format_ok"] else "ERRORS"}</div></div>
 <div class="card"><div class="v {"ok" if verdict == "НАЙДЕН" else "bad"}">{"✓" if verdict == "НАЙДЕН" else "✗"}</div><div class="l">Вердикт V1: {verdict}</div></div>
 <div class="card"><div class="v">{done_tasks}/{n_tasks}</div><div class="l">Задач по CHECKLIST выполнено</div></div>
</div>
<div class="tabs">
 <button class="tab active" onclick="show(0)">Тесты и ошибки</button>
 <button class="tab" onclick="show(1)">Покрытие</button>
 <button class="tab" onclick="show(2)">Критерии V1</button>
 <button class="tab" onclick="show(3)">Эксперимент M0</button>
 <button class="tab" onclick="show(4)">Задачи</button>
</div>

<div class="pane active">
 <h2>Падения тестов</h2>{failures_html}
 <h2>По файлам</h2>
 <table><tr><th>Файл</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Время, с</th><th>Статус</th></tr>{files_rows}</table>
 <h2>Все тест-кейсы ({tests["total"]})</h2>
 <table><tr><th>Файл</th><th>Тест</th><th>Статус</th><th>Время, с</th></tr>{cases_rows}</table>
</div>

<div class="pane">
 <h2>Покрытие по модулям (от худшего)</h2>
 <table><tr><th>Модуль</th><th>Строк</th><th>Не покрыто</th><th>Покрытие</th><th>Непокрытые строки</th></tr>{cov_rows}</table>
</div>

<div class="pane">
 <div class="grid">
  <div><h2>Определения критериев</h2><table><tr><th>Критерий</th><th>Условие</th></tr>{crit_defs}</table></div>
  <div><h2>Канонические пороги (config)</h2><table><tr><th>Параметр</th><th>Значение</th></tr>{thr_rows}</table></div>
 </div>
 <h2>Матрица sweep ({len(report["combos"])} комбо x {len(CRITERIA)} критериев) — вердикт: {verdict}</h2>
 <table><tr><th>combo</th>{crit_header}<th>pass</th></tr>{matrix_rows}</table>
</div>

<div class="pane">
 <h2>Динамика по тикам</h2>
 <select id="combo" onchange="draw()">{combo_opts}</select>
 <div style="margin:.8rem 0"><canvas id="chart" width="960" height="320"></canvas></div>
 <div class="muted" id="legend"></div>
</div>

<div class="pane">
 <h2>Чек-лист задач (iski-tasks-v3.0/CHECKLIST.md)</h2>
 <table><tr><th>T</th><th>Задача</th><th>Статус</th><th>Заметки/issues</th></tr>{task_rows}</table>
</div>

<footer class="muted">{"Все проверки зелёные: тесты пройдены, линтер чистый." if all_green else "Есть падения — см. вкладку «Тесты и ошибки»."} Вердикт V1: {verdict}.</footer>

<script>
const LOGS = {json.dumps(logs_json)};
function show(i) {{
 document.querySelectorAll('.tab').forEach((t,j)=>t.classList.toggle('active', j===i));
 document.querySelectorAll('.pane').forEach((p,j)=>p.classList.toggle('active', j===i));
}}
function draw() {{
 const name = document.getElementById('combo').value;
 const d = LOGS.find(l=>l.name===name); if(!d) return;
 const cv = document.getElementById('chart'), ctx = cv.getContext('2d');
 ctx.clearRect(0,0,cv.width,cv.height);
 const series = [{{k:'activity',c:'#4ade80'}},{{k:'H',c:'#38bdf8'}},{{k:'rho_j',c:'#f87171'}}];
 const all = series.flatMap(s=>d[s.k]);
 const mn = Math.min(...all), mx = Math.max(...all);
 const pad = 20, W = cv.width-2*pad, Hh = cv.height-2*pad;
 ctx.strokeStyle = '#262c3d';
 for(let i=0;i<=4;i++){{const y=pad+Hh*i/4;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(pad+W,y);ctx.stroke();}}
 series.forEach(s=>{{
  ctx.strokeStyle = s.c; ctx.beginPath();
  d[s.k].forEach((v,i)=>{{
   const x = pad + W*i/Math.max(1,d[s.k].length-1);
   const y = pad + Hh*(1-(v-mn)/((mx-mn)||1));
   i?ctx.lineTo(x,y):ctx.moveTo(x,y);
  }});
  ctx.stroke();
 }});
 document.getElementById('legend').innerHTML =
  series.map(s=>`<span style='color:${{s.c}}'>— ${{s.k}}</span>`).join(' &nbsp; ') +
  ` &nbsp; <span class='muted'>min=${{mn.toFixed(3)}} max=${{mx.toFixed(3)}} n=${{d.t.length}} точек</span>`;
}}
draw();
</script>
</body>
</html>
"""


def main() -> int:
    print("[1/5] pytest + coverage...")
    tests = collect_tests()
    print("[2/5] coverage...")
    cov = collect_coverage()
    print("[3/5] ruff...")
    ruff = collect_ruff()
    print("[4/5] REPORT/cfg/logs/checklist...")
    report = collect_report()
    cfg = collect_cfg()
    logs_json = collect_logs()
    (DASH / "logs.json").write_text(json.dumps(logs_json), encoding="utf-8")
    checklist = collect_checklist()

    passed = tests["total"] - tests["failures"] - tests["errors"] - tests["skipped"]
    all_green = tests["failures"] == 0 and tests["errors"] == 0 and ruff["lint_ok"]
    out = DASH / "index.html"
    out.write_text(
        build_html(tests, cov, ruff, report, cfg, logs_json, checklist),
        encoding="utf-8",
    )
    print(f"Дашборд записан: {out} ({len(logs_json)} csv-серий)")
    print(
        f"Итог: {passed}/{tests['total']} passed, coverage {cov['total_pct']:.1f}%, ruff {'clean' if ruff['lint_ok'] else 'FAIL'}"
    )
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
