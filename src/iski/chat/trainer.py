"""Обучение чат-модели арифметики (next-token, loss только по ответу)."""

from __future__ import annotations

import argparse
import math
import random

import torch
from torch import nn

from iski.chat.dataset import build_corpus
from iski.chat.model import BOS, EOS, PAD, CharGPT, encode


def make_sample(q: str, a: str):
    """Возвращает (ids, target_mask): loss только на токенах ответа + EOS."""
    q_ids = encode(q)
    a_ids = encode(a)
    ids = [BOS] + q_ids + a_ids + [EOS]
    mask = [0] * (1 + len(q_ids)) + [1] * (len(a_ids) + 1)
    return ids, mask


def make_batch(samples, max_len):
    xs, ys, ms = [], [], []
    for ids, mask in samples:
        pad = max_len - len(ids)
        x = ids[:-1] + [PAD] * pad
        y = ids[1:] + [PAD] * pad
        m = mask[1:] + [0] * pad
        xs.append(x)
        ys.append(y)
        ms.append(m)
    return (
        torch.tensor(xs, dtype=torch.long),
        torch.tensor(ys, dtype=torch.long),
        torch.tensor(ms, dtype=torch.float),
    )


def train(
    n_corpus: int = 6000,
    epochs: int = 12,
    batch_size: int = 64,
    lr: float = 1e-3,
    dim: int = 96,
    layers: int = 3,
    heads: int = 4,
    seed: int = 7,
    out_path: str = "models/chat_arith.pt",
    holdout_frac: float = 0.1,
):
    torch.manual_seed(seed)
    random.seed(seed)
    corpus = build_corpus(n=n_corpus, seed=seed)
    split = int(len(corpus) * (1 - holdout_frac))
    train_s, hold_s = corpus[:split], corpus[split:]

    tr = [make_sample(q, a) for q, a in train_s]
    max_len = max(len(ids) for ids, _ in tr)

    model = CharGPT(dim=dim, layers=layers, heads=heads)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    steps = epochs * math.ceil(len(tr) / batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=lr, total_steps=steps, pct_start=0.1
    )
    ce = nn.CrossEntropyLoss(reduction="none")

    step = 0
    for ep in range(epochs):
        random.shuffle(tr)
        tot = 0.0
        nb = 0
        for i in range(0, len(tr), batch_size):
            xb, yb, mb = make_batch(tr[i : i + batch_size], max_len)
            logits = model(xb)
            loss = (ce(logits.transpose(1, 2), yb) * mb).sum() / mb.sum().clamp(min=1)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += float(loss)
            nb += 1
            step += 1
            if step % 400 == 0:
                print(
                    f"epoch {ep + 1}/{epochs} loss={tot / max(nb, 1):.4f} step={step}",
                    flush=True,
                )
        print(
            f"epoch {ep + 1}/{epochs} loss={tot / max(nb, 1):.4f} step={step}",
            flush=True,
        )

    acc = evaluate(model, hold_s)
    print(f"accuracy on holdout: {acc:.2%}", flush=True)

    import os

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "dim": dim,
            "layers": layers,
            "heads": heads,
            "holdout_acc": acc,
        },
        out_path,
    )
    print(f"saved checkpoint -> {out_path}", flush=True)
    return model, acc


def evaluate(model: CharGPT, pairs, limit: int | None = None) -> float:
    from iski.chat.model import decode

    model.eval()
    ok = 0
    items = pairs[:limit] if limit else pairs
    for q, a in items:
        ids = encode(q)
        gen = decode(model.generate([BOS] + ids, max_new=len(a) + 4))
        if gen.strip() == a.strip():
            ok += 1
    return ok / max(len(items), 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=int, default=6000)
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", default="models/chat_arith.pt")
    args = p.parse_args()
    train(n_corpus=args.corpus, epochs=args.epochs, lr=args.lr, out_path=args.out)
