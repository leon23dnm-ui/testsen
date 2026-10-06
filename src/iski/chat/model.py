"""Мини-языковая модель для чата: цифры и арифметика (+ - * /).

Архитектура: char-level GPT (embedding -> N transformer blocks -> head),
обучается на синтетическом корпусе примеров вида "1+2=3" и отвечает
автогретивно. Модель небольшая, обучается за секунды на CPU.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

# Словарь: служебные токены + символы арифметики.
SPECIAL = ["<pad>", "<eos>", "<bos>"]
CHARS = list("0123456789+-*/=.? ")
VOCAB = SPECIAL + CHARS
STOI = {c: i for i, c in enumerate(VOCAB)}
ITOS = {i: c for c, i in STOI.items()}
PAD, EOS, BOS = STOI["<pad>"], STOI["<eos>"], STOI["<bos>"]
VSIZE = len(VOCAB)


class CausalSelfAttention(nn.Module):
    def __init__(self, dim: int, n_heads: int, dropout: float = 0.0) -> None:
        super().__init__()
        assert dim % n_heads == 0
        self.n_heads = n_heads
        self.d_head = dim // n_heads
        self.qkv = nn.Linear(dim, 3 * dim)
        self.proj = nn.Linear(dim, dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        qkv = self.qkv(x).view(b, t, 3, self.n_heads, self.d_head)
        q, k, v = (qkv[:, :, i].transpose(1, 2) for i in range(3))
        mask = torch.triu(torch.ones(t, t, device=x.device, dtype=torch.bool), diagonal=1)
        p = self.drop.p if self.training else 0.0
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, dropout_p=p)
        y = y.transpose(1, 2).contiguous().view(b, t, d)
        return self.proj(y)


class Block(nn.Module):
    def __init__(self, dim: int, n_heads: int, dropout: float = 0.0) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.attn = CausalSelfAttention(dim, n_heads, dropout)
        self.ln2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, 4 * dim),
            nn.GELU(),
            nn.Linear(4 * dim, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class CharGPT(nn.Module):
    """Char-level GPT с sin-cos позиционным embedding."""

    def __init__(self, dim: int = 64, n_layers: int = 2, n_heads: int = 4, max_len: int = 48) -> None:
        super().__init__()
        self.max_len = max_len
        self.tok_emb = nn.Embedding(VSIZE, dim)
        self.pos_emb = nn.Parameter(self._sin_cos(max_len, dim), requires_grad=False)
        self.blocks = nn.Sequential(*[Block(dim, n_heads) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, VSIZE)

    @staticmethod
    def _sin_cos(T: int, D: int) -> torch.Tensor:
        pos = torch.arange(T).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, D, 2).float() * (-math.log(10000.0) / D))
        pe = torch.zeros(T, D)
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div[: pe[:, 1::2].shape[1]])
        return pe

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        b, t = idx.shape
        x = self.tok_emb(idx) + self.pos_emb[:t].unsqueeze(0)
        x = self.blocks(x)
        return self.head(self.ln_f(x))

    # ---------- кодирование ----------
    @staticmethod
    def encode(text: str) -> list[int]:
        return [STOI.get(c, PAD) for c in text]

    @staticmethod
    def decode(ids: list[int]) -> str:
        out = []
        for i in ids:
            if i == EOS:
                break
            if i in (PAD, BOS):
                continue
            out.append(ITOS[i])
        return "".join(out)

    @torch.no_grad()
    def generate(self, prompt: str, max_new: int = 16, temperature: float = 0.2) -> str:
        """Автогрегативная генерация продолжения после промпта."""
        self.eval()
        ids = [BOS] + self.encode(prompt)
        start = len(ids)
        for _ in range(max_new):
            ctx = ids[-self.max_len :]
            logits = self.forward(torch.tensor([ctx]))[0, -1] / max(temperature, 1e-6)
            nxt = int(logits.argmax())
            if nxt == EOS:
                break
            ids.append(nxt)
        return self.decode(ids[start:])
