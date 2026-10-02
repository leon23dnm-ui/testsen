def forget_decision(
    w: float,
    forget_rho: float,
    imp: float,
    w_min: float,
    th_forget: float,
    th_I: float,
) -> str:
    """Решение о забывании: архивировать или сохранить."""
    if (w < w_min and imp < th_I) or (w < w_min and forget_rho > th_forget):
        return "archive"
    return "keep"
