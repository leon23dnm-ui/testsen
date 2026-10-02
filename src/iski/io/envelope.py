from dataclasses import dataclass


@dataclass
class Envelope:
    """Протокол внешнего payload с provenance."""

    payload: str
    source_id: str
    t_capture: int
    t_encode: int
    confidence: float
    metadata: dict
