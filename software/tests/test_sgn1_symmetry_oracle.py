#!/usr/bin/env python3
"""Independent SGN tetrahedral correspondence; no routing/scheduling claims."""
import hashlib
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.sgn1.geometry import inverse_lift, quadray_image
from software.research.sgn1.graph_oracle import reference_graph
from software.research.sgn1.literals import PORTS
from software.research.sgn1.symmetry_action import permute_port, permute_quadray
from software.research.sgn1.symmetry_oracle import catalogue, cartesian_action, check_action

ROWS = catalogue()


def node_action(node, sigma):
    return quadray_image(permute_quadray(inverse_lift(node), sigma))


class SymmetryOracleTests(unittest.TestCase):
    def test_catalogue(self):
        self.assertEqual(tuple(r[0] for r in ROWS), tuple(permutations(range(4))))
        self.assertEqual(sum(r[3] == 1 for r in ROWS), 12)
        self.assertEqual(sum(r[3] == -1 for r in ROWS), 12)
        # Non-identity literal anchors fix old-to-new convention.
        self.assertEqual(node_action((0, 1, 1), (1, 0, 2, 3)), (0, -1, -1))
        self.assertEqual(permute_port((0, 2), (1, 2, 0, 3)), (1, 0))

    def test_node_edge_and_port_correspondence(self):
        for radius in (1, 2):
            nodes, adjacency = reference_graph(radius)
            by_node = {node: i for i, node in enumerate(nodes)}
            for sigma, axes, signs, _ in ROWS:
                with self.subTest(radius=radius, sigma=sigma):
                    mapped = tuple(node_action(v, sigma) for v in nodes)
                    ports = tuple(permute_port(pair, sigma) for pair, _ in PORTS)
                    check_action(radius, sigma, mapped, ports)
                    self.assertEqual(set(mapped), set(nodes))
                    self.assertEqual(len(set(ports)), 12)
                    for i, neighbours in enumerate(adjacency):
                        mapped_ids = {by_node[mapped[j]] for j in neighbours}
                        self.assertEqual(mapped_ids, set(adjacency[by_node[mapped[i]]]))
                    for pair, delta in PORTS:
                        target_delta = dict(PORTS)[permute_port(pair, sigma)]
                        self.assertEqual(target_delta, cartesian_action(delta, axes, signs))
                        self.assertEqual(permute_port(pair[::-1], sigma), permute_port(pair, sigma)[::-1])

    def test_all_compositions_and_inverses(self):
        nodes = reference_graph(1)[0] + reference_graph(2)[0]
        rows = {r[0]: r for r in ROWS}
        for sigma, axes, signs, _ in ROWS:
            inverse = tuple(sigma.index(i) for i in range(4))
            for node in nodes:
                self.assertEqual(node_action(node_action(node, sigma), inverse), node)
            for tau, t_axes, t_signs, _ in ROWS:
                combined = tuple(tau[sigma[i]] for i in range(4))
                _, c_axes, c_signs, _ = rows[combined]
                for node in nodes:
                    expected = cartesian_action(cartesian_action(node, axes, signs), t_axes, t_signs)
                    self.assertEqual(cartesian_action(node, c_axes, c_signs), expected)
                    self.assertEqual(node_action(node_action(node, sigma), tau), expected)
                    q = inverse_lift(node)
                    self.assertEqual(permute_quadray(permute_quadray(q, sigma), tau),
                                     permute_quadray(q, combined))
                for pair, _ in PORTS:
                    self.assertEqual(permute_port(permute_port(pair, sigma), tau),
                                     permute_port(pair, combined))

    def test_offsets_and_rejections(self):
        q = (2, -1, -1, 0)
        for sigma, _, _, _ in ROWS:
            shifted = tuple(v + 10**100 for v in q)
            result = permute_quadray(q, sigma)
            self.assertEqual(permute_quadray(shifted, sigma), tuple(v + 10**100 for v in result))
        for sigma in ((0, 0, 2, 3), (0, 1, 2, 4), (False, 1, 2, 3), '0123'):
            with self.assertRaises(ValueError):
                permute_quadray(q, sigma)
        with self.assertRaisesRegex(ValueError, 'INVALID_FCC_PARITY'):
            permute_quadray((1, 1, 0, 0), (0, 1, 2, 3))
        for port in ((0, 0), (-1, 0), (0, 4), (False, 1), (0,)):
            with self.assertRaises(ValueError):
                permute_port(port, (0, 1, 2, 3))

    def test_negative_controls(self):
        nodes = reference_graph(1)[0]
        sigma = (1, 2, 0, 3)
        mapped = tuple(node_action(v, sigma) for v in nodes)
        ports = tuple(permute_port(pair, sigma) for pair, _ in PORTS)
        check_action(1, sigma, mapped, ports)
        bad_nodes = ((99, 0, 0),) + mapped[1:]
        bad_ports = (ports[0][::-1],) + ports[1:]
        for label, ns, ps, reason in (
            (sigma, bad_nodes, ports, 'NODE_ACTION'),
            (sigma, mapped[:-1], ports, 'NODE_ACTION_LENGTH'),
            (sigma, mapped, bad_ports, 'PORT_ACTION'),
            (sigma, mapped, ports[:-1], 'PORT_ACTION_LENGTH'),
            ((0, 1, 2, 3), mapped, ports, 'NODE_ACTION'),
            ((0, 0, 2, 3), mapped, ports, 'SYMMETRY_LABEL'),
        ):
            with self.assertRaisesRegex(AssertionError, reason):
                check_action(1, label, ns, ps)


if __name__ == '__main__':
    # Stable semantic digest, independent of unittest timings and hash seed.
    payload = [(radius, sigma, tuple(node_action(v, sigma) for v in reference_graph(radius)[0]),
                tuple(permute_port(pair, sigma) for pair, _ in PORTS))
               for radius in (1, 2) for sigma, _, _, _ in ROWS]
    print('ACTION_SHA256=' + hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest(), flush=True)
    unittest.main()
