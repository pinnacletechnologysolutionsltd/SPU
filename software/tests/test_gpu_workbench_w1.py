#!/usr/bin/env python3
"""Focused W1 tests for the T1d scene workbench."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval import workbench_catalog
from software.spu_gpu_eval.packet import compile_packet
from software.spu_gpu_eval.scene import parse_scene_bytes
from software.spu_gpu_eval.workbench import _inspect, _inspect_packet, main


class WorkbenchTests(unittest.TestCase):
    def test_allowlist_is_complete_and_hash_pinned(self) -> None:
        entries = workbench_catalog.load_catalog()
        self.assertEqual(len(entries), 13)
        self.assertEqual(len({entry["id"] for entry in entries}), 13)
        original = json.loads((ROOT / 'fixtures/sg0_v1/catalogue_before.json').read_bytes())
        frozen = json.loads((ROOT / 'fixtures/sg0_v1/inputs.json').read_bytes())
        fields = ('id', 'path', 'sha256', 'group')
        actual = [{key: entry[key] for key in fields} for entry in entries]
        self.assertEqual(actual[:11], original['scenes'])
        self.assertEqual(actual[11:], frozen['publication_entries'])
        for entry in entries:
            data = Path(entry["absolute_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
        with self.assertRaisesRegex(workbench_catalog.CatalogError, "unknown scene"):
            workbench_catalog.find_scene("not-allowlisted")

    def test_catalog_rejects_non_object_and_invalid_entry_fields(self) -> None:
        for document in ([], {"format": workbench_catalog.FORMAT, "profile": "t1d-two-triangle-v1",
                              "scenes": [{"id": "a", "path": "examples/a.json",
                                          "sha256": "bad", "group": "test"}]}):
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "catalog.json"
                source.write_text(json.dumps(document), encoding="utf-8")
                with patch.object(workbench_catalog, "CATALOG", source):
                    with self.assertRaises(workbench_catalog.CatalogError):
                        workbench_catalog.load_catalog()

    def test_catalog_rejects_changed_scene_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scene = root / "scene.json"
            scene.write_text("{}", encoding="utf-8")
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({
                "format": workbench_catalog.FORMAT,
                "profile": "t1d-two-triangle-v1",
                "scenes": [{"id": "frozen", "path": "scene.json",
                            "sha256": "0" * 64, "group": "control"}],
            }), encoding="utf-8")
            with patch.object(workbench_catalog, "ROOT", root), \
                    patch.object(workbench_catalog, "CATALOG", catalog):
                with self.assertRaisesRegex(workbench_catalog.CatalogError, "hash mismatch"):
                    workbench_catalog.load_catalog()

    def test_pixel_report_keeps_depth_separate(self) -> None:
        report = _inspect("baseline", 320, 0)
        self.assertEqual(report["comparison"]["coverage_equal"], True)
        self.assertEqual(report["comparison"]["covered_triangles_equal"], True)
        self.assertEqual(report["comparison"]["winner_equal"], True)
        self.assertEqual(report["comparison"]["rgb_equal"], True)
        self.assertEqual(report["comparison"]["depths_equal"], False)
        self.assertEqual(report["comparison"]["depths"], [
            {"triangle": 0, "ideal": "2000", "device_model": 1999, "equal": False},
            {"triangle": 1, "ideal": "2000", "device_model": 1999, "equal": False},
        ])

    def test_packet_inspection_is_strict_and_reports_both_triangles(self) -> None:
        raw_scene = (ROOT / "examples/gpu/t1d_two_triangle.json").read_bytes()
        packet = compile_packet(parse_scene_bytes(raw_scene))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.bin"
            path.write_bytes(packet)
            report = _inspect_packet(str(path))
            self.assertEqual(report["packet_bytes"], 64)
            self.assertEqual(report["start_byte"], "0xa5")
            self.assertEqual(report["sha256"], hashlib.sha256(packet).hexdigest())
            self.assertEqual(len(report["triangles"]), 2)
            for malformed in (packet[:-1], bytes([0]) + packet[1:]):
                path.write_bytes(malformed)
                with self.assertRaises(ValueError):
                    _inspect_packet(str(path))
                stderr, stdout = io.StringIO(), io.StringIO()
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(["inspect-packet", str(path)]), 2)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn("error:", stderr.getvalue())

    def test_cli_render_outputs_are_repeatable_and_separate(self) -> None:
        base = ROOT / "build/gpu_evaluation"
        base.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix="w1_test_", dir=base))
        try:
            outputs = {}
            for mode in ("ideal", "device"):
                for repeat in (1, 2):
                    destination = temp / f"{mode}_{repeat}"
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        status = main(["render", "baseline", "--mode", mode,
                                       "--out", str(destination)])
                    self.assertEqual(status, 0)
                    outputs[mode, repeat] = {
                        path.name: path.read_bytes() for path in destination.iterdir()
                    }
                    manifest = json.loads(outputs[mode, repeat]["manifest.json"])
                    self.assertEqual(manifest["device_model"], mode == "device")
                    self.assertFalse(manifest["physical_observation"])
            self.assertEqual(outputs["ideal", 1], outputs["ideal", 2])
            self.assertEqual(outputs["device", 1], outputs["device", 2])
            self.assertIn("preview.ppm", outputs["ideal", 1])
            self.assertIn("ideal_preview.ppm", outputs["device", 1])
            self.assertIn("device_preview.ppm", outputs["device", 1])
            collision = io.StringIO()
            with contextlib.redirect_stderr(collision):
                self.assertEqual(main(["render", "baseline", "--mode", "ideal",
                                       "--out", str(temp / "ideal_1")]), 2)
            self.assertIn("already exists", collision.getvalue())
        finally:
            shutil.rmtree(temp)

    def test_cli_rejects_invalid_pixel_and_unknown_scene(self) -> None:
        for args in (("inspect", "baseline", "--x", "640", "--y", "0"),
                     ("inspect", "missing", "--x", "1", "--y", "1")):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(list(args)), 2)
            self.assertIn("error:", stderr.getvalue())

    def test_sg0_scene_render_and_exact_diagnostics(self) -> None:
        frozen = json.loads((ROOT / 'fixtures/sg0_v1/inputs.json').read_bytes())
        base = ROOT / 'build/gpu_evaluation'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='w1_sg0_', dir=base) as directory:
            for variant in frozen['variants']:
                scene_id = 'sg0_' + variant['id']
                for expected in variant['diagnostic_pixels']:
                    report = _inspect(scene_id, expected['x'], expected['y'])
                    self.assertEqual(report['ideal_reference'], expected)
                    self.assertFalse(report['evidence']['physical_observation'])
                for mode in ('ideal', 'device'):
                    target = Path(directory) / f'{scene_id}_{mode}'
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(main(['render', scene_id, '--mode', mode,
                                               '--out', str(target)]), 0)
                    manifest = json.loads((target / 'manifest.json').read_bytes())
                    self.assertFalse(manifest['physical_observation'])
                    self.assertEqual(manifest['device_model'], mode == 'device')


if __name__ == "__main__":
    unittest.main()
