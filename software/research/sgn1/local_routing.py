"""Stateless FCC routing probe: local displacement and available ports only."""
from .geometry import integer_vector
from .literals import PORTS

DISPLACEMENTS = dict(PORTS)


def fcc_delta(value):
    delta = integer_vector(value, 3)
    if sum(delta) % 2:
        raise ValueError('INVALID_FCC_PARITY')
    return delta


def metric(value):
    dx, dy, dz = map(abs, fcc_delta(value))
    return max(dx, dy, dz, (dx + dy + dz) // 2)


def select_port(displacement, available):
    delta = fcc_delta(displacement)
    if type(available) not in (tuple, list):
        raise ValueError('PORT_CONTAINER_TYPE')
    pairs = tuple(integer_vector(pair, 2) for pair in available)
    if any(pair not in DISPLACEMENTS for pair in pairs):
        raise ValueError('INVALID_PORT')
    if len(set(pairs)) != len(pairs):
        raise ValueError('DUPLICATE_PORT')
    pairs = tuple(sorted(pairs))
    if delta == (0, 0, 0):
        return None
    before = metric(delta)
    for pair in pairs:
        remaining = tuple(a - b for a, b in zip(delta, DISPLACEMENTS[pair]))
        if metric(remaining) < before:
            return pair
    raise ValueError('ROUTE_STALL', delta, pairs)
