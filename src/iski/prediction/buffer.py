class RingBufferH:
    """Кольцевой буфер истории h[t] для delayed credit."""

    def __init__(self, cap: int):
        self.cap = cap
        self._latest = 0
        self._data: dict[int, object] = {}

    def push(self, t: int, h) -> None:
        self._latest = t
        self._data[t] = h
        evict = t - self.cap
        if evict in self._data:
            del self._data[evict]

    def get(self, t: int):
        """Вернуть h[t] или None, если t вытеснен/не существует."""
        if t < self._latest - self.cap + 1 or t > self._latest:
            return None
        return self._data.get(t)
