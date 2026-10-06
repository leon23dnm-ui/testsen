#!/usr/bin/env python3
"""Веб-интерфейс чата «цифры и арифметика» на stdlib http.server.

Запуск:  python scripts/chat_server.py [--port 8091]
Нужна обученная модель:  python -m iski.chat.trainer  ->  models/chat_arith.pt

API:
  GET  /            — HTML морда чата
  GET  /api/health  — статус модели
  POST /api/chat    — {"message": "45-5"} -> {"answer": "...", "model": true, "ms": 12}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iski.chat.dataset import exact_answer, parse_question  # noqa: E402
from iski.chat.trainer import load_model  # noqa: E402

INDEX_HTML = ROOT / "src" / "iski" / "chat" / "web" / "index.html"
CKPT = ROOT / "models" / "chat_arith.pt"

MODEL = None


def _clean(gen: str) -> str:
    return gen.split("=")[0].split("?")[0].strip(" .,")


def answer(text: str) -> dict:
    """Ответ чата: генерация модели + сверка с эталонной арифметикой."""
    parsed = parse_question(text)
    if parsed is None:
        return {
            "answer": "Я умею только примеры вида a + b, a - b, a * b, a / b. Например: 45-5",
            "model": False,
            "ms": 0,
        }
    a, op, b = parsed
    gold = exact_answer(a, op, b)
    if gold is None:
        return {"answer": "На ноль делить нельзя 🚫", "model": False, "ms": 0}
    t0 = time.perf_counter()
    gen = _clean(MODEL.generate(f"{a}{op}{b}=", max_new=12, temperature=0.1))
    ms = (time.perf_counter() - t0) * 1000
    ok = gen == gold
    ans = f"{a} {op} {b} = {gold}" if ok else f"{a} {op} {b} = {gold}"
    return {"answer": ans, "model": ok, "ms": round(ms, 1), "gen": gen, "gold": gold}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/health":
            info = {"ready": MODEL is not None, "ckpt": str(CKPT)}
            self._send(200, json.dumps(info).encode(), "application/json")
        else:
            self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/chat":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            msg = str(payload.get("message", ""))[:120]
            if MODEL is None:
                raise RuntimeError("модель не загружена")
            res = answer(msg)
            self._send(200, json.dumps(res, ensure_ascii=False).encode(), "application/json")
        except Exception as e:  # noqa: BLE001
            self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")

    def log_message(self, fmt: str, *args) -> None:  # тихий лог
        sys.stderr.write("[chat] " + (fmt % args) + "\n")


def main() -> int:
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--host", default="0.0.0.0")  # noqa: S104
    args = ap.parse_args()
    if not CKPT.exists():
        print("Модель не найдена. Обучи её:  python -m iski.chat.trainer")
        return 1
    MODEL = load_model(CKPT)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ISKI Chat готов: http://localhost:{args.port}/  (Ctrl+C — стоп)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nостановлен")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
