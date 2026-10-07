#!/usr/bin/env python3
"""Визуализация когнитивной модели ISKI M0 (stdlib http.server).

Запуск:  python scripts/viz_server.py --port 8092
API:     GET  /               -> HTML визуализатора
         GET  /api/state?step=N   -> сделать N тиков и вернуть снапшот
         POST /api/inject {"word": str, "dur": int} -> подать вход на dur тиков
         POST /api/reset {"eta_plast": f, "Lambda": f, "eta_g": f}
         POST /api/scenario {"auto": bool}  -> авто-сценарий warm/auto
         GET  /api/health    -> {"ok", "t", "phase", "N", "M"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import types
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import yaml

from iski.core.kernels import kernel_similarity
from iski.encoders.hash_text import encode_text
from iski.runtime.bootstrap import bootstrap

ROOT = os.path.join(os.path.dirname(__file__), "..")
HTML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "iski", "viz", "web", "index.html"
)
WORDS = ["one", "two", "three", "four"]
HIST_LEN = 400


def make_cfg(model_file: str = "model.yaml") -> types.SimpleNamespace:
    cfg = {}
    exp = "m1.yaml" if "m1" in model_file else "m0.yaml"
    for rel in (
        f"config/{model_file}",
        "config/runtime.yaml",
        "config/bootstrap.yaml",
        f"config/experiments/{exp}",
    ):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            cfg.update(yaml.safe_load(f))
    return types.SimpleNamespace(**cfg)


class Engine:
    """Обёртка над Pipeline: сценарий warm/auto + инъекции + снапшоты."""

    def __init__(self, model_file: str = "model.yaml") -> None:
        self.model_file = model_file
        self.reset()

    def reset(self, eta_plast=0.01, Lambda=0.3, eta_g=0.05) -> None:
        self.cfg = make_cfg(self.model_file)
        self.cfg.eta_plast = float(eta_plast)
        self.cfg.Lambda = float(Lambda)
        self.cfg.eta_g = float(eta_g)
        self.pipe = bootstrap(self.cfg)
        self.auto = True  # сценарий warm/auto как в run_m0
        self.inject_until = -1
        self.inject_vec = None
        self.hist = deque(maxlen=HIST_LEN)
        self.last_flux = np.zeros(len(self.pipe.state.graph.w_plus))
        self.flux_log = []  # [(t, flux_list)] с момента последнего snapshot
        self.rate = 12.0  # тиков/сек, 0 = пауза
        self.lock = threading.Lock()

    # вход на тик: инъекция имеет приоритет над сценарием
    def _input_for(self, t: int):
        if t <= self.inject_until:
            return self.inject_vec, 1.0
        if self.auto and t < self.cfg.warm_ticks:
            word = WORDS[t % len(WORDS)]
            return encode_text(word, self.cfg.D, seed=self.cfg.seeds["boot"] + t), 1.0
        return None, 0.0

    def _edge_flux(self) -> np.ndarray:
        """Что dst реально получает на этом тике (зеркало propagate)."""
        g = self.pipe.state.graph
        w = g.w_eff()
        fl = np.zeros(len(w))
        src_all = g.edge_index[0]
        for d in sorted(set(g.delays.tolist())):
            mask = g.delays == d
            xd = self.pipe.state.delayed(int(d)).mean(axis=1)
            fl[mask] = w[mask] * xd[src_all[mask]]
        return fl

    def _tick_once(self):
        st = self.pipe.state
        self.last_flux = self._edge_flux()
        e_in, conf = self._input_for(st.tick)
        out = self.pipe.tick(e_in, conf)
        self.flux_log.append((st.tick, self.last_flux.tolist()))
        if self.pipe.state.tick > 0 and self.pipe.state.tick % self.cfg.T_maint == 0:
            self.pipe.maintenance()
        m = out["metrics"]
        self.hist.append({"t": st.tick, "activity": m.get("activity"), "H": m.get("H")})
        return out

    def step(self, n: int = 1) -> dict:
        out = None
        with self.lock:
            for _ in range(max(1, int(n))):
                out = self._tick_once()
        return self.snapshot(out)

    def run_loop(self) -> None:
        """Фоновый тикер: модель работает в реальном времени, rate тиков/сек."""
        while True:
            rate = self.rate
            if rate <= 0:
                time.sleep(0.05)
                continue
            t0 = time.perf_counter()
            with self.lock:
                self._tick_once()
            dt = time.perf_counter() - t0
            time.sleep(max(0.0, 1.0 / rate - dt))

    def snapshot(self, out: dict | None) -> dict:
        st = self.pipe.state
        g = st.graph
        N, K = st.X.shape
        x_mean = st.X.mean(axis=1)
        mem = []
        for it in st.store:
            Ks = kernel_similarity(st.E, it.e, self.cfg.sigma)
            mem.append(
                {
                    "node": int(np.argmax(Ks)),
                    "w": round(float(it.rho[4]), 4),
                    "status": int(it.status),
                    "age": int(st.tick - it.t_create),
                }
            )
        metrics = out["metrics"] if out else {}
        return {
            "t": int(st.tick),
            "phase": "warm" if st.tick < self.cfg.warm_ticks else "auto",
            "model": self.model_file,
            "auto": self.auto,
            "inject_left": max(0, self.inject_until - st.tick + 1),
            "N": N,
            "K": K,
            "x": [round(float(v), 5) for v in x_mean],
            "xk": [[round(float(v), 4) for v in row] for row in st.X],
            "mu": [round(float(v), 5) for v in st.S[:, 0]],
            "theta": [round(float(v), 5) for v in st.S[:, 1]],
            "g": [round(float(v), 5) for v in st.S[:, 2]],
            "edges": [[int(s), int(d)] for s, d in g.edge_index.T],
            "w": [round(float(v), 4) for v in g.w_eff()],
            "delay": [int(v) for v in g.delays],
            "flux": [round(float(v), 6) for v in self.last_flux],
            "flux_log": self.drain_flux(),
            "rate": self.rate,
            "mem": mem,
            "gws": [bool(v) for v in (out["gws"] if out else np.zeros(N))],
            "att": [round(float(v), 4) for v in (out["att"] if out else np.zeros(N))],
            "metrics": {
                k: round(float(v), 5)
                for k, v in metrics.items()
                if isinstance(v, (int, float))
            },
            "hist": list(self.hist),
        }

    def drain_flux(self):
        with self.lock:
            out = self.flux_log
            self.flux_log = []
        return [(t, [round(float(v), 6) for v in fl]) for t, fl in out[-60:]]

    def inject(self, word: str, dur: int = 20) -> None:
        if word not in WORDS:
            word = WORDS[0]
        st = self.pipe.state
        seed = self.cfg.seeds["boot"] + 10000 + st.tick
        self.inject_vec = encode_text(word, self.cfg.D, seed=seed)
        self.inject_until = st.tick + max(1, int(dur))


ARGS = None
ENGINE = None


def _init_engine(model_file: str) -> None:
    global ENGINE
    ENGINE = Engine(model_file)


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:  # noqa: BLE001
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            with open(HTML_PATH, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif u.path == "/api/state":
            step = int(parse_qs(u.query).get("step", ["0"])[0])
            self._json(ENGINE.step(step) if step else ENGINE.snapshot(None))
        elif u.path == "/api/health":
            st = ENGINE.pipe.state
            self._json(
                {
                    "ok": True,
                    "t": int(st.tick),
                    "phase": "warm" if st.tick < ENGINE.cfg.warm_ticks else "auto",
                    "N": int(st.X.shape[0]),
                    "M": len(st.store),
                    "edges": len(st.graph.w_plus),
                }
            )
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        b = self._body()
        if u.path == "/api/inject":
            ENGINE.inject(str(b.get("word", "one")), int(b.get("dur", 20)))
            self._json({"ok": True})
        elif u.path == "/api/reset":
            ENGINE.reset(
                b.get("eta_plast", 0.01), b.get("Lambda", 0.3), b.get("eta_g", 0.05)
            )
            self._json({"ok": True})
        elif u.path == "/api/scenario":
            ENGINE.auto = bool(b.get("auto", True))
            self._json({"ok": True, "auto": ENGINE.auto})
        elif u.path == "/api/rate":
            ENGINE.rate = max(0.0, min(200.0, float(b.get("rate", 12))))
            self._json({"ok": True, "rate": ENGINE.rate})
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8092)
    p.add_argument(
        "--model",
        default="model.yaml",
        choices=["model.yaml", "model_m1.yaml"],
        help="M0 (N=4) или M1 (N=16) конфиг",
    )
    args = p.parse_args()
    _init_engine(args.model)
    ticker = threading.Thread(target=ENGINE.run_loop, daemon=True)
    ticker.start()
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"[viz] морда: http://localhost:{args.port}/")
    srv.serve_forever()


if __name__ == "__main__":
    main()
