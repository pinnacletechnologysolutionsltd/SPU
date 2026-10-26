#!/usr/bin/env python3
"""Exhaustive bounded-graph local routing probe; no packet/tick simulation."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.sgn1.graph_oracle import reference_graph
from software.research.sgn1.literals import PORTS
from software.research.sgn1.local_routing import metric, select_port
from software.research.sgn1.routing_oracle import bfs_distances, check_distance, check_path


def available_ports(node, by_node):
    return tuple(pair for pair, delta in PORTS
                 if tuple(a + b for a, b in zip(node, delta)) in by_node)


def local_path(nodes, by_node, source, target):
    current, path = source, [source]
    while current != target:
        node = nodes[current]
        delta = tuple(a - b for a, b in zip(nodes[target], node))
        pair = select_port(delta, available_ports(node, by_node))
        following = tuple(a + b for a, b in zip(node, dict(PORTS)[pair]))
        current = by_node[following]
        path.append(current)
        if len(path) > len(nodes):
            raise AssertionError(('PATH_LIMIT', source, target, path))
    return tuple(path)


def qualify_profile(radius):
    nodes, adjacency = reference_graph(radius)
    by_node = {v: i for i, v in enumerate(nodes)}
    distances = bfs_distances(radius)
    paths, boundary_cases = [], 0
    for source, node in enumerate(nodes):
        ports = available_ports(node, by_node)
        for target, destination in enumerate(nodes):
            delta = tuple(a - b for a, b in zip(destination, node))
            check_distance(source, target, metric(delta), distances)
            selected = select_port(delta, ports)
            if source == target:
                if selected is not None:
                    raise AssertionError(('SELF_PORT', source, selected))
            else:
                if len(ports) < 12:
                    boundary_cases += 1
                if selected not in ports:
                    raise AssertionError(('ABSENT_PORT', source, target, selected))
                after = tuple(a - b for a, b in zip(delta, dict(PORTS)[selected]))
                if metric(after) >= metric(delta):
                    raise AssertionError(('NON_IMPROVING_PORT', source, target, selected))
            path = local_path(nodes, by_node, source, target)
            check_path(source, target, path, adjacency, distances)
            paths.append(path)
    return dict(radius=radius, nodes=len(nodes), ordered_pairs=len(paths),
                boundary_nonself_cases=boundary_cases, stalls=0,
                diameter=max(max(row) for row in distances), paths=paths)


def negative_cases():
    nodes, adjacency = reference_graph(1)
    distances = bfs_distances(1)
    # IDs 0,1 are adjacent; 0,6,1 is a legal but unnecessarily long path.
    return adjacency, distances, (
        (0, 1, (), 'MISSING_PATH'),
        (0, 1, (6, 1), 'SOURCE_MISMATCH'),
        (0, 1, (0, 6), 'DESTINATION_MISMATCH'),
        (0, 12, (0, 12), 'ILLEGAL_EDGE'),
        (0, 1, (0, 1, 0, 1), 'REPEATED_NODE'),
        (0, 1, (0, 6, 1), 'HOP_COUNT'),
        (0, 1, (0, True), 'INVALID_NODE_ID'),
        (False, 1, (0, 1), 'INVALID_ENDPOINT'),
    )


class RoutingOracleTests(unittest.TestCase):
    def test_all_pairs(self):
        for radius, cases, diameter in ((1, 169, 2), (2, 3969, 6)):
            report = qualify_profile(radius)
            self.assertEqual(report['ordered_pairs'], cases)
            self.assertEqual(report['diameter'], diameter)
            self.assertGreater(report['boundary_nonself_cases'], 0)

    def test_checker_rejects_faults(self):
        adjacency, distances, cases = negative_cases()
        for source, target, path, reason in cases:
            with self.assertRaisesRegex(AssertionError, reason):
                check_path(source, target, path, adjacency, distances)

    def test_stall_and_lexicographic_choice(self):
        ports = tuple(pair for pair, _ in PORTS)
        self.assertEqual(select_port((2, 0, 0), ports[::-1]), (0, 2))
        with self.assertRaisesRegex(ValueError, 'ROUTE_STALL'):
            select_port((2, 0, 0), ((1, 0),))
        with self.assertRaisesRegex(ValueError, 'ROUTE_STALL'):
            select_port((0, 1, 1), ())
        self.assertIsNone(select_port((0, 0, 0), ()))

    def test_input_rejection_and_exactness(self):
        for delta in ((1, 0, 0), (True, 1, 0), (0.0, 0, 0), (0, 0), '000'):
            with self.assertRaises(ValueError):
                metric(delta)
        for ports in (((0, 0),), ((0, 4),), ((False, 1),), ((0, 1), (0, 1)), None):
            with self.assertRaises(ValueError):
                select_port((0, 0, 0), ports)
        self.assertEqual(metric((10**100, 10**100, 0)), 10**100)
        # A max-coordinate-only metric is detectably wrong for this FCC delta.
        self.assertEqual(metric((2, 2, 2)), 3)
        nodes = reference_graph(2)[0]
        source, target = nodes.index((0, 0, 0)), nodes.index((2, 2, 2))
        with self.assertRaisesRegex(AssertionError, 'METRIC_DISTANCE'):
            check_distance(source, target, max(map(abs, (2, 2, 2))), bfs_distances(2))


if __name__ == '__main__':
    reports = [qualify_profile(radius) for radius in (1, 2)]
    digest = hashlib.sha256(json.dumps(reports, separators=(',', ':')).encode()).hexdigest()
    print('ROUTE_SHA256=' + digest, flush=True)
    unittest.main()
