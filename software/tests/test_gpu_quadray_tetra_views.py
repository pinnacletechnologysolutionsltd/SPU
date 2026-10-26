#!/usr/bin/env python3
"""Exact Quadray-to-T1d tetrahedron views and independent pixel expectations."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval.device_model import pixel_decision as device_pixel_decision
from software.spu_gpu_eval.device_model import prepare_scene
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.quadray import make_permuted_demo_scene, permutation_sign
from software.spu_gpu_eval.reference import pixel_decision as ideal_pixel_decision
from software.spu_gpu_eval.scene import parse_scene_bytes, parse_scene_data


VIEWS = ROOT / "examples/gpu/golden_core_tetra_views"
REFERENCE = ROOT / "fixtures/golden_core_t1d_tetra_views_reference.json"
FACE_INDICES = ((0, 1, 2), (0, 3, 2))
COLORS = ((15, 2, 1), (1, 8, 15))
PERMUTATIONS = {
    "identity": (0, 1, 2, 3),
    "rotate_bcd": (0, 2, 3, 1),
    "reflect_bc": (0, 2, 1, 3),
}


def round_even(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    if 2 * remainder < value.denominator:
        return quotient
    if 2 * remainder > value.denominator:
        return quotient + 1
    return quotient if quotient % 2 == 0 else quotient + 1


def independent_projected_vertices(permutation: tuple[int, ...]) -> list[list[int]]:
    """Independent exact coordinate pipeline; does not call the scene compiler."""
    basis = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))
    # The component permutation acts on basis labels; its Cartesian image is
    # reconstructed from the explicit basis table, not the production mapper.
    mapped = [basis[permutation[source]] for source in range(4)]
    result = []
    for x, y, z in mapped:
        u = Fraction(x + 8 * y + 4 * z, 9)
        v = Fraction(8 * x + y - 4 * z, 9)
        d = Fraction(-4 * x + 4 * y - 7 * z, 9)
        px = round_even(Fraction(639, 2) + 80 * u)
        py = round_even(Fraction(479, 2) - 80 * v)
        pz = round_even(Fraction(32768) + 1000 * d)
        result.append([px, py, pz])
    return result


class QuadrayTetraT1dViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = json.loads(REFERENCE.read_text(encoding="utf-8"))

    def test_exact_transform_projection_packet_and_frozen_pixels(self) -> None:
        self.assertEqual(self.reference["vertex_labels"], ["A", "B", "C", "D"])
        self.assertEqual(self.reference["face_labels"], ["ABC", "ADC"])
        for expected in self.reference["views"]:
            name = expected["id"]
            permutation = PERMUTATIONS[name]
            self.assertEqual(expected["permutation"], list(permutation))
            self.assertEqual(expected["permutation_sign"], permutation_sign(permutation))
            self.assertEqual(expected["projected_vertices"],
                             independent_projected_vertices(permutation))

            raw = (VIEWS / f"{name}.json").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["scene_sha256"])
            scene = parse_scene_bytes(raw)
            self.assertEqual(scene, make_permuted_demo_scene(permutation))
            projected = expected["projected_vertices"]
            for triangle, face, color in zip(scene.triangles, FACE_INDICES, COLORS):
                self.assertEqual([[v.x, v.y, v.z] for v in triangle.vertices],
                                 [projected[index] for index in face])
                self.assertEqual(triangle.rgb, color)

            packet = compile_packet(scene)
            self.assertEqual(hashlib.sha256(packet).hexdigest(), expected["packet_sha256"])
            device_scene = prepare_scene(packet)
            for sample in expected["pixels"]:
                x, y = sample["x"], sample["y"]
                for decision in (ideal_pixel_decision(scene, x, y),
                                 device_pixel_decision(device_scene, x, y)):
                    self.assertEqual(decision["coverage"], sample["coverage"])
                    self.assertEqual(decision["winner"], sample["winner"])
                    self.assertEqual(decision["rgb"], sample["rgb"])

    def test_reflection_negative_control_changes_frozen_projection(self) -> None:
        baseline = json.loads((VIEWS / "identity.json").read_text(encoding="utf-8"))
        changed = copy.deepcopy(baseline)
        changed["triangles"][0]["vertices"][0][0] += 1
        broken = parse_scene_data(changed)
        frozen_x = self.reference["views"][0]["projected_vertices"][0][0]
        self.assertNotEqual(broken.triangles[0].vertices[0].x, frozen_x)


if __name__ == "__main__":
    unittest.main(verbosity=2)
