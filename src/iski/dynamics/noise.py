import torch


def make_rng(seed: int) -> torch.Generator:
    """Создать seeded torch Generator."""
    gen = torch.Generator()
    gen.manual_seed(seed)
    return gen


def xi(rng: torch.Generator, shape, xi_max: float) -> torch.Tensor:
    """Равномерный шум в [-xi_max, xi_max]."""
    raw = torch.rand(shape, generator=rng, dtype=torch.float64)
    return (raw * 2.0 - 1.0) * xi_max
