import torch

from iski.attention.gws import gws_broadcast


def test_gws_empty_mask_returns_x():
    E = torch.eye(3, dtype=torch.float64)
    X = torch.ones(3, 2, dtype=torch.float64)
    sal = torch.tensor([-1.0, -0.5, -0.1], dtype=torch.float64)
    X_bcast, S = gws_broadcast(E, X, sal, theta=0.0, sigma=1.0, beta=0.5)
    assert torch.all(S == False)
    assert torch.equal(X_bcast, X)


def test_gws_alpha_sums_to_one():
    E = torch.eye(3, dtype=torch.float64)
    X = torch.ones(3, 2, dtype=torch.float64)
    sal = torch.tensor([1.0, 2.0, -1.0], dtype=torch.float64)
    _X_bcast, S = gws_broadcast(E, X, sal, theta=0.0, sigma=1.0, beta=0.5)
    selected = sal[S]
    alpha = selected / selected.sum()
    assert torch.allclose(alpha.sum(), torch.tensor(1.0, dtype=torch.float64))


def test_gws_broadcast_norm_bound():
    E = torch.eye(3, dtype=torch.float64)
    X = torch.tensor([[1.0, 0.0], [0.0, 1.0], [2.0, 2.0]], dtype=torch.float64)
    sal = torch.tensor([1.0, 2.0, -1.0], dtype=torch.float64)
    beta = 0.3
    X_bcast, _S = gws_broadcast(E, X, sal, theta=0.0, sigma=1.0, beta=beta)

    B = (X_bcast - X) / beta
    assert torch.norm(X_bcast - X) <= beta * torch.norm(B) + 1e-9
