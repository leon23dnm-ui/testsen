import torch

from iski.dynamics.update import field_update


def test_field_update_decay_with_zero_input():
    X = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float64)
    I_src = torch.zeros_like(X)
    L = torch.zeros((2, 2), dtype=torch.float64)
    xi = torch.zeros_like(X)

    new = field_update(X, I_src, Lam=0.1, kappa=0.0, L=L, xi=xi)
    expected = X * 0.9
    assert torch.allclose(new, expected)
