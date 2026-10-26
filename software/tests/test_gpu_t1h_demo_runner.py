"""Offline checks for T1H sequence-runner failure evidence."""

import importlib
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
SENDER = importlib.import_module("send_gpu_t1h_scene")
SPEC = importlib.util.spec_from_file_location(
    "gpu_t1h_demo_runner", TOOLS / "run_gpu_t1h_demo.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class FakeTerminal:
    def isatty(self):
        return True


class T1HDemoRunnerTests(unittest.TestCase):
    def create_load_evidence(self, evidence, started=None, monotonic_start=None):
        load_evidence = evidence.parent / "programming_01"
        load_evidence.mkdir()
        if started is None:
            started = datetime.now(timezone.utc)
        if monotonic_start is None:
            monotonic_start = time.monotonic_ns()
        (load_evidence / "result.json").write_text(json.dumps({
            "status": "COMPLETE",
            "attempt_limit_seconds": 1800,
            "attempt_started_monotonic_ns": monotonic_start,
            "attempt_deadline_monotonic_ns": monotonic_start +
            1_800_000_000_000,
            "host_boot_id": RUNNER.current_boot_id(),
            "commands": [{"started_utc": started.isoformat(),
                           "started_monotonic_ns": monotonic_start}],
        }))
        (load_evidence / "COMPLETE").write_text("COMPLETE\n")
        return load_evidence

    def test_stale_or_duplicate_gate_reply_cannot_advance(self):
        prefix = "PASS unique 02 cycle 1 scene B: "
        with patch.object(RUNNER, "read_operator_observation",
                          side_effect=["PASS stale 01 cycle 1 scene A: old",
                                       prefix + "current B and lock"]):
            confirmation, replies = RUNNER.read_confirmation(
                prefix, time.monotonic() + 10, timeout=10)
        self.assertEqual(confirmation, prefix + "current B and lock")
        self.assertEqual([reply["text"] for reply in replies],
                         ["PASS stale 01 cycle 1 scene A: old",
                          prefix + "current B and lock"])

    def test_scene_runner_uses_the_loader_deadline_without_restarting_it(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            result = json.loads((load_evidence / "result.json").read_text())
            _path, deadline, budget = RUNNER.load_attempt_deadline(load_evidence)
            self.assertLessEqual(
                abs(int(deadline * 1_000_000_000) -
                    result["attempt_deadline_monotonic_ns"]), 1_000)
            self.assertEqual(budget, result["attempt_limit_seconds"])

    def test_loader_deadline_from_another_boot_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            result_path = load_evidence / "result.json"
            result = json.loads(result_path.read_text())
            result["host_boot_id"] = "different-boot"
            result_path.write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError, "different host boot"):
                RUNNER.load_attempt_deadline(load_evidence)

    def test_uart_open_failure_leaves_terminal_manifest(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/missing_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(RUNNER, "read_confirmation",
                                 return_value=("READY: LOCK_STABLE offline", [])), \
                    patch.object(SENDER, "open_uart",
                                 side_effect=FileNotFoundError("device vanished")):
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(manifest["status"], "FAILED")
            self.assertEqual(manifest["failure_stage"], "uart_open")
            self.assertEqual(manifest["transmission_classification"],
                             "UART_OPEN_FAILURE_ZERO_BYTES")
            self.assertEqual(manifest["bytes_written"], 0)
            self.assertIn("device vanished", manifest["error"])
            self.assertEqual(manifest["sends"], [])

    def test_sequence_opens_once_and_reuses_descriptor(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/fake_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            sent = []

            def send_scene(scene, fd, transcript, timeout_seconds,
                           overall_deadline=None):
                sent.append((scene, fd))
                transcript.parent.mkdir(parents=True, exist_ok=True)
                transcript.write_text("offline mocked packet\n")
                return {"written": 151, "tcdrain_completed": True,
                        "write_calls": 1, "write_return_counts": [151],
                        "send_drain_timeout_seconds": timeout_seconds,
                        "transport_worker_pid": 1234,
                        "transport_worker_exitcode": 0,
                        "write_start_unix_ns": time.time_ns(),
                        "write_start_monotonic_ns": time.monotonic_ns(),
                        "drain_complete_unix_ns": time.time_ns(),
                        "drain_complete_monotonic_ns": time.monotonic_ns(),
                        "post_drain_delay_seconds": 0.020,
                        "post_drain_delay_completed": True,
                        "post_drain_complete_monotonic_ns": time.monotonic_ns(),
                        "transmission_classification": "COMPLETED_HOST_WRITE"}

            def confirm(prefix, _deadline, _timeout):
                return prefix + "offline observation", []

            real_sleep = time.sleep

            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(SENDER, "open_uart", return_value=42) as opened, \
                    patch.object(SENDER, "send_scene_fd", side_effect=send_scene), \
                    patch.object(RUNNER.os, "close"), \
                    patch.object(RUNNER, "DWELL_SECONDS", 0.001), \
                    patch.object(RUNNER.time, "sleep",
                                 side_effect=lambda seconds: (
                                     real_sleep(seconds) if seconds < 1 else None)), \
                    patch.object(RUNNER, "read_confirmation",
                                 side_effect=confirm):
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 0)
            opened.assert_called_once_with("/offline/fake_uart")
            self.assertEqual([scene for scene, _fd in sent],
                             ["A", "B", "C", "A"])
            self.assertEqual({fd for _scene, fd in sent}, {42})
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(len(manifest["sends"]), 4)
            starts = [send["write_start_monotonic_ns"]
                      for send in manifest["sends"]]
            self.assertTrue(all(later - earlier >= RUNNER.MIN_START_TO_START_NS
                                for earlier, later in zip(starts, starts[1:])))
            self.assertTrue((evidence / "PASS").is_file())
            self.assertTrue(all(send["operator_observation"] for send in manifest["sends"]))
            self.assertTrue(all(send["transmission_classification"] ==
                                "COMPLETED_HOST_WRITE"
                                for send in manifest["sends"]))
            self.assertTrue(all(send["post_drain_delay_completed"] is True and
                                send["post_drain_delay_seconds"] == 0.020
                                for send in manifest["sends"]))
            self.assertTrue(all(send["remaining_attempt_seconds_at_send_start"] >=
                                send["send_observation_reserve_seconds"]
                                for send in manifest["sends"]))
            self.assertTrue(all(send["prior_start_to_start_ns"] >=
                                RUNNER.MIN_START_TO_START_NS
                                for send in manifest["sends"][1:]))
            self.assertTrue(all(send["dwell_completed_seconds"] >= 0.001
                                for send in manifest["sends"][:-1]))

    def test_expired_attempt_deadline_prevents_uart_open(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(
                evidence, datetime.now(timezone.utc) - timedelta(seconds=1801),
                time.monotonic_ns() - 1_801_000_000_000)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/fake_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(SENDER, "open_uart") as opened:
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(manifest["status"], "ATTEMPT_TIME_LIMIT")
            self.assertEqual(manifest["failure_stage"], "before_uart_open")
            opened.assert_not_called()

    def test_send_is_not_started_without_full_observation_reserve(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            # 180 seconds remain, less than the 180-second scene gate plus
            # the contract's five-second bounded transaction reserve.
            load_evidence = self.create_load_evidence(
                evidence, monotonic_start=time.monotonic_ns() -
                1_620_000_000_000)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/fake_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(SENDER, "open_uart") as opened:
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(manifest["status"], "ATTEMPT_TIME_LIMIT")
            self.assertEqual(manifest["failure_stage"], "before_uart_open")
            opened.assert_not_called()

    def test_operator_gate_timeout_stops_before_next_scene(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/fake_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            sent = []

            def send_scene(scene, fd, transcript, timeout_seconds,
                           overall_deadline=None):
                sent.append(scene)
                transcript.write_text("offline mocked packet\n")
                return {"written": 151, "tcdrain_completed": True,
                        "write_calls": 1, "write_return_counts": [151],
                        "send_drain_timeout_seconds": timeout_seconds,
                        "transport_worker_pid": 1234,
                        "transport_worker_exitcode": 0,
                        "write_start_unix_ns": time.time_ns(),
                        "write_start_monotonic_ns": time.monotonic_ns(),
                        "drain_complete_unix_ns": time.time_ns(),
                        "drain_complete_monotonic_ns": time.monotonic_ns(),
                        "post_drain_delay_seconds": 0.020,
                        "post_drain_delay_completed": True,
                        "post_drain_complete_monotonic_ns": time.monotonic_ns(),
                        "transmission_classification": "COMPLETED_HOST_WRITE"}

            def confirm(prefix, _deadline, _timeout):
                if prefix.startswith("READY:"):
                    return prefix + "offline lock", []
                return None, []

            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(SENDER, "open_uart", return_value=42), \
                    patch.object(SENDER, "send_scene_fd", side_effect=send_scene), \
                    patch.object(RUNNER.os, "close"), \
                    patch.object(RUNNER, "read_confirmation",
                                 side_effect=confirm):
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(sent, ["A"])
            self.assertEqual(manifest["status"], "OBSERVATION_TIMEOUT")
            self.assertEqual(manifest["stop_reason"],
                             "operator observation deadline expired")

    def test_transport_timeout_stops_sequence_before_later_writes(self):
        with tempfile.TemporaryDirectory(prefix="t1h_runner_test_",
                                         dir=ROOT / "build") as temporary:
            evidence = Path(temporary) / "demo"
            load_evidence = self.create_load_evidence(evidence)
            args = ["run_gpu_t1h_demo.py", "--execute", "--port",
                    "/offline/fake_uart", "--evidence-dir", str(evidence),
                    "--load-evidence-dir", str(load_evidence),
                    "--send-drain-bound-seconds", "5"]
            sent = []

            def timeout_scene(scene, _fd, transcript, _timeout,
                              overall_deadline=None):
                sent.append(scene)
                transcript.write_text(json.dumps({
                    "written": 40,
                    "write_calls": 1,
                    "write_return_counts": [40],
                    "tcdrain_completed": False,
                    "transmission_classification":
                        "TRANSMISSION_STATE_UNKNOWN_AFTER_WRITE_TIMEOUT",
                    "device_write_state_unknown": True,
                    "send_drain_timeout_stage": "write",
                }))
                raise SENDER.SendDrainTimeout("test transport deadline")

            def confirm(prefix, _deadline, _timeout):
                return prefix + "stable lock", []

            with patch.object(RUNNER.sys, "argv", args), \
                    patch.object(RUNNER.sys, "stdin", FakeTerminal()), \
                    patch.object(SENDER, "open_uart", return_value=42), \
                    patch.object(SENDER, "send_scene_fd",
                                 side_effect=timeout_scene), \
                    patch.object(RUNNER.os, "close"), \
                    patch.object(RUNNER, "read_confirmation",
                                 side_effect=confirm):
                result = RUNNER.main()
            manifest = json.loads((evidence / "sequence.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(sent, ["A"])
            self.assertEqual(manifest["status"], "FAILED")
            self.assertEqual(manifest["sends"][0]["written"], 40)
            self.assertTrue(manifest["sends"][0]["device_write_state_unknown"])
            self.assertTrue((evidence / "FAIL").is_file())


if __name__ == "__main__":
    unittest.main()
