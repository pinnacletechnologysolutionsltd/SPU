#!/usr/bin/env python3
"""Focused filesystem fixtures for the read-only build inventory."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.build_artifact_inventory import inventory, main


class BuildArtifactInventoryTests(unittest.TestCase):
    def test_hidden_paths_symlinks_counts_and_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "build"
            (root / "repository_cleanup").mkdir(parents=True)
            (root / ".hidden").mkdir()
            (root / ".hidden" / "payload.bin").write_bytes(b"hidden")
            for folder in ("run_a", "run_b"):
                target = root / folder
                target.mkdir()
                (target / "same.dat").write_bytes(b"same")
            (root / "COMPLETE").write_bytes(b"done")
            (root / "result.json").write_bytes(b"{}")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_bytes(b"meta")

            outside_file = base / "outside.bin"
            outside_file.write_bytes(b"outside")
            outside_dir = base / "outside_dir"
            outside_dir.mkdir()
            (outside_dir / "ignored.bin").write_bytes(b"ignored")
            try:
                (root / "linked_file").symlink_to(outside_file)
                (root / "linked_dir").symlink_to(outside_dir, target_is_directory=True)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symlink fixtures unavailable: {error}")

            report = inventory(root)
            self.assertEqual(report["regular_file_count"], 6)
            self.assertEqual(report["directory_count"], 5)
            self.assertEqual(report["symlink_count"], 2)
            self.assertEqual(report["apparent_bytes"], 24)
            self.assertEqual(report["terminal_markers"], {"COMPLETE": 1})
            self.assertEqual(report["result_json_count"], 1)
            self.assertIn(".hidden", report["top_level"])
            self.assertEqual(report["git_metadata_paths"], [".git"])
            self.assertEqual(report["same_name_size_candidate_group_count"], 1)
            candidate = report["same_name_size_review_candidates"][0]
            self.assertEqual(candidate["basename"], "same.dat")
            self.assertEqual(candidate["apparent_bytes"], 4)
            self.assertEqual(candidate["path_count"], 2)
            self.assertFalse(candidate["content_hash_checked"])
            self.assertFalse(report["cleanup_authorized"])

    def test_cli_writes_fresh_output_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "build"
            (root / "repository_cleanup").mkdir(parents=True)
            (root / "one.bin").write_bytes(b"one")
            output = root / "repository_cleanup" / "inventory_01"
            argv = ["build_artifact_inventory.py", "--root", str(root), "--out", str(output)]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 0)
            report_path = output / "inventory.json"
            original = report_path.read_bytes()
            self.assertFalse(json.loads(original)["cleanup_authorized"])

            errors = io.StringIO()
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
                self.assertEqual(main(), 2)
            self.assertIn("already exists", errors.getvalue())
            self.assertEqual(report_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
