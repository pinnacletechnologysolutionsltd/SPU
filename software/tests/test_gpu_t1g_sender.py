"""Offline failure-path checks for the frozen T1G UART sender."""

import importlib.util
import json
import multiprocessing
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import sys


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "gpu_t1g_sender", ROOT / "tools/send_gpu_t1g_scene.py")
SENDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SENDER)


class T1GSenderTests(unittest.TestCase):
    def test_write_all_handles_partial_writes(self):
        packet = bytes(range(127))
        accepted = bytearray()
        progress = []
        results = iter((13, 47, 67))

        def writer(_fd, remaining):
            count = next(results)
            accepted.extend(remaining[:count])
            return count

        total = SENDER.write_all(9, packet, writer, progress.append)
        self.assertEqual(total, len(packet))
        self.assertEqual(bytes(accepted), packet)
        self.assertEqual(progress, [13, 60, 127])

    def test_zero_progress_is_a_transmission_error(self):
        progress = []
        with self.assertRaises(OSError):
            SENDER.write_all(9, b"abc", lambda _fd, _data: 0,
                             progress.append)
        self.assertEqual(progress, [])

    def run_send(self, writes, drain_error=None, timeout=2, sleeper=None):
        evidence_root = ROOT / "build"
        with tempfile.TemporaryDirectory(prefix="t1g_sender_test_",
                                         dir=evidence_root) as temporary:
            transcript = Path(temporary) / "scene_A.json"
            if callable(writes[0]):
                writer = writes[0]
            else:
                actions = iter(writes)

                def writer(_fd, _remaining):
                    action = next(actions)
                    if isinstance(action, BaseException):
                        raise action
                    return action

            def drainer(_fd):
                if drain_error:
                    if callable(drain_error):
                        return drain_error(_fd)
                    raise drain_error

            try:
                SENDER.send_scene_fd("A", 9, transcript, timeout,
                                     writer=writer, drainer=drainer,
                                     sleeper=sleeper)
            except (OSError, TimeoutError):
                pass
            return json.loads(transcript.read_text())

    def test_partial_uart_error_preserves_transcript(self):
        result = self.run_send((40, OSError("serial disconnected")))
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["written"], 40)
        self.assertFalse(result["tcdrain_completed"])
        self.assertIn("serial disconnected", result["error"])
        self.assertEqual(result["transmission_classification"],
                         "PARTIAL_TRANSMISSION")

    def test_drain_error_preserves_completed_write_transcript(self):
        result = self.run_send((127,), OSError("drain failed"))
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["written"], 127)
        self.assertFalse(result["tcdrain_completed"])
        self.assertIn("drain failed", result["error"])
        self.assertEqual(result["transmission_classification"],
                         "FULL_PACKET_WRITTEN_DRAIN_FAILED")

    def test_successful_partial_writes_record_completion(self):
        sizes = iter((29, 98))

        def writer(_fd, remaining):
            count = next(sizes)
            return count

        result = self.run_send((writer,))
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["written"], 127)
        self.assertEqual(result["write_calls"], 2)
        self.assertEqual(result["write_return_counts"], [29, 98])
        self.assertTrue(result["tcdrain_completed"])
        self.assertTrue(result["post_drain_delay_completed"])
        self.assertEqual(result["transmission_classification"],
                         "COMPLETED_HOST_WRITE")
        self.assertGreaterEqual(
            result["post_drain_complete_monotonic_ns"] -
            result["drain_complete_monotonic_ns"], 20_000_000)
        wire = SENDER.load_scene("A")[3]
        self.assertEqual(result["write_return_counts"], [29, 98])
        self.assertEqual(sum(result["write_return_counts"]), len(wire))

    def test_partial_writes_continue_from_unwritten_offset(self):
        offsets = [0]
        sizes = iter((13, 47, 67))
        wire = SENDER.load_scene("A")[3]

        def writer(_fd, remaining):
            self.assertEqual(len(remaining), len(wire) - offsets[0])
            count = next(sizes)
            offsets[0] += count
            return count

        result = self.run_send((writer,))
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["write_return_counts"], [13, 47, 67])

    def test_blocked_write_is_killed_at_transport_deadline(self):
        def blocked_writer(_fd, _remaining):
            time.sleep(10)
            return 127

        started = time.monotonic()
        result = self.run_send((blocked_writer,), timeout=0.15)
        elapsed = time.monotonic() - started
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["send_drain_timeout_stage"], "write")
        self.assertEqual(result["transmission_classification"],
                         "TRANSMISSION_STATE_UNKNOWN_AFTER_WRITE_TIMEOUT")
        self.assertTrue(result["device_write_state_unknown"])
        self.assertLess(elapsed, 1.0)
        self.assertLess(result["transport_worker_exitcode"], 0)
        self.assertFalse(any(child.name == "gpu-t1g-bounded-transport"
                             for child in multiprocessing.active_children()))

    def test_blocked_drain_is_killed_after_full_write(self):
        def blocked_drainer(_fd):
            time.sleep(10)

        started = time.monotonic()
        result = self.run_send((127,), drain_error=blocked_drainer,
                               timeout=0.15)
        elapsed = time.monotonic() - started
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["written"], 127)
        self.assertEqual(result["send_drain_timeout_stage"], "drain")
        self.assertEqual(result["transmission_classification"],
                         "FULL_PACKET_WRITTEN_DRAIN_FAILED")
        self.assertLess(elapsed, 1.0)
        self.assertLess(result["transport_worker_exitcode"], 0)
        self.assertFalse(any(child.name == "gpu-t1g-bounded-transport"
                             for child in multiprocessing.active_children()))

    def test_expiry_after_partial_progress_stops_without_replay(self):
        offset = [0]

        def partial_then_block(_fd, remaining):
            if offset[0] == 0:
                offset[0] = 40
                return 40
            time.sleep(10)
            return len(remaining)

        result = self.run_send((partial_then_block,), timeout=0.15)
        self.assertEqual(result["written"], 40)
        self.assertEqual(result["write_return_counts"], [40])
        self.assertEqual(result["send_drain_timeout_stage"], "write")
        self.assertEqual(result["transmission_classification"],
                         "TRANSMISSION_STATE_UNKNOWN_AFTER_WRITE_TIMEOUT")
        self.assertLess(result["transport_worker_exitcode"], 0)

    def test_post_drain_delay_is_inside_the_transport_bound(self):
        def blocked_delay(_seconds):
            time.sleep(10)

        result = self.run_send((127,), timeout=0.15, sleeper=blocked_delay)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(result["tcdrain_completed"])
        self.assertFalse(result["post_drain_delay_completed"])
        self.assertEqual(result["send_drain_timeout_stage"], "post_drain_delay")
        self.assertEqual(result["transmission_classification"],
                         "COMPLETED_HOST_WRITE")
        self.assertLess(result["transport_worker_exitcode"], 0)

    def test_existing_transcript_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="t1g_sender_test_",
                                         dir=ROOT / "build") as temporary:
            transcript = Path(temporary) / "scene_A.json"
            transcript.write_text("prior evidence\n")
            args = ["send_gpu_t1g_scene.py", "--scene", "A", "--port",
                    "/offline/fake_uart", "--transcript", str(transcript),
                    "--timeout-seconds", "2"]
            with patch.object(sys, "argv", args), \
                    patch.object(SENDER.os, "open") as uart_open:
                with self.assertRaises(FileExistsError):
                    SENDER.main()
            uart_open.assert_not_called()
            self.assertEqual(transcript.read_text(), "prior evidence\n")

    def test_open_failure_preserves_zero_byte_transcript(self):
        with tempfile.TemporaryDirectory(prefix="t1g_sender_test_",
                                         dir=ROOT / "build") as temporary:
            transcript = Path(temporary) / "scene_A.json"
            args = ["send_gpu_t1g_scene.py", "--scene", "A", "--port",
                    "/offline/missing_uart", "--transcript", str(transcript),
                    "--timeout-seconds", "2"]
            with patch.object(sys, "argv", args), \
                    patch.object(SENDER, "open_uart",
                                 side_effect=FileNotFoundError("gone")):
                with self.assertRaises(FileNotFoundError):
                    SENDER.main()
            result = json.loads(transcript.read_text())
            self.assertEqual(result["result"], "FAIL")
            self.assertEqual(result["written"], 0)
            self.assertFalse(result["tcdrain_completed"])
            self.assertIn("gone", result["error"])
            self.assertEqual(result["transmission_classification"],
                             "UART_OPEN_FAILURE_ZERO_BYTES")


if __name__ == "__main__":
    unittest.main()
