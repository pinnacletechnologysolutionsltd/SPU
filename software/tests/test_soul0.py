#!/usr/bin/env python3
"""Focused Soul-0 checkpoint and adaptation controls."""

from __future__ import annotations

import json
import unittest

from software.research.soul0.model import DeviceCalibration, Soul0


class Soul0Test(unittest.TestCase):
    def test_checkpoint_roundtrip_preserves_future_trace_and_bytes(self) -> None:
        source = Soul0.seeded([98, 99, 100, 101, 102, 98, 99, 100])
        for value in (198, 199, 201):
            source.observe(value)
        checkpoint = source.to_bytes()
        restored = Soul0.from_bytes(checkpoint)
        future = (202, 100, 99, 101, 260, 100)
        source_trace = [source.observe(value)[0] for value in future]
        restored_trace = [restored.observe(value)[0] for value in future]
        self.assertEqual(source_trace, restored_trace)
        self.assertEqual(source.to_bytes(), restored.to_bytes())

    def test_transient_does_not_create_regime_but_persistent_shift_does(self) -> None:
        soul = Soul0.seeded([99, 100, 101, 102, 98, 99, 100, 101])
        soul.observe(160)
        soul.observe(101)
        self.assertEqual(len(soul.profiles), 1)
        for value in (198, 199, 201):
            soul.observe(value)
        self.assertEqual(len(soul.profiles), 2)

    def test_calibration_is_external_and_exact(self) -> None:
        soul = Soul0.seeded([98, 99, 100, 101, 102, 98, 99, 100])
        checkpoint = soul.to_bytes()
        document = json.loads(checkpoint)
        self.assertNotIn("calibration", document)
        calibration = DeviceCalibration(gain=3, offset=-7)
        self.assertEqual(calibration.normalize(calibration.encode(137)), 137)
        with self.assertRaises(ValueError):
            calibration.normalize(-5)

    def test_checkpoint_rejects_unknown_fields_and_versions(self) -> None:
        soul = Soul0.seeded([100, 101])
        document = json.loads(soul.to_bytes())
        document["firmware"] = "other"
        with self.assertRaises(ValueError):
            Soul0.from_bytes(json.dumps(document).encode("ascii"))
        document = json.loads(soul.to_bytes())
        document["schema_version"] = 99
        with self.assertRaises(ValueError):
            Soul0.from_bytes(json.dumps(document).encode("ascii"))


if __name__ == "__main__":
    unittest.main()
