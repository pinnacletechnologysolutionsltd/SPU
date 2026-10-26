"""Certified hierarchical query over a REL-1 metric state (HEX-C1 tree and bounds, read-only).

A node verdict is a certificate stored with a dependency key: the shape's parameters plus ONLY the
metric entries the shape uses. It is reused iff the key still matches (content, so a restored metric
reuses old evidence). Mutants: check_dep=False (ignore keys), dep_mode='wrong_entry' (declare the
wrong entry), dep_mode='all' (over-broad), wrong_bound=True (use the metric-free hex bound table).
"""
from __future__ import annotations

from collections import Counter

import gi_metric as GM
import gi_scene as S
import hier as H
from geom import INSIDE, OUTSIDE, classify_disk

EXACT = {INSIDE: "EXACT_INSIDE", OUTSIDE: "EXACT_OUTSIDE"}
UNRESOLVED = "UNRESOLVED"


class Engine:
    def __init__(self, bounds="exact", check_dep=True, dep_mode="declared", wrong_bound=False,
                 slots="single"):
        self.h = H.Hierarchy(S.K, S.refine_rule)
        self.bounds, self.check_dep, self.dep_mode, self.wrong_bound = bounds, check_dep, dep_mode, wrong_bound
        self.slots = slots                      # 'single': one slot per (node, shape); 'content': one per dependency key
        self.certs, self.tables, self.ctr = {}, {}, Counter()
        self.hex_R2 = H.bound_table(S.K)

    def depkey(self, shape, M):
        if shape.native is not None:
            return (shape.fp(),)
        if self.dep_mode == "all":
            return (shape.fp(), tuple(v for r in M for v in r))
        pair = shape.pair if self.dep_mode == "declared" else ((0, 1) if shape.pair != (0, 1) else (0, 2))
        return (shape.fp(), M[pair[0]][pair[1]])

    def table(self, m):
        if self.wrong_bound:
            return self.hex_R2
        key = (self.bounds, m)
        if key not in self.tables:
            self.tables[key] = (GM.table_exact if self.bounds == "exact" else GM.table_scaled)(m, S.K, self.ctr)
        else:
            self.ctr["table_hits"] += 1
        return self.tables[key]

    def classify(self, c, shape, M):
        if shape.native is not None:
            return classify_disk(c[:2], self.hex_R2[c[2]], shape.native)
        m = S.entry(M, shape)
        return GM.disk_vs_disk_q(m, c[:2], self.table(m)[c[2]], shape.centre, shape.rho)

    def query(self, shape, M, mode="refine"):
        cover, dep = {}, self.depkey(shape, M)
        if shape.native is None:
            self.table(S.entry(M, shape))                      # bound certificate for this metric entry

        def walk(c):
            self.ctr["visited"] += 1
            slot = (c, shape.sid) + ((dep,) if self.slots == "content" else ())
            cert = self.certs.get(slot)
            self.ctr["cert_compare"] += 1
            if cert is not None and (not self.check_dep or cert[1] == dep):
                self.ctr["reused"] += 1
                v = cert[0]
            else:
                if c[2] == 0:
                    self.ctr["point"] += 1
                    v = INSIDE if S.contains(shape, M, c[:2]) else OUTSIDE
                else:
                    self.ctr["bound"] += 1
                    v = self.classify(c, shape, M)
                self.certs[slot] = (v, dep)
            if v in EXACT:
                cover[c] = EXACT[v]
                return
            if c not in self.h.kids and mode == "refine":
                self.h.refine(c)
            if c in self.h.kids:
                for k in self.h.kids[c]:
                    walk(k)
            else:
                cover[c] = UNRESOLVED
        walk((0, 0, S.K))
        return cover

    def footprint(self):
        return {"nodes": len(self.h.nodes), "certs": len(self.certs),
                "table_ints": sum(len(t) for t in self.tables.values())}


def points_of(cover):
    """(inside, outside, unresolved) point sets from a cover."""
    inside, outside, unres = set(), set(), set()
    for c, v in cover.items():
        pts = {(c[0] + x[0], c[1] + x[1]) for x in H.offsets(c[2])}
        {"EXACT_INSIDE": inside, "EXACT_OUTSIDE": outside, UNRESOLVED: unres}[v].update(pts)
    return inside, outside, unres
