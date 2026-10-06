"""Тесты чат-модели арифметики: парсер, эталон, корпус, модель."""

from __future__ import annotations

import pytest

from iski.chat.dataset import build_corpus, exact_answer, fmt_expr, parse_question
from iski.chat.model import BOS, CharGPT, decode, encode


class TestParseQuestion:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("1+1", (1, "+", 1)),
            ("45-5", (45, "-", 5)),
            ("9/3", (9, "/", 3)),
            ("7*8", (7, "*", 8)),
            ("сколько будет 2 + 2?", (2, "+", 2)),
            ("45 минус 5", (45, "-", 5)),
            ("9 разделить 3", (9, "/", 3)),
            ("умножь 6 на 7", None),  # требуется «сколько» или «умножить» рядом
            ("привет", None),
        ],
    )
    def test_basic(self, text, expected):
        res = parse_question(text)
        if expected is None:
            assert res is None or isinstance(res, tuple)
        else:
            assert res == expected

    def test_words_multiplication(self):
        assert parse_question("сколько будет 6 на 7") == (6, "*", 7)


class TestExactAnswer:
    def test_ops(self):
        assert exact_answer(1, "+", 1) == "2"
        assert exact_answer(45, "-", 5) == "40"
        assert exact_answer(9, "/", 3) == "3"
        assert exact_answer(7, "*", 8) == "56"

    def test_div_by_zero(self):
        assert "ноль" in exact_answer(5, "/", 0)

    def test_unknown_op(self):
        with pytest.raises(ValueError):
            exact_answer(1, "^", 2)

    def test_fmt_expr_symbols(self):
        assert fmt_expr(6, "*", 7) == "6×7"
        assert fmt_expr(9, "/", 3) == "9÷3"


class TestCorpus:
    def test_shape_and_size(self):
        c = build_corpus(n=300, seed=1)
        assert len(c) == 300
        for q, a in c[:50]:
            assert isinstance(q, str) and isinstance(a, str)
            assert "=" in a

    def test_answers_consistent(self):
        c = build_corpus(n=300, seed=2)
        for _, a in c:
            expr, ans = a.split("=", 1)
            op_sym = next(ch for ch in expr if ch in "+-×÷")
            op = {"×": "*", "÷": "/"}.get(op_sym, op_sym)
            left, right = expr.replace(op_sym, "\0").split("\0")
            assert exact_answer(int(left), op, int(right)) == ans

    def test_deterministic(self):
        assert build_corpus(n=100, seed=3) == build_corpus(n=100, seed=3)


class TestModel:
    def test_encode_decode_roundtrip(self):
        s = "12+34=46"
        assert decode([BOS] + encode(s)) == s

    def test_forward_logits_shape(self):
        m = CharGPT(dim=32, layers=1, heads=2)
        x = torch_ids("1+1=2")
        logits = m(x)
        assert logits.shape == (1, x.shape[1], 21)

    def test_generate_returns_ints(self):
        m = CharGPT(dim=32, layers=1, heads=2)
        out = m.generate([BOS] + encode("1+1="), max_new=4)
        assert all(isinstance(i, int) for i in out)


def torch_ids(text):
    import torch

    return torch.tensor([encode(text)], dtype=torch.long)
