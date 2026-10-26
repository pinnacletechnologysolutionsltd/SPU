"""Flat 7x7 bucket index with the same exact bounds and certificate/dependency semantics."""
from __future__ import annotations

from collections import Counter

import gi_metric as GM
import gi_scene as S
from geom import INSIDE, OUTSIDE, N, classify_disk

EXACT = (INSIDE, OUTSIDE)


class Flat:
    def __init__(self, points, bucket=7, check_dep=True):
        g = {}
        for p in points:
            g.setdefault((p[0] // bucket, p[1] // bucket), []).append(p)
        self.groups, self.check_dep = g, check_dep
        self.centre = {k: v[len(v) // 2] for k, v in g.items()}
        self.ctr = Counter()
        self.hexR2 = {}
        for k, v in g.items():
            c = self.centre[k]
            self.ctr["table_evals"] += len(v)
            self.hexR2[k] = max(N((x[0] - c[0], x[1] - c[1])) for x in v)
        self.tables, self.certs = {}, {}

    def table(self, m):
        if m not in self.tables:
            t = {}
            for k, v in self.groups.items():
                c = self.centre[k]
                self.ctr["table_evals"] += len(v)
                t[k] = max(GM.Q(m, (x[0] - c[0], x[1] - c[1])) for x in v)
            self.tables[m] = t
        return self.tables[m]

    def query(self, shape, M):
        m = S.entry(M, shape)
        dep = (shape.fp(), m)
        inside = set()
        tab = self.table(m) if m is not None else None
        for k, pts in self.groups.items():
            c = self.centre[k]
            self.ctr["cert_compare"] += 1
            cert = self.certs.get((k, shape.sid))
            if cert is not None and (not self.check_dep or cert[1] == dep):
                self.ctr["reused"] += 1
                v = cert[0]
            else:
                self.ctr["bound"] += 1
                v = (classify_disk(c, self.hexR2[k], shape.native) if shape.native is not None
                     else GM.disk_vs_disk_q(m, c, tab[k], shape.centre, shape.rho))
                self.certs[(k, shape.sid)] = (v, dep)
            if v == INSIDE:
                inside.update(pts)
            elif v != OUTSIDE:
                for p in pts:                                 # point verdicts are certificates too
                    pc = self.certs.get(("pt", p, shape.sid))
                    self.ctr["cert_compare"] += 1
                    if pc is not None and (not self.check_dep or pc[1] == dep):
                        self.ctr["reused"] += 1
                        hit = pc[0]
                    else:
                        self.ctr["point"] += 1
                        hit = S.contains(shape, M, p)
                        self.certs[("pt", p, shape.sid)] = (hit, dep)
                    if hit:
                        inside.add(p)
        return inside

    def footprint(self):
        return {"buckets": len(self.groups), "certs": len(self.certs),
                "table_ints": len(self.groups) * (1 + len(self.tables))}
