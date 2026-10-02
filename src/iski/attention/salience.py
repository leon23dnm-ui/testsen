import torch


def salience(nov, pe, lam_n: float, lam_e: float):
    """Sal_i = lambda_N Nov_i + lambda_E PE_i.

    Для M0 GR=Int=0 (T07).
    """
    nov_t = torch.as_tensor(nov, dtype=torch.float64)
    pe_t = torch.as_tensor(pe, dtype=torch.float64)
    return lam_n * nov_t + lam_e * pe_t
