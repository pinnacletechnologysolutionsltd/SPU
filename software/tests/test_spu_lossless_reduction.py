#!/usr/bin/env python3
"""Independent R0 reconstruction, malformed-stream and vertex-area oracles."""
from __future__ import annotations

import hashlib
import io
import itertools
import json
import math
import platform
import random
import subprocess
import sys
import tempfile
import time
import unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_lossless_reduction as candidate

EXAMPLE = ROOT / "examples/gpu/t1d_two_triangle.json"
COUNTS, GEOMETRY = Counter(), {}
SCENE_INPUTS = tuple(sorted((ROOT / "examples/gpu").glob("t1d_two_triangle*.json")))
REFERENCE_SOURCE = ROOT / "software/spu_gpu_eval/reference.py"


def tagged_block(values):
    """Size experiment only: tag 0=fixed, 1=packed, 2=factored-packed."""
    if len(values) > 32:
        raise ValueError("experiment block exceeds 32 values")
    fixed = len(values).to_bytes(4, "little") + b"".join(
        x.to_bytes(8, "little", signed=True) for x in values)
    alternatives = [b"\x00"+fixed, b"\x01"+candidate.pack(values),
                    b"\x02"+candidate.factor_pack(values)]
    selected = min(range(3), key=lambda i: len(alternatives[i]))
    return selected, alternatives


def collection_sizes():
    records = []
    for path in SCENE_INPUTS:
        scene = json.loads(path.read_text())
        for index, triangle in enumerate(scene["triangles"]):
            values = tuple(c for edge in candidate.triangle_edges(triangle["vertices"]) for c in edge)
            mode, streams = tagged_block(values)
            records.append({"scene": str(path.relative_to(ROOT)), "triangle": index,
                            "values": len(values), "tagged_bytes": [len(s) for s in streams],
                            "selected_mode": mode, "selected_bytes": len(streams[mode])})
    return {"scope": "existing related T1d bringup examples; not a representative scene corpus",
            "scene_count": len(SCENE_INPUTS), "block_policy": "one nine-coefficient triangle per block",
            "mode_tags": {"0": "fixed_i64", "1": "candidate_a", "2": "factor_plus_candidate_a"},
            "tag_bytes_per_block": 1, "tie_rule": "lowest mode tag",
            "blocks": records, "selected_total_bytes": sum(r["selected_bytes"] for r in records),
            "tagged_mode_total_bytes": [sum(r["tagged_bytes"][i] for r in records) for i in range(3)]}


