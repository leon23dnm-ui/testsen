"""Обучение чат-модели (цифры и + - * /) и оценка качества."""

from __future__ import annotations

import random
from pathlib import Path

import torch
import torch.nn.functional as F

from iski.chat.dataset import build_corpus, exact_answer, parse_question
from iski.chat.model import BOS, EOS, PAD, CharGPT


def _encode_pair(q: str, a: str) -> tuple[list[int], list[int]]:
    """Вход '<bos>'+q+'=' -> цель a+'<eos>'."""
    inp = [BOS] + CharGPT.encode(q + "=")
    tgt = CharGPT.encode(a) + [EOS]
    return inp, tgt


def make_batch(
    corpus: list[tuple[str, str]], batch: int, rng: random.Random, max_len: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Пакет next-token: x[:-1] предсказывает x[1:], loss только по токенам ответа и <eos>."""
    pairs = rng.sample(corpus, batch)
    enc = [_encode_pair(q, a) for q, a in pairs]
    L = min(max(len(i) + len(t) for i, t in enc), max_len)
    xs = torch.full((batch, L), PAD, dtype=torch.long)
    ys = torch.full((batch, L), -100, dtype=torch.long)
    for b, (inp, tgt) in enumerate(enc):
        seq = inp + tgt
        if len(seq) > L:  # обрезаем цель, вход всегда короткий
            keep_in = min(len(inp), L)
            seq = inp[:keep_in] + tgt[: L - keep_in]
            n_in = keep_in
        else:
            n_in = len(inp)
        pad = L - len(seq)
        row = seq + [PAD] * pad
        for j, tok in enumerate(row):
            xs[b, j] = tok
        # позиция j предсказывает токен j+1; цели — только для токенов ответа
        for j in range(n_in - 1, len(seq) - 1):
            ys[b, j] = seq[j + 1]
    return xs, ys


def train(
    epochs: int = 12,
    steps_per_epoch: int = 400,
    batch: int = 128,
    lr: float = 1e-3,
    n_corpus: int = 6000,
    seed: int = 7,
    ckpt: str | Path = "models/chat_arith.pt",
    verbose: bool = True,
) -> CharGPT:
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model = CharGPT(dim=96, n_layers=3, n_heads=6, max_len=48)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    corpus = build_corpus(n=n_corpus, seed=seed)
    step = 0
    for ep in range(epochs):
        model.train()
        tot = 0.0
        for _ in range(steps_per_epoch):
            x, y = make_batch(corpus, batch, rng, model.max_len)
            logits = model(x)[:, :-1]
            loss = F.cross_entropy(
                logits.reshape(-1, logits.size(-1)), y[:, 1:].reshape(-1), ignore_index=-100
            )
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item()
            step += 1
        avg = tot / steps_per_epoch
        if verbose:
            print(f"epoch {ep + 1}/{epochs} loss={avg:.4f} step={step}")
    p = Path(ckpt)
    p.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "dim": 96, "layers": 3, "heads": 6}, p)
    return model


def load_model(ckpt: str | Path = "models/chat_arith.pt") -> CharGPT:
    obj = torch.load(ckpt, map_location="cpu", weights_only=False)
    model = CharGPT(dim=obj["dim"], n_layers=obj["layers"], n_heads=obj["heads"])
    model.load_state_dict(obj["state_dict"])
    model.eval()
    return model


@torch.no_grad()
def evaluate(model: CharGPT, n: int = 200, seed: int = 991) -> float:
    """Доля точных ответов на holdout (эталон — parse_question/exact_answer)."""
    rng = random.Random(seed)
    corpus = build_corpus(n=20000, seed=seed)
    model.eval()
    ok = tested = 0
    for q, _ in rng.sample(corpus, n):
        parsed = parse_question(q)
        if parsed is None:
            continue
        gold = exact_answer(*parsed)
        gen = model.generate(q + "=", max_new=12, temperature=0.1)
        pred = gen.split("=")[0].strip().split("?")[0]
        tested += 1
        if gold is not None and pred == gold:
            ok += 1
    return ok / max(tested, 1)


if __name__ == "__main__":
    m = train()
    print(f"accuracy on holdout: {evaluate(m):.2%}")
