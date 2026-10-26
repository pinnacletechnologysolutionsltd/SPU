"""NGW-H1 correctness tests (run before results are generated).

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/ngw_h1/test_ngw_h1.py'
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from itertools import product

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache                 # noqa: E402
import gbt                   # noqa: E402
import scene as S            # noqa: E402
import spec                  # noqa: E402
import workloads as W        # noqa: E402

SC = S.Scene()


def test_digit_system_unique_on_domain():
    keys = {gbt._key(d) for d in gbt.DIGITS}
    assert len(keys) == 7 == gbt.NORM, "digits are a complete residue system mod pi"
    dom = gbt.domain(spec.K)
    assert len(dom) == len(set(dom)) == 7 ** spec.K, "7^K distinct points"
    for p in dom:
        d = gbt.encode(p, spec.K)
        assert d is not None and gbt.decode(d) == p, p
    for digs in product(range(7), repeat=3):              # injective on 3-digit strings
        assert gbt.encode(gbt.decode(list(digs)), 3) == list(digs)
    outside = (500, 0)                                    # norm 250000 >> domain extent
    assert outside not in set(dom) and gbt.encode(outside, spec.K) is None


def test_parent_child_relations():
    for c in SC.nodes:
        if c[2] < spec.K:
            P = gbt.parent(c)
            assert P in SC.node_set and c in SC.kids[P], c
            assert SC.addr[c][:-1] == SC.addr[P], "parent = address prefix"
    for P, ks in SC.kids.items():
        assert len(set(ks)) == 7 and all(gbt.parent(k) == P for k in ks)
    # exact logical partition: every fine domain point has exactly one level-1 parent
    owners = {}
    for p in gbt.domain(spec.K):
        owners.setdefault(gbt.parent((p[0], p[1], 0)), 0)
        owners[gbt.parent((p[0], p[1], 0))] += 1
    assert set(owners.values()) == {7} and len(owners) == 7 ** (spec.K - 1)


def test_scene_is_non_uniform():
    assert len(SC.nodes) == 372 and SC.size[(0, 0, spec.K)] == 372
    sizes_l1 = {SC.size[c] for c in SC.nodes if c[2] == 1}
    assert len(sizes_l1) > 1, "structural weight must vary within a level"
    assert {c[2] for c in SC.leaves} != {0}, "leaves at several levels"


def test_layouts_are_identity_bijections():
    for name in ("axial", "morton", "gbt", "tiled"):
        slot_of, cell_at, *_ = S.make_layout(SC, name)
        assert set(slot_of) == SC.node_set, name
        assert len(set(slot_of.values())) == len(SC.nodes), name
        assert all(cell_at[s] == c for c, s in slot_of.items()), name
        assert sum(c is not None for c in cell_at) == len(SC.nodes), name


def test_workloads_reference_existing_cells():
    for w, f in W.WORKLOADS.items():
        cells = f(SC)
        assert cells and all(c in SC.node_set for c in cells), w


def test_cache_model_hand_traces():
    # One set: slots on lines 0, 4, 8, 12, 16 all map to set 0 (line % 4 == 0).
    L = [0, 16, 32, 48, 64]                               # slot = line*4 -> lines 0,4,8,12,16
    w = [0] * 20
    r = cache.simulate(L + L, "lru", w)                  # cyclic 5 lines in a 4-way set
    assert (r["hits"], r["misses"]) == (0, 10), "LRU thrashes on a cycle of WAYS+1"
    r = cache.simulate(L + L, "belady", w)
    assert r["misses"] == 6, "Belady: 5 cold + 1"
    r = cache.simulate([0, 1, 2, 3], "lru", w)
    assert (r["misses"], r["utilisation"]) == (1, 1.0), "one line, fully used"
    ws = [0] * 20
    ws[0] = 99                                           # structural keeps heavy line 0
    r = cache.simulate([0, 16, 32, 48, 64, 0], "structural", ws)
    assert r["misses"] == 5


def _brute_min_misses(lines, ways):
    @lru_cache(maxsize=None)
    def go(i, resident):
        if i == len(lines):
            return 0
        ln = lines[i]
        if ln in resident:
            return go(i + 1, resident)
        if len(resident) < ways:
            return 1 + go(i + 1, resident | {ln})
        return 1 + min(go(i + 1, (resident - {v}) | {ln}) for v in resident)
    return go(0, frozenset())


def test_belady_is_optimal_on_small_streams():
    x = 3
    for trial in range(40):
        seq = []
        for _ in range(14):
            x = (spec.LCG_A * x + spec.LCG_C) % spec.LCG_M
            seq.append((x >> 16) % 6 * spec.SETS)         # 6 lines, all in set 0
        slots = [ln * spec.PER_LINE for ln in seq]
        b = cache.simulate(slots, "belady", [0] * 64)["misses"]
        assert b == _brute_min_misses(tuple(seq), spec.WAYS), (trial, seq)
        for p in ("lru", "lfu", "structural", "adaptive"):
            assert cache.simulate(slots, p, [0] * 64)["misses"] >= b


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} NGW-H1 test groups")
