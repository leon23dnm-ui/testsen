"""Тесты набора данных для дообучения чат-модели (scripts/build_dataset.py)."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "build_dataset", ROOT / "scripts" / "build_dataset.py"
)
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

from iski.chat.model import VOCAB


def test_build_small_dataset():
    rows = bd.build_dataset(n=300, seed=1)
    assert len(rows) == 300
    kinds = {r["kind"] for r in rows}
    assert {"basic", "word"} <= kinds
    splits = {r["split"] for r in rows}
    assert splits == {"train", "holdout"}


def test_answers_consistent_with_oracle():
    rows = bd.build_dataset(n=500, seed=2)
    for r in rows:
        if r["kind"] == "err":
            assert r["answer"] == f"{r['a']}/0=-1"
            continue
        if r["kind"] == "multi":
            lhs, ans = r["answer"].split("=")
            assert int(eval(lhs)) == int(ans)
            continue
        if r["kind"] == "word":
            # кириллический вопрос: сверяем только ответ с эталоном
            expect = f"{r['a']}{r['op']}{r['b']}=" + bd.exact_answer(
                r["a"], r["op"], r["b"]
            )
            assert r["answer"] == expect, (r, expect)
            continue
        # basic: вопрос содержит точное выражение — сверяем его и эталон
        expr = f"{r['a']}{r['op']}{r['b']}"
        assert expr in r["question"], r
        expect = f"{expr}=" + bd.exact_answer(r["a"], r["op"], r["b"])
        assert r["answer"] == expect, (r, expect)


def test_answers_in_vocab():
    """Ответы всегда в словаре модели; вопросы — кроме kind=word (кириллица)."""
    rows = bd.build_dataset(n=400, seed=3)
    vocab = set(VOCAB)
    for r in rows:
        bad_a = set(r["answer"]) - vocab
        assert not bad_a, (r["answer"], bad_a)
        if r["kind"] != "word":
            bad = set(r["question"]) - vocab
            assert not bad, (r["question"], bad)


def test_jsonl_roundtrip(tmp_path):
    rows = bd.build_dataset(n=120, seed=4)
    p = tmp_path / "ds.jsonl"
    bd.write_jsonl(rows, p)
    loaded = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]
    assert len(loaded) == 120
    assert loaded[0].keys() >= {"id", "question", "answer", "split"}


def test_tokens_bin_shape(tmp_path):
    rows = bd.build_dataset(n=100, seed=5)
    p = tmp_path / "t.bin"
    info = bd.write_tokens_bin(rows, p, max_len=64)
    assert (
        info["samples"] + info["dropped_too_long"] + info["skipped_out_of_vocab"] == 100
    )
    import numpy as np

    arr = np.fromfile(p, dtype=np.uint16).reshape(-1, 64)
    assert arr.shape[0] == info["samples"]
    assert (arr[:, 0] == 1).all()  # BOS в начале каждой строки


def test_multi_examples_valid_arithmetic():
    rows = [r for r in bd.build_dataset(n=2000, seed=6) if r["kind"] == "multi"]
    assert rows, "нет multi-примеров"
    for r in rows[:50]:
        lhs, ans = r["answer"].split("=")
        assert int(eval(lhs)) == int(ans)
