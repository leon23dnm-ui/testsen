#!/usr/bin/env python3
"""M0 falsification run V1."""

import argparse
import sys
import types
from pathlib import Path

import numpy as np
import torch
import yaml

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from iski.core.state import OmegaState
from iski.dynamics.homeostasis import init_S
from iski.dynamics.noise import make_rng
from iski.encoders.hash_text import encode_text
from iski.graph.topology import GraphCOO
from iski.prediction.buffer import RingBufferH
from iski.prediction.heads import PredHead
from iski.runtime.pipeline import Pipeline
from iski.runtime.scheduler import Clocks

WORDS = ["one", "two", "three", "four"]


def make_cfg(root: Path, fast: bool) -> types.SimpleNamespace:
    with open(root / "config" / "model.yaml", encoding="utf-8") as f:
        model = yaml.safe_load(f)
    with open(root / "config" / "runtime.yaml", encoding="utf-8") as f:
        runtime = yaml.safe_load(f)
    with open(root / "config" / "bootstrap.yaml", encoding="utf-8") as f:
        bootstrap = yaml.safe_load(f)
    with open(root / "config" / "experiments" / "m0.yaml", encoding="utf-8") as f:
        experiment = yaml.safe_load(f)

    cfg = types.SimpleNamespace(**model, **runtime, **bootstrap, **experiment)
    if fast:
        cfg.warm_ticks = 10
        cfg.auto_ticks = 10
        cfg.T_maint = 5
    return cfg


def bootstrap(cfg: types.SimpleNamespace) -> Pipeline:
    torch.manual_seed(cfg.seeds["boot"])
    rng = np.random.default_rng(cfg.seeds["boot"])
    N, D, K = cfg.N, cfg.D, cfg.K

    E = rng.standard_normal((N, D))
    norms = np.linalg.norm(E, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    E = E / norms

    src, dst = [], []
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            if rng.random() < cfg.p0:
                src.append(i)
                dst.append(j)
    M = len(src)
    edge_index = np.array([src, dst], dtype=int) if M else np.empty((2, 0), dtype=int)
    w_plus = rng.uniform(0.0, cfg.w_init_max, M) if M else np.zeros(0)
    w_minus = np.zeros(M)
    delays = rng.integers(0, cfg.Dmax, M) if M else np.zeros(0, dtype=int)
    q_elig = np.zeros(M)
    graph = GraphCOO(edge_index, w_plus, w_minus, delays, q_elig)

    X = np.zeros((N, K))
    S = init_S(N, cfg.mu_star)
    state = OmegaState(cfg, E, X, graph, S, store=[], tick=0)
    clocks = Clocks(cfg.clocks["m"], cfg.clocks["s"], cfg.clocks["q"])
    head = PredHead(N, K, cfg.H_head)
    hbuf = RingBufferH(cfg.tau1 + 2)
    rng_noise = make_rng(cfg.seeds["noise"])
    return Pipeline(state, clocks, cfg, head, hbuf, rng_noise)


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

LOG_KEYS = DIAG_KEYS + ("wm_fro", "h_norm", "node_spread")

OBS_KEYS = ("h_norm", "node_spread", "w_fro", "wm_fro", "mask_frac", "gate_frac", "s_ed")


def _write_log(path: Path, log) -> None:
    keys = ["t"] + list(LOG_KEYS) + ["n_viol"]
    lines = [",".join(keys)]
    for t, m, nv in log:
        row = [str(t)] + [f"{m.get(k, float('nan')):.6g}" for k in LOG_KEYS] + [str(nv)]
        lines.append(",".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot_traj(path: Path, log, tag: str) -> None:
    series = ("w_fro", "wm_fro", "mask_frac", "gate_frac", "s_ed", "h_norm", "node_spread")
    ts = [t for t, _, _ in log]
    fig, axes = plt.subplots(len(series), 1, figsize=(8, 2.2 * len(series)), sharex=True)
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
    pipeline: Pipeline, cfg: types.SimpleNamespace, eta_plast: float, Lambda: float, eta_g: float
):
    cfg.eta = eta_plast
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

    return {
        "warm_ok": warm_ok,
        "activity_band": activity_band,
        "entropy_band": entropy_band,
        "rho_stable": rho_stable,
        "no_recovery": no_recovery,
        "nontrivial": nontrivial,
        "pass": warm_ok and activity_band and entropy_band and rho_stable and no_recovery and nontrivial,
        "diag": diag,
        "log": list(pipeline.log),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="reduced ticks for CI")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    cfg = make_cfg(root, args.fast)

    logs_dir = root / "experiments" / "m0" / "logs"
    plots_dir = root / "experiments" / "m0" / "plots"
    logs_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    found = False
    for eta_plast in cfg.sweep["eta_plast"]:
        for Lambda in cfg.sweep["Lambda"]:
            for eta_g in cfg.sweep["eta_g"]:
                pipeline = bootstrap(cfg)
                result = run_combo(pipeline, cfg, eta_plast, Lambda, eta_g)
                tag = f"eta{eta_plast}_L{Lambda}_etag{eta_g}"
                _write_log(logs_dir / f"{tag}.csv", result["log"])
                if not args.fast:
                    _plot_traj(plots_dir / f"{tag}.png", result["log"], tag)
                rows.append((eta_plast, Lambda, eta_g, result))
                if result["pass"]:
                    found = True
                    break
            if found:
                break
        if found:
            break

    verdict = "НАЙДЕН" if found else "НЕ НАЙДЕН"

    lines = ["| combo | warm_ok | activity_band | entropy_band | rho_stable | no_recovery | nontrivial | pass |"]
    lines.append("|-------|---------|---------------|--------------|------------|-------------|------------|------|")
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        cells = [combo] + ["x" if r[k] else " " for k in ("warm_ok", "activity_band", "entropy_band", "rho_stable", "no_recovery", "nontrivial", "pass")]
        lines.append("| " + " | ".join(cells) + " |")

    diag_lines = [
        "",
        "## Диагностика (лог тика, среднее по тикам)",
        "",
        "| combo | " + " | ".join(DIAG_KEYS) + " |",
        "|-------|" + "|".join(["---"] * len(DIAG_KEYS)) + "|",
    ]
    for eta_plast, Lambda, eta_g, r in rows:
        combo = f"eta={eta_plast}, Lambda={Lambda}, eta_g={eta_g}"
        cells = [combo] + [f"{r['diag'][k]:.4f}" for k in DIAG_KEYS]
        diag_lines.append("| " + " | ".join(cells) + " |")

    if not args.fast:
        obs_lines = [
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
            obs_lines.append("| " + " | ".join(cells) + " |")
        diag_lines += obs_lines

    report_path = root / "REPORT.md"
    template = (root / "experiments" / "m0" / "REPORT.template.md").read_text(encoding="utf-8")
    table = "\n".join(lines)
    text = template.replace("<!-- ROWS -->", table).replace("{{VERDICT}}", verdict)
    text += "\n".join(diag_lines) + "\n"
    report_path.write_text(text, encoding="utf-8")

    print(verdict)
    sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()
