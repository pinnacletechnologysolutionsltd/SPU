#!/usr/bin/env python3
"""Native C parity, not MCU speed evidence. Includes independent controls."""
import ctypes as c
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "software")]
from lib.som_current_monitor import extract_current_features
from software.lib.spu4_som_edge_oracle import find_bmu_edge
from software.lib.rational_som import RationalSurd


class Result(c.Structure):
    _fields_ = [("distance", c.c_uint32), ("node", c.c_uint8)]


def require(ok, msg):
    if not ok:
        raise AssertionError(msg)


def run():
    encoded = (ROOT / "docs/bench_captures/2026-09-08_spu4_ina226_freeze.json").read_bytes()
    require(hashlib.sha256(encoded).hexdigest() ==
            "6dcbb8e73597e0172531eca15baf3c2d666827e056c1eede45e59ab019188de6",
            "frozen benchmark artifact changed")
    data = json.loads(encoded)
    with tempfile.TemporaryDirectory(prefix="spu4-c-parity-") as tmp:
        lib_path = Path(tmp) / "edge.so"
        subprocess.run(["cc", "-std=c11", "-O3", "-Wall", "-Wextra", "-Werror",
                        "-shared", "-fPIC", "-fsanitize=undefined",
                        str(ROOT / "software/benchmarks/spu4_ina226_kernel.c"),
                        "-o", str(lib_path)], check=True)
        lib = c.CDLL(str(lib_path))
        i4, u4, i32 = c.c_int32*4, c.c_uint16*4, c.c_int32*32
        matrix = u4*4
        lib.edge_classify.restype = Result
        count = 0
        for fold in data["folds"]:
            weights = matrix(*(u4(*w) for w in fold["weights_p"]))
            for case in fold["cases"]:
                features, scaled = i4(), u4()
                lib.edge_features(i32(*case["raw_uA"]), features)
                require(list(features) == case["features"], "features mismatch")
                lib.edge_scale(features, i4(*fold["scaler"]["minima"]),
                               i4(*fold["scaler"]["maxima"]), scaled)
                require(list(scaled) == case["scaled"], "scaling mismatch")
                result = lib.edge_classify(scaled, weights)
                require((result.node, result.distance) == (case["best"], case["distance"]),
                        "classifier mismatch")
                require(fold["labels"][result.node] == case["label"], "label mismatch")
                count += 1
        rng = random.Random(188)
        controls = [[500]*32, [1500]*32, [-500]*32, [-1500]*32,
                    [-(2**31), 2**31-1]*16]
        controls += [[rng.randrange(-750000, 750001) for _ in range(32)] for _ in range(1000)]
        for samples in controls:
            features = i4()
            lib.edge_features(i32(*samples), features)
            require(tuple(features) == extract_current_features(samples), "feature control")
        for _ in range(1000):
            f = [rng.randrange(30001) for _ in range(4)]
            w = [[rng.randrange(30001) for _ in range(4)] for _ in range(4)]
            result = lib.edge_classify(u4(*f), matrix(*(u4(*row) for row in w)))
            node, distance = find_bmu_edge([RationalSurd(v, 0) for v in f],
                [[RationalSurd(v, 0) for v in row] for row in w])
            require((result.node, result.distance) == (node, distance), "random distance")
        result = lib.edge_classify(u4(0, 0, 0, 0), matrix(*(u4(30000, 30000, 30000, 30000) for _ in range(4))))
        require((result.node, result.distance) == (0, 3600000000), "unsigned bound/tie")
        print(f"PASS {count} frozen cases; 1005 feature controls; 1000 distance controls; unsigned bound/tie")


if __name__ == "__main__":
    run()
