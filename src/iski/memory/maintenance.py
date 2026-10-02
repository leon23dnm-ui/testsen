def archive_sweep(items, tick: int, T_archive: int):
    """Вернуть индексы элементов, готовых к физическому удалению из архива."""
    return [
        i
        for i, item in enumerate(items)
        if item.status == 1 and (tick - item.last_access) > T_archive
    ]
