"""Тесты чат-модели арифметики: датасет, разметка пакетов, модель, CLI-ответ."""

from __future__ import annotations

import random

import pytest

torch = pytest.importorskip("torch")

from iski.chat.dataset import build_corpus, exact_answer, make_example, parse_question  # noqa: E402
from iski.chat.model import BOS, EOS, CharGPT  # noqa: E402
from iski.chat.trainer import _encode_pair, make_batch  # noqa: E402


def test_parse_question_basic():
    assert parse_question("1+1") == (1, "+", 1)
    assert parse_question(" 45 - 5 ") == (45, "-", 5)
    assert parse_question("9/3=") == (9, "/", 3)
    assert parse_question("привет") is None
    assert parse_question("12*0") == (12, "*", 0)


def test_exact_answer_all_ops():
    assert exact_answer(1, "+", 1) == "2"
    assert exact_answer(45, "-", 5) == "40"
    assert exact_answer(9, "/", 3) == "3"
    assert exact_answer(7, "*", 8) == "56"
    assert exact_answer(7, "/", 0) is None  # деление на ноль
    assert exact_answer(7, "/", 2) == "3.5"


def test_make_examples_are_consistent():
    rng = random.Random(0)
    for _ in range(200):
        q, a = make_example(rng)
        parsed = parse_question(q)
        assert parsed is not None
        assert exact_answer(*parsed) == a


def test_build_corpus_unique_and_bounded():
    corpus = build_corpus(n=300, seed=3)
    qs = [q for q, _ in corpus]
    assert len(corpus) <= 300
    assert len(set(qs)) == len(qs)
    assert len(corpus) > 100


def test_encode_pair_shape():
    inp, tgt = _encode_pair("1+1", "2")
    assert inp[0] == BOS
    assert tgt[-1] == EOS
    assert CharGPT.decode(tgt[:-1]) == "2"


def test_make_batch_targets_only_answer():
    corpus = [("1+1", "2"), ("45-5", "40")] * 10
    rng = random.Random(0)
    x, y = make_batch(corpus, 4, rng, max_len=48)
    assert x.shape == y.shape
    assert (y != -100).sum() > 0
    # все цели — из токенов ответов/EOS, не промпта
    for b in range(x.size(0)):
        for j in range(y.size(1)):
            if y[b, j].item() != -100:
                assert y[b, j].item() == x[b, j + 1].item()


def test_model_forward_and_generate_shapes():
    m = CharGPT(dim=32, n_layers=1, n_heads=4, max_len=32)
    m.eval()
    idx = torch.tensor([[BOS] + CharGPT.encode("1+1=")])
    logits = m(idx)
    assert logits.shape == (1, 5, logits.shape[-1])
    out = m.generate("1+1=", max_new=4)
    assert isinstance(out, str)
