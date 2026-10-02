import numpy as np

from iski.core.kernels import kernel_similarity


def test_kernel_identity_for_same_vector():
    E = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    k = kernel_similarity(E, E[0], sigma=1.0)
    assert k[0] == 1.0


def test_kernel_decreases_with_distance():
    E = np.array([[0.0, 0.0], [1.0, 0.0], [10.0, 0.0]])
    e = E[0]
    k = kernel_similarity(E, e, sigma=1.0)
    assert k[0] > k[1] > k[2]
