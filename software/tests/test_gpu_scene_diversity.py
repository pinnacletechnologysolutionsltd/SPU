"""Focused correctness gates for the frozen T1d scene-diversity fixtures."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval import packet, reference
from software.spu_gpu_eval.device_model import pixel_decision, prepare_scene
from software.spu_gpu_eval.scene import PROFILE, parse_scene_bytes
from software.spu_gpu_eval.scene_diversity import evaluate_scene
from software.spu_gpu_eval import scene_diversity_artifacts as artifacts
from software.spu_gpu_eval import scene_diversity_publish as publisher
from software.spu_gpu_eval.scene_diversity_artifacts import _frozen_sources

SUITE = json.loads((ROOT / "examples/gpu/scene_diversity/manifest.json").read_text())
ORACLE = json.loads((ROOT / "fixtures/gpu_scene_diversity_reference.json").read_text())


class SceneDiversityTests(unittest.TestCase):
    def test_hashes_roles_and_frozen_samples(self) -> None:
        self.assertEqual(SUITE["profile"], PROFILE)
        self.assertEqual(hashlib.sha256((ROOT / "fixtures/gpu_scene_diversity_reference.json").read_bytes()).hexdigest(),
                         SUITE["reference_fixture_sha256"])
        self.assertEqual(_frozen_sources(), json.loads(
            (ROOT / "fixtures/gpu_scene_diversity_source_lock.json").read_text())["source_sha256"])
        self.assertEqual({item["role"] for item in SUITE["scenes"]}, {
            "collision-pair-a", "collision-pair-b", "overlap-depth-order-0",
            "overlap-depth-order-1", "equal-depth-tie", "shared-color-control"})
        for entry in SUITE["scenes"]:
            raw = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            scene = parse_scene_bytes(raw)
            device = prepare_scene(packet.compile_packet(scene))
            points = ORACLE["scenes"][entry["id"]]
            self.assertEqual(len({(row["x"], row["y"]) for row in points}), len(points))
            for row in points:
                ideal = reference.pixel_decision(scene, row["x"], row["y"])
                actual = pixel_decision(device, row["x"], row["y"])
                for field in ORACLE["task_fields"]:
                    self.assertEqual(ideal[field], row["ideal"][field])
                    self.assertEqual(actual[field], row["device"][field])
                self.assertEqual(ideal["depths"], row["ideal"]["depths"])
                self.assertEqual([item["value"] for item in actual["depths"]], row["device"]["depth_values"])

    def test_exact_collision_and_independent_pixel_difference(self) -> None:
        pair = ORACLE["collision_pairs"][0]
        results = {}
        for scene_id in (pair["a"], pair["b"]):
            entry = next(item for item in SUITE["scenes"] if item["id"] == scene_id)
            results[scene_id] = evaluate_scene(scene_id, (ROOT / entry["path"]).read_bytes(),
                                               ORACLE["scenes"][scene_id])
        self.assertEqual(results[pair["a"]]["features"], results[pair["b"]]["features"])
        self.assertEqual(results[pair["a"]]["result"]["feature_sha256"],
                         results[pair["b"]]["result"]["feature_sha256"])
        self.assertEqual(results[pair["a"]]["result"]["pixel_decisions"], 307200)
        self.assertEqual(len(results[pair["a"]]["task_signatures"]), 307200 * 6)
        self.assertNotEqual(results[pair["a"]]["result"]["ideal_reference_map_sha256"],
                            results[pair["b"]]["result"]["ideal_reference_map_sha256"])
        differences = sum(results[pair["a"]]["task_signatures"][i:i + 6]
                          != results[pair["b"]]["task_signatures"][i:i + 6]
                          for i in range(0, 307200 * 6, 6))
        self.assertEqual(differences, pair["expected_task_differing_pixels"])
        collision = artifacts.collision_result({**pair, "kind": "within-tile-translation"},
                                                results[pair["a"]], results[pair["b"]], differences)
        self.assertTrue(collision["task_relevant_collision"])
        entry = next(item for item in SUITE["scenes"] if item["id"] == pair["a"])
        replay = evaluate_scene(pair["a"], (ROOT / entry["path"]).read_bytes(),
                                ORACLE["scenes"][pair["a"]])
        self.assertEqual(replay["features"], results[pair["a"]]["features"])
        self.assertEqual(replay["result"]["ideal_reference_map_sha256"],
                         results[pair["a"]]["result"]["ideal_reference_map_sha256"])
        self.assertEqual(replay["task_signatures"], results[pair["a"]]["task_signatures"])

    def test_atomic_publication_failure_cleans_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result"
            with mock.patch.object(publisher, "rename_noreplace", side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    publisher.publish(target, {"result.json": b"{}\n"})
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_existing_output_refused_before_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing"
            target.mkdir()
            with mock.patch.object(artifacts, "OUTPUT", target):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    artifacts.write_scene_diversity(artifacts.SUITE, target)
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
