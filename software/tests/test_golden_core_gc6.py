#!/usr/bin/env python3
"""GC-6 exact operator rank, inverse, and paired-state reversibility checks."""

import json
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from golden_core.dynamics import state_sha256
from golden_core.exact import ONE, Q5, ZERO
from golden_core.linear import apply, inverse, matmul, nullspace, rref
from golden_core.oriented_edge_turns import OrientedEdgeTurns
from golden_core.symmetry import icosahedral_symmetries

FIXTURE_PATH = ROOT / "fixtures/golden_core_gc6_reversibility.json"
FIXTURE_BYTES = FIXTURE_PATH.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)
FIXTURE_SHA256 = "41675726b6bd017c17dcc4d699fb06c4119342977546942daee4a9b1e4e616db"
PROFILES = {"equal": (ONE, ONE), "signed": (Q5(3, 1), Q5(1, -1))}
SIZE = 60


def zero_vector():
    return (ZERO,) * SIZE


def basis(index):
    return tuple(ONE if i == index else ZERO for i in range(SIZE))


def operator_matrix(turns, left_weight, right_weight):
    rows = [[ZERO for _ in range(SIZE)] for _ in range(SIZE)]
    for source in range(SIZE):
        rows[turns.left_image[source]][source] += left_weight
        rows[turns.right_image[source]][source] += right_weight
    return tuple(tuple(row) for row in rows)


def basis_operator_image(turns, left_weight, right_weight, edge):
    result = [ZERO] * SIZE
    result[turns.left_image[edge]] += left_weight
    result[turns.right_image[edge]] += right_weight
    return tuple(result)


def identity(size):
    return tuple(tuple(ONE if i == j else ZERO for j in range(size))
                 for i in range(size))


def q5_power(value, exponent):
    result = ONE
    for _ in range(exponent):
        result *= value
    return result


def relative_cycles(turns):
    inverse_left = [0] * SIZE
    for source, target in enumerate(turns.left_image):
        inverse_left[target] = source
    relative = tuple(inverse_left[turns.right_image[source]] for source in range(SIZE))
    cycles = []
    visited = set()
    for start in range(SIZE):
        if start in visited:
            continue
        cycle, current = [], start
        while current not in visited:
            visited.add(current)
            cycle.append(current)
            current = relative[current]
        if current != start:
            raise AssertionError("relative turn map is not a permutation cycle cover")
        cycles.append(tuple(cycle))
    return tuple(cycles)


def push(state, edge_image):
    result = [ZERO] * SIZE
    for source, target in enumerate(edge_image):
        result[target] = state[source]
    return tuple(result)


def edge_image(turns, symmetry):
    index = {edge: i for i, edge in enumerate(turns.directed_edges)}
    return tuple(index[(symmetry.vertex_image[u], symmetry.vertex_image[v])]
                 for u, v in turns.directed_edges)


def paired_forward(turns, left, right, state):
    x, y = state
    fx = turns.weighted(x, left, right)
    return tuple(a - b for a, b in zip(fx, y)), x


def paired_inverse(turns, left, right, state):
    u, v = state
    fv = turns.weighted(v, left, right)
    return v, tuple(a - b for a, b in zip(fv, u))


class GoldenCoreGc6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.turns = OrientedEdgeTurns.build()
        cls.symmetries = icosahedral_symmetries()
        cls.cycles = relative_cycles(cls.turns)

    def test_frozen_fixture_and_exact_rank_inverse_or_kernel(self):
        self.assertEqual(hashlib.sha256(FIXTURE_BYTES).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(FIXTURE["steps"], {
            "directed_edge_dimension": SIZE,
            "paired_state_dimension": 2 * SIZE,
        })
        self.assertEqual(FIXTURE["relative_permutation_cycle_lengths"],
                         sorted(len(cycle) for cycle in self.cycles))
        actual = {}
        for name, (left, right) in PROFILES.items():
            matrix = operator_matrix(self.turns, left, right)
            reduced, pivots = rref(matrix)
            kernel = nullspace(matrix)
            rank = len(pivots)
            cycle_rank = sum(
                len(cycle) if q5_power(left, len(cycle)) -
                q5_power(-right, len(cycle)) != ZERO else len(cycle) - 1
                for cycle in self.cycles)
            self.assertEqual(rank, cycle_rank)
            self.assertEqual(len(kernel), SIZE - rank)
            actual[name] = {"rank": rank, "nullity": len(kernel)}
            if rank == SIZE:
                inv = inverse(matrix)
                self.assertEqual(matmul(matrix, inv), identity(SIZE))
                self.assertEqual(matmul(inv, matrix), identity(SIZE))
                actual[name]["inverse_sha256"] = self._matrix_hash(inv)
            else:
                for vector in kernel:
                    self.assertNotEqual(vector, zero_vector())
                    self.assertEqual(apply(matrix, vector), zero_vector())
                actual[name]["kernel_basis_sha256"] = [
                    self._vector_hash(vector) for vector in kernel]
        self.assertEqual(actual, FIXTURE["operators"])

    def test_paired_rule_inverse_on_every_basis_vector(self):
        paired_basis = [(basis(i), zero_vector()) for i in range(SIZE)] + \
                       [(zero_vector(), basis(i)) for i in range(SIZE)]
        for left, right in PROFILES.values():
            for vector in paired_basis:
                self.assertEqual(paired_inverse(
                    self.turns, left, right,
                    paired_forward(self.turns, left, right, vector)), vector)
                self.assertEqual(paired_forward(
                    self.turns, left, right,
                    paired_inverse(self.turns, left, right, vector)), vector)

    def test_paired_rule_mirror_covariance_on_all_maps_and_basis_states(self):
        self.assertEqual(len(self.symmetries), 120)
        for symmetry in self.symmetries:
            image = edge_image(self.turns, symmetry)
            for left, right in PROFILES.values():
                mirror_left, mirror_right = ((right, left) if symmetry.determinant < 0
                                              else (left, right))
                # For (e_i,0), the paired law yields (F e_i,e_i). Check
                # transport of both components and the mirrored first block.
                for edge in range(SIZE):
                    original_first = basis_operator_image(self.turns, left, right, edge)
                    transported_first = push(original_first, image)
                    transported_edge = image[edge]
                    mirrored_first = basis_operator_image(
                        self.turns, mirror_left, mirror_right, transported_edge)
                    self.assertEqual(transported_first, mirrored_first)
                    self.assertEqual(push(basis(edge), image), basis(transported_edge))
                    # For (0,e_i), J(0,e_i)=(-e_i,0); parity commutes with
                    # negation, so this block is checked without reapplying F.
                    negative_basis = tuple(-value for value in basis(edge))
                    self.assertEqual(push(negative_basis, image),
                                     tuple(-value for value in push(basis(edge), image)))

    @staticmethod
    def _vector_hash(vector):
        return state_sha256(vector)

    @classmethod
    def _matrix_hash(cls, matrix):
        return state_sha256(tuple(value for row in matrix for value in row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
