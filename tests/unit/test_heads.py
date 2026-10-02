import torch

from iski.prediction.heads import PredHead


def test_head_encode_predict_shapes():
    N, K, H = 2, 3, 4
    model = PredHead(N, K, H)
    X = torch.randn(N, K, dtype=torch.float64)
    h = model.encode(X)
    assert h.shape == (H,)
    xhat = model.predict(h)
    assert xhat.shape == (N * K,)


def test_train_step_loss_decreases():
    N, K, H = 2, 2, 8
    model = PredHead(N, K, H, lr=0.05)
    h_old = torch.randn(H, dtype=torch.float64)
    x_obs = torch.randn(N * K, dtype=torch.float64)

    losses = [model.train_step(h_old, x_obs) for _ in range(20)]
    assert all(losses[i] <= losses[i - 1] + 1e-12 for i in range(1, len(losses)))
