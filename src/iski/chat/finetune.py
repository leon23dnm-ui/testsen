"""Дообучение (fine-tune) CharGPT на внешнем датасете из scripts/build_dataset.py.

Поддерживает два входа:
  * JSONL-датасет (--data data/chat_arith.jsonl) — удобен для правок;
  * бинарные токены (--tokens models/chat_ft_tokens.bin, --max-len 64) — быстрее.

Чекпойнт модели сохраняется отдельно от исходного (models/chat_arith_ft.pt),
чтобы не затирать базовую модель.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
import torch
from iski.chat.trainer import evaluate
from torch import nn

from iski.chat.model import BOS, EOS, PAD, CharGPT, encode


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def make_sample(q: str, a: str):
    q_ids = encode(q)
    a_ids = encode(a)
    ids = [BOS] + q_ids + a_ids + [EOS]
    mask = [0] * (1 + len(q_ids)) + [1] * (len(a_ids) + 1)
    return ids, mask


def batchify(samples, max_len):
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


def samples_from_tokens(bin_path: str, max_len: int):
    """Прочитать uint16 [.N x max_len] и восстановить (ids, mask).

    Формат записи build_dataset.write_tokens_bin: [BOS]+q+a+[EOS]+PAD...
    Маску ответа восстанавливаем по позиции EOS: всё до первого EOS после
    вопроса — prompt. Чтобы не гадать, используем правило: loss ставим на
    токены начиная с символа '=' (включая сам '=') до EOS включительно —
    это ровно числовая часть ответа модели.
    """
    arr = np.fromfile(bin_path, dtype=np.uint16).reshape(-1, max_len)
    out = []
    eq_id = encode("=")[0]
    for row in arr:
        seq = row.tolist()
        if EOS not in seq:
            continue
        end = seq.index(EOS)
        # позиция последнего '=' в ответе (первый '=' после цифр выражения)
        try:
            eq_pos = seq.index(eq_id)
        except ValueError:
            continue
        mask = [0] * (eq_pos) + [1] * (end - eq_pos + 1)
        out.append((seq[: end + 1], mask[: end + 1]))
    return out


def finetune(
    ckpt_in: str = "models/chat_arith.pt",
    ckpt_out: str = "models/chat_arith_ft.pt",
    data: str | None = "data/chat_arith.jsonl",
    tokens: str | None = None,
    max_len: int = 64,
    epochs: int = 3,
    batch_size: int = 128,
    lr: float = 2e-4,
    seed: int = 7,
    holdout_limit: int = 300,
):
    torch.manual_seed(seed)
    random.seed(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CharGPT(dim=96, layers=3, heads=4).to(device)
    info = torch.load(ckpt_in, map_location=device)
    missing, unexpected = model.load_state_dict(info["state_dict"], strict=False)
    print(f"loaded {ckpt_in} (missing={len(missing)}, unexpected={len(unexpected)})")

    if tokens:
        tr_samples = samples_from_tokens(tokens, max_len=max_len)
        rng = random.Random(seed)
        rng.shuffle(tr_samples)
        n_hold = min(holdout_limit, len(tr_samples) // 10)
        tr_samples = tr_samples[n_hold:]
        # для оценки accuracy восстановим пары из jsonl если он задан
        pairs = [(r["question"], r["answer"]) for r in load_jsonl(data)] if data else []
        hold_pairs = pairs[-n_hold:] if pairs else []
    else:
        rows = load_jsonl(data)
        train_rows = [r for r in rows if r.get("split", "train") == "train"]
        hold_rows = [r for r in rows if r.get("split") == "holdout"][:holdout_limit]
        tr_samples = [make_sample(r["question"], r["answer"]) for r in train_rows]
        max_len = min(max_len, max(len(s) for s, _ in tr_samples) + 1)
        hold_pairs = [(r["question"], r["answer"]) for r in hold_rows]

    print(f"train samples: {len(tr_samples)} | holdout pairs: {len(hold_pairs)}")

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    steps = epochs * math.ceil(len(tr_samples) / batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=lr, total_steps=steps, pct_start=0.1
    )
    ce = nn.CrossEntropyLoss(reduction="none")

    step = 0
    for ep in range(epochs):
        random.shuffle(tr_samples)
        tot, nb = 0.0, 0
        for i in range(0, len(tr_samples), batch_size):
            xb, yb, mb = batchify(tr_samples[i : i + batch_size], max_len)
            xb, yb, mb = xb.to(device), yb.to(device), mb.to(device)
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
        print(f"ft epoch {ep + 1}/{epochs} loss={tot / max(nb, 1):.4f}", flush=True)

    acc = evaluate(model.cpu(), hold_pairs) if hold_pairs else float("nan")
    print(f"holdout accuracy after FT: {acc:.2%}")

    out_path = Path(ckpt_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "dim": 96,
            "layers": 3,
            "heads": 4,
            "holdout_acc": acc,
            "base_ckpt": ckpt_in,
            "dataset": data or tokens,
        },
        out_path,
    )
    print(f"saved fine-tuned checkpoint -> {out_path}")
    return model, acc


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="ckpt_in", default="models/chat_arith.pt")
    p.add_argument("--out", dest="ckpt_out", default="models/chat_arith_ft.pt")
    p.add_argument("--data", default="data/chat_arith.jsonl")
    p.add_argument("--tokens", default=None, help="models/chat_ft_tokens.bin")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-4)
    args = p.parse_args()
    finetune(
        ckpt_in=args.ckpt_in,
        ckpt_out=args.ckpt_out,
        data=args.data,
        tokens=args.tokens,
        epochs=args.epochs,
        lr=args.lr,
    )
