#!/usr/bin/env python3
"""Веб-интерфейс чата арифметики (stdlib http.server, без внешних зависимостей).

Запуск:  python scripts/chat_server.py --port 8091
API:     GET /            -> HTML чата
         POST /api/chat   -> {"message": str} => {"reply", "source", "ms"}
         GET /api/health  -> {"ok", "model_loaded", "holdout_acc"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import torch

from iski.chat.dataset import exact_answer, fmt_expr, parse_question
from iski.chat.model import BOS, CharGPT, decode, encode

CKPT = os.environ.get("CHAT_CKPT", "models/chat_arith.pt")
HTML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "iski", "chat", "web", "index.html"
)

MODEL = None
META = {}


def load_model():
    global MODEL, META
    if not os.path.exists(CKPT):
        return False
    try:
        ck = torch.load(CKPT, map_location="cpu")
        m = CharGPT(
            dim=ck.get("dim", 96), layers=ck.get("layers", 3), heads=ck.get("heads", 4)
        )
        m.load_state_dict(ck["state_dict"])
        m.eval()
        MODEL = m
        META = {"holdout_acc": float(ck.get("holdout_acc", -1.0))}
        return True
    except Exception as e:  # noqa: BLE001  # несовместимый чекпойнт — работаем от эталона
        print(f"[chat] checkpoint incompatible: {e}", file=sys.stderr)
        return False


def answer(message: str) -> dict:
    parsed = parse_question(message)
    if parsed is None:
        return {
            "reply": "Я умею только арифметику с числами и + − × ÷. Например: 1+1, 45-5, 9/3.",
            "source": "n/a",
            "ms": 0,
        }
    a, op, b = parsed
    gold = exact_answer(a, op, b)
    t0 = time.perf_counter()
    model_text = None
    if MODEL is not None:
        expr = fmt_expr(a, op, b)
        q = f"сколько будет {expr}?"
        gen = decode(
            MODEL.generate([BOS] + encode(q), max_new=len(gold) + len(expr) + 8)
        )
        # извлекаем хвост после '=' если он есть
        tail = gen.split("=", 1)[1].strip() if "=" in gen else gen.strip()
        if tail and all(ch in "0123456789.-" for ch in tail):
            model_text = tail
    ms = (time.perf_counter() - t0) * 1000
    shown = model_text if model_text is not None else "—"
    mark = "✓" if model_text == gold else "✗"
    reply = f"{fmt_expr(a, op, b)}:  модель «{shown}» {mark}   |   эталон «{gold}»"
    source = (
        "генеративная модель"
        if model_text is not None
        else "модель молчит — только эталон"
    )
    return {"reply": reply, "source": source, "ms": round(ms, 1)}


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(HTML_PATH, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/health":
            self._json(
                {
                    "ok": True,
                    "model_loaded": MODEL is not None,
                    "holdout_acc": META.get("holdout_acc", -1.0),
                }
            )
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/api/chat":
            self._json({"error": "not found"}, 404)
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n).decode())
        except Exception:  # noqa: BLE001
            self._json({"error": "bad json"}, 400)
            return
        self._json(answer(str(body.get("message", ""))))

    def log_message(self, fmt, *args):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8091)
    args = p.parse_args()
    loaded = load_model()
    print(
        f"[chat] модель: {'загружена, holdout=' + format(META.get('holdout_acc', 0), '.2%') if loaded else 'нет чекпойнта — работаю от эталона'}"
    )
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"[chat] веб-морда: http://localhost:{args.port}/")
    srv.serve_forever()


if __name__ == "__main__":
    main()
