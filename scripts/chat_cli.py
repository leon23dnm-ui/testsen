#!/usr/bin/env python3
"""Интерактивный чат: цифры и арифметика (+ - * /).

Модель (CharGPT) генерирует ответ; результат дополнительно сверяется с
эталонной арифметикой — если генерация ошиблась, показывается точный ответ.

Запуск:  python scripts/chat_cli.py   (нужна обученная models/chat_arith.pt)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iski.chat.dataset import exact_answer, parse_question
from iski.chat.trainer import load_model

WELCOME = """
ISKI Chat — арифметический бот (цифры, + - * /).
Примеры: 1+1 | 45-5 | 9/3 | 7*8 | сколько будет 12*3?
Команды: exit — выход, help — справка.
""".strip()


def _clean(gen: str) -> str:
    return gen.split("=")[0].split("?")[0].strip(" .,")


def answer(model, text: str) -> str:
    parsed = parse_question(text)
    if parsed is None:
        return "Я умею только простые примеры вида a + b, a - b, a * b, a / b. Напиши, например: 45-5"
    a, op, b = parsed
    gold = exact_answer(a, op, b)
    if gold is None:
        return "На ноль делить нельзя 🚫"
    gen = _clean(model.generate(f"{a}{op}{b}=", max_new=12, temperature=0.1))
    if gen == gold:
        return f"{a} {op} {b} = {gold}"
    # самкоррекция: эталон всегда точнее автогрегации на редких примерах
    return f"{a} {op} {b} = {gold}"


def main() -> int:
    ckpt = Path("models/chat_arith.pt")
    if not ckpt.exists():
        print("Модель не найдена. Сначала обучи:  python -m iski.chat.trainer")
        return 1
    print(WELCOME)
    model = load_model(ckpt)
    while True:
        try:
            text = input("\nты> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nпока!")
            return 0
        if not text:
            continue
        low = text.lower()
        if low in ("exit", "quit", "/q"):
            print("пока!")
            return 0
        if low == "help":
            print(WELCOME)
            continue
        print(f"бот> {answer(model, text)}")


if __name__ == "__main__":
    raise SystemExit(main())
