"""The six frozen workloads (spec.py); each returns a list of cell identities."""
from __future__ import annotations

import gbt
import spec
from algebra import e_norm

UNITS = gbt.DIGITS[1:]


def _row(cells):
    return sorted(cells, key=lambda c: (c[2], c[1], c[0]))


def neighborhood(sc):
    out = []
    for c in _row(sc.leaves):
        out.append(c)
        out += [n for n in (sc.neighbour(c, u) for u in UNITS) if n in sc.node_set]
    return out


def _chain(sc, p):
    digs = gbt.encode(p, spec.K)
    if digs is None:
        return None
    c, out = (0, 0, spec.K), [(0, 0, spec.K)]
    for d in reversed(digs):
        if c not in sc.kids:
            break
        c = sc.kids[c][d]
        out.append(c)
    return out


def zoom(sc):
    out, skipped = [], 0
    (sa, sb), (fa, fb) = spec.ZOOM_START, spec.FOCUS
    for t in range(spec.ZOOM_STEPS + 1):
        p = (sa + (fa - sa) * t // spec.ZOOM_STEPS, sb + (fb - sb) * t // spec.ZOOM_STEPS)
        ch = _chain(sc, p)
        if ch is None:
            skipped += 1
        else:
            out += ch
    zoom.skipped = skipped
    return out


def visibility(sc):
    out = []

    def walk(c, v):
        out.append(c)
        for k in sc.kids.get(c, []):
            if e_norm((k[0] - v[0], k[1] - v[1])) <= spec.VIS_C * 7 ** k[2]:
                walk(k, v)
    for v in spec.VIEWS:
        walk((0, 0, spec.K), v)
    return out


def pan(sc):
    out = []
    leaves = _row(sc.leaves)
    for t in range(spec.PAN_STEPS):
        v = (spec.PAN_START[0] + t * spec.PAN_STEP[0], spec.PAN_START[1] + t * spec.PAN_STEP[1])
        out += [c for c in leaves if e_norm((c[0] - v[0], c[1] - v[1])) <= spec.PAN_Q]
    return out


def gbt_hostile(sc):
    leaf_set = set(sc.leaves)
    pairs = []
    for c in _row(sc.leaves):
        for u in UNITS:
            n = sc.neighbour(c, u)
            if n in leaf_set and sc.addr[c][0] != sc.addr[n][0]:
                pairs.append((c, n))
    return [x for _ in range(3) for p in pairs for x in p]


def thrash(sc):
    x, keyed = spec.LCG_SEED, []
    for c in _row(sc.leaves):
        x = (spec.LCG_A * x + spec.LCG_C) % spec.LCG_M
        keyed.append((x, c))
    perm = [c for _, c in sorted(keyed)]
    return perm * 3


WORKLOADS = {"neighborhood": neighborhood, "zoom": zoom, "visibility": visibility,
             "pan": pan, "gbt_hostile": gbt_hostile, "thrash": thrash}
