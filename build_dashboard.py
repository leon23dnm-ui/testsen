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


def collect_failures() -> list[dict]:
    """Детали упавших/ошибочных тестов из junit.xml (сообщение + трейсировка)."""
    root = ET.parse(DASH / "junit.xml").getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    fails = []
    for tc in suite.iter("testcase"):
        node = tc.find("failure")
        kind = "failure"
        if node is None:
            node = tc.find("error")
            kind = "error"
        if node is None:
            continue
        fails.append(
            {
                "file": (tc.get("classname", "") or "?").split(".")[0],
                "name": tc.get("name", ""),
                "kind": kind,
                "message": (node.get("message") or "").strip(),
                "text": (node.text or "").strip(),
            }
        )
    return fails


def collect_uncovered() -> list[dict]:
    """Список непокрытых строк по файлам (для секции ошибок покрытия)."""
    cov = json.loads((DASH / "coverage.json").read_text())
    out = []
    for fname, d in cov.get("files", {}).items():
        miss = d.get("missing_lines") or []
        if miss:
            out.append(
                {
                    "file": fname.replace("src/iski/", ""),
                    "pct": d["summary"]["percent_covered"],
                    "lines": miss,
                }
            )
    out.sort(key=lambda x: x["pct"])
    return out


def parse_report_md() -> dict:
    """Парсинг REPORT.md: таблица критериев V1, вердикт и диагностическая таблица."""
    p = ROOT / "REPORT.md"
    result = {
        "criteria_rows": [],
        "verdict": "нет данных",
        "diag_rows": [],
        "crit_cols": [],
        "diag_cols": [],
    }
    if not p.exists():
        return result
    text = p.read_text(encoding="utf-8")

    def parse_table(block: list[str]) -> tuple[list[str], list[list[str]]]:
        header = [c.strip() for c in block[0].strip().strip("|").split("|")]
        rows = []
        for line in block[2:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == len(header):
                rows.append(cells)
        return header, rows

    tables = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.startswith("|"):
            cur.append(line)
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    if tables:
        result["crit_cols"], result["criteria_rows"] = parse_table(tables[0])
    if len(tables) > 1:
        result["diag_cols"], result["diag_rows"] = parse_table(tables[-1])
    m = __import__("re").search(r"\*\*(.+?)\*\*", text)
    if m:
        result["verdict"] = m.group(1)
    return result


def collect_checklist() -> list[dict]:
    """Парсинг CHECKLIST.iski-tasks-v3.0: статус задач T01–T27."""
    p = ROOT / "iski-tasks-v3.0" / "CHECKLIST.md"
    tasks = []
    if not p.exists():
        return tasks
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        tasks.append(
            {
                "id": f"T{cells[0]}",
                "title": cells[1],
                "tests_green": "[x]" in cells[2],
                "yaml": cells[3],
                "issues": cells[4] if len(cells) > 4 else "-",
            }
        )
    return tasks


def collect_experiment_series() -> dict:
    """CSV-логи прогонов M0 → ряды для графиков (downsample до ~200 точек)."""
    import csv as _csv
    import glob as _glob

    series = {}
    for path in sorted(_glob.glob(str(ROOT / "experiments/m0/logs/*.csv"))):
        combo = Path(path).stem
        with open(path) as fh:
            rows = list(_csv.DictReader(fh))
        if not rows:
            continue
        step = max(1, len(rows) // 200)
        pts = rows[::step]
        series[combo] = {
            "t": [int(float(r["t"])) for r in pts],
            "activity": [float(r["activity"]) for r in pts],
            "H": [float(r["H"]) for r in pts],
            "rho_j": [float(r["rho_j"]) for r in pts],
        }
    return series


def collect_config_thresholds() -> dict:
    """Канонические пороги критериев V1 из config/bootstrap.yaml."""
    try:
        import yaml

        raw = yaml.safe_load((ROOT / "config/bootstrap.yaml").read_text())
        return {k: v for k, v in raw.items() if isinstance(v, (int, float))}
    except (OSError, ValueError, ModuleNotFoundError):
        return {}


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>ISKI M0 — Dashboard</title>
<style>
 body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background:#0f1117; color:#e6e6e6; }}
 .wrap {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
 h1 {{ font-size:1.5rem; }} h2 {{ font-size:1.15rem; margin-top:2rem; }} .muted {{ color:#8b93a7; font-size:.85rem; }}
 .cards {{ display:flex; gap:1rem; flex-wrap:wrap; margin:1.2rem 0; }}
 .card {{ background:#1a1f2e; border-radius:10px; padding:1rem 1.4rem; min-width:150px; }}
 .card .v {{ font-size:1.8rem; font-weight:700; }} .card .l {{ color:#8b93a7; font-size:.8rem; }}
 .ok {{ color:#4ade80; }} .bad {{ color:#f87171; }} .warn {{ color:#fbbf24; }}
 table {{ border-collapse:collapse; width:100%; margin-top:1rem; background:#1a1f2e; border-radius:10px; overflow:hidden; }}
 th, td {{ padding:.5rem .9rem; text-align:left; font-size:.85rem; border-bottom:1px solid #262c3d; }}
 th {{ background:#232a3b; color:#8b93a7; text-transform:uppercase; font-size:.72rem; }}
 tr:hover td {{ background:#20273a; }}
 .bar {{ background:#262c3d; border-radius:4px; height:10px; width:220px; display:inline-block; vertical-align:middle; }}
 .bar > div {{ background:linear-gradient(90deg,#38bdf8,#4ade80); height:10px; border-radius:4px; }}
 .badge {{ padding:.15rem .5rem; border-radius:6px; font-size:.75rem; font-weight:600; }}
 .badge.pass {{ background:#14351f; color:#4ade80; }} .badge.fail {{ background:#3b1a1a; color:#f87171; }}
 .badge.skip {{ background:#33301a; color:#fbbf24; }}
 .tabs {{ display:flex; gap:.4rem; margin:1.5rem 0 0; flex-wrap:wrap; }}
 .tab-btn {{ background:#1a1f2e; color:#8b93a7; border:none; padding:.55rem 1.1rem; border-radius:8px 8px 0 0; cursor:pointer; font-size:.9rem; }}
 .tab-btn.active {{ background:#232a3b; color:#e6e6e6; font-weight:600; }}
 .tab {{ display:none; }} .tab.active {{ display:block; }}
 pre {{ background:#151a26; border:1px solid #262c3d; border-radius:8px; padding:.8rem; overflow-x:auto; font-size:.78rem; }}
 details {{ margin:.4rem 0; background:#1a1f2e; border-radius:8px; padding:.5rem .9rem; }}
 summary {{ cursor:pointer; font-size:.88rem; }}
 select {{ background:#232a3b; color:#e6e6e6; border:1px solid #262c3d; border-radius:6px; padding:.35rem .6rem; }}
 canvas {{ background:#151a26; border:1px solid #262c3d; border-radius:8px; width:100%; max-width:1100px; }}
 .kv {{ font-size:.85rem; }} .kv code {{ color:#38bdf8; }}
 .scroll {{ overflow-x:auto; }}
 footer {{ margin-top:2rem; }}
</style>
</head>
<body><div class="wrap">
<h1>🛰 ISKI M0 v3.0 — Quality Dashboard (расширенный)</h1>
<div class="muted">Сгенерирован: {generated} · пересобрать: <code>python build_dashboard.py</code></div>

<div class="cards">
  <div class="card"><div class="v {tests_cls}">{tests_passed}/{tests_total}</div><div class="l">Тесты: passed {tests_passed} · failed {tests_failed} · errors {tests_errors} · skipped {tests_skipped}</div></div>
  <div class="card"><div class="v">{tests_duration:.1f}s</div><div class="l">Время прогона pytest</div></div>
  <div class="card"><div class="v {cov_cls}">{coverage:.1f}%</div><div class="l">Покрытие ({cov_covered}/{cov_stmts} строк; не покрыто {cov_missed})</div></div>
  <div class="card"><div class="v">{ruff_label} / {fmt_label}</div><div class="l">Ruff lint / формат</div></div>
  <div class="card"><div class="v {verdict_cls}">{verdict_short}</div><div class="l">Вердикт V1 (M0 falsification)</div></div>
  <div class="card"><div class="v">{tasks_done}/{tasks_total}</div><div class="l">Задачи T закрыты (CHECKLIST)</div></div>
</div>

<div class="tabs">
 <button class="tab-btn active" data-t="t-tests">Тесты и ошибки</button>
 <button class="tab-btn" data-t="t-cov">Покрытие</button>
 <button class="tab-btn" data-t="t-crit">Критерии V1</button>
 <button class="tab-btn" data-t="t-exp">Эксперимент M0</button>
 <button class="tab-btn" data-t="t-tasks">Задачи</button>
</div>

<div id="t-tests" class="tab active">
 <h2>Падения тестов ({n_failures})</h2>
 {failures_block}
 <h2>Тесты по файлам</h2>
 <table><tr><th>Файл</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Время, с</th><th>Статус</th></tr>{test_rows}</table>
 <h2>Все тест-кейсы ({tests_total})</h2>
 <div class="scroll"><table><tr><th>Файл</th><th>Тест</th><th>Статус</th><th>Время, с</th></tr>{case_rows}</table></div>
</div>

<div id="t-cov" class="tab">
 <h2>Покрытие по модулям (сортировка от худшего)</h2>
 <table><tr><th>Модуль</th><th>Строк</th><th>Не покрыто</th><th>Покрытие</th></tr>{cov_rows}</table>
 <h2>Непокрытые строки (ошибки/риски покрытия)</h2>
 {uncovered_block}
</div>

<div id="t-crit" class="tab">
 <h2>Критерии фальсификации V1</h2>
 <div class="kv"><b>Определения и канонические пороги (<code>config/bootstrap.yaml</code>, <code>experiments/m0/run_m0.py</code>):</b>
 <table><tr><th>Критерий</th><th>Условие прохождения</th><th>Порог</th></tr>
 <tr><td><code>warm_ok</code></td><td>среднее s_ed за последние 200 warm-тиков &gt; θ</td><td>θ = {th_theta:.2f}</td></tr>
 <tr><td><code>activity_band</code></td><td>A_min &lt; mean(activity) &lt; A_max</td><td>({th_amin}, {th_amax})</td></tr>
 <tr><td><code>entropy_band</code></td><td>H_min &lt; mean(H) &lt; H_max</td><td>({th_hmin}, {th_hmax})</td></tr>
 <tr><td><code>rho_stable</code></td><td>max ρ(J) &lt; rho_max</td><td>&lt; {th_rho:.2f}</td></tr>
 <tr><td><code>no_recovery</code></td><td>сумма нарушений инвариантов == 0</td><td>0 viol</td></tr>
 <tr><td><code>nontrivial</code></td><td>std(activity) &gt; 1e-3</td><td>&gt; 0.001</td></tr>
 <tr><td><code>pass</code></td><td>ИИ всех шести критериев</td><td>—</td></tr>
 </table></div>
 <h2>Результаты sweep по комбо (✗ = FAIL, ✓ = PASS)</h2>
 <div class="scroll"><table>{crit_table}</table></div>
 <p class="kv">Вердикт полного V1: <span class="badge {verdict_cls}">{verdict_short}</span> — известные причины провалов: <code>warm_ok</code>, <code>entropy_band</code> (см. ISSUE-001…003).</p>
</div>

<div id="t-exp" class="tab">
 <h2>Динамика метрик по тикам</h2>
 <div class="kv">Комбо (лог): <select id="comboSel">{combo_opts}</select></div>
 <canvas id="chartA" height="120"></canvas>
 <div class="muted">activity (синий), rho_j (зелёный) — левая шкала; H (жёлтый) — правая шкала.</div>
 <h2>Диагностика (среднее по тикам, из REPORT.md)</h2>
 <div class="scroll"><table>{diag_table}</table></div>
</div>

<div id="t-tasks" class="tab">
 <h2>Чек-лист задач (iski-tasks-v3.0/CHECKLIST.md)</h2>
 <table><tr><th>T</th><th>Задание</th><th>Тесты зелёные</th><th>operators.yaml</th><th>Issues / заметки</th></tr>{task_rows}</table>
</div>

<footer class="muted">{verdict_line}</footer>
</div>
<script>
const SERIES = {{series_json}};
document.querySelectorAll('.tab-btn').forEach(b => b.onclick = () => {{
  document.querySelectorAll('.tab-btn').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  b.classList.add('active'); document.getElementById(b.dataset.t).classList.add('active');
}});
function draw(combo) {{
  const d = SERIES[combo]; if (!d) return;
  const c = document.getElementById('chartA'), ctx = c.getContext('2d');
  const W = c.width = c.clientWidth * devicePixelRatio, Hh = c.height = 320 * devicePixelRatio;
  ctx.clearRect(0,0,W,Hh); ctx.fillStyle='#0f1117'; ctx.fillRect(0,0,W,Hh);
  function line(vals, min, max, color, off) {{
    ctx.strokeStyle=color; ctx.lineWidth=2*devicePixelRatio; ctx.beginPath();
    vals.forEach((y,i)=>{{ const x=(i/(vals.length-1))*(W-off*2)+off;
      const yy=Hh-off-(y-min)/(max-min||1)*(Hh-off*2);
      i?ctx.lineTo(x,yy):ctx.moveTo(x,yy); }});
    ctx.stroke();
  }}
  const mx=v=>Math.max(...v), mn=v=>Math.min(...v);
  line(d.activity, mn(d.activity)*0.9, Math.max(mx(d.activity)*1.1,1e-6), '#38bdf8', 40);
  line(d.rho_j, mn(d.rho_j)*0.95, mx(d.rho_j)*1.05+1e-9, '#4ade80', 40);
  line(d.H, mn(d.H)*0.95, mx(d.H)*1.05, '#fbbf24', 40);
  ctx.fillStyle='#8b93a7'; ctx.font=(11*devicePixelRatio)+'px sans-serif';
  ctx.fillText(combo, 46, 18*devicePixelRatio);
}}
const sel=document.getElementById('comboSel');
if (sel) {{ sel.onchange=()=>draw(sel.value); draw(sel.value); }}
</script>
</body>
</html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    print("[1/4] Запуск pytest + coverage…")
    tests = collect_tests()
    print("[2/4] Чтение coverage.json / junit.xml…")
    cov = collect_coverage()
    failures = collect_failures()
    uncovered = collect_uncovered()
    print("[3/4] REPORT.md / CHECKLIST / логи M0…")
    report = parse_report_md()
    tasks = collect_checklist()
    series = collect_experiment_series()
    th = collect_config_thresholds()
    print("[4/4] Проверка ruff…")
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
        f"<td>{f['skipped']}</td><td>{f['time']:.2f}</td>"
        f'<td><span class="badge {"fail" if f["failed"] else "pass"}">'
        f"{'FAIL' if f['failed'] else 'OK'}</span></td></tr>"
        for f in tests["files"]
    )

    # все тест-кейсы из junit (пересбор списка)
    root_ = ET.parse(DASH / "junit.xml").getroot()
    suite_ = root_ if root_.tag == "testsuite" else root_.find("testsuite")
    case_rows_list = []
    for tc in suite_.iter("testcase"):
        st = (
            "failed"
            if tc.find("failure") is not None or tc.find("error") is not None
            else "skipped"
            if tc.find("skipped") is not None
            else "passed"
        )
        badge = {"failed": "fail", "skipped": "skip", "passed": "pass"}[st]
        case_rows_list.append(
            f"<tr><td><code>{esc((tc.get('classname', '') or '?').split('.')[0])}</code></td>"
            f"<td>{esc(tc.get('name', ''))}</td>"
            f'<td><span class="badge {badge}">{st}</span></td>'
            f"<td>{float(tc.get('time', 0.0)):.3f}</td></tr>"
        )
    case_rows = "\n".join(case_rows_list)

    if failures:
        failures_block = "\n".join(
            f"<details open><summary><span class='badge fail'>{f['kind'].upper()}</span> "
            f"<code>{esc(f['file'])}</code> · {esc(f['name'])}</summary>"
            f"<pre>{esc(f['message'] or f['text'])}\n\n{esc(f['text'])}</pre></details>"
            for f in failures
        )
    else:
        failures_block = (
            '<p class="ok">✅ Падений нет — все тестовые кейсы зелёные.</p>'
        )

    uncov_blocks = []
    for u in uncovered:
        lines = ", ".join(str(x) for x in u["lines"][:60])
        more = f" … (+{len(u['lines']) - 60})" if len(u["lines"]) > 60 else ""
        uncov_blocks.append(
            f"<details><summary><code>{esc(u['file'])}</code> — {u['pct']:.1f}% "
            f"({len(u['lines'])} строк не покрыто)</summary><pre>{esc(lines)}{more}</pre></details>"
        )
    uncovered_block = (
        "\n".join(uncov_blocks) or "<p class='ok'>Полное покрытие во всех файлах.</p>"
    )

    cc = report["crit_cols"]
    crit_head = "<tr>" + "".join(f"<th>{esc(c)}</th>" for c in cc) + "</tr>"
    crit_body_rows = []
    for row in report["criteria_rows"]:
        cells_html = []
        for i, cell in enumerate(row):
            if i == 0:
                cells_html.append(f"<td><code>{esc(cell)}</code></td>")
            elif cell.lower() == "x":
                label = cc[i] if i < len(cc) else "?"
                cells_html.append(
                    f'<td><span class="badge fail" title="{esc(label)}">✗</span></td>'
                )
            else:
                cells_html.append('<td><span class="badge pass">✓</span></td>')
        crit_body_rows.append("<tr>" + "".join(cells_html) + "</tr>")
    crit_table = crit_head + "\n".join(crit_body_rows)

    dc = report["diag_cols"]
    diag_head = "<tr>" + "".join(f"<th>{esc(c)}</th>" for c in dc) + "</tr>"
    diag_body = "\n".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
        for row in report["diag_rows"]
    )
    diag_table = diag_head + diag_body

    task_rows = "\n".join(
        f"<tr><td><b>{t['id']}</b></td><td>{esc(t['title'])}</td>"
        f'<td><span class="badge "{"pass" if t["tests_green"] else "fail"}">'
        f"{'OK' if t['tests_green'] else 'NO'}</span></td>"
        f"<td>{esc(t['yaml'])}</td><td class='muted'>{esc(t['issues'])}</td></tr>"
        for t in tasks
    )

    combo_opts = "".join(f"<option>{esc(k)}</option>" for k in series)
    verdict_found = "НАЙДЕН" in report["verdict"] and not "НЕ" in report["verdict"]
    verdict_cls = "ok" if verdict_found else "bad"

    html = HTML_TEMPLATE.format(
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        tests_total=tests["total"],
        tests_passed=passed,
        tests_failed=tests["failures"],
        tests_errors=tests["errors"],
        tests_skipped=tests["skipped"],
        tests_duration=tests["duration"],
        tests_cls="ok" if all_green else "bad",
        coverage=cov["total_pct"],
        cov_covered=cov.get("covered", cov["stmts"] - cov["missed"]),
        cov_stmts=cov["stmts"],
        cov_missed=cov["missed"],
        cov_cls="ok" if cov["total_pct"] >= 80 else "bad",
        ruff_label="OK" if ruff["lint_ok"] else "ERRORS",
        fmt_label="OK" if ruff["format_ok"] else "ERRORS",
        verdict_short=esc(report["verdict"]),
        verdict_cls=verdict_cls,
        tasks_done=sum(1 for t in tasks if t["tests_green"]),
        tasks_total=len(tasks),
        n_failures=len(failures),
        failures_block=failures_block,
        test_rows=test_rows,
        case_rows=case_rows,
        cov_rows=cov_rows,
        uncovered_block=uncovered_block,
        th_theta=th.get("theta_ed_warm", 0.15),
        th_amin=th.get("A_min", 0.0),
        th_amax=th.get("A_max", 1.0),
        th_hmin=th.get("H_min", 0.0),
        th_hmax=th.get("H_max", 2.5),
        th_rho=th.get("rho_max", 1.5),
        crit_table=crit_table,
        combo_opts=combo_opts,
        diag_table=diag_table,
        task_rows=task_rows,
        series_json=json.dumps(series),
        verdict_line=(
            "✅ CI-гейт зелёный: тесты пройдены, линтер чистый. Научный гейт V1: "
            + report["verdict"]
            if all_green
            else "❌ Есть падения — см. вкладку «Тесты и ошибки»."
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
