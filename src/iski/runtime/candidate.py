from iski.core.delta import Delta


def assemble(state, deltas):
    """Собрать кандидата Omega^cand = Omega_t (+) Sum Delta активных часов."""
    merged = Delta()
    for d in deltas:
        merged = merged.merge(d)

    cand = state.clone_for_candidate()
    cand.apply_delta(merged)
    return cand
