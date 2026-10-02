from iski.memory.item import MemoryItem
from iski.memory.maintenance import archive_sweep


def test_archive_sweep_respects_status_and_age():
    items = [
        MemoryItem(e=None, x=None, rho=None, status=1, last_access=0),  # старый архив
        MemoryItem(
            e=None, x=None, rho=None, status=0, last_access=0
        ),  # активный старый
        MemoryItem(
            e=None, x=None, rho=None, status=1, last_access=95
        ),  # архив недавний
    ]
    result = archive_sweep(items, tick=100, T_archive=10)
    assert 0 in result
    assert 1 not in result
    assert 2 not in result
