#!/usr/bin/env python3
"""R1 independent sizes, reconstruction, strict-stream and geometry checks."""
import hashlib
import io
import itertools
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_lossless_reduction_r1 as experiment
from software.experiments import spu_lossless_storage as storage
from software.experiments import spu_lossless_reduction as r0
from software.tests.test_spu_lossless_reduction import reference_depth, reference_pack

COUNTS, GEOMETRY = Counter(), {}


def independent_sizes(values):
    count = len(values)
    unsigned = [2*v if v >= 0 else -2*v-1 for v in values]
    bits = max((u.bit_length() for u in unsigned), default=0)
    packed = 5+(1+(count*bits+7)//8 if count else 0)
    g = math.gcd(*values) or 1
    reduced = [v//g for v in values]
    reduced_bits = max(((2*v if v >= 0 else -2*v-1).bit_length() for v in reduced), default=0)
    sizes = {0: 5+8*count, 2: packed, 3: 13+(1+(count*reduced_bits+7)//8 if count else 0)}
    widths = [(16, 16, 32)[i % 3] for i in range(count)]
    if all(-(1 << (w-1)) <= v < (1 << (w-1)) for v, w in zip(values, widths)):
        sizes[1] = 5+sum(widths)//8
    return sizes


class R1Tests(unittest.TestCase):
    scenes = []

    def test_corpus_blocks_and_every_mode(self):
        self.assertEqual(experiment.corpus(), self.scenes)
        self.assertEqual(len([s for s in self.scenes if s["kind"] == "synthetic"]), 36)
        self.assertEqual(len({s["name"] for s in self.scenes}), len(self.scenes))
        for name, values in experiment.blocks(self.scenes):
            self.assertEqual(len(values), 9)
            expected = independent_sizes(values)
            streams = storage.alternatives(values)
            self.assertEqual(set(streams), set(expected))
            for mode, stream in streams.items():
                self.assertEqual(len(stream), expected[mode], name)
                self.assertEqual(stream[0], mode)
                self.assertEqual(storage.decode(stream), list(values), name)
                self.assertEqual(storage.encode(storage.decode(stream), mode), stream)
                if mode == 2:
                    self.assertEqual(stream[1:], reference_pack(values))
                COUNTS["eligible_mode_roundtrips"] += 1
            selected = storage.select(values)
            expected_mode = min(expected, key=lambda m: (expected[m], m))
            self.assertEqual(selected, streams[expected_mode])
            self.assertEqual(storage.decode(selected), list(values))
            COUNTS["corpus_blocks"] += 1
        rows = experiment.sizes(experiment.blocks(self.scenes))
        self.assertEqual(rows["all_blocks"]["selected"], sum(r["selected_bytes"] for r in rows["blocks"]))
        self.assertTrue(any(r["renderer_field_exclusion"] for r in rows["blocks"]))

    def test_winners_ties_domains_and_golden_fields(self):
        for values, mode in (([], 0), ([r0.MIN_I64], 0), ([0]*9, 2),
                             ([12000, -24000, 36000, 0]*8, 3)):
            self.assertEqual(storage.select(values)[0], mode)
            for stream in storage.alternatives(values).values():
                self.assertEqual(storage.decode(stream), values)
        self.assertEqual(storage.encode([-1, 2, -3], 1),
                         bytes.fromhex("0103000000ffff0200fdffffff"))
        baseline = next(s for s in self.scenes if s["name"] == "synthetic_large")
        values = tuple(c for e in r0.triangle_edges(baseline["triangles"][0]) for c in e)
        self.assertEqual(storage.raw_renderer_bytes(values), 24)
        self.assertEqual(len(storage.encode(values, 1)), 29)
        self.assertEqual(storage.select(values)[0], min(independent_sizes(values), key=lambda m: (independent_sizes(values)[m], m)))
        for count in (1, 31, 32):
            for value in (r0.MIN_I64, r0.MAX_I64, -1, 0, 1):
                values = [value]*count
                for stream in storage.alternatives(values).values():
                    self.assertEqual(storage.decode(stream), values)
                    COUNTS["boundary_roundtrips"] += 1
        for values in ([True], [1.0], [r0.MIN_I64-1], [r0.MAX_I64+1], [0]*33):
            for method in (storage.select, storage.alternatives):
                with self.assertRaises(ValueError):
                    method(values)
        for mode in (True, -1, 4):
            with self.assertRaises(ValueError):
                storage.encode([], mode)
        with self.assertRaises(ValueError):
            storage.encode([32768], 1)
        with self.assertRaises(ValueError):
            storage.encode([0, 0, 1 << 31], 1)

    def test_malformed_stream_rejection(self):
        for mode, stream in storage.alternatives([-4, 2, 0]).items():
            for end in range(len(stream)):
                with self.assertRaises(ValueError):
                    storage.decode(stream[:end])
                COUNTS["malformed_streams"] += 1
            with self.assertRaises(ValueError):
                storage.decode(stream+b"\x00")
            offset = 9 if mode == 3 else 1
            invalid_count = stream[:offset]+(33).to_bytes(4, "little")+stream[offset+4:]
            with self.assertRaises(ValueError):
                storage.decode(invalid_count)
            COUNTS["malformed_streams"] += 2
        broken = [b"\xff"+bytes(4), bytearray(storage.encode([1], 0)),
                  b"\x02"+bytes.fromhex("010000004100"),
                  b"\x02"+bytes.fromhex("01000000030f"),
                  b"\x02"+bytes.fromhex("010000000201"),
                  b"\x03"+bytes(8)+r0.pack([1]),
                  b"\x03"+(2).to_bytes(8, "little")+r0.pack([2]),
                  b"\x03"+(2).to_bytes(8, "little")+r0.pack([0]),
                  b"\x03"+((1 << 64)-1).to_bytes(8, "little")+r0.pack([2])]
        for stream in broken:
            with self.assertRaises(ValueError):
                storage.decode(stream)
            COUNTS["malformed_streams"] += 1

    def test_selected_geometry(self):
        selected_names = {"synthetic_awkward", "synthetic_shared_factor", "synthetic_boundary_tie",
                          "synthetic_large_outlier", "synthetic_pixel", "synthetic_sliver", "real_t1d_two_triangle"}
        for scene in self.scenes:
            if scene["name"] not in selected_names:
                continue
            decoded = []
            for vertices in scene["triangles"]:
                values = tuple(c for e in r0.triangle_edges(vertices) for c in e)
                restored = storage.decode(storage.select(values))
                decoded.append(tuple(tuple(restored[i:i+3]) for i in range(0, 9, 3)))
            full = scene["name"] == "synthetic_awkward"
            if full:
                points = ((x, y) for y in range(480) for x in range(640))
            else:
                grid = set(itertools.product(range(0, 640, 16), range(0, 480, 16)))
                for vertices in scene["triangles"]:
                    for x, y, _ in vertices:
                        grid.update((x+dx, y+dy) for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)))
                points = sorted(grid)
            samples, overlap, digest = 0, 0, hashlib.sha256()
            for x, y in points:
                expected = [reference_depth(v, x, y) for v in scene["triangles"]]
                actual = [r0.edge_depth(e, [v[2] for v in vertices], x, y)
                          for e, vertices in zip(decoded, scene["triangles"])]
                self.assertEqual(actual, expected, (scene["name"], x, y))
                expected_winner = min((d, i) for i, d in enumerate(expected) if d is not None)[1] if any(d is not None for d in expected) else None
                actual_winner = min((d, i) for i, d in enumerate(actual) if d is not None)[1] if any(d is not None for d in actual) else None
                self.assertEqual(actual_winner, expected_winner)
                overlap += sum(d is not None for d in expected) > 1
                digest.update(repr(expected).encode())
                samples += 1
            GEOMETRY[scene["name"]] = {"samples": samples, "full_640x480": full, "overlap_samples": overlap,
                                       "coverage_depth_sha256": digest.hexdigest()}
            COUNTS["geometry_pixels"] += samples
            COUNTS["geometry_triangle_samples"] += 2*samples
        self.assertEqual(GEOMETRY["synthetic_awkward"]["samples"], 640*480)
        self.assertGreater(GEOMETRY["synthetic_boundary_tie"]["overlap_samples"], 0)
        with self.assertRaises(ValueError):
            r0.triangle_edges([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    def test_existing_output_refusal(self):
        base = ROOT / "build/spu_lossless_reduction"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".r1_existing_", dir=base) as temporary:
            marker = Path(temporary)/"existing.txt"
            marker.write_text("preserve")
            result = subprocess.run([sys.executable, str(Path(experiment.__file__)), "--out", temporary],
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(marker.read_text(), "preserve")
            self.assertEqual(list(Path(temporary).iterdir()), [marker])


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args)
        self.passed_methods = set()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_methods.add(test._testMethodName)


def check_correctness(scenes=None):
    COUNTS.clear()
    GEOMETRY.clear()
    R1Tests.scenes = experiment.corpus() if scenes is None else scenes
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2, failfast=True, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(R1Tests))
    lossless = {"test_corpus_blocks_and_every_mode", "test_winners_ties_domains_and_golden_fields", "test_malformed_stream_rejection"}
    return {"coefficient_reconstruction": "LOSSLESS_PASS" if lossless <= result.passed_methods else "INCOMPLETE_OR_FAILED",
            "geometry": "IDEAL_GEOMETRY_PASS" if "test_selected_geometry" in result.passed_methods else "INCOMPLETE_OR_FAILED",
            "tests_run": result.testsRun, "passed_methods": sorted(result.passed_methods), "check_counts": dict(COUNTS),
            "geometry_scenes": dict(GEOMETRY), "failures": [{"test": t.id(), "details": trace} for t, trace in result.failures+result.errors],
            "device_equivalence": "DEVICE_EQUIVALENCE_NOT_TESTED"}, result.wasSuccessful()


if __name__ == "__main__":
    record, success = check_correctness()
    print(json.dumps(record, indent=2, sort_keys=True))
    raise SystemExit(0 if success else 1)
