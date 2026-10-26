"""Offline checks for the one-shot T1d vertex A/B sender."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import send_gpu_t1d_vertex_ab as sender


def staged_root():
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    for spec in sender.SCENES.values():
        source = ROOT / spec["packet"]
        target = root / spec["packet"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (root / sender.EVIDENCE).mkdir(parents=True)
    return temp, root


class T1dVertexAbSenderTests(unittest.TestCase):
    def test_a_and_b_are_frozen_64_byte_packets(self):
        temp, root = staged_root()
        with temp:
            for scene in ("A", "B"):
                spec = sender.SCENES[scene]
                packet_path, payload, digest, transcript = sender.prepare(
                    scene, sender.PORT, spec["transcript"], root
                )
                self.assertEqual(packet_path, root / spec["packet"])
                self.assertEqual(len(payload), 64)
                self.assertEqual(payload[0], 0xA5)
                self.assertEqual(digest, spec["sha256"])
                self.assertEqual(transcript, root / spec["transcript"])

    def test_bad_request_rejects_before_port_open(self):
        cases = (
            ("C", sender.PORT, sender.SCENES["A"]["transcript"]),
            ("A", "/dev/ttyUSB0", sender.SCENES["A"]["transcript"]),
            ("A", sender.PORT, "build/other/transcript.json"),
        )
        for scene, port, transcript in cases:
            with self.subTest(scene=scene, port=port, transcript=transcript):
                temp, root = staged_root()
                with temp, patch.object(sender.os, "open") as port_open:
                    with self.assertRaises(ValueError):
                        sender.send_once(scene, port, transcript, root)
                    port_open.assert_not_called()

    def test_existing_transcript_rejects_before_port_open(self):
        temp, root = staged_root()
        with temp:
            output = root / sender.SCENES["A"]["transcript"]
            output.write_text("preserve\n", encoding="utf-8")
            with patch.object(sender.os, "open") as port_open:
                with self.assertRaises(FileExistsError):
                    sender.send_once(
                        "A", sender.PORT, sender.SCENES["A"]["transcript"], root
                    )
                port_open.assert_not_called()
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve\n")

    def test_bad_packet_bytes_reject_before_port_open(self):
        mutations = (
            b"short",
            bytes([0x00]) + bytes(63),
            bytes([0xA5]) + bytes(63),
        )
        for payload in mutations:
            with self.subTest(length=len(payload), start=payload[:1]):
                temp, root = staged_root()
                with temp:
                    packet = root / sender.SCENES["A"]["packet"]
                    packet.write_bytes(payload)
                    with patch.object(sender.os, "open") as port_open:
                        with self.assertRaises(ValueError):
                            sender.send_once(
                                "A", sender.PORT,
                                sender.SCENES["A"]["transcript"], root
                            )
                        port_open.assert_not_called()

    def test_success_writes_one_transaction_and_transcript(self):
        temp, root = staged_root()
        with temp:
            transcript = sender.SCENES["A"]["transcript"]
            with (
                patch.object(sender.os, "open", return_value=17),
                patch.object(sender, "configure_port") as configure,
                patch.object(sender.os, "write", return_value=64) as write,
                patch.object(sender.termios, "tcdrain") as drain,
                patch.object(sender.time, "sleep") as wait,
                patch.object(sender.os, "close") as close,
            ):
                record = sender.send_once("A", sender.PORT, transcript, root)

            configure.assert_called_once_with(17)
            write.assert_called_once_with(
                17, (root / sender.SCENES["A"]["packet"]).read_bytes()
            )
            drain.assert_called_once_with(17)
            wait.assert_called_once_with(0.1)
            close.assert_called_once_with(17)
            self.assertEqual(record["status"], "TRANSMISSION_COMPLETE")
            output = root / transcript
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["scene"], "A")
            self.assertEqual(saved["written"], 64)
            self.assertTrue(saved["tcdrain_completed"])
            self.assertEqual(saved["post_drain_wait_ms"], 100)

    def test_short_write_is_drained_recorded_and_not_retried(self):
        temp, root = staged_root()
        with temp:
            transcript = sender.SCENES["B"]["transcript"]
            with (
                patch.object(sender.os, "open", return_value=19),
                patch.object(sender, "configure_port"),
                patch.object(sender.os, "write", return_value=17) as write,
                patch.object(sender.termios, "tcdrain") as drain,
                patch.object(sender.time, "sleep") as wait,
                patch.object(sender.os, "close"),
            ):
                with self.assertRaisesRegex(RuntimeError, "short write: 17/64"):
                    sender.send_once("B", sender.PORT, transcript, root)

            write.assert_called_once()
            drain.assert_called_once_with(19)
            wait.assert_called_once_with(0.1)
            saved = json.loads((root / transcript).read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "SHORT_WRITE")
            self.assertEqual(saved["written"], 17)
            self.assertTrue(saved["tcdrain_completed"])


if __name__ == "__main__":
    unittest.main()
