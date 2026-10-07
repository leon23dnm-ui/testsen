#!/usr/bin/env python3
"""Сборка расширенного датасета для дообучения чат-модели арифметики.

Формат вывода — JSONL (по одной записи на строку):
    {"id": int, "question": str, "answer": str, "op": "+|-|*|/",
     "a": num, "b": num, "kind": "basic|word|multi", "split": "train|holdout"}

По умолчанию генерируется ДВОИЧНЫЙ файл токенов models/chat_ft_tokens.bin
(совместим с CharGPT: словарь из iski.chat.model), готовый к дообучению без
кодирования в рантайме.

Примеры:
    python scripts/build_dataset.py --n 40000 --out data/chat_arith.jsonl
    python scripts/build_dataset.py --tokens-out models/chat_ft_tokens.bin
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from iski.chat.dataset import exact_answer
from iski.chat.model import BOS, EOS, VOCAB, stoi

# ---------------------------------------------------------------------------
# Генерация пар (вопрос, ответ)
# ---------------------------------------------------------------------------

# Все фразы-шаблоны состоят только из символов словаря CharGPT
# (латиница в словарь не входит — используются цифры, знаки и пробел).
PHRASES = ["? {e}", "{e} ?", "?? {e}", "{lhs} ?", "{e} ??"]

WORD_OPS_RU = {
    "+": ["плюс", "прибавь", "сложи"],
    "-": ["минус", "отними", "вычти"],
    "*": ["умножить", "умножь", "на"],
    "/": ["разделить", "раздели", "поделить"],
}


def _expr_pair(a, op, b):
    """Каноническое выражение и ответ (только символы из словаря модели).

    Символьный ответ использует * и / (не ×/÷), т.к. словарь CharGPT их содержит.
    """
    lhs = f"{a}{op}{b}"
    ans = exact_answer(a, op, b)
    return lhs, f"{lhs}={ans}", ans


def gen_basic(rng: random.Random, max_digits: int) -> tuple[str, str, dict] | None:
    op = rng.choice("+-*/")
    hi = 10**max_digits
    if op == "/":
        b = rng.randint(1, 12)
        a = b * rng.randint(0, (hi - 1) // b)
    else:
        a = rng.randint(0, hi - 1)
        b = rng.randint(0, hi - 1)
        if op == "-" and rng.random() < 0.5:
            a, b = max(a, b), min(a, b)
    try:
        lhs, resp, _ans = _expr_pair(a, op, b)
    except ZeroDivisionError:
        return None
    q = rng.choice(PHRASES).format(e=resp, lhs=lhs)
    return q, resp, {"op": op, "a": a, "b": b, "kind": "basic"}


def gen_word(rng: random.Random, max_digits: int) -> tuple[str, str, dict] | None:
    """Русские слова-операторы; ответ всегда символьным выражением.

    NOTE: вопрос содержит кириллицу (вне словаря CharGPT) — такие примеры
    годятся для текстового JSONL/эталонной проверки, но не для прямого
    токенизационного дообучения модели. Бинарные токены фильтруются в
    write_tokens_bin по символному составу.
    """
    op = rng.choice("+-*/")
    hi = 10**max_digits
    if op == "/":
        b = rng.randint(1, 12)
        a = b * rng.randint(0, (hi - 1) // b)
    else:
        a = rng.randint(0, hi - 1)
        b = rng.randint(0, hi - 1)
        if op == "-" and rng.random() < 0.5:
            a, b = max(a, b), min(a, b)
    word = rng.choice(WORD_OPS_RU[op])
    try:
        _lhs, resp, _ans = _expr_pair(a, op, b)
    except ZeroDivisionError:
        return None
    q = f"сколько будет {a} {word} {b}?"
    return q, resp, {"op": op, "a": a, "b": b, "kind": "word"}


CHAIN_RE = re.compile(r"^(\d+)([+\-*/])(\d+)([+\-*/])(\d+)$")


def gen_multi(rng: random.Random, max_digits: int) -> tuple[str, str, dict] | None:
    """Цепочки вида a+b*c — только если результат целое и <= 999999."""
    d = max(1, max_digits - 1)
    a = rng.randint(0, 10**d - 1)
    b = rng.randint(0, 10**d - 1)
    c = rng.randint(0, 10**d - 1)
    o1 = rng.choice("+-*/")
    o2 = rng.choice("+-*/")
    try:
        r = eval(f"{a}{o1}{b}{o2}{c}")
    except ZeroDivisionError:
        return None
    if not isinstance(r, int) or abs(r) > 999_999:
        return None
    lhs = f"{a}{o1}{b}{o2}{c}"
    resp = f"{lhs}={r}"
    q = rng.choice(PHRASES).format(e=resp, lhs=lhs)
    return q, resp, {"op": f"{o1}{o2}", "a": a, "b": b, "kind": "multi"}


def gen_zero_div(rng: random.Random) -> tuple[str, str, dict]:
    a = rng.randint(0, 99)
    q = rng.choice(PHRASES).format(e=f"{a}/0", lhs=f"{a}/0")
    return q, f"{a}/0=-1", {"op": "/", "a": a, "b": 0, "kind": "err"}


def build_dataset(
    n: int = 40000, seed: int = 7, max_digits: int = 2, multi_frac: float = 0.1
) -> list[dict]:
    rng = random.Random(seed)
    seen: set[tuple[str, str]] = set()
    rows: list[dict] = []
    tries = 0
    while len(rows) < n and tries < n * 20:
        tries += 1
        r = rng.random()
        if r < multi_frac:
            item = gen_multi(rng, max_digits)
        elif r < multi_frac + 0.002:
            item = gen_zero_div(rng)
        elif r < multi_frac + 0.25:
            item = gen_word(rng, max_digits)
        else:
            item = gen_basic(rng, max_digits)
        if item is None:
            continue
        q, resp, meta = item
        key = (q, resp)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "id": len(rows),
                "question": q,
                "answer": resp,
                **meta,
            }
        )
    rng.shuffle(rows)
    for i, row in enumerate(rows):
        row["id"] = i
        split = int(len(rows) * 0.9)
        row["split"] = "train" if i < split else "holdout"
    return rows


# ---------------------------------------------------------------------------
# Экспорт
# ---------------------------------------------------------------------------


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def encode_sample(q: str, a: str) -> list[int]:
    ids_q = [stoi.get(ch, 0) for ch in q]
    ids_a = [stoi.get(ch, 0) for ch in a]
    return [BOS] + ids_q + ids_a + [EOS]


def write_tokens_bin(rows: list[dict], path: Path, max_len: int = 64) -> dict:
    """Упаковать train+holdout в uint16 .bin (padding=0/PAD) для быстрого дообучения.

    Пропускаем примеры, содержащие символы вне словаря CharGPT (кириллица и т.п.).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    import numpy as np

    vocab = set(VOCAB)
    seqs = []
    skipped_vocab = 0
    for row in rows:
        text = row["question"] + row["answer"]
        if set(text) - vocab:
            skipped_vocab += 1
            continue
        s = encode_sample(row["question"], row["answer"])
        if len(s) <= max_len:
            seqs.append(s)
    arr = np.zeros((len(seqs), max_len), dtype=np.uint16)
    for i, s in enumerate(seqs):
        arr[i, : len(s)] = s
    path.write_bytes(arr.tobytes())
    return {
        "samples": len(seqs),
        "dropped_too_long": len(rows) - len(seqs) - skipped_vocab,
        "skipped_out_of_vocab": skipped_vocab,
        "max_len": max_len,
        "dtype": "uint16",
        "vocab": "".join(VOCAB),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=40000, help="число примеров")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--max-digits", type=int, default=2)
    p.add_argument("--multi-frac", type=float, default=0.1)
    p.add_argument("--out", default="data/chat_arith.jsonl")
    p.add_argument(
        "--tokens-out", default=None, help="например models/chat_ft_tokens.bin"
    )
    args = p.parse_args()

    rows = build_dataset(
        args.n, seed=args.seed, max_digits=args.max_digits, multi_frac=args.multi_frac
    )
    out = Path(args.out)
    write_jsonl(rows, out)

    stats = {
        "total": len(rows),
        "train": sum(r["split"] == "train" for r in rows),
        "holdout": sum(r["split"] == "holdout" for r in rows),
        "by_kind": {
            k: sum(r["kind"] == k for r in rows)
            for k in ("basic", "word", "multi", "err")
        },
        "by_op": {k: sum(r["op"] == k for r in rows) for k in "+-*/"},
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"jsonl -> {out}")

    if args.tokens_out:
        tok_path = Path(args.tokens_out)
        info = write_tokens_bin(rows, tok_path)
        print(f"tokens -> {tok_path}: {json.dumps(info)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
