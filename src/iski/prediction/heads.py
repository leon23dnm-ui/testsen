import torch
import torch.nn.functional as F
from torch import nn


class PredHead(nn.Module):
    """Предсказательная голова M0: enc(flat X) -> h; head(h) -> Xhat."""

    def __init__(self, N: int, K: int, H: int, lr: float = 0.01):
        super().__init__()
        self.N = N
        self.K = K
        self.NK = N * K
        self.H = H
        self.enc = nn.Linear(self.NK, H, dtype=torch.float64)
        self.head = nn.Linear(H, self.NK, dtype=torch.float64)
        self.optimizer = torch.optim.SGD(self.head.parameters(), lr=lr)

    def encode(self, X):
        x = torch.as_tensor(X, dtype=torch.float64).reshape(-1)
        return torch.tanh(self.enc(x))

    def predict(self, h):
        return self.head(h)

    def train_step(self, h_old, x_obs):
        h = torch.as_tensor(h_old, dtype=torch.float64)
        target = torch.as_tensor(x_obs, dtype=torch.float64).reshape(-1)

        self.optimizer.zero_grad()
        pred = self.predict(h)
        loss = F.mse_loss(pred, target)
        loss.backward()
        self.optimizer.step()
        return loss.item()
