#!/usr/bin/env python3
"""SGN-1 first increment: reference geometry only, no packet simulation."""
import json
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.sgn1.geometry import inverse_lift, quadray_image
from software.research.sgn1.graph_oracle import check_graph, reference_graph
from software.research.sgn1.literals import PORTS

PLAN = json.loads((ROOT / 'spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json').read_text())


class GeometryOracleTests(unittest.TestCase):
    def test_literal_domain_fixtures(self):
        for row in PLAN['domain_fixtures']:
            with self.subTest(row=row['id']):
                if row['expected_reason'] == 'SUCCESS':
                    self.assertEqual(quadray_image(row['input']), tuple(row['expected_image']))
                    self.assertEqual(quadray_image(tuple(row['input'])), tuple(row['expected_image']))
                else:
                    with self.assertRaisesRegex(ValueError, '^' + row['expected_reason'] + '$'):
                        quadray_image(row['input'])

    def test_strict_types_and_precedence(self):
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        for value, reason in ((None, 'CONTAINER_TYPE'),
                              (ListSubclass([0] * 4), 'CONTAINER_TYPE'),
                              ([IntSubclass(0)] * 4, 'COEFFICIENT_TYPE'),
                              ([True], 'TUPLE_LENGTH')):
            with self.assertRaisesRegex(ValueError, '^' + reason + '$'):
                quadray_image(value)

    def test_domain_against_unscaled_cartesian_image(self):
        basis = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))
        for q in product(range(-2, 3), repeat=4):
            d = tuple(sum(q[i] * basis[i][axis] for i in range(4)) for axis in range(3))
            valid = all(v % 2 == 0 for v in d) and sum(v // 2 for v in d) % 2 == 0
            if valid:
                self.assertEqual(quadray_image(q), tuple(v // 2 for v in d))
            else:
                with self.assertRaisesRegex(ValueError, '^INVALID_FCC_PARITY$'):
                    quadray_image(q)

    def test_graph_profiles_and_boundaries(self):
        for radius, size, edge_count in ((1, 13, 36), (2, 63, 240)):
            nodes, adjacency = reference_graph(radius)
            cartesian = tuple(v for v in product(range(-radius, radius + 1), repeat=3)
                              if sum(v) % 2 == 0)
            self.assertEqual(nodes, cartesian)
            self.assertEqual(len(nodes), size)
            self.assertEqual(sum(map(len, adjacency)), 2 * edge_count)
            self.assertEqual(len(adjacency[nodes.index((0, 0, 0))]), 12)
            # Corner degree differs from the interior: no wrapped neighbours.
            corner = (-1, -1, 0) if radius == 1 else (-2, -2, -2)
            self.assertEqual(len(adjacency[nodes.index(corner)]), 5 if radius == 1 else 3)
            for i, neighbours in enumerate(adjacency):
                self.assertNotIn(i, neighbours)
                self.assertEqual(neighbours, tuple(sorted(set(neighbours))))
                for j in neighbours:
                    self.assertIn(i, adjacency[j])
            seen, pending = {0}, [0]
            while pending:
                for j in adjacency[pending.pop()]:
                    if j not in seen:
                        seen.add(j)
                        pending.append(j)
            self.assertEqual(len(seen), size)

    def test_lift_and_common_offsets(self):
        for radius in (1, 2):
            for node in reference_graph(radius)[0]:
                q = inverse_lift(node)
                self.assertEqual(sum(q), 0)
                for offset in (-10**100, -1, 0, 1, 10**100):
                    self.assertEqual(quadray_image(tuple(v + offset for v in q)), node)
        for node in ((1, 0, 0), (False, 0, 0), (0.0, 0, 0)):
            with self.assertRaises(ValueError):
                inverse_lift(node)

    def test_ports_against_prepared_literals(self):
        self.assertEqual(PORTS, tuple((tuple(r['pair']), tuple(r['delta']))
                                     for r in PLAN['port_fixtures']))
        ports = dict(PORTS)
        self.assertEqual(len(set(ports.values())), 12)
        for (i, j), delta in PORTS:
            q = tuple(int(k == i) - int(k == j) for k in range(4))
            self.assertEqual(quadray_image(q), delta)
            self.assertEqual(ports[j, i], tuple(-v for v in delta))

    def test_graph_checker_negative_controls(self):
        nodes, adjacency = reference_graph(1)
        check_graph(1, nodes, adjacency)
        with self.assertRaisesRegex(AssertionError, 'NODE_SET_OR_ORDER'):
            check_graph(1, nodes[::-1], adjacency)
        with self.assertRaisesRegex(AssertionError, 'ADJACENCY_LENGTH'):
            check_graph(1, nodes, adjacency[:-1])
        for first in (adjacency[0][1:], adjacency[0] + (0,), adjacency[0][::-1]):
            with self.assertRaisesRegex(AssertionError, 'ADJACENCY_MISMATCH'):
                check_graph(1, nodes, (first,) + adjacency[1:])
        for radius in (True, 0, 3, '1'):
            with self.assertRaisesRegex(ValueError, '^UNSUPPORTED_PROFILE$'):
                reference_graph(radius)


if __name__ == '__main__':
    unittest.main()
