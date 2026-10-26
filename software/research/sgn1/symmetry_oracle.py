"""Independent Cartesian signed-axis reference, with no Quadray imports."""
from itertools import permutations, product

from .graph_oracle import reference_graph
from .literals import PORTS

BASIS = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))


def cartesian_action(node, axes, signs):
    return tuple(signs[i] * node[axes[i]] for i in range(3))


def catalogue():
    """Rows: (basis permutation, axis permutation, signs, orientation)."""
    rows = []
    for axes in permutations(range(3)):
        parity = sum(axes[i] > axes[j] for i in range(3) for j in range(i + 1, 3))
        for signs in product((-1, 1), repeat=3):
            if signs[0] * signs[1] * signs[2] != 1:
                continue
            sigma = tuple(BASIS.index(cartesian_action(v, axes, signs)) for v in BASIS)
            rows.append((sigma, axes, signs, (-1) ** parity))
    return tuple(sorted(rows))


def check_action(radius, sigma, observed_nodes, observed_ports):
    """Compare observations to Cartesian action; preserve first discrepancy."""
    rows = {row[0]: row for row in catalogue()}
    if type(sigma) is not tuple or any(type(i) is not int for i in sigma):
        raise AssertionError(('SYMMETRY_LABEL', sigma))
    if sigma not in rows:
        raise AssertionError(('SYMMETRY_LABEL', sigma))
    _, axes, signs, _ = rows[sigma]
    nodes = reference_graph(radius)[0]
    expected_nodes = tuple(cartesian_action(v, axes, signs) for v in nodes)
    if len(observed_nodes) != len(expected_nodes):
        raise AssertionError(('NODE_ACTION_LENGTH', len(observed_nodes), len(nodes)))
    for i, (observed, expected) in enumerate(zip(observed_nodes, expected_nodes)):
        if observed != expected:
            raise AssertionError(('NODE_ACTION', i, observed, expected))
    by_delta = {delta: pair for pair, delta in PORTS}
    expected_ports = tuple(by_delta[cartesian_action(delta, axes, signs)]
                           for _, delta in PORTS)
    if len(observed_ports) != len(expected_ports):
        raise AssertionError(('PORT_ACTION_LENGTH', len(observed_ports), len(PORTS)))
    for i, (observed, expected) in enumerate(zip(observed_ports, expected_ports)):
        if observed != expected:
            raise AssertionError(('PORT_ACTION', i, observed, expected))
