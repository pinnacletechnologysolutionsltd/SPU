"""Check required frontend registration and failure propagation."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from run_all_tests import run_cpu_frontend_test


class FrontendRegistrationTests(unittest.TestCase):
    def test_missing_nonzero_timeout_and_success(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            self.assertEqual(run_cpu_frontend_test(root), (0, 1))
            script = root / "hardware/tests/cpu_frontend_v02/run.py"
            script.parent.mkdir(parents=True)
            script.write_text("")
            with patch("run_all_tests.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess([], 1, "", "failure")
                self.assertEqual(run_cpu_frontend_test(root), (0, 1))
                run.side_effect = subprocess.TimeoutExpired("frontend", 120)
                self.assertEqual(run_cpu_frontend_test(root), (0, 1))
                run.side_effect = None
                run.return_value = subprocess.CompletedProcess([], 0, "pass", "")
                self.assertEqual(run_cpu_frontend_test(root), (1, 0))
                self.assertEqual(run.call_args.args[0][:2], [sys.executable, str(script)])

    def test_real_registered_frontend(self):
        self.assertEqual(run_cpu_frontend_test(ROOT), (1, 0))


if __name__ == "__main__":
    unittest.main()
