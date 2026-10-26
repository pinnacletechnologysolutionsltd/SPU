"""Independent BFS distances and observed-path checker, with no metric import."""
from collections import deque

from .graph_oracle import reference_graph


def bfs_distances(radius):
    nodes, adjacency = reference_graph(radius)
    rows = []
    for source in range(len(nodes)):
        distances = [None] * len(nodes)
        distances[source] = 0
        pending = deque([source])
        while pending:
            current = pending.popleft()
            for neighbour in adjacency[current]:
                if distances[neighbour] is None:
                    distances[neighbour] = distances[current] + 1
                    pending.append(neighbour)
        rows.append(tuple(distances))
    return tuple(rows)


def check_distance(source, target, observed, distances):
    expected = distances[source][target]
    if type(observed) is not int or observed != expected:
        raise AssertionError(('METRIC_DISTANCE', source, target, observed, expected))


def check_path(source, target, path, adjacency, distances):
    """Validate against supplied independent BFS/graph, retaining first fault."""
    size = len(adjacency)
    if any(type(i) is not int or not 0 <= i < size for i in (source, target)):
        raise AssertionError(('INVALID_ENDPOINT', source, target))
    if type(path) not in (list, tuple) or not path:
        raise AssertionError(('MISSING_PATH', source, target, path))
    if any(type(i) is not int or not 0 <= i < size for i in path):
        raise AssertionError(('INVALID_NODE_ID', path))
    if path[0] != source:
        raise AssertionError(('SOURCE_MISMATCH', source, path))
    if path[-1] != target:
        raise AssertionError(('DESTINATION_MISMATCH', target, path))
    for a, b in zip(path, path[1:]):
        if b not in adjacency[a]:
            raise AssertionError(('ILLEGAL_EDGE', a, b, path))
    if len(set(path)) != len(path):
        raise AssertionError(('REPEATED_NODE', path))
    expected = distances[source][target]
    if expected is None or len(path) - 1 != expected:
        raise AssertionError(('HOP_COUNT', len(path) - 1, expected, path))
