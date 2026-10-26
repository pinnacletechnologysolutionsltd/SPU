"""Independent mesh graph/BFS from frozen literal coordinate labels, not ports."""
from collections import deque
from functools import lru_cache

from .reference import plan


@lru_cache(maxsize=1)
def oracle_data():
    baseline = plan()['mesh_baseline']
    if baseline['dimensions'] != [7, 3, 3] or baseline['nodes'] != 63:
        raise AssertionError(('MESH_PROFILE',))
    mapping = baseline['endpoint_mapping']
    if [row['id'] for row in mapping] != list(range(63)):
        raise AssertionError(('ENDPOINT_MAPPING',))
    nodes = tuple(tuple(row['mesh']) for row in mapping)
    adjacency = tuple(tuple(j for j, other in enumerate(nodes)
                            if sum(abs(a - b) for a, b in zip(node, other)) == 1)
                      for node in nodes)
    distances = []
    for source in range(63):
        row, pending = [None] * 63, deque([source])
        row[source] = 0
        while pending:
            current = pending.popleft()
            for neighbour in adjacency[current]:
                if row[neighbour] is None:
                    row[neighbour] = row[current] + 1
                    pending.append(neighbour)
        distances.append(tuple(row))
    return nodes, adjacency, tuple(distances)
