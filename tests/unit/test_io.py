import numpy as np

from iski.encoders.hash_text import encode_text
from iski.io.buffer import InputBuffer


def test_pop_ready_empty_buffer():
    buf = InputBuffer()
    assert buf.pop_ready(100) == []


def test_encoder_deterministic():
    e1 = encode_text("hello", D=8, seed=123)
    e2 = encode_text("hello", D=8, seed=123)
    assert np.allclose(e1, e2)


def test_encoder_norm_one():
    e = encode_text("test", D=8, seed=42)
    assert np.isclose(np.linalg.norm(e), 1.0)
