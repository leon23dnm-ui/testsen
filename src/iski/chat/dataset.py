"""Синтетический корпус: примеры арифметики для обучения чат-модели."""

from __future__ import annotations

import random
import re

OPS = "+-*/"


def _fmt(x: float) -> str:
    """Без хвостового .0; деление — с точностью до сотых, если не целое."""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s


def make_example(rng: random.Random, max_op: int = 99) -> tuple[str, str]:
    """Возвращает (вопрос, ответ) вида ('45-5', '40')."""
    op = rng.choice(OPS)
    a = rng.randint(0, max_op)
    b = rng.randint(0, max_op)
    if op == "/":
        # делим нацело, чтобы модель учила корректные целые частные
        b = rng.randint(1, 12)
        c = rng.randint(0, 12)
        q, ans = f"{b * c}/{b}", str(c)
    elif op == "-":
        if b > a:
            a, b = b, a
        q, ans = f"{a}-{b}", _fmt(a - b)
    elif op == "*":
        a = rng.randint(0, 12)
        b = rng.randint(0, 12)
        q, ans = f"{a}*{b}", _fmt(a * b)
    else:
        q, ans = f"{a}+{b}", _fmt(a + b)
    return q, ans


def build_corpus(
    n: int = 6000, seed: int = 7, max_retries: int | None = None
) -> list[tuple[str, str]]:
    """Уникальные примеры; гарантированный выход при перенасыщении пространства."""
    if max_retries is None:
        max_retries = 50 * n
    rng = random.Random(seed)
    seen: dict[str, str] = {}
    tries = 0
    while len(seen) < n and tries < max_retries:
        q, a = make_example(rng)
        seen.setdefault(q, a)
        tries += 1
    return list(seen.items())


Q_RE = re.compile(r"^\s*(\d+)\s*([+\-*/])\s*(\d+)\s*=?\s*$")


def parse_question(text: str) -> tuple[int, str, int] | None:
    """Извлекает (a, op, b) из строки вопроса. None — если не математика."""
    m = Q_RE.match(text)
    if not m:
        return None
    return int(m.group(1)), m.group(2), int(m.group(3))


def exact_answer(a: int, op: str, b: int) -> str | None:
    """Эталонный ответ по правилам арифметики (для верификации генерации)."""
    if op == "+":
        return _fmt(a + b)
    if op == "-":
        return _fmt(a - b)
    if op == "*":
        return _fmt(a * b)
    if op == "/":
        if b == 0:
            return None
        return _fmt(a / b)
    return None
