"""Чат-модель арифметики: цифры и операции + - * /."""
from iski.chat.model import CharGPT, VOCAB, encode, decode
from iski.chat.dataset import parse_question, exact_answer, build_corpus

__all__ = ["CharGPT", "VOCAB", "encode", "decode", "parse_question", "exact_answer", "build_corpus"]
