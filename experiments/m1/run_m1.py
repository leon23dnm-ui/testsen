#!/usr/bin/env python3
"""M1 falsification run: масштабирование канона (N=16, K=8, D=64).

Та же семантика, те же 6 критериев и пороги; отличается только
размерность из config/model_m1.yaml. Пишет в experiments/m1/{logs,plots}
и experiments/m1/REPORT_M1.md — канонический REPORT.md не трогает.
"""

import argparse
import sys
import types
from pathlib import Path

import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from iski.encoders.hash_text import encode_text
from iski.runtime.bootstrap import bootstrap
from iski.runtime.pipeline import Pipeline

WORDS = ["one", "two", "three", "four"]


def make_cfg(root: Path) -> types.SimpleNamespace:
    with open(root / "config" / "model_m1.yaml", encoding="utf-8") as f:
        model = yaml.safe_load(f)
    with open(root / "config" / "runtime.yaml", encoding="utf-8") as f:
        runtime = yaml.safe_load(f)
    with open(root / "config" / "bootstrap.yaml", encoding="utf-8") as f:
        boot = yaml.safe_load(f)
    with open(root / "config" / "experiments" / "m1.yaml", encoding="utf-8") as f:
        experiment = yaml.safe_load(f)
    return types.SimpleNamespace(**model, **runtime, **boot, **experiment)


DIAG_KEYS = (
    "activity",
    "H",
    "s_ed",
    "rho_j",
    "eps_norm",
    "gate_frac",
    "mean_F_ext",
    "mask_frac",
    "w_fro",
    "mean_g",
)

LOG_KEYS = DIAG_KEYS + (
    "wm_fro",
    "h_norm",
    "node_spread",
    "mean_mu",
    "mean_theta",
    "mem_fro",
    "recall",
)

OBS_KEYS = (
    "h_norm",
    "node_spread",
    "w_fro",
    "wm_fro",
    "mask_frac",
    "gate_frac",
    "s_ed",
    "mem_fro",
    "recall",
)


