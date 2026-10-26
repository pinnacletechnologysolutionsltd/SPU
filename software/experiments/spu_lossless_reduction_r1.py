#!/usr/bin/env python3
"""Bounded R1 scene storage/cost experiment using the existing R0 codecs."""
import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_lossless_reduction as r0, spu_lossless_storage as storage

SEED, TRIALS, REPETITIONS = 13, 5, 100
PRESETS = {
    "pixel": [(0, 0), (1, 0), (0, 1)], "small": [(40, 40), (43, 40), (40, 42)],
    "large": [(0, 0), (639, 0), (0, 479)], "awkward": [(0, 0), (639, 1), (1, 478)],
    "sliver": [(0, 0), (639, 479), (638, 478)], "shared_factor": [(0, 0), (600, 0), (0, 400)],
    "translated": [(127, 113), (509, 114), (130, 431)], "clipped": [(-50, -20), (400, 3), (2, 300)],
    "background": [(1000, 1000), (1003, 1000), (1000, 1004)],
    "large_outlier": [(10**9, 10**9), (10**9+600, 10**9+1), (10**9+1, 10**9+400)],
    "wide_signed": [(-10**9, 10**9), (10**9, -10**9+1), (10**9-1, 10**9)],
    "boundary_tie": [(40, 0), (600, 0), (320, 460)]}


def corpus():
    scenes, rng = [], random.Random(SEED)
    for path in sorted((ROOT / "examples/gpu").glob("t1d_two_triangle*.json")):
        source = json.loads(path.read_text())
        scenes.append({"name": "real_"+path.stem, "origin": str(path.relative_to(ROOT)),
                       "kind": "maintained_example", "triangles": [t["vertices"] for t in source["triangles"]]})
    shapes = list(PRESETS.items())
    for i in range(24):
        x, y, w, h = rng.randint(-128, 639), rng.randint(-128, 479), rng.randint(3, 640), rng.randint(3, 480)
        shapes.append(("seeded_"+str(i), [(x, y), (x+w, y+1), (x+2, y+h)]))
    for i, (name, points) in enumerate(shapes):
        depths = [1000]*3 if name in ("shared_factor", "boundary_tie") else [0, 65535, 1] if i < 12 else [rng.randrange(65536) for _ in range(3)]
        first = [[x, y, z] for (x, y), z in zip(points, depths)]
        if i % 2:
            first.reverse()
        second = [[x+3, y-2, z] for x, y, z in reversed(first)]
        scenes.append({"name": "synthetic_"+name, "kind": "synthetic", "origin": "seed_13" if i >= 12 else "designed",
                       "triangles": [first, second]})
    return scenes


def blocks(scenes):
    return [(scene["name"]+"/"+str(i), tuple(c for e in r0.triangle_edges(v) for c in e))
            for scene in scenes for i, v in enumerate(scene["triangles"])]


def sizes(items):
    rows = []
    for name, values in items:
        streams = storage.alternatives(values)
        selected = storage.select(values)
        rows.append({"name": name, "values": len(values), "factor": r0.factor(values)[0],
                     "tagged_bytes": {storage.MODE_NAMES[m]: len(s) for m, s in streams.items()},
                     "renderer_raw_field_bytes": storage.raw_renderer_bytes(values) if 1 in streams else None,
                     "renderer_field_exclusion": None if 1 in streams else "signed 16/16/32 coefficient range exceeded",
                     "selected_mode": storage.MODE_NAMES[selected[0]], "selected_bytes": len(selected)})
    eligible = [r for r in rows if r["renderer_raw_field_bytes"] is not None]
    return {"blocks": rows, "selected_mode_counts": {name: sum(r["selected_mode"] == name for r in rows) for name in storage.MODE_NAMES.values()},
            "all_blocks": {"selected": sum(r["selected_bytes"] for r in rows), "tagged_i64": sum(r["tagged_bytes"]["fixed_i64"] for r in rows)},
            "renderer_eligible_blocks": {"count": len(eligible), "selected": sum(r["selected_bytes"] for r in eligible),
                                         "tagged_renderer": sum(r["tagged_bytes"]["fixed_renderer_fields"] for r in eligible),
                                         "raw_renderer_fields": sum(r["renderer_raw_field_bytes"] for r in eligible)}}


