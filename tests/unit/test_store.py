import numpy as np

from iski.memory.item import MemoryItem
from iski.memory.store import MemoryStore


def test_empty_store_projection_is_zero():
    store = MemoryStore([], m_max=5)
    E = np.eye(3, dtype=float)
    F = store.projection(E, sigma=1.0, K=2)
    assert F.shape == (3, 2)
    assert np.allclose(F, 0.0)


def test_store_projection_shape_and_status_filter():
    items = [
        MemoryItem(
            e=np.array([1.0, 0.0, 0.0]),
            x=np.array([1.0, 2.0]),
            rho=np.array([0.0, 0.0, 0.0, 0.0, 1.0]),
            status=0,
        ),
        MemoryItem(
            e=np.array([0.0, 1.0, 0.0]),
            x=np.array([3.0, 4.0]),
            rho=np.array([0.0, 0.0, 0.0, 0.0, 2.0]),
            status=1,
        ),
    ]
    store = MemoryStore(items, m_max=5)
    E = np.eye(3, dtype=float)
    F = store.projection(E, sigma=1.0, K=2)
    assert F.shape == (3, 2)
    assert not np.allclose(F, 0.0)
