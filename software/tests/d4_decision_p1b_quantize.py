"""Independent exact bounded-D4 minimizers; reject ties rather than choose one."""

from itertools import product

from d4_canonical_exact import STATES


def unique_minimum(candidates):
    best = None
    winners = []
    for cost, point in candidates:
        if best is None or cost < best:
            best, winners = cost, [point]
        elif cost == best:
            winners.append(point)
    if len(winners) != 1:
        raise ValueError(f"nearest-D4 tie: {len(winners)} minima at distance {best}")
    return winners[0], best


def exhaustive(z):
    """Defining oracle: visit every one of the 3,281 candidates."""
    costs = tuple({q: (value - 16 * q) ** 2 for q in range(-4, 5)} for value in z)
    return unique_minimum((sum(costs[i][q[i]] for i in range(4)), q) for q in STATES)


def parity_oracle(z):
    """Independent separable search: all eight even coordinate-parity patterns."""
    minima = []
    for value in z:
        axis = []
        for parity in (0, 1):
            options = [(value - 16 * q) ** 2 for q in range(-4, 5) if q % 2 == parity]
            cost = min(options)
            axis.append((cost, tuple(q for q in range(-4, 5)
                                     if q % 2 == parity and (value - 16 * q) ** 2 == cost)))
        minima.append(axis)
    candidates = []
    for parities in product((0, 1), repeat=4):
        if sum(parities) % 2 == 0:
            chosen = [minima[i][parities[i]] for i in range(4)]
            candidates.extend((sum(c for c, _ in chosen), q)
                              for q in product(*(points for _, points in chosen)))
    return unique_minimum(candidates)


def negative_controls():
    # Halfway between (0,0,0,0) and (1,1,0,0); both defining oracles must reject.
    for oracle in (exhaustive, parity_oracle):
        try:
            oracle((8, 8, 0, 0))
        except ValueError:
            continue
        raise AssertionError("quantizer accepted a tied nearest point")
    return {"tie_oracles_rejected": 2}