def benchmark(items, cohort):
    records = []
    for mode in (*storage.MODE_NAMES, "automatic"):
        eligible = [(v, storage.select(v) if mode == "automatic" else storage.encode(v, mode))
                    for _, v in items if mode == "automatic" or mode in storage.alternatives(v)]
        encode = storage.select if mode == "automatic" else lambda v, m=mode: storage.encode(v, m)
        enc, dec = [], []
        for _ in range(TRIALS):
            started = time.perf_counter_ns()
            for _ in range(REPETITIONS):
                for values, _ in eligible:
                    encode(values)
            enc.append(time.perf_counter_ns()-started)
            started = time.perf_counter_ns()
            for _ in range(REPETITIONS):
                for _, stream in eligible:
                    storage.decode(stream)
            dec.append(time.perf_counter_ns()-started)
        operations = len(eligible)*REPETITIONS
        records.append({"cohort": cohort, "mode": mode if mode == "automatic" else storage.MODE_NAMES[mode], "eligible_blocks": len(eligible),
                        "operations_per_trial": operations, "values_per_trial": sum(len(v) for v, _ in eligible)*REPETITIONS,
                        "bytes_per_trial": sum(len(s) for _, s in eligible)*REPETITIONS, "encode_trial_ns": enc, "decode_trial_ns": dec,
                        "encode_median_ns": statistics.median(enc), "decode_median_ns": statistics.median(dec),
                        "encode_ns_per_block": {"numerator": statistics.median(enc), "denominator": operations},
                        "decode_ns_per_block": {"numerator": statistics.median(dec), "denominator": operations}})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    target = parser.parse_args().out.resolve()
    base = (ROOT / "build/spu_lossless_reduction").resolve()
    if target == base or not target.is_relative_to(base) or target.exists():
        parser.error("output must be a fresh child of build/spu_lossless_reduction")
    scenes = corpus()
    from software.tests.test_spu_lossless_reduction_r1 import check_correctness
    correctness, success = check_correctness(scenes)
    items = blocks(scenes) if success else []
    renderer_items = [(name, v) for name, v in items if 1 in storage.alternatives(v)]
    raw = (json.dumps(scenes, indent=2, sort_keys=True)+"\n").encode()
    source_paths = [Path(__file__), Path(storage.__file__), Path(r0.__file__), ROOT / "software/tests/test_spu_lossless_reduction_r1.py",
                    ROOT / "software/tests/test_spu_lossless_reduction.py"] + sorted((ROOT / "examples/gpu").glob("t1d_two_triangle*.json"))
    report = {"format": "spu_lossless_storage_r1_v1", "seed": SEED, "correctness": correctness,
              "identity": {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                           "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
                           "source_input_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                           "independent_reference": "software/tests/test_spu_lossless_reduction.py:reference_depth/reference_pack",
                           "corpus_sha256": hashlib.sha256(raw).hexdigest()},
              "sizes": sizes(items) if success else None,
              "timing": {"clock": "perf_counter_ns", "trials": TRIALS, "repetitions": REPETITIONS, "host": platform.platform(),
                         "python": sys.version, "strict_decode_includes_canonicality": True,
                         "untimed_preparation": "eligibility and encoded-stream construction before each mode",
                         "measurements": benchmark(items, "all_i64_blocks")+benchmark(renderer_items, "renderer_eligible_blocks") if success else []},
              "limits": {"command_timeout_seconds": 60, "maximum_block_values": 32, "mode_tags": storage.MODE_NAMES,
                         "hardware_operations": 0, "device_equivalence_tested": False, "device_equivalence": "DEVICE_EQUIVALENCE_NOT_TESTED",
                         "scope": "coefficient blocks only; excludes depth, colour, scene metadata and GPU packet framing",
                         "corpus_scope": "designed synthetic cases and maintained examples; not a workload-frequency sample"}}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".r1_", dir=target.parent) as temporary:
        for name, data in (("corpus.json", raw), ("results.json", (json.dumps(report, indent=2, sort_keys=True)+"\n").encode())):
            (Path(temporary)/name).write_bytes(data)
        target.mkdir()
        for name in ("corpus.json", "results.json"):
            os.replace(Path(temporary)/name, target/name)
    print(json.dumps({"results": str(target/"results.json"), "pass": success}))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
