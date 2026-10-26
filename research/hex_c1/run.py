"""HEX-C1 scene, exhaustive comparison and metrics.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/hex_c1/run.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hier as H                                    # noqa: E402
from geom import N, HalfPlane, Shape                # noqa: E402

K = 4
FOCUS = (3, 1)


def refine_rule(c):
    """Irregular refinement: only near FOCUS."""
    return N((c[0] - FOCUS[0], c[1] - FOCUS[1])) <= 2 * 7 ** c[2]


def tangent_node(h):
    return min(c for c in h.nodes if c[2] == 1)


def scene(h):
    a1, b1, _ = tangent_node(h)
    hp = lambda a, b, g: HalfPlane(Fr(a), Fr(b), Fr(g))       # noqa: E731
    return [
        Shape("disk", disk=((3, 1), 40)),
        Shape("halfplane", planes=[hp(1, -2, 5)]),
        Shape("triangle", planes=[hp(1, 0, 10), hp(0, 1, 12), hp(-1, -1, -6)]),
        # tangent to the level-1 bound disk of tangent_node: f(c) = 2, R2*|grad|^2 = 1*4
        Shape("tangent", planes=[hp(1, 1, 2 - a1 - b1)]),
        Shape("lattice_circle", disk=((0, 0), 49)),          # boundary through (7,0) etc.
        Shape("sparse_disk", disk=((-15, 5), 3)),            # in the unrefined region
    ]


def domain():
    return H.gbt.domain(K)


def compare(h, cover, shape):
    """Return (wrong, unresolved_points) against exhaustive exact tests."""
    wrong = unresolved = 0
    for p in domain():
        v = cover[H.owner_in(cover, p, K)]
        if v == H.UNRESOLVED:
            unresolved += 1
        elif (v == "EXACT_INSIDE") != shape.contains(p):
            wrong += 1
    return wrong, unresolved


def metrics():
    rows = []
    pts = domain()
    for mode in ("static", "refine"):
        h = H.Hierarchy(K, refine_rule)
        n0 = len(h.nodes)
        certs = {}
        for s in scene(h):
            st = H.Stats()
            cover = H.query(h, s, certs, st, mode=mode)
            wrong, unres = compare(h, cover, s)
            _, bst, nb = H.baseline(pts, s)
            rows.append({"mode": mode, "shape": s.sid, "visited": st.visited,
                         "bound_checks": st.bound_checks, "point_tests": st.point_tests,
                         "unresolved_pts": unres, "wrong": wrong,
                         "baseline_bounds": bst.bound_checks, "baseline_points": bst.point_tests,
                         "exhaustive": len(pts)})
        rows[-1]["nodes"] = (n0, len(h.nodes), h.expansions, len(certs))
    return rows


if __name__ == "__main__":
    print("| mode | shape | visited | bound chk | point tests | unresolved pts | wrong | "
          "baseline bound/point | exhaustive |")
    print("|---|---|---:|---:|---:|---:|---:|---|---:|")
    for r in metrics():
        print(f"| {r['mode']} | {r['shape']} | {r['visited']} | {r['bound_checks']} | "
              f"{r['point_tests']} | {r['unresolved_pts']} | {r['wrong']} | "
              f"{r['baseline_bounds']}/{r['baseline_points']} | {r['exhaustive']} |")
        if "nodes" in r:
            print(f"nodes before/after, expansions, certificates: {r['nodes']}")
