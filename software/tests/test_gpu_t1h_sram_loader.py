"""Offline terminal-marker and guard checks for the T1H SRAM loader."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "gpu_t1h_sram_loader", ROOT / "tools/load_gpu_t1h_sram.py")
LOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOADER)


class T1HSramLoaderTests(unittest.TestCase):
    def run_with(self, responses, attempt_limit_seconds=1800):
        evidence_parent = ROOT / "build"
        with tempfile.TemporaryDirectory(prefix="t1g_loader_test_",
                                         dir=evidence_parent) as temporary:
            evidence = Path(temporary) / "load"
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(
                    command, *responses[len(calls) - 1])

            status = LOADER.run_load(
                evidence, 99, runner,
                attempt_limit_seconds=attempt_limit_seconds)
            manifest = json.loads((evidence / "result.json").read_text())
            markers = {path.name for path in evidence.iterdir()
                       if path.name in LOADER.TERMINALS}
            return status, manifest, markers, calls

    def test_success_requires_idcode_and_done_flags(self):
        status, manifest, markers, calls = self.run_with([
            (0, "Found Device ID 0x03631093\n", ""),
            (0, "Load SRAM 100%\nisc_done 1\ninit 1\ndone 1\n", ""),
        ])
        self.assertEqual(status, "COMPLETE")
        self.assertEqual(len(calls), 2)
        self.assertEqual(markers, {"COMPLETE"})
        self.assertEqual(manifest["status"], "COMPLETE")
        self.assertEqual(manifest["attempt_limit_seconds"], 1800)
        self.assertEqual(manifest["attempt_started_monotonic_ns"],
                         manifest["commands"][0]["started_monotonic_ns"])
        self.assertEqual(manifest["attempt_deadline_monotonic_ns"],
                         manifest["attempt_started_monotonic_ns"] +
                         1_800_000_000_000)
        self.assertTrue(manifest["host_boot_id"])

    def test_owner_limit_is_stored_for_the_shared_deadline(self):
        status, manifest, _markers, _calls = self.run_with([
            (0, "Found Device ID 0x03631093\n", ""),
            (0, "Load SRAM 100%\nisc_done 1\ninit 1\ndone 1\n", ""),
        ], attempt_limit_seconds=1200)
        self.assertEqual(status, "COMPLETE")
        self.assertEqual(manifest["attempt_limit_seconds"], 1200)
        self.assertEqual(manifest["attempt_deadline_monotonic_ns"],
                         manifest["attempt_started_monotonic_ns"] +
                         1_200_000_000_000)

    def test_wrong_idcode_prevents_load(self):
        status, manifest, markers, calls = self.run_with([
            (0, "Found Device ID 0x12345678\n", ""),
        ])
        self.assertEqual(status, "FAILED")
        self.assertEqual(len(calls), 1)
        self.assertEqual(markers, {"FAILED"})
        self.assertEqual(manifest["status"], "FAILED")

    def test_timeout_has_only_timeout_marker(self):
        status, manifest, markers, calls = self.run_with([
            (0, "Found Device ID 0x03631093\n", ""),
            (124, "Load SRAM 50%\n", "timeout\n"),
        ])
        self.assertEqual(status, "TIMEOUT")
        self.assertEqual(len(calls), 2)
        self.assertEqual(markers, {"TIMEOUT"})
        self.assertEqual(manifest["status"], "TIMEOUT")

    def test_exit_zero_without_all_done_flags_is_failed(self):
        status, manifest, markers, calls = self.run_with([
            (0, "Found Device ID 0x03631093\n", ""),
            (0, "isc_done=1\ninit=1\n", ""),
        ])
        self.assertEqual(status, "FAILED")
        self.assertEqual(len(calls), 2)
        self.assertEqual(markers, {"FAILED"})
        self.assertEqual(manifest["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
