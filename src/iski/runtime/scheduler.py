class Clocks:
    """Часы pipeline: fast/medium/structural/slow."""

    def __init__(self, m: int, s: int, q: int):
        assert 1 <= m <= s <= q, "clock constraint violated: 1 <= m <= s <= q"
        self.m = m
        self.s = s
        self.q = q

    def active(self, t: int, clock: str) -> bool:
        if clock == "fast":
            return True
        if clock == "medium":
            return t % self.m == 0
        if clock == "structural":
            return t % self.s == 0
        if clock == "slow":
            return t % self.q == 0
        raise ValueError(f"unknown clock '{clock}'")
