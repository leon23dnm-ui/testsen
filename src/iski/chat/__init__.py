"""Чат-модель арифметики: цифры и операции + - * /."""

from iski.chat.dataset import build_corpus, exact_answer, parse_question
from iski.chat.model import VOCAB, CharGPT, decode, encode

__all__ = [
    "VOCAB",
    "CharGPT",
    "build_corpus",
    "decode",
    "encode",
    "exact_answer",
    "parse_question",
]
