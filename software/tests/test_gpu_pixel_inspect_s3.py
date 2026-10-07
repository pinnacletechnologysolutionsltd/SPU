#!/usr/bin/env python3
"""Tests for the one-pixel S3 inspector CLI and report."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval.device_inspect import inspect_pixel
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.scene import parse_scene_bytes


SCENE = ROOT / "examples/gpu/t1d_two_triangle.json"
RAW_SCENE = SCENE.read_bytes()


class PixelInspectTests(unittest.TestCase):
    def test_report_hashes_schema_and_decisions(self) -> None:
        scene = parse_scene_bytes(RAW_SCENE)
        packet = compile_packet(scene)
        report = inspect_pixel(RAW_SCENE, 320, 0)
        self.assertEqual(set(report), {
            "format", "profile", "x", "y", "input_scene_sha256",
            "scene_packet_sha256", "ideal_reference", "device_decision",
            "decision_match", "evidence",
        })
        self.assertEqual(report["format"], "spu_gpu_pixel_inspection_s3_v1")
        self.assertEqual(report["profile"], "t1d-two-triangle-v1")
        self.assertEqual(report["input_scene_sha256"], hashlib.sha256(RAW_SCENE).hexdigest())
        self.assertEqual(report["scene_packet_sha256"], hashlib.sha256(packet).hexdigest())
        self.assertEqual(report["decision_match"], {
            "coverage": True, "covered_by": True, "winner": True, "rgb": True,
        })
        self.assertEqual(report["ideal_reference"]["coverage"], "overlap")
        self.assertEqual(report["ideal_reference"]["covered_by"], [0, 1])
        self.assertEqual(report["ideal_reference"]["winner"], 0)
        self.assertEqual(report["ideal_reference"]["rgb"], [15, 0, 0])
        self.assertEqual(report["ideal_reference"]["depths"], [
            {"triangle": 0, "numerator": 2000, "denominator": 1},
            {"triangle": 1, "numerator": 2000, "denominator": 1},
        ])
        self.assertEqual(report["device_decision"]["depths"], [
            {"triangle": 0, "accumulator": 17179859200000, "value": 1999},
            {"triangle": 1, "accumulator": 17179859200000, "value": 1999},
        ])
        self.assertEqual(report["device_decision"]["winner"], 0)
        self.assertEqual(report["evidence"], {
            "device_model": True, "physical_observation": False,
            "cycle_timing_model": False,
        })

    def test_background_and_triangle_only_samples(self) -> None:
        background = inspect_pixel(RAW_SCENE, 10, 10)
        self.assertEqual(background["ideal_reference"]["coverage"], "background")
        self.assertEqual(background["device_decision"]["coverage"], "background")
        self.assertEqual(background["decision_match"], {
            "coverage": True, "covered_by": True, "winner": True, "rgb": True,
        })

        triangle = inspect_pixel(RAW_SCENE, 100, 300)
        self.assertEqual(triangle["ideal_reference"]["coverage"], "triangle0")
        self.assertEqual(triangle["device_decision"]["coverage"], "triangle0")
        self.assertEqual(triangle["ideal_reference"]["winner"], 0)
        self.assertEqual(triangle["device_decision"]["rgb"], [15, 0, 0])

    def test_report_json_is_deterministic(self) -> None:
        first = json.dumps(inspect_pixel(RAW_SCENE, 320, 0), sort_keys=True,
                           separators=(",", ":")) + "\n"
        second = json.dumps(inspect_pixel(RAW_SCENE, 320, 0), sort_keys=True,
                            separators=(",", ":")) + "\n"
        self.assertEqual(first, second)

    def test_coordinate_validation(self) -> None:
        for x, y in ((640, 0), (0, 480), (-1, 0), (0, -1), (True, 0), (0, 1.0)):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                inspect_pixel(RAW_SCENE, x, y)

    def test_cli_success_and_errors_write_no_report_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            valid_before = set(temp.iterdir())
            result = subprocess.run(
                [sys.executable, "-m", "software.spu_gpu_eval.cli", "inspect",
                 str(SCENE), "--x", "320", "--y", "0"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertTrue(result.stdout.endswith("\n"))
            self.assertEqual(json.loads(result.stdout), inspect_pixel(RAW_SCENE, 320, 0))
            self.assertEqual(set(temp.iterdir()), valid_before)

            invalid = temp / "invalid.json"
            invalid.write_text("{bad", encoding="utf-8")
            before_error = set(temp.iterdir())
            bad_scene = subprocess.run(
                [sys.executable, "-m", "software.spu_gpu_eval.cli", "inspect",
                 str(invalid), "--x", "1", "--y", "1"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(bad_scene.returncode, 2)
            self.assertEqual(bad_scene.stdout, "")
            self.assertIn("error:", bad_scene.stderr)
            self.assertEqual(set(temp.iterdir()), before_error)

            bad_pixel = subprocess.run(
                [sys.executable, "-m", "software.spu_gpu_eval.cli", "inspect",
                 str(SCENE), "--x", "640", "--y", "0"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(bad_pixel.returncode, 2)
            self.assertEqual(bad_pixel.stdout, "")
            self.assertIn("error:", bad_pixel.stderr)
            self.assertEqual(set(temp.iterdir()), before_error)


if __name__ == "__main__":
    unittest.main()
