"""Char-level GPT для арифметических ответов (цифры, + - * / =)."""

from __future__ import annotations

import math

import torch
from torch import nn

# Служебные токены первыми: pad=0, bos=1, eos=2
SPECIAL = ["<pad>", "<bos>", "<eos>"]
CHARS = list("0123456789+-*/=.? ")
VOCAB = SPECIAL + CHARS
stoi = {c: i for i, c in enumerate(VOCAB)}
itos = {i: c for c, i in stoi.items()}
PAD, BOS, EOS = 0, 1, 2


def encode(text: str) -> list[int]:
    return [stoi.get(ch, 0) for ch in text]


def decode(ids) -> str:
    out = []
    for i in ids:
        i = int(i)
        if i == EOS:
            break
        if i in (PAD, BOS):
            continue
        out.append(itos.get(i, ""))
    return "".join(out)


class Block(nn.Module):
    def __init__(self, dim: int, heads: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.ln2 = nn.LayerNorm(dim)
        self.ff = nn.Sequential(
            nn.Linear(dim, 4 * dim), nn.GELU(), nn.Linear(4 * dim, dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        T = x.size(1)
        mask = torch.full((T, T), float("-inf"), device=x.device)
        mask = torch.triu(mask, diagonal=1)
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, attn_mask=mask, need_weights=False)
        x = x + a
        x = x + self.ff(self.ln2(x))
        return x


class CharGPT(nn.Module):
    def __init__(self, dim: int = 96, layers: int = 3, heads: int = 4):
        super().__init__()
        self.dim = dim
        max_pos = 64
        self.tok = nn.Embedding(len(VOCAB), dim)
        self.pos = nn.Embedding(max_pos, dim)
        self.blocks = nn.ModuleList([Block(dim, heads) for _ in range(layers)])
        self.lnf = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, len(VOCAB), bias=False)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        _, T = idx.shape
        pos = torch.arange(T, device=idx.device).clamp(max=self.pos.num_embeddings - 1)
        x = self.tok(idx) + self.pos(pos)
        for blk in self.blocks:
            x = blk(x)
        return self.head(self.lnf(x))

    @torch.no_grad()
    def generate(self, prompt_ids: list[int], max_new: int = 24) -> list[int]:
        self.eval()
        ids = torch.tensor([prompt_ids], dtype=torch.long)
        dev = next(self.parameters()).device
        ids = ids.to(dev)
        for _ in range(max_new):
            ctx = ids[:, -self.pos.num_embeddings :]
            logits = self(ctx)[:, -1, :]
            logits[:, PAD] = -math.inf
            logits[:, BOS] = -math.inf
            nxt = logits.argmax(dim=-1, keepdim=True)
            ids = torch.cat([ids, nxt], dim=1)
            if int(nxt) == EOS:
                break
        return ids[0, len(prompt_ids) :].tolist()
