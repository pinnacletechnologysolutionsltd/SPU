"""Bounded aperture-7 hierarchy, conservative bounds, certified queries, baseline.

Ownership: a fine point p belongs to exactly one level-l node, given by its
digit expansion (NGW-H1 gbt.py, read-only); ties in Euclidean distance are
irrelevant because ownership is logical, never Voronoi. Every node's
descendant set is the FINITE set c + D_l, D_l = {sum_{i<l} d_i pi^i}; no claim
is made about the infinite (Gosper-island) limit. The bound for a level-l
node is the closed disk N(x - c) <= R2[l], R2[l] = max N over D_l, computed
by enumeration and independently re-checked per node in the tests.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ngw_h1"))
import gbt                                            # noqa: E402  (read-only)
from geom import INSIDE, OUTSIDE, N, classify_disk, classify_polygon  # noqa: E402

UNRESOLVED = "UNRESOLVED"
EXACT = {INSIDE: "EXACT_INSIDE", OUTSIDE: "EXACT_OUTSIDE"}


def offsets(level):
    return gbt.domain(level)                          # D_l, 7^l points


def bound_table(K):
    return [max(N(x) for x in offsets(l)) for l in range(K + 1)]


def hexagon(node):
    """Regular hexagon = level-l Voronoi cell of pi^l L (the WRONG parent region)."""
    a, b, l = node
    p = gbt.pi_pow(l)
    out = []
    for u in gbt.DIGITS[1:]:
        v = gbt.e_mul(u, (2, 1))                      # unit * (2 + w); vertex = /3
        w = gbt.e_mul(p, v)
        out.append((a + Fr(w[0], 3), b + Fr(w[1], 3)))
    return out


class Hierarchy:
    def __init__(self, K, refine_rule):
        self.K, self.R2 = K, bound_table(K)
        self.kids, self.nodes = {}, []
        stack = [(0, 0, K)]
        while stack:
            c = stack.pop()
            self.nodes.append(c)
            if c[2] > 0 and refine_rule(c):
                self.kids[c] = gbt.children(c)
                stack.extend(self.kids[c])
        self.expansions = 0

    def refine(self, c):
        if c not in self.kids and c[2] > 0:
            self.kids[c] = gbt.children(c)
            self.nodes.extend(self.kids[c])
            self.expansions += 1


class Stats:
    def __init__(self):
        self.visited = self.bound_checks = self.point_tests = self.reused = 0


def query(h, shape, certs, st, mode="static", check_version=True, region="disk"):
    """Cover of the domain: {node: EXACT_INSIDE | EXACT_OUTSIDE | UNRESOLVED}."""
    cover = {}

    def walk(c):
        st.visited += 1
        key = (c, shape.sid)
        cert = certs.get(key)
        if cert is not None and (not check_version or cert[1] == shape.version):
            st.reused += 1
            v = cert[0]
        else:
            if c[2] == 0:
                st.point_tests += 1
                v = INSIDE if shape.contains(c[:2]) else OUTSIDE
            else:
                st.bound_checks += 1
                v = (classify_disk(c[:2], h.R2[c[2]], shape) if region == "disk"
                     else classify_polygon(hexagon(c), shape))
            certs[key] = (v, shape.version)
        if v in EXACT:
            cover[c] = EXACT[v]
            return
        if c not in h.kids and mode == "refine":
            h.refine(c)
        if c in h.kids:
            for k in h.kids[c]:
                walk(k)
        else:
            cover[c] = UNRESOLVED
    walk((0, 0, h.K))
    return cover


def owner_in(cover, p, K):
    """The unique cover node owning fine point p (by digit ancestry)."""
    node = (p[0], p[1], 0)
    for _ in range(K + 1):
        if node in cover:
            return node
        node = gbt.parent(node)
    raise AssertionError(f"point {p} not covered")


def baseline(points, shape, bucket=7):
    """Flat (non-hierarchical) buckets in (a, b), each with an exact bounding disk."""
    groups = {}
    for p in points:
        groups.setdefault((p[0] // bucket, p[1] // bucket), []).append(p)
    st, verdict = Stats(), {}
    for pts in groups.values():
        c = pts[len(pts) // 2]
        R2 = max(N((x[0] - c[0], x[1] - c[1])) for x in pts)
        st.bound_checks += 1
        v = classify_disk(c, R2, shape)
        for p in pts:
            if v in EXACT:
                verdict[p] = v == INSIDE
            else:
                st.point_tests += 1
                verdict[p] = shape.contains(p)
    return verdict, st, len(groups)
