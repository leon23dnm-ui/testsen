import numpy as np

from iski.memory.item import MemoryItem


def test_item_w_is_rho_4():
    rho = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    item = MemoryItem(e=np.zeros(3), x=np.zeros(2), rho=rho)
    assert item.w == 0.5


def test_item_clone_is_independent():
    rho = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    item = MemoryItem(
        e=np.array([1.0, 2.0]),
        x=np.array([3.0, 4.0]),
        rho=rho,
    )
    cloned = item.clone()
    item.rho[4] = 99.0
    item.e[0] = -1.0
    assert cloned.w == 0.5
    assert cloned.e[0] == 1.0