def _write_log(path: Path, log) -> None:
    keys = ["t"] + list(LOG_KEYS) + ["n_viol"]
    lines = [",".join(keys)]
    for t, m, nv in log:
        row = [str(t)] + [f"{m.get(k, float('nan')):.6g}" for k in LOG_KEYS] + [str(nv)]
        lines.append(",".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot_traj(path: Path, log, tag: str) -> None:
    series = (
        "w_fro",
        "wm_fro",
        "mask_frac",
        "gate_frac",
        "s_ed",
        "h_norm",
        "node_spread",
    )
    ts = [t for t, _, _ in log]
    fig, axes = plt.subplots(
        len(series), 1, figsize=(8, 2.2 * len(series)), sharex=True
    )
    for ax, k in zip(axes, series, strict=True):
        ax.plot(ts, [m.get(k, float("nan")) for _, m, _ in log])
        ax.set_ylabel(k)
        ax.grid(True, alpha=0.3)
    axes[0].set_title(tag)
    axes[-1].set_xlabel("t")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _tail_stats(log, keys, window: int = 100) -> dict:
    tail = [m for _, m, _ in log][-window:]
    out = {}
    for k in keys:
        vals = [
            m[k]
            for m in tail
            if k in m and not (isinstance(m[k], float) and np.isnan(m[k]))
        ]
        out[k] = float(np.mean(vals)) if vals else float("nan")
    return out


def run_combo(
    pipeline: Pipeline,
    cfg: types.SimpleNamespace,
    eta_plast: float,
    Lambda: float,
    eta_g: float,
):
    cfg.eta_plast = eta_plast
    cfg.Lambda = Lambda
    cfg.eta_g = eta_g

    s_ed = []
    for t in range(cfg.warm_ticks):
        word = WORDS[t % len(WORDS)]
        e_in = encode_text(word, cfg.D, seed=cfg.seeds["boot"] + t)
        out = pipeline.tick(e_in, 1.0)
        s_ed.append(out["metrics"]["s_ed"])
        if t > 0 and t % cfg.T_maint == 0:
            pipeline.maintenance()

    recent = [v for v in s_ed[-200:] if not np.isnan(v)]
    warm_ok = bool(recent and np.mean(recent) > cfg.theta_ed_warm)

    activities, entropies, rho_js, viols = [], [], [], []
    for _ in range(cfg.auto_ticks):
        out = pipeline.tick(None, 0.0)
        m = out["metrics"]
        activities.append(m["activity"])
        entropies.append(m["H"])
        rho_js.append(m["rho_j"])
        viols.append(len(out["viol"]))

    activity_band = cfg.A_min < np.mean(activities) < cfg.A_max
    entropy_band = cfg.H_min < np.mean(entropies) < cfg.H_max
    rho_stable = np.max(rho_js) < cfg.rho_max
    no_recovery = sum(viols) == 0
    nontrivial = np.std(activities) > 1e-3

    logged = [m for _, m, _ in pipeline.log]
    diag = {}
    for k in DIAG_KEYS:
        vals = [
            m[k]
            for m in logged
            if k in m and not (isinstance(m[k], float) and np.isnan(m[k]))
        ]
        diag[k] = float(np.mean(vals)) if vals else float("nan")

    last_m = logged[-1]
    graph = pipeline.state.graph
    W = np.zeros((cfg.N, cfg.N))
    W[graph.edge_index[0], graph.edge_index[1]] += graph.w_eff()
    w_row = float(W.sum(axis=1).mean())
    homeo = {
        "g_end": float(last_m["mean_g"]),
        "mu_end": float(last_m["mean_mu"]),
        "theta_end": float(last_m["mean_theta"]),
        "w_row": w_row,
        "gw_row": float(last_m["mean_g"]) * w_row,
    }

    return {
        "warm_ok": warm_ok,
        "activity_band": activity_band,
        "entropy_band": entropy_band,
        "rho_stable": rho_stable,
        "no_recovery": no_recovery,
        "nontrivial": nontrivial,
        "pass": warm_ok
        and activity_band
        and entropy_band
        and rho_stable
        and no_recovery
        and nontrivial,
        "diag": diag,
        "log": list(pipeline.log),
        "homeo": homeo,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    cfg = make_cfg(root)

    logs_dir = root / "experiments" / "m1" / "logs"
    plots_dir = root / "experiments" / "m1" / "plots"
    logs_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for eta_plast in cfg.sweep["eta_plast"]:
        for Lambda in cfg.sweep["Lambda"]:
            for eta_g in cfg.sweep["eta_g"]:
                pipeline = bootstrap(cfg)
                result = run_combo(pipeline, cfg, eta_plast, Lambda, eta_g)
                tag = f"m1_eta{eta_plast}_L{Lambda}_etag{eta_g}"
                _write_log(logs_dir / f"{tag}.csv", result["log"])
                _plot_traj(plots_dir / f"{tag}.png", result["log"], tag)
                rows.append((eta_plast, Lambda, eta_g, result))
    found = any(r["pass"] for _, _, _, r in rows)
    verdict = "НАЙДЕН" if found else "НЕ НАЙДЕН"

    crit = (
        "warm_ok",
        "activity_band",
        "entropy_band",
        "rho_stable",
        "no_recovery",
        "nontrivial",
        "pass",
    )
    lines = [
        f"# REPORT M1 — масштабирование канона (N={cfg.N}, K={cfg.K}, D={cfg.D})",
        "",
        f"**Вердикт: {verdict}**",
        "",
        "Семантика M0 и все пороги/критерии без изменений; отличается только",
        "размерность (config/model_m1.yaml). Канонический REPORT.md не затрагивается.",
        "",
        "| combo | " + " | ".join(crit) + " |",
        "|-------|" + "|".join(["---"] * len(crit)) + "|",
    ]
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        cells = [combo] + ["x" if r[k] else " " for k in crit]
        lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Диагностика (лог тика, среднее по тикам)",
        "",
        "| combo | " + " | ".join(DIAG_KEYS) + " |",
        "|-------|" + "|".join(["---"] * len(DIAG_KEYS)) + "|",
    ]
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        cells = [combo] + [f"{r['diag'][k]:.4f}" for k in DIAG_KEYS]
        lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Наблюдения (диагностика, среднее по последним 100 тикам)",
        "",
        "| combo | " + " | ".join(OBS_KEYS) + " |",
        "|-------|" + "|".join(["---"] * len(OBS_KEYS)) + "|",
    ]
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        obs = _tail_stats(r["log"], OBS_KEYS)
        cells = [combo] + [f"{obs[k]:.4f}" for k in OBS_KEYS]
        lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Петля гомеостаза (конец прогона)",
        "",
        "| combo | g_end | mu_end | theta_end | w_row | g*w_row | loop |",
        "|-------|---|---|---|---|---|---|",
    ]
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        h = r["homeo"]
        loop = "closed" if h["g_end"] >= 2.0 else "open"
        cells = [
            combo,
            f"{h['g_end']:.4f}",
            f"{h['mu_end']:.4f}",
            f"{h['theta_end']:.4f}",
            f"{h['w_row']:.4f}",
            f"{h['gw_row']:.4f}",
            loop,
        ]
        lines.append("| " + " | ".join(cells) + " |")

    report_path = root / "experiments" / "m1" / "REPORT_M1.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(verdict)
    sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()
