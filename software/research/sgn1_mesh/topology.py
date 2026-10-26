"""Candidate mesh links and local Manhattan routing, without global tables."""
from itertools import product

PORTS = ((-1, 0, 0), (0, -1, 0), (0, 0, -1),
         (0, 0, 1), (0, 1, 0), (1, 0, 0))
INDEX = {port: i for i, port in enumerate(PORTS)}


def topology():
    nodes = tuple(product(range(7), range(3), range(3)))
    ids, links = {node: i for i, node in enumerate(nodes)}, []
    for node in nodes:
        available = {}
        for port in PORTS:
            target = tuple(a + b for a, b in zip(node, port))
            if target in ids:
                reverse = tuple(-v for v in port)
                available[port] = ids[target], INDEX[reverse]
        links.append(available)
    return nodes, tuple(links)


def select_port(delta, available):
    if type(delta) not in (tuple, list) or len(delta) != 3 or any(type(v) is not int for v in delta):
        raise ValueError('DISPLACEMENT_DOMAIN')
    if type(available) not in (tuple, list):
        raise ValueError('PORT_DOMAIN')
    if any(type(p) is not tuple or len(p) != 3 or any(type(v) is not int for v in p)
           or p not in PORTS for p in available) or len(set(available)) != len(available):
        raise ValueError('PORT_DOMAIN')
    if not any(delta):
        return None
    before = sum(map(abs, delta))
    for port in sorted(available):
        if sum(abs(a - b) for a, b in zip(delta, port)) < before:
            return port
    raise ValueError('ROUTE_STALL', tuple(delta), tuple(sorted(available)))
