import copy
from typing import Any


def export_snapshot(state: Any, metrics_cache: Any) -> dict:
    """Создать параллельную Gamma-проекцию Omega_t.

    Все поля — клоны одного и того же Omega_t; после фазы 0 Gamma считается
    frozen и не должна изменяться.
    """
    w_eff = (state.graph.w_plus - state.graph.w_minus).copy()

    return {
        "X": state.X.copy(),
        "E": state.E.copy(),
        "W_eff": w_eff,
        "S": state.S.copy(),
        "metrics_cache": copy.deepcopy(metrics_cache),
        "frozen": True,
    }
