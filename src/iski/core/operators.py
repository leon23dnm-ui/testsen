from pathlib import Path
from typing import Any

import yaml

from iski.core.delta import CHANNELS as ALLOWED_CHANNELS

VALID_CLOCKS = {"fast", "medium", "structural", "slow"}


def load_registry(path: str) -> list[Any]:
    """Загрузить YAML-реестр операторов."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return []
    if not isinstance(data, list):
        raise TypeError("registry YAML must contain a list of operator specs")
    return data


def validate_registry(specs: list[Any]) -> None:
    """Проверить корректность реестра операторов."""
    writers: dict[str, int] = {}

    for idx, spec in enumerate(specs):
        clock = spec.get("clock")
        assert clock in VALID_CLOCKS, f"invalid clock '{clock}' in spec {idx}"

        level = spec.get("level")
        assert isinstance(level, int) and 0 <= level <= 3, (
            f"invalid level {level} in spec {idx}"
        )

        for ch in spec.get("channels", []):
            assert ch in ALLOWED_CHANNELS, f"channel '{ch}' not allowed in spec {idx}"
            assert ch not in writers, (
                f"channel '{ch}' has multiple writers (spec {idx} and {writers[ch]})"
            )
            writers[ch] = idx
