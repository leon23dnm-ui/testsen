import torch


def attention(sal, T_A: float):
    """Att_i = softmax(Sal_i / T_A, dim=0)."""
    sal_t = torch.as_tensor(sal, dtype=torch.float64)
    return torch.softmax(sal_t / T_A, dim=0)
