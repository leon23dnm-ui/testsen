import torch

from iski.attention.attention import attention


def test_attention_sums_to_one():
    sal = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64)
    att = attention(sal, T_A=1.0)
    assert torch.allclose(att.sum(), torch.tensor(1.0, dtype=torch.float64), rtol=1e-5)


def test_attention_monotonic_with_salience():
    sal = torch.tensor([1.0, 4.0, 2.0], dtype=torch.float64)
    att = attention(sal, T_A=1.0)
    assert att[1] > att[2] > att[0]
