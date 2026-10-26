"""Independent bounded FCC graph: literal nodes, pairwise squared distance.

No neighbour-generation, port mapping, Quadray conversion or router imports.
Node IDs and neighbour IDs are lexicographic Cartesian positions.
"""
from .literals import PROFILES


def reference_graph(radius):
    if type(radius) is not int or radius not in PROFILES:
        raise ValueError('UNSUPPORTED_PROFILE')
    nodes = PROFILES[radius]
    adjacency = tuple(
        tuple(j for j, other in enumerate(nodes)
              if sum((a - b) ** 2 for a, b in zip(node, other)) == 2)
        for node in nodes
    )
    return nodes, adjacency


def check_graph(radius, nodes, adjacency):
    """Check an observed graph; retain the first discrepancy in the exception."""
    expected_nodes, expected_adjacency = reference_graph(radius)
    if nodes != expected_nodes:
        raise AssertionError(('NODE_SET_OR_ORDER', nodes, expected_nodes))
    if len(adjacency) != len(nodes):
        raise AssertionError(('ADJACENCY_LENGTH', len(adjacency), len(nodes)))
    for node_id, (observed, expected) in enumerate(zip(adjacency, expected_adjacency)):
        if observed != expected:
            raise AssertionError(('ADJACENCY_MISMATCH', node_id, observed, expected))
