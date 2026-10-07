#!/usr/bin/env python3
"""S1 scene compiler, exact reference, and deterministic preview checks."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval.packet import compile_packet, wire_edges
from software.spu_gpu_eval.preview import (
    MODULE_SOURCES,
    PROFILE_SOURCES,
    build_artifacts,
    write_preview,
)
from software.spu_gpu_eval.reference import pixel_decision
from software.spu_gpu_eval.scene import SceneError, parse_scene_bytes, parse_scene_data


EXAMPLE = ROOT / "examples/gpu/t1d_two_triangle.json"
WIRE_FIXTURE = ROOT / "fixtures/gpu_t1d_scene_wire_64b.bin"
REFERENCE_FIXTURE = ROOT / "fixtures/gpu_t1d_scene_reference.json"
OUT_BASE = ROOT / "build/gpu_evaluation"
EXPECTED_PACKET_SHA256 = "aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee"


class T1dSceneCompilerS1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = EXAMPLE.read_bytes()
        cls.data = json.loads(cls.raw)
        cls.scene = parse_scene_bytes(cls.raw)

    def _rejected_without_output(self, mutate) -> None:
        data = copy.deepcopy(self.data)
        mutate(data)
        name = f".s1_rejected_{len(list(OUT_BASE.glob('.s1_rejected_*')))}"
        target = OUT_BASE / name
        self.assertFalse(target.exists())
        with tempfile.TemporaryDirectory(prefix="gpu_s1_invalid_") as temp:
            source = Path(temp) / "invalid.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises((SceneError, ValueError)):
                write_preview(source, target)
        self.assertFalse(target.exists(), f"rejected input created {target}")

    def test_baseline_packet_and_six_reference_samples(self) -> None:
        packet = compile_packet(self.scene)
        self.assertEqual(packet, WIRE_FIXTURE.read_bytes())
        self.assertEqual(len(packet), 64)
        self.assertEqual(hashlib.sha256(packet).hexdigest(), EXPECTED_PACKET_SHA256)

        frozen = json.loads(REFERENCE_FIXTURE.read_text(encoding="utf-8"))
        for expected in frozen["diagnostic_pixels"]:
            actual = pixel_decision(self.scene, expected["x"], expected["y"])
            self.assertEqual(actual["coverage"], expected["coverage"])
            self.assertEqual(actual["rgb"], expected["rgb"])
            if expected["coverage"] == "background":
                self.assertIsNone(actual["winner"])
            elif expected["coverage"] != "overlap":
                self.assertEqual(actual["winner"], 0 if expected["coverage"] == "triangle0" else 1)
            else:
                near = expected["near"]
                self.assertEqual(actual["winner"], 1 if near == "triangle1" else 0)
                if near == "tie_triangle0":
                    self.assertEqual(actual["depths"][0]["numerator"] * actual["depths"][1]["denominator"],
                                     actual["depths"][1]["numerator"] * actual["depths"][0]["denominator"])

        edge = pixel_decision(self.scene, 320, 0)
        self.assertEqual(edge["coverage"], "overlap")
        self.assertEqual(edge["covered_by"], [0, 1])
        self.assertEqual(edge["winner"], 0)
        self.assertEqual(edge["depths"][0]["numerator"] * edge["depths"][1]["denominator"],
                         edge["depths"][1]["numerator"] * edge["depths"][0]["denominator"])

    def test_vertex_edit_changes_packet_and_coverage(self) -> None:
        changed_data = copy.deepcopy(self.data)
        changed_data["triangles"][0]["vertices"][2] = [120, 240, 700]
        changed = parse_scene_data(changed_data)
        self.assertNotEqual(compile_packet(changed), compile_packet(self.scene))
        before = pixel_decision(self.scene, 100, 300)
        after = pixel_decision(changed, 100, 300)
        self.assertEqual(before["rgb"], [15, 0, 0])
        self.assertEqual(after["coverage"], "background")
        self.assertEqual(after["rgb"], [0, 0, 0])
        changed_artifacts = build_artifacts(json.dumps(changed_data).encode("utf-8"), changed)
        changed_decisions = json.loads(changed_artifacts["pixel_decisions.json"])
        edited_sample = next(
            sample for sample in changed_decisions["samples"]
            if sample["actual_scene_decision"]["x"] == 100
            and sample["actual_scene_decision"]["y"] == 300
        )
        self.assertEqual(edited_sample["baseline_fixture_expectation"]["rgb"], [15, 0, 0])
        self.assertEqual(edited_sample["actual_scene_decision"]["rgb"], [0, 0, 0])
        self.assertEqual(
            changed_decisions["expectation_scope"],
            "frozen baseline fixture; actual values describe the input scene",
        )

    def test_reversed_winding_keeps_positive_packet_interiors(self) -> None:
        reversed_data = copy.deepcopy(self.data)
        for triangle in reversed_data["triangles"]:
            vertices = triangle["vertices"]
            triangle["vertices"] = [vertices[0], vertices[2], vertices[1]]
        reversed_scene = parse_scene_data(reversed_data)
        for triangle in reversed_scene.triangles:
            edges = wire_edges(triangle)
            opposite = (triangle.vertices[2], triangle.vertices[0], triangle.vertices[1])
            for (a, b, c), point in zip(edges, opposite):
                self.assertGreater(a * point.x + b * point.y + c, 0)
        for x, y in ((100, 300), (200, 100), (320, 100), (400, 100), (540, 300)):
            original = pixel_decision(self.scene, x, y)
            reversed_decision = pixel_decision(reversed_scene, x, y)
            self.assertEqual(reversed_decision["coverage"], original["coverage"])
            self.assertEqual(reversed_decision["winner"], original["winner"])
            self.assertEqual(reversed_decision["rgb"], original["rgb"])

    def test_invalid_inputs_are_rejected_before_output_creation(self) -> None:
        invalid_cases = []
        invalid_cases.append(lambda d: d["triangles"][0]["vertices"].__setitem__(2, [600, 0, 3600]))
        invalid_cases.append(lambda d: d["triangles"][0]["vertices"][0].__setitem__(0, 640))
        invalid_cases.append(lambda d: d["triangles"][0]["vertices"][0].__setitem__(1, 480))
        invalid_cases.append(lambda d: d["triangles"][0]["vertices"][0].__setitem__(2, 65536))
        invalid_cases.append(lambda d: d["triangles"][0]["rgb"].__setitem__(0, 16))
        invalid_cases.extend((
            lambda d: d.__setitem__("width", 639), lambda d: d.__setitem__("width", 641),
            lambda d: d.__setitem__("height", 479), lambda d: d.__setitem__("height", 481),
            lambda d: d.__setitem__("width", True), lambda d: d.__setitem__("height", False),
            lambda d: d.__setitem__("width", 640.0), lambda d: d.__setitem__("height", 480.0),
            lambda d: d["triangles"][0]["vertices"][0].__setitem__(0, True),
            lambda d: d["triangles"][0]["vertices"][0].__setitem__(1, False),
            lambda d: d["triangles"][0]["vertices"][0].__setitem__(2, True),
            lambda d: d["triangles"][0]["rgb"].__setitem__(0, False),
            lambda d: d.__setitem__("unexpected", 1),
            lambda d: d["triangles"][0].__setitem__("unexpected", 1),
            lambda d: d.__setitem__("profile", "unsupported"),
            lambda d: d["triangles"].pop(),
        ))
        for field in ("format", "profile", "width", "height", "triangles"):
            invalid_cases.append(lambda d, field=field: d.pop(field))
        for field in ("vertices", "rgb"):
            invalid_cases.append(lambda d, field=field: d["triangles"][0].pop(field))
        for mutate in invalid_cases:
            with self.subTest(case=mutate):
                self._rejected_without_output(mutate)

    def test_fraction_discard_metadata_vector(self) -> None:
        points = ((0, 0), (639, 1), (1, 478))
        twice_area = ((points[1][0] - points[0][0]) * (points[2][1] - points[0][1])
                      - (points[1][1] - points[0][1]) * (points[2][0] - points[0][0]))
        denominator = abs(twice_area)
        shift = max(0, denominator.bit_length() - 16)
        discarded = denominator & ((1 << shift) - 1)
        self.assertEqual(denominator, 305441)
        self.assertEqual(shift, 3)
        self.assertEqual(discarded, 1)

    def test_ppm_manifest_and_deterministic_artifacts(self) -> None:
        tag = f"s1_test_{os.getpid()}"
        first = OUT_BASE / f"{tag}_a"
        second = OUT_BASE / f"{tag}_b"
        try:
            write_preview(EXAMPLE, first)
            artifacts1 = {path.name: path.read_bytes() for path in first.iterdir()}
            artifacts2 = build_artifacts(self.raw, self.scene)
            self.assertEqual(artifacts1, artifacts2)
            self.assertEqual(set(artifacts1), {
                "scene_packet.bin", "preview.ppm", "pixel_decisions.json", "manifest.json"
            })
            self.assertEqual(artifacts1["scene_packet.bin"], WIRE_FIXTURE.read_bytes())
            ppm = artifacts1["preview.ppm"]
            header = b"P6\n640 480\n255\n"
            self.assertTrue(ppm.startswith(header))
            self.assertEqual(len(ppm), len(header) + 640 * 480 * 3)

            decisions = json.loads(artifacts1["pixel_decisions.json"])
            self.assertEqual(len(decisions["samples"]), 7)
            manifest = json.loads(artifacts1["manifest.json"])
            self.assertEqual(manifest["profile"], "t1d-two-triangle-v1")
            self.assertEqual(manifest["schema"], "spu_gpu_scene_v1")
            self.assertEqual(manifest["repository_head"], subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
            ).strip())
            status = subprocess.check_output(
                ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
            )
            self.assertEqual(manifest["repository_worktree"], "dirty" if status.strip() else "clean")
            self.assertEqual(manifest["input_scene_sha256"], hashlib.sha256(self.raw).hexdigest())
            self.assertEqual(
                manifest["reference_fixture_sha256"],
                hashlib.sha256(REFERENCE_FIXTURE.read_bytes()).hexdigest(),
            )
            for field, paths in (("compiler_reference_source_sha256", MODULE_SOURCES),
                                 ("profile_source_sha256", PROFILE_SOURCES)):
                self.assertEqual(set(manifest[field]), set(paths))
                for path in paths:
                    self.assertEqual(manifest[field][path], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertEqual(manifest["packet_sha256"], hashlib.sha256(artifacts1["scene_packet.bin"]).hexdigest())
            self.assertEqual(manifest["preview_sha256"], hashlib.sha256(ppm).hexdigest())
            self.assertIs(manifest["device_model"], False)
            self.assertIs(manifest["physical_observation"], False)
            self.assertNotIn(str(ROOT), artifacts1["manifest.json"].decode("utf-8"))
            self.assertNotIn("timestamp", artifacts1["manifest.json"].decode("utf-8").lower())
        finally:
            shutil.rmtree(first, ignore_errors=True)
            shutil.rmtree(second, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
