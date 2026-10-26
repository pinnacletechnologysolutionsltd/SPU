"""NGW-H1 runner: layout x policy x workload grid, identity-checked.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/ngw_h1/run.py'
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache                     # noqa: E402
import scene as S                # noqa: E402
import spec                      # noqa: E402
import workloads as W            # noqa: E402

LAYOUTS = ("axial", "morton", "gbt", "tiled")


def run():
    sc = S.Scene()
    layouts = {n: S.make_layout(sc, n) for n in LAYOUTS}
    weights = {n: cache.line_weights(layouts[n][1], sc.size) for n in LAYOUTS}
    streams = {w: f(sc) for w, f in W.WORKLOADS.items()}
    res = {}
    for w, cells in streams.items():
        for ln in LAYOUTS:
            slot_of, cell_at, key_ops, index_ops, _ = layouts[ln]
            slots = [slot_of[c] for c in cells]
            if any(cell_at[s] != c for s, c in zip(slots, cells)):
                raise AssertionError(f"identity broken: {ln}/{w}")
            addr = sum(key_ops(c) + index_ops for c in cells)
            for p in cache.POLICIES:
                r = cache.simulate(slots, p, weights[ln])
                r["bytes"] = r["misses"] * spec.LINE_B
                r["addr_ops"] = addr
                r["cost"] = r["hits"] * spec.HIT + r["misses"] * spec.MISS + addr * spec.ADDR_OP
                res[(w, ln, p)] = r
    return sc, layouts, streams, res


def effects(res, w):
    """Layout effect (under LRU), policy effect (within layout), interaction, in misses."""
    m = {(ln, p): res[(w, ln, p)]["misses"] for ln in LAYOUTS for p in cache.POLICIES}
    out = {}
    for ln in LAYOUTS:
        for p in cache.POLICIES:
            out[(ln, p)] = {
                "layout": m[(ln, "lru")] - m[("axial", "lru")],
                "policy": m[(ln, p)] - m[(ln, "lru")],
                "interaction": m[(ln, p)] - m[(ln, "lru")] - m[("axial", p)] + m[("axial", "lru")],
            }
    return out


def report():
    sc, layouts, streams, res = run()
    print(f"nodes {len(sc.nodes)} leaves {len(sc.leaves)}; zoom points skipped "
          f"(outside {spec.K}-digit domain): {W.zoom.skipped}")
    for ln, lay in layouts.items():
        pad = sum(c is None for c in lay[1])
        print(f"layout {ln}: slots {len(lay[1])} padding {pad} index_bytes {lay[4]}")
    for w, cells in streams.items():
        print(f"\n## {w} ({len(cells)} accesses)")
        print("| layout | policy | miss rate | bytes | util | addr ops | cost |")
        print("|---|---|---:|---:|---:|---:|---:|")
        for ln in LAYOUTS:
            for p in cache.POLICIES:
                r = res[(w, ln, p)]
                print(f"| {ln} | {p} | {r['misses'] / r['accesses']:.3f} | {r['bytes']} | "
                      f"{r['utilisation']:.2f} | {r['addr_ops']} | {r['cost']} |")
    return res


if __name__ == "__main__":
    report()
