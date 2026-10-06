"""Синтетический корпус арифметических диалогов и парсер вопросов."""
from __future__ import annotations

import random
import re

OP_WORDS = {
    "+": ["+", "плюс", "прибавь", "сложить", "сумма"],
    "-": ["-", "минус", "отними", "вычти", "разность"],
    "*": ["*", "умножить", "умножь", "раз", "x"],
    "/": ["/", "разделить", "раздели", "поделить", ":"],
}

Q_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*(plus|minus|times|multiplied by|divided by|делится на|плюс|минус|умножить|умножь|на\s*\d+|разделить|раздели|поделить|[\+\-\*/x:])\s*(-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def parse_question(text: str) -> tuple[float, str, float] | None:
    """Вернуть (a, op, b) из простого вопроса вида '1+1', '45 минус 5' или None."""
    t = text.strip().lower().replace(" ", " ")
    # явные числа с оператором-символом
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", t)
    if m:
        a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
        return (int(a) if a == int(a) else a, op, int(b) if b == int(b) else b)
    # русские слова-операторы
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(плюс|минус|умножить|умножь|разделить|раздели|поделить)\s*(-?\d+(?:\.\d+)?)", t)
    if m:
        word = m.group(2)
        op = {"плюс": "+", "минус": "-", "умножить": "*", "умножь": "*", "разделить": "/", "раздели": "/", "поделить": "/"}[word]
        return (_num(m.group(1)), op, _num(m.group(3)))
    # «сколько будет 9 / 3» уже покрыто первым regex; «a на b» для умножения
    m = re.search(r"(-?\d+)\s+на\s+(-?\d+)", t)
    if m and ("умно" in t or "сколько" in t):
        return (int(m.group(1)), "*", int(m.group(2)))
    return None


def _num(s: str):
    v = float(s)
    return int(v) if v == int(v) else v


def exact_answer(a: float, op: str, b: float) -> str:
    """Эталонный ответ строкой (или сообщение об ошибке)."""
    if op == "/" and b == 0:
        return "деление на ноль невозможно"
    if op not in "+-*/":
        raise ValueError(f"unknown operator: {op!r}")
    r = {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[op]
    if isinstance(r, float) and r == int(r):
        r = int(r)
    if isinstance(r, float):
        r = round(r, 6)
        s = f"{r:.6f}".rstrip("0").rstrip(".")
    else:
        s = str(r)
    return s


def fmt_expr(a: float, op: str, b: float) -> str:
    disp = {"*": "×", "/": "÷"}.get(op, op)
    return f"{a}{disp}{b}"


def build_corpus(n: int = 6000, seed: int = 7, max_digits: int = 2) -> list[tuple[str, str]]:
    """Корпус (вопрос, ответ-строка). Ответ содержит '=результат' в конце."""
    rng = random.Random(seed)
    seen: set[tuple] = set()
    variants: list[tuple[str, str]] = []

    hi = 10**max_digits
    tries = 0
    while len(seen) < n and tries < n * 20:
        tries += 1
        op = rng.choice("+-*/")
        if op == "/":
            b = rng.randint(1, 12)
            a = b * rng.randint(0, (hi - 1) // b)  # делимость без остатка
        else:
            a = rng.randint(0, hi - 1)
            b = rng.randint(0, hi - 1)
            if op == "-" and rng.random() < 0.5:
                a, b = max(a, b), min(a, b)  # чаще неотрицательный результат
        key = (a, op, b)
        if key in seen:
            continue
        try:
            ans = exact_answer(a, op, b)
        except ZeroDivisionError:
            continue
        seen.add(key)
        resp = f"{fmt_expr(a, op, b)}={ans}"
        phrasings = [
            f"сколько будет {resp}?",
            f"{resp}? ответ",
            f"посчитай {resp}",
            f"{resp.split('=')[0]} равно чему?",
        ]
        variants.append((rng.choice(phrasings), resp))

    rng.shuffle(variants)
    return variants[:n]
