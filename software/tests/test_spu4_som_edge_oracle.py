#!/usr/bin/env python3
"""Tests for the SPU-4 edge SOM oracle (software/lib/spu4_som_edge_oracle.py).

This oracle's fixture (4 nodes x 4 features, and its 8 query vectors) is the
one hand-transcribed into hardware/tests/spu4/spu4_som_edge_full_chain_tb.v.
Keep the two in sync -- this file exists to prove the expected (best_node,
best_quadrance) pairs the Verilog TB checks against are actually oracle
output, not hand-arithmetic that could itself be wrong.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.rational_som import RationalSurd
from lib.spu4_som_edge_oracle import feature_quadrance_scalar, find_bmu_edge, node_quadrance


PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def rs(p, q=0):
    return RationalSurd(p, q)


# The exact fixture transcribed into spu4_som_edge_full_chain_tb.v's mock
# flash image and query sequence.
NODES = [
    [rs(100, 0), rs(0, 0), rs(0, 0), rs(0, 0)],
    [rs(0, 0), rs(0, 40), rs(0, 0), rs(0, 0)],
    [rs(-30, 0), rs(-30, 0), rs(60, 0), rs(0, 0)],
    [rs(0, 0), rs(0, 0), rs(0, 0), rs(50, 50)],
]

QUERIES = [
    ("exact match node 0", [rs(100, 0), rs(0, 0), rs(0, 0), rs(0, 0)], 0, 0),
    ("exact match node 1", [rs(0, 0), rs(0, 40), rs(0, 0), rs(0, 0)], 1, 0),
    ("exact match node 2", [rs(-30, 0), rs(-30, 0), rs(60, 0), rs(0, 0)], 2, 0),
    ("exact match node 3", [rs(0, 0), rs(0, 0), rs(0, 0), rs(50, 50)], 3, 0),
    ("near node 1, Q-dominated delta", [rs(0, 0), rs(0, 45), rs(0, 0), rs(0, 0)], 1, 75),
    ("negative deltas near node 2", [rs(-40, 0), rs(-25, 0), rs(55, 0), rs(0, 0)], 2, 150),
    # Exact tie between node 0 and node 1 (both quadrance 3700) -- the RTL's
    # strict `<` scan keeps the first (lowest-index) winner, never revisiting.
    ("exact tie node 0 / node 1", [rs(50, 0), rs(0, 20), rs(0, 0), rs(0, 0)], 0, 3700),
    # Feature index 3 is the deciding term here: dropping it (the bug found
    # 2026-08-17 in spu4_som_edge.v, where the quadrance sum was hardcoded to
    # exactly three terms regardless of NUM_FEATURES) flips the verdict from
    # node 1 (Q=6400, correct) to node 3 (Q=300) -- see this file's
    # test_feature_3_is_load_bearing below.
    ("far from all nodes, mixed sign", [rs(-5, 5), rs(5, -5), rs(-5, 5), rs(5, -5)], 1, 6400),
]


def test_oracle_matches_hand_fixture():
    for label, features, exp_node, exp_q in QUERIES:
        got_node, got_q = find_bmu_edge(features, NODES)
        check(f"{label}: best_node", got_node == exp_node)
        check(f"{label}: best_quadrance", got_q == exp_q)


def test_feature_quadrance_scalar_is_p2_plus_3q2():
    # dp=3, dq=2 -> 9 + 3*4 = 21
    check(
        "feature_quadrance_scalar(3,2 delta) == 21",
        feature_quadrance_scalar(rs(5, 5), rs(2, 3)) == 21,
    )


def test_node_quadrance_is_additive_across_features():
    a = [rs(1, 0), rs(0, 2)]
    b = [rs(0, 0), rs(0, 0)]
    # feature0: dp=1,dq=0 -> 1; feature1: dp=0,dq=2 -> 12; total 13
    check("node_quadrance additive", node_quadrance(a, b) == 13)


def test_feature_3_is_load_bearing():
    # The regression this file guards: with feature index 3 dropped, the
    # "far from all nodes" query's verdict flips from node 1 to node 3.
    full_features = QUERIES[-1][1]
    full_node, full_q = find_bmu_edge(full_features, NODES)
    dropped_node, dropped_q = find_bmu_edge(full_features[:3], [n[:3] for n in NODES])
    check("feature 3 included gives node 1", full_node == 1 and full_q == 6400)
    check("dropping feature 3 flips the verdict (proves it was load-bearing)",
          dropped_node != full_node)


def main():
    test_oracle_matches_hand_fixture()
    test_feature_quadrance_scalar_is_p2_plus_3q2()
    test_node_quadrance_is_additive_across_features()
    test_feature_3_is_load_bearing()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
