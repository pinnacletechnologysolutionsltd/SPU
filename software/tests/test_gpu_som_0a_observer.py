#!/usr/bin/env python3
"""Focused tests for the observational GPU-SOM-0A sidecar."""

from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval import device_preview, observer, observer_artifacts
from software.spu_gpu_eval.device_model import pixel_decision, prepare_scene
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.scene import parse_scene_bytes

SCENES = (
    ROOT / "examples/gpu/t1d_two_triangle.json",
    ROOT / "examples/gpu/t1d_two_triangle_vertex_b.json",
)
BASE = ROOT / "build/gpu_evaluation/gpu_som_0a"


def _background_decision() -> dict[str, object]:
    return {"coverage": "background", "covered_by": [], "winner": None,
            "rgb": [0, 0, 0], "depths": []}


class GpuSomObserverTests(unittest.TestCase):
    def test_both_frozen_scenes_emit_complete_deterministic_frames(self) -> None:
        for source in SCENES:
            with self.subTest(scene=source.name):
                raw = source.read_bytes()
                prepared = prepare_scene(compile_packet(parse_scene_bytes(raw)))
                first = observer.extract_tile_features(prepared)
                second = observer.extract_tile_features(prepared)
                self.assertEqual(first, second)
                document = json.loads(first)
                self.assertEqual(document["format"], "spu_gpu_som_tile_features_v1")
                self.assertEqual(document["pixel_decisions"], 307200)
                self.assertEqual(len(document["tiles"]), 1200)
                self.assertEqual(sum(t["sample_count"] for t in document["tiles"]), 307200)
                self.assertEqual(document["tiles"][0]["coverage_counts"], {
                    "background": 256, "triangle0": 0, "triangle1": 0, "overlap": 0,
                })
                self.assertEqual(document["tiles"][0]["rgb444_histogram"], [
                    {"rgb": [0, 0, 0], "count": 256},
                ])
                self.assertEqual(document["tiles"][0]["depth_ranges"], {
                    "0": {"min": None, "max": None},
                    "1": {"min": None, "max": None},
                })

    def test_tile_aggregation_matches_independent_oracle_and_is_order_independent(self) -> None:
        raw = SCENES[0].read_bytes()
        prepared = prepare_scene(compile_packet(parse_scene_bytes(raw)))
        observations = [
            (x, y, pixel_decision(prepared, x, y))
            for y in range(160, 176) for x in range(160, 176)
        ]
        expected_coverage = {name: 0 for name in ("background", "triangle0", "triangle1", "overlap")}
        expected_covered = {"0": 0, "1": 0}
        expected_winners = {"0": 0, "1": 0}
        expected_rgb: dict[tuple[int, int, int], int] = {}
        expected_depths: dict[str, list[int]] = {"0": [], "1": []}
        for _x, _y, decision in observations:
            expected_coverage[decision["coverage"]] += 1
            for primitive in decision["covered_by"]:
                expected_covered[str(primitive)] += 1
            if decision["winner"] is not None:
                expected_winners[str(decision["winner"])] += 1
            rgb = tuple(decision["rgb"])
            expected_rgb[rgb] = expected_rgb.get(rgb, 0) + 1
            for depth in decision["depths"]:
                expected_depths[str(depth["triangle"])].append(depth["value"])

        record = observer._tile_record(10, 10, observations)
        self.assertEqual(record["tile_x"], 160)
        self.assertEqual(record["tile_y"], 160)
        self.assertEqual(record["coverage_counts"], expected_coverage)
        self.assertEqual(record["covered_pixels"], expected_covered)
        self.assertEqual(record["winner_counts"], expected_winners)
        self.assertEqual(record["rgb444_histogram"], [
            {"rgb": list(rgb), "count": expected_rgb[rgb]} for rgb in sorted(expected_rgb)
        ])
        for primitive in ("0", "1"):
            values = expected_depths[primitive]
            expected = {"min": min(values), "max": max(values)} if values else {"min": None, "max": None}
            self.assertEqual(record["depth_ranges"][primitive], expected)

        shuffled = list(observations)
        random.Random(4001).shuffle(shuffled)
        self.assertEqual(observer._tile_record(10, 10, shuffled), record)
        self.assertEqual(observer._json_bytes(observer._tile_record(10, 10, shuffled)),
                         observer._json_bytes(record))

    def test_tile_rejects_missing_duplicate_and_invalid_decisions(self) -> None:
        complete = [(x, y, _background_decision())
                    for y in range(16) for x in range(16)]
        with self.assertRaises(observer.ObserverError):
            observer._tile_record(0, 0, complete[:-1])
        with self.assertRaises(observer.ObserverError):
            observer._tile_record(0, 0, complete[:-1] + [complete[0]])
        invalid = list(complete)
        invalid[0] = (0, 0, {**_background_decision(), "coverage": "triangle0"})
        with self.assertRaises(observer.ObserverError):
            observer._tile_record(0, 0, invalid)

    def test_capacity_is_bounded(self) -> None:
        observer._check_tile_capacity(1200)
        with self.assertRaises(observer.ObserverError):
            observer._check_tile_capacity(1201)

    def test_observer_preview_matches_device_preview_path(self) -> None:
        raw = SCENES[0].read_bytes()
        scene = parse_scene_bytes(raw)
        observed = observer_artifacts._build_artifacts(raw, scene)
        reference = device_preview.build_artifacts(raw, scene)
        self.assertEqual(observed["device_preview.ppm"], reference["device_preview.ppm"])
        self.assertEqual(hashlib.sha256(observed["device_preview.ppm"]).digest(),
                         hashlib.sha256(reference["device_preview.ppm"]).digest())
        manifest = json.loads(observed["manifest.json"])
        self.assertTrue(manifest["device_model"])
        self.assertFalse(manifest["physical_observation"])

    def test_existing_output_is_preserved_and_failed_stage_is_removed(self) -> None:
        BASE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="test_", dir=BASE) as temp:
            parent = Path(temp)
            target = parent / "existing"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(observer.ObserverError):
                observer_artifacts.write_observation(SCENES[0], target)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

            absent = parent / "failed"
            with mock.patch.object(observer_artifacts, "_build_artifacts", side_effect=RuntimeError("injected")):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    observer_artifacts.write_observation(SCENES[0], absent)
            self.assertFalse(absent.exists())
            self.assertFalse(any(parent.glob(".gpu_som_0a_stage_*")))

            empty_tile = {
                "sample_count": 256,
                "coverage_counts": {"background": 256, "triangle0": 0,
                                    "triangle1": 0, "overlap": 0},
                "rgb444_histogram": [{"rgb": [0, 0, 0], "count": 256}],
            }
            tiles = [{**empty_tile, "tile_x": (i % 40) * 16, "tile_y": (i // 40) * 16}
                     for i in range(1200)]
            features = observer._json_bytes({"pixel_decisions": 307200, "tiles": tiles})
            packet_bytes, preview = b"packet", b"preview"
            digest = lambda data: hashlib.sha256(data).hexdigest()
            manifest = observer._json_bytes({
                "scene_packet_sha256": digest(packet_bytes),
                "tile_features_sha256": digest(features),
                "device_preview_sha256": digest(preview),
                "tile_records": 1200, "pixel_decisions": 307200, "tile_size": 16,
            })
            artifacts = {"scene_packet.bin": packet_bytes, "device_preview.ppm": preview,
                         "tile_features.json": features, "manifest.json": manifest}
            publish_failure = parent / "publish_failed"
            with mock.patch.object(observer_artifacts, "_build_artifacts", return_value=artifacts), \
                    mock.patch.object(observer_artifacts, "_rename_noreplace",
                                      side_effect=OSError("injected publish failure")):
                with self.assertRaisesRegex(OSError, "injected publish failure"):
                    observer_artifacts.write_observation(SCENES[0], publish_failure)
            self.assertFalse(publish_failure.exists())
            self.assertFalse(any(parent.glob(".gpu_som_0a_stage_*")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
