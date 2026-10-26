"""Integrated session: a REL-1 machine owns the metric state; spatial engines query it.

REL-1 (research/rel1, read-only) admits/refuses metric transitions atomically. The geometry layer reads
the CURRENT state's metric entries, never coordinates. Coordinates materialise only in observe().
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rel1"))
import backends as RB          # noqa: E402  (REL-1, read-only)
import machine as RM           # noqa: E402
import gi_baseline as B        # noqa: E402
import gi_engine as E          # noqa: E402
import gi_flat as F            # noqa: E402
import gi_scene as S           # noqa: E402
import hier as H               # noqa: E402


def default_engines():
    return {"H_exact_refine": (E.Engine(), "refine"), "H_exact_static": (E.Engine(), "static"),
            "H_scaled_refine": (E.Engine(bounds="scaled"), "refine"),
            "H_content_refine": (E.Engine(slots="content"), "refine")}


class Session:
    def __init__(self, engines=None, flat_check_dep=True):
        self.rel = RM.Machine(RB.Relational, d=1)
        self.pts = H.gbt.domain(S.K)
        self.engines = engines if engines is not None else default_engines()
        self.flat, self.exh = F.Flat(self.pts, check_dep=flat_check_dep), B.ExhaustiveCached()
        self.coord_ctr, self.oracle_ctr, self.log, self.obs_ctr = Counter(), Counter(), [], Counter()

    def command(self, cmd):
        return self.rel.step(cmd)

    def metric(self):
        s = self.rel.states[self.rel.current]
        return s.M if s.kind == "metric" else None

    def _snap(self):
        snap = {n: Counter(e.ctr) for n, (e, _) in self.engines.items()}
        snap.update(flat=Counter(self.flat.ctr), exh=Counter(self.exh.ctr), coord=Counter(self.coord_ctr))
        return snap

    def query_all(self, label, shapes=None):
        M = self.metric()
        if M is None:
            row = {"step": label, "status": "REFUSED", "error": "NOT_A_METRIC_STATE"}
            self.log.append(row)
            return row
        before, shapes_out = self._snap(), {}
        for sh in (shapes or S.scene()):
            truth = B.oracle(sh, M, self.pts, self.oracle_ctr)
            rec = {"truth": len(truth)}
            for n, (eng, mode) in self.engines.items():
                ins, out, unres = E.points_of(eng.query(sh, M, mode))
                rec[n] = {"wrong": len(ins - truth) + len(out & truth), "unres": len(unres),
                          "partition_ok": len(ins) + len(out) + len(unres) == len(self.pts)}
            rec["flat"] = {"wrong": len(self.flat.query(sh, M) ^ truth)}
            rec["exh"] = {"wrong": len(self.exh.query(sh, M, self.pts) ^ truth)}
            try:
                rec["coord"] = {"wrong": len(B.coord_query(sh, M, self.pts, self.coord_ctr) ^ truth)}
            except B.OutOfField:
                rec["coord"] = {"refused": "OUT_OF_FIELD"}
            shapes_out[sh.sid] = rec
        after = self._snap()
        delta = {k: Counter({c: after[k][c] - before[k][c] for c in after[k]
                             if after[k][c] != before[k][c]}) for k in after}
        row = {"step": label, "status": "OK", "shapes": shapes_out, "delta": delta}
        self.log.append(row)
        return row

    def observe(self, points):
        """Selective observation: coordinates of chosen lattice points in the (0,1) plane, or refusal."""
        M = self.metric()
        if M is None:
            return {"status": "REFUSED", "error": "NOT_A_METRIC_STATE"}
        m = M[0][1]
        try:
            r = B.embed(m)
        except B.OutOfField:
            return {"status": "REFUSED", "error": "OUT_OF_FIELD"}
        self.obs_ctr["materialise"] += 1
        self.obs_ctr["points"] += len(points)
        return {"status": "EXACT", "coords": [(p[0] + m * p[1], r * p[1]) for p in points]}

    def footprint(self):
        out = {n: e.footprint() for n, (e, _) in self.engines.items()}
        out.update(flat=self.flat.footprint(), exh=self.exh.footprint(), rel=self.rel.sizes())
        return out


def M3(m12=0, m13=0, m23=0):
    a, b, c = Fr(m12), Fr(m13), Fr(m23)
    return ((1, a, b), (a, 1, c), (b, c, 1))


PROGRAM = (
    ("start", None),
    ("T m12=3/5", ("TRANSFORM", M3(Fr(3, 5)))),
    ("T m13=1/2 (m12 kept)", ("TRANSFORM", M3(Fr(3, 5), Fr(1, 2)))),
    ("T m13=0 restored", ("TRANSFORM", M3(Fr(3, 5)))),
    ("T singular (refused)", ("TRANSFORM", M3(Fr(1)))),
    ("MOVE strut (non-affine)", ("MOVE", (0, 1), (0, 0, 1))),
    ("T relational-only M2", ("TRANSFORM", M3(Fr(1, 3), Fr(1, 4), Fr(1, 5)))),
    ("T identity restored", ("TRANSFORM", M3())),
)