def reference_pack(values):
    """Bit-by-bit serialization, independent of the candidate accumulator."""
    result = bytearray(len(values).to_bytes(4, "little"))
    for offset in range(0, len(values), 32):
        values32 = values[offset:offset+32]
        unsigned = [2*x if x >= 0 else 2*(-x-1)+1 for x in values32]
        width = max(u.bit_length() for u in unsigned)
        result.append(width)
        payload = bytearray((width*len(unsigned)+7)//8)
        for index, value in enumerate(unsigned):
            for bit in range(width):
                position = index*width+bit
                if value & (1 << bit):
                    payload[position//8] |= 1 << (position % 8)
        result.extend(payload)
    return bytes(result)


def oriented_area(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def reference_depth(vertices, x, y):
    """Only vertices and oriented areas; no edge tuples or reducers."""
    area = oriented_area(*vertices)
    if not area:
        raise ValueError("degenerate reference triangle")
    p = (x, y)
    weights = (oriented_area(p, vertices[1], vertices[2]),
               oriented_area(vertices[0], p, vertices[2]),
               oriented_area(vertices[0], vertices[1], p))
    if any(w*area < 0 for w in weights):
        return None
    return Fraction(sum(w*v[2] for w, v in zip(weights, vertices)), area)


def prepared(vertices):
    edges = candidate.triangle_edges(vertices)
    g, reduced = candidate.factor(tuple(c for edge in edges for c in edge))
    return edges, tuple(tuple(reduced[i:i+3]) for i in range(0, 9, 3)), g


def width_distribution(values):
    # Minimal signed two's-complement widths (zero still needs one bit).
    return dict(sorted(Counter((x if x >= 0 else ~x).bit_length()+1
                               for x in values).items()))


def size_record(name, values):
    values = tuple(values)
    g, reduced = candidate.factor(values)
    record = {"name": name, "count": len(values), "factor": g,
              "coefficient_widths": width_distribution(values),
              "reduced_coefficient_widths": width_distribution(reduced)}
    try:
        packed = candidate.pack(values)
        baseline = len(values).to_bytes(4, "little") + b"".join(
            value.to_bytes(8, "little", signed=True) for value in values)
        factored = candidate.factor_pack(values)
    except (ValueError, OverflowError) as error:
        record.update(storage_supported=False, exclusion=str(error))
        return record
    sizes = {"fixed_baseline": len(baseline), "candidate_a": len(packed),
             "factor_plus_candidate_a": len(factored)}
    record.update(storage_supported=True, bytes=sizes,
                  encoded_sha256={"fixed_baseline": hashlib.sha256(baseline).hexdigest(),
                                  "candidate_a": hashlib.sha256(packed).hexdigest(),
                                  "factor_plus_candidate_a": hashlib.sha256(factored).hexdigest()})
    record["comparisons"] = {}
    for alternative, baseline_key in (("candidate_a", "fixed_baseline"),
                                      ("factor_plus_candidate_a", "candidate_a"),
                                      ("factor_plus_candidate_a", "fixed_baseline")):
        delta = sizes[alternative]-sizes[baseline_key]
        record["comparisons"][alternative+"_vs_"+baseline_key] = {
            "bytes_delta": delta,
            "result": "SIZE_REDUCTION" if delta < 0 else "EXPANSION" if delta > 0 else "UNCHANGED"}
    return record


class LosslessReductionTests(unittest.TestCase):
    def test_tagged_selection_and_reference_provenance(self):
        blocks = [([1]*31+[candidate.MAX_I64], 0), ([-3, -1, 0, 2]*8, 1),
                  ([12000, -24000, 36000, 0]*8, 2)]
        for path in SCENE_INPUTS:
            for triangle in json.loads(path.read_text())["triangles"]:
                blocks.append(([c for e in candidate.triangle_edges(triangle["vertices"]) for c in e], None))
        for values, expected_mode in blocks:
            mode, streams = tagged_block(values)
            if expected_mode is not None:
                self.assertEqual(mode, expected_mode)
            self.assertEqual(len(streams[mode]), min(map(len, streams)))
            for stream in streams:
                tag, data = stream[0], stream[1:]
                if tag == 0:
                    count = int.from_bytes(data[:4], "little")
                    decoded = [int.from_bytes(data[4+i*8:12+i*8], "little", signed=True)
                               for i in range(count)]
                elif tag == 1:
                    decoded = candidate.unpack(data)
                else:
                    factor = int.from_bytes(data[:8], "little")
                    decoded = [factor*x for x in candidate.unpack(data[8:])]
                self.assertEqual(decoded, values)
            COUNTS["tagged_selection_blocks"] += 1
        if SCENE_INPUTS and REFERENCE_SOURCE.is_file():
            from software.spu_gpu_eval.reference import pixel_decision
            from software.spu_gpu_eval.scene import parse_scene_bytes
            for path in SCENE_INPUTS:
                scene = parse_scene_bytes(path.read_bytes())
                vertices = json.loads(path.read_text())["triangles"]
                for x, y in ((0, 0), (320, 0), (100, 300), (320, 240), (639, 479)):
                    expected = [reference_depth(t["vertices"], x, y) for t in vertices]
                    actual = pixel_decision(scene, x, y)
                    self.assertEqual(actual["covered_by"], [i for i, d in enumerate(expected) if d is not None])
                    for d in actual["depths"]:
                        self.assertEqual(Fraction(d["numerator"], d["denominator"]), expected[d["triangle"]])
                    COUNTS["existing_reference_crosschecks"] += 1

    def check_vector(self, values):
        actual = candidate.pack(values)
        self.assertEqual(actual, reference_pack(values))
        self.assertEqual(candidate.unpack(actual), list(values))
        self.assertEqual(candidate.pack(candidate.unpack(actual)), actual)
        expected_length = 4
        for offset in range(0, len(values), 32):
            block = values[offset:offset+32]
            width = max((2*x if x >= 0 else -2*x-1).bit_length() for x in block)
            expected_length += 1+(len(block)*width+7)//8
        self.assertEqual(len(actual), expected_length)
        COUNTS["packing_vectors"] += 1

    def reject_stream(self, data):
        with self.assertRaises(ValueError):
            candidate.unpack(data)
        COUNTS["malformed_streams"] += 1

    def test_packing_exhaustive_and_seeded(self):
        for length in range(4):
            for values in itertools.product(range(-4, 5), repeat=length):
                self.check_vector(values)
        rng = random.Random(13)
        for _ in range(1000):
            self.check_vector(tuple(rng.randint(candidate.MIN_I64, candidate.MAX_I64)
                                    for _ in range(rng.randint(0, 128))))

    def test_packing_golden_and_boundaries(self):
        self.assertEqual(candidate.pack([]), bytes.fromhex("00000000"))
        self.assertEqual(candidate.pack([0, 0, 0]), bytes.fromhex("0300000000"))
        self.assertEqual(candidate.pack([-1, 0, 1]), bytes.fromhex("030000000221"))
        self.assertEqual(candidate.pack([candidate.MIN_I64, candidate.MAX_I64]),
                         bytes.fromhex("0200000040") + b"\xff"*8 + b"\xfe" + b"\xff"*7)
        for length in (0, 1, 31, 32, 33, 64, 65, 128):
            for value in (0, -7, 7, candidate.MIN_I64, candidate.MAX_I64):
                self.check_vector([value]*length)
        for values in ([candidate.MIN_I64, candidate.MAX_I64, 0, -1, 1],
                       [1]*31+[candidate.MAX_I64], [-1, 0, 1]*11):
            self.check_vector(values)
        # Domain's maximum count: all-zero blocks avoid an enormous test payload.
        zeros = [0]*candidate.MAX_COUNT
        encoded = candidate.pack(zeros)
        self.assertEqual(len(encoded), 4+(candidate.MAX_COUNT+31)//32)
        self.assertEqual(candidate.unpack(encoded), zeros)
        COUNTS["packing_vectors"] += 1

    def test_packing_invalid_inputs_and_streams(self):
        for values in ([True], [False], [1.0], ["1"], [None],
                       [candidate.MIN_I64-1], [candidate.MAX_I64+1],
                       [0]*(candidate.MAX_COUNT+1)):
            with self.assertRaises(ValueError):
                candidate.pack(values)
            COUNTS["invalid_inputs"] += 1
        for values in ([-4, 0, 2], [0]*33, [candidate.MIN_I64]*33):
            encoded = candidate.pack(values)
            for end in range(len(encoded)):
                self.reject_stream(encoded[:end])
            self.reject_stream(encoded+b"\x00")
            self.reject_stream(bytes(4)+encoded[4:])
            self.reject_stream(encoded[:4]+b"\x41"+encoded[5:])
        self.reject_stream((candidate.MAX_COUNT+1).to_bytes(4, "little"))
        self.reject_stream(bytes.fromhex("010000000201"))  # over-wide canonical field
        self.reject_stream(bytes.fromhex("01000000030f"))  # nonzero padding
        self.reject_stream(bytes.fromhex("0100000000ff"))  # width-zero trailing payload
        self.reject_stream((33).to_bytes(4, "little")+b"\x00")  # missing second width
        self.reject_stream(bytearray(candidate.pack([1])))

    def test_factors_rationals_and_surds(self):
        vectors = [(), (0, 0), (-6, 12, 18), (7, -11, 13),
                   (candidate.MIN_I64, 0), (10**18, -2*10**18, 3*10**18),
                   (1 << 70, 2 << 70)]
        for values in vectors:
            g, reduced = candidate.factor(values)
            self.assertGreater(g, 0)
            self.assertEqual(tuple(g*x for x in reduced), values)
            if any(values):
                self.assertEqual(math.gcd(*reduced), 1)
            else:
                self.assertEqual(g, 1)
            if g < 1 << 64 and all(candidate.MIN_I64 <= v <= candidate.MAX_I64 for v in values):
                stored = candidate.factor_pack(values)
                self.assertEqual(stored[:8], g.to_bytes(8, "little"))
                decoded_factor = int.from_bytes(stored[:8], "little")
                decoded_values = candidate.unpack(stored[8:])
                self.assertEqual(tuple(decoded_factor*v for v in decoded_values), values)
                self.assertEqual(len(stored), 8+len(reference_pack(reduced)))
            COUNTS["factor_tuples"] += 1
        self.assertEqual(size_record("empty", ())["bytes"],
                         {"fixed_baseline": 4, "candidate_a": 4, "factor_plus_candidate_a": 12})
        self.assertEqual(size_record("factor", (6, 12))["bytes"],
                         {"fixed_baseline": 20, "candidate_a": 7, "factor_plus_candidate_a": 14})
        with self.assertRaises(ValueError):
            candidate.factor_pack((1 << 64,))
        for values in ([True], [1.0]):
            with self.assertRaises(ValueError):
                candidate.factor(values)
        for p in range(-12, 13):
            for q in range(-12, 13):
                if q == 0:
                    with self.assertRaises(ValueError):
                        candidate.reduce_rational(p, q)
                else:
                    a, b = candidate.reduce_rational(p, q)
                    self.assertGreater(b, 0)
                    self.assertEqual(Fraction(a, b), Fraction(p, q))
                    self.assertEqual(math.gcd(a, b), 1)
                COUNTS["rational_pairs"] += 1
        operands = [(0, 0, 1), (6, -12, 7), (-10, 15, 3), (7, 11, 5),
                    (candidate.MIN_I64, 0, 17), (14, 21, 10)]
        for left, right in itertools.product(operands, repeat=2):
            l, r = candidate.reduce_surd(*left), candidate.reduce_surd(*right)
            for original, reduced in ((left, l), (right, r)):
                g, a, b, scale = reduced
                self.assertEqual((g*a, g*b, scale), original)
            polynomial = [Fraction(0)]*3
            for i in range(2):
                for j in range(2):
                    polynomial[i+j] += Fraction(left[i], left[2])*Fraction(right[j], right[2])
            expected = polynomial[0]+3*polynomial[2], polynomial[1]
            self.assertEqual(candidate.multiply_surds(l, r), expected)
            COUNTS["surd_products"] += 1
        g, a, b, scale = candidate.reduce_surd(6, 12, 7)
        self.assertNotEqual((Fraction(a, scale), Fraction(b, scale)),
                            (Fraction(g*a, scale), Fraction(g*b, scale)))
        GEOMETRY["dropped_surd_factor_detected"] = True
        for args in ((1, 2, 0), (1, 2, -1), (True, 2, 1), (1, 2, True)):
            with self.assertRaises(ValueError):
                candidate.reduce_surd(*args)
        for args in ((True, 1), (1, False), (1.0, 1)):
            with self.assertRaises(ValueError):
                candidate.reduce_rational(*args)

    def compare_geometry(self, triangles, width, height, name, origin=(0, 0)):
        plans = [prepared(v) for v in triangles]
        covered, overlap, background = [0]*len(triangles), 0, 0
        digest = hashlib.sha256()
        for y in range(origin[1], origin[1]+height):
            for x in range(origin[0], origin[0]+width):
                ref = [reference_depth(v, x, y) for v in triangles]
                for index, (v, (edges, reduced, g)) in enumerate(zip(triangles, plans)):
                    depths = [point[2] for point in v]
                    self.assertEqual(candidate.edge_depth(edges, depths, x, y), ref[index])
                    self.assertEqual(candidate.edge_depth(reduced, depths, x, y), ref[index])
                    covered[index] += ref[index] is not None
                    COUNTS["geometry_triangle_samples"] += 1
                count = sum(d is not None for d in ref)
                overlap += count > 1
                background += count == 0
                digest.update(repr(ref).encode("ascii"))
                COUNTS["geometry_pixels"] += 1
        GEOMETRY[name] = {"width": width, "height": height, "origin": list(origin),
                          "coverage_per_triangle": covered, "overlap_pixels": overlap,
                          "background_pixels": background, "depth_coverage_sha256": digest.hexdigest(),
                          "factors": [p[2] for p in plans]}

    def test_triangle_synthetic_and_negative_control(self):
        vertices = ((0, 0, 0), (4, 0, 12), (0, 2, 24))
        shifted = tuple((x+1, y+1, z) for x, y, z in vertices)
        self.compare_geometry([vertices, shifted], 9, 7, "synthetic", (-2, -2))
        self.compare_geometry([vertices[::-1], shifted[::-1]], 9, 7, "synthetic_reversed", (-2, -2))
        self.assertEqual(reference_depth(vertices, 0, 0), Fraction(0))
        self.assertEqual(reference_depth(vertices, 4, 0), Fraction(12))
        self.assertIsNone(reference_depth(vertices, 5, 5))
        edges, reduced, _ = prepared(vertices)
        separate = [candidate.factor(edge)[1] for edge in edges]
        depths = [v[2] for v in vertices]
        self.assertEqual(reference_depth(vertices, 1, 1), Fraction(15))
        self.assertEqual(candidate.edge_depth(reduced, depths, 1, 1), Fraction(15))
        self.assertEqual(candidate.edge_depth(separate, depths, 1, 1), Fraction(12))
        for y in range(-2, 5):
            for x in range(-2, 7):
                self.assertEqual(candidate.edge_depth(edges, depths, x, y) is None,
                                 candidate.edge_depth(separate, depths, x, y) is None)
        GEOMETRY["negative_control"] = {"detected": True, "pixel": [1, 1],
                                        "exact_depth": 15, "independent_edge_reduction_depth": 12}
        zero_area = ((0, 0, 1), (1, 1, 2), (2, 2, 3))
        with self.assertRaises(ValueError):
            candidate.triangle_edges(zero_area)
        with self.assertRaises(ValueError):
            reference_depth(zero_area, 1, 1)
        with self.assertRaises(ValueError):
            candidate.triangle_edges(((True, 0, 0), (4, 0, 12), (0, 2, 24)))
        self.assertGreater(GEOMETRY["synthetic"]["overlap_pixels"], 0)
        self.assertGreater(GEOMETRY["synthetic"]["background_pixels"], 0)

    def test_triangle_t1d_full_raster(self):
        if not EXAMPLE.is_file():
            GEOMETRY["t1d"] = {"status": "NOT_AVAILABLE"}
            self.skipTest("optional named T1d JSON absent; synthetic checks remain runnable")
        scene = json.loads(EXAMPLE.read_text())
        self.assertEqual((scene["width"], scene["height"]), (640, 480))
        self.compare_geometry([t["vertices"] for t in scene["triangles"]], 640, 480, "t1d")

    def test_output_refusal(self):
        base = ROOT / "build/spu_lossless_reduction"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".r0_existing_", dir=base) as temp:
            sentinel = Path(temp) / "preserve.txt"
            sentinel.write_text("existing evidence")
            result = subprocess.run([sys.executable, str(candidate.__file__), "--out", temp],
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(sentinel.read_text(), "existing evidence")
            self.assertEqual(sorted(p.name for p in Path(temp).iterdir()), ["preserve.txt"])
        with tempfile.TemporaryDirectory(prefix="r0_outside_") as temp:
            result = subprocess.run([sys.executable, str(candidate.__file__), "--out", str(Path(temp)/"new")],
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(temp)/"new").exists())


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args)
        self.passed_methods = set()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_methods.add(test._testMethodName)


def collect_results():
    COUNTS.clear()
    GEOMETRY.clear()
    started, log = time.perf_counter_ns(), io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2, failfast=True,
                                    resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LosslessReductionTests))
    elapsed = time.perf_counter_ns()-started
    success = result.wasSuccessful()
    lossless_methods = {"test_packing_exhaustive_and_seeded", "test_packing_golden_and_boundaries",
                        "test_packing_invalid_inputs_and_streams", "test_factors_rationals_and_surds",
                        "test_output_refusal", "test_tagged_selection_and_reference_provenance"}
    geometry_methods = {"test_triangle_synthetic_and_negative_control"}
    if EXAMPLE.is_file():
        geometry_methods.add("test_triangle_t1d_full_raster")
    failures = [{"test": t.id(), "details": trace} for t, trace in result.failures+result.errors]
    workloads = [("empty", ()), ("zeros_32", (0,)*32), ("small_signed_32", (-3, -1, 0, 2)*8),
                 ("large_factor_32", (12000, -24000, 36000, 0)*8),
                 ("one_large_outlier_32", (1,)*31+(candidate.MAX_I64,)),
                 ("signed_endpoints", (candidate.MIN_I64, candidate.MAX_I64)),
                 ("unsupported_factor", (1 << 64,))]
    if EXAMPLE.is_file():
        scene = json.loads(EXAMPLE.read_text())
        workloads.extend(("t1d_triangle_"+str(i), tuple(c for e in candidate.triangle_edges(t["vertices"]) for c in e))
                         for i, t in enumerate(scene["triangles"]))
    paths = [Path(candidate.__file__), Path(__file__)] + list(SCENE_INPUTS)
    if SCENE_INPUTS and REFERENCE_SOURCE.is_file():
        paths.extend([REFERENCE_SOURCE, ROOT / "software/spu_gpu_eval/scene.py"])
    report = {"format": "spu_lossless_reduction_r0_v3", "seed": 13,
              "identity": {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                           "worktree": "dirty" if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT) else "clean",
                           "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},
              "correctness": {"lossless": "LOSSLESS_PASS" if lossless_methods <= result.passed_methods else "INCOMPLETE_OR_FAILED",
                              "ideal_geometry": "IDEAL_GEOMETRY_PASS" if geometry_methods <= result.passed_methods else "INCOMPLETE_OR_FAILED",
                              "device_equivalence": "DEVICE_EQUIVALENCE_NOT_TESTED",
                              "tests_run": result.testsRun, "passed_methods": sorted(result.passed_methods),
                              "check_counts": dict(COUNTS), "failures": failures,
                              "skips": [{"test": t.id(), "reason": reason} for t, reason in result.skipped],
                              "geometry": dict(GEOMETRY)},
              "sizes": {"named_inputs": [size_record(name, values) for name, values in workloads] if success else [],
                        "collection": collection_sizes() if success else None},
              "timing": {"host": platform.platform(), "python": sys.version,
                         "elapsed_ns": elapsed, "clock": "perf_counter_ns", "repetitions": 1,
                         "kind": "verification runtime; no encode/decode performance benchmark"},
              "limits": {"command_timeout_seconds": 60, "maximum_count": candidate.MAX_COUNT,
                         "hardware_operations": 0, "device_equivalence_tested": False,
                         "signed_integer_bits": 64, "factor_storage_bits": 64, "block_values": 32,
                         "exhaustive_lengths": [0, 3], "exhaustive_values": [-4, 4],
                         "random_vectors": 1000, "random_lengths": [0, 128],
                         "device_equivalence": "DEVICE_EQUIVALENCE_NOT_TESTED",
                         "storage_baseline": "four-byte count plus signed int64 values",
                         "reference_roles": {"test_spu_lossless_reduction.py": "independent vertex-area and bit serialization oracles",
                                             "software/spu_gpu_eval/reference.py": "additional existing-reference sample crosschecks"}}}
    return report, success


if __name__ == "__main__":
    report, success = collect_results()
    print(json.dumps(report["correctness"], indent=2, sort_keys=True))
    print("verification elapsed nanoseconds:", report["timing"]["elapsed_ns"])
    raise SystemExit(0 if success else 1)
