import torch

from iski.dynamics.noise import make_rng, xi


def test_noise_bounded_and_seeded():
    rng1 = make_rng(42)
    noise1 = xi(rng1, (1000,), 0.1)

    assert torch.max(torch.abs(noise1)) <= 0.1

    rng2 = make_rng(42)
    noise2 = xi(rng2, (1000,), 0.1)
    assert torch.equal(noise1, noise2)
