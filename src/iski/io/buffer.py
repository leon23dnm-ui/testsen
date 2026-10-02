class InputBuffer:
    """Буфер входных envelope; pop_ready(t) возвращает готовые к t."""

    def __init__(self):
        self._items: list = []

    def push(self, env) -> None:
        self._items.append(env)

    def pop_ready(self, t: int):
        ready = [env for env in self._items if env.t_encode <= t]
        self._items = [env for env in self._items if env.t_encode > t]
        return ready
