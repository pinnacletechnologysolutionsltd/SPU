#!/usr/bin/env python3
"""spu4_som_edge_demo.py — customer-facing demo for the SPU-4 SOM edge
classifier's interactive bench probe
(hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v).

Sends a small built-in set of feature vectors to real silicon (or the
board flashed with a demo/synthetic weight profile -- see
tools/gen_spu4_som_boot_image.py) over UART, and prints the hardware
result next to the independent software oracle
(software/lib/spu4_som_edge_oracle.py) result for each one. Doubles as a
portable regression, not just a demo: exit code is 0 only if every query's
hardware result matches the oracle exactly.

IMPORTANT: this runs against demo/synthetic weights by default (whichever
--profile matches what's actually flashed on the board) -- it is NOT a
validated real-sensor anomaly-detection result. See
knowledge/spu4-edge-node-focus and the INA226 capture campaign for that.

Wiring: same as tools/spu4_som_edge_smoketest.py -- the interactive
probe's uart_tx/uart_rx are the Tang Primer 25K dock's own host-bound
USB-CDC UART, no RP2350 southbridge involved. Board must be flashed with
the interactive probe bitstream, and the PMOD J4 SPI flash must carry a
boot image matching --profile -- see
build_25k_spu4_som_edge_interactive_probe.sh's header for the exact
commands.

--weights points at a trained weights JSON (tools/spu4_som_edge_trainer.py's
output, or anything matching tools/gen_spu4_som_boot_image.py's WeightsError
schema) instead of a canned profile -- for verifying a board actually
flashed with real trained weights rather than one of the three synthetic
profiles.

Usage:
    python3 tools/spu4_som_edge_demo.py --port /dev/ttyACM0
    python3 tools/spu4_som_edge_demo.py --port /dev/ttyACM0 --profile demo
    python3 tools/spu4_som_edge_demo.py --port /dev/ttyACM0 \\
        --weights tools/build/spu4_som_edge_synthetic_weights.json
"""

import argparse
import os
import sys
import types

try:
    import serial
except ImportError:
    # Deferred, same rationale as tools/robotics_demo.py.
    serial = types.ModuleType("serial")
    serial.Serial = None

REPO_ROOT = __file__.rsplit("/tools/", 1)[0]
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from software.lib.rational_som import RationalSurd
from software.lib.spu4_som_edge_oracle import find_bmu_edge
from software.lib.spu4_som_probe_client import ProbeTransport
from gen_spu4_som_boot_image import ORACLE_FIXTURE_WEIGHTS, load_weights, synthetic_profile

NUM_FEATURES = 4


def node_weights_as_surds(profile):
    """The 4 nodes' weight vectors for `profile`, as RationalSurd features
    -- the same source of truth tools/gen_spu4_som_boot_image.py uses to
    build the flash image, so a demo run only means something if the
    board was actually flashed with the same --profile."""

    if profile == "oracle_fixture":
        raw = ORACLE_FIXTURE_WEIGHTS
    else:
        raw = synthetic_profile(profile, NUM_FEATURES)
    return [[RationalSurd(p, q) for p, q in node] for node in raw]


def node_weights_from_file(path):
    """Same shape as node_weights_as_surds, but sourced from a trained
    weights JSON -- the demo run only means something if the board was
    actually flashed with tools/gen_spu4_som_boot_image.py --weights path
    using this exact file."""

    _feature_count, raw = load_weights(path)
    return [[RationalSurd(p, q) for p, q in node] for node in raw]


def build_demo_queries(nodes):
    """A small, profile-agnostic set of feature vectors: an exact match to
    each node (expected verdict is trivially that node, quadrance 0, by
    construction -- no profile-specific tuning needed) plus one
    between-nodes query for a genuinely interesting classification."""

    queries = [(f"exact match: node {i}", nodes[i]) for i in range(len(nodes))]
    midpoint = [
        RationalSurd((a.p + b.p) // 2, (a.q + b.q) // 2)
        for a, b in zip(nodes[0], nodes[1])
    ]
    queries.append(("midpoint of node 0 and node 1", midpoint))
    return queries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True, help="e.g. /dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--profile", choices=("oracle_fixture", "demo", "zero"),
                     default="oracle_fixture",
                     help="which flashed weight profile to assume (default: "
                          "oracle_fixture) -- must match what's actually on "
                          "the board's PMOD J4 flash chip; ignored if "
                          "--weights is given")
    ap.add_argument("--weights",
                     help="path to a trained weights JSON (overrides "
                          "--profile) -- must match what's actually on the "
                          "board's PMOD J4 flash chip")
    ap.add_argument("--timeout", type=float, default=5.0)
    ns = ap.parse_args(argv)

    if serial.Serial is None:
        print("ERROR: pyserial is not installed (pip install pyserial).", file=sys.stderr)
        return 1

    print("SPU-4 SOM edge classifier -- interactive demo")
    if ns.weights:
        print(f"(assuming weights from {ns.weights} are flashed; this is "
              f"demo/synthetic data, not a validated anomaly result -- see "
              f"knowledge/spu4-edge-node-focus)")
    else:
        print(f"(assuming --profile {ns.profile} is flashed; this is demo/synthetic "
              f"data, not a validated anomaly result -- see knowledge/spu4-edge-node-focus)")
    print("=" * 72)

    nodes = node_weights_from_file(ns.weights) if ns.weights else node_weights_as_surds(ns.profile)
    queries = build_demo_queries(nodes)

    ser = serial.Serial(ns.port, ns.baud, timeout=1)
    transport = ProbeTransport(ser)
    all_match = True
    try:
        for label, features in queries:
            hw = transport.classify(features, timeout_s=ns.timeout)
            oracle_node, oracle_q = find_bmu_edge(features, nodes)

            if hw is None:
                print(f"  {label:<32} HARDWARE: no response (timeout)")
                all_match = False
                continue
            if hw.status_char != "D":
                print(f"  {label:<32} HARDWARE: probe reported '{hw.status_char}' "
                      f"(malformed query, not a classification)")
                all_match = False
                continue

            match = (hw.best_node == oracle_node and hw.best_quadrance == oracle_q)
            all_match = all_match and match
            tag = "OK" if match else "MISMATCH"
            print(f"  {label:<32} HW: node={hw.best_node} Q={hw.best_quadrance:<6} "
                  f"ORACLE: node={oracle_node} Q={oracle_q:<6} [{tag}]")
    finally:
        ser.close()

    print("=" * 72)
    if all_match:
        print("PASS: every hardware classification matched the software oracle exactly.")
        return 0
    print("FAIL: at least one hardware result diverged from the oracle -- see above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
