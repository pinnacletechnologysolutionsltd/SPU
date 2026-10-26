"""Simulator topology generation; oracle adjacency remains independent."""
from itertools import product

from .literals import PORTS


def topology(radius):
    if type(radius) is not int or radius not in (1, 2):
        raise ValueError('UNSUPPORTED_PROFILE')
    nodes = tuple(v for v in product(range(-radius, radius + 1), repeat=3) if sum(v) % 2 == 0)
    ids = {v: i for i, v in enumerate(nodes)}
    indices = {pair: i for i, (pair, _) in enumerate(PORTS)}
    links = []
    for node in nodes:
        neighbours = {}
        for pair, delta in PORTS:
            coordinate = tuple(a + b for a, b in zip(node, delta))
            if coordinate in ids:
                neighbours[pair] = (ids[coordinate], indices[pair[::-1]])
        links.append(neighbours)
    return nodes, tuple(links)
