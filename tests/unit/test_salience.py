import torch

from iski.attention.salience import salience


def test_salience_linear_combination():
    nov = torch.tensor([1.0, 0.5, 0.0], dtype=torch.float64)
    pe = torch.tensor([0.0, 1.0, 2.0], dtype=torch.float64)
    out = salience(nov, pe, lam_n=0.3, lam_e=0.7)
    expected = 0.3 * nov + 0.7 * pe
    assert torch.allclose(out, expected)
