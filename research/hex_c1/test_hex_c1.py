"""HEX-C1 tests.

Run: timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/hex_c1/test_hex_c1.py'
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import run as R                                       # noqa: E402
import hier as H                                      # noqa: E402
from geom import (N, B, HalfPlane, Shape, INSIDE, STRADDLE,   # noqa: E402
                  classify_disk, disk_vs_disk)
sys.path.insert(0, os.path.join(_HERE, "..", "phy_r1"))
from field import QF                                  # noqa: E402  (read-only)

K, DOM = R.K, R.domain()


def full_tree():
    h = H.Hierarchy(K, lambda c: True)
    return h


def test_bounds_exact_and_conservative():
    assert H.bound_table(K) == [0, 1, 13, 109, 819]
    h = full_tree()
    for c in h.nodes:                                  # every node, every descendant
        desc = [(c[0] + x[0], c[1] + x[1]) for x in H.offsets(c[2])]
        assert max(N((p[0] - c[0], p[1] - c[1])) for p in desc) == h.R2[c[2]]
    for l in range(1, K + 1):                          # independent triangle-inequality bound
        s = QF(Fr(0), Fr(0), 7)
        for i in range(l):
            s = s + (QF(Fr(7 ** (i // 2)), Fr(0), 7) if i % 2 == 0
                     else QF(Fr(0), Fr(7 ** (i // 2)), 7))
        assert (s * s - QF(Fr(H.bound_table(K)[l]), Fr(0), 7)).sign() >= 0, l


def test_finite_ownership_partition():
    assert len(DOM) == len(set(DOM)) == 7 ** K
    h = full_tree()
    cover = {c: "EXACT_INSIDE" for c in h.nodes if c[2] == 2}
    owners = [H.owner_in(cover, p, K) for p in DOM]
    assert len(set(owners)) == 7 ** (K - 2) and all(owners.count(o) == 49 for o in set(owners[:5]))


def test_ancestry_is_not_geometric_containment():
    counts = []
    for l in range(1, K + 1):
        p = H.gbt.pi_pow(l)
        nbrs = [H.gbt.e_mul(u, p) for u in H.gbt.DIGITS[1:]]
        counts.append(sum(any(N((x[0] - v[0], x[1] - v[1])) < N(x) for v in nbrs)
                          for x in H.offsets(l)))
    assert counts == [0, 0, 24, 192], counts            # descendants outside the parent hexagon
    assert H.bound_table(K)[4] > Fr(7 ** 4, 3)          # beyond even the hexagon's circumdisk


def test_exhaustive_agreement_both_modes():
    for row in R.metrics():
        assert row["wrong"] == 0, row
        if row["mode"] == "refine":
            assert row["unresolved_pts"] == 0, row
    static = {r["shape"]: r for r in R.metrics() if r["mode"] == "static"}
    assert static["sparse_disk"]["unresolved_pts"] > 0, "UNRESOLVED must occur in sparse region"


def test_boundary_contact():
    h = H.Hierarchy(K, R.refine_rule)
    c = R.tangent_node(h)
    tangent = [s for s in R.scene(h) if s.sid == "tangent"][0]
    assert classify_disk(c[:2], h.R2[1], tangent) == INSIDE, "tangent closed disk is inside"
    on = (c[0] - 1, c[1] - 1)                          # c + w^2 lies exactly on the line
    assert tangent.planes[0].f(on) == 0 and tangent.contains(on)
    assert disk_vs_disk((0, 0), 1, (3, 0), 4) == STRADDLE, "external touching is not disjoint"
    circle = Shape("c", disk=((0, 0), 49))
    assert circle.contains((7, 0)) and not circle.contains((8, 0))


def test_certificate_reuse_and_invalidation():
    h = H.Hierarchy(K, R.refine_rule)
    shapes, certs = R.scene(h), {}
    for s in shapes:
        H.query(h, s, certs, H.Stats())
    for s in shapes:                                   # full reuse, no new tests
        st = H.Stats()
        H.query(h, s, certs, st)
        assert st.reused == st.visited and st.bound_checks == st.point_tests == 0
    disk = shapes[0]
    disk.disk, disk.version = ((4, 1), 40), disk.version + 1          # edit
    st = H.Stats()
    cover = H.query(h, disk, certs, st)
    assert st.reused == 0 and R.compare(h, cover, disk)[0] == 0, "edited shape recomputed"
    st = H.Stats()
    H.query(h, shapes[1], certs, st)
    assert st.reused == st.visited, "other shapes' certificates survive the edit"
    # refinement edit: bounds of fixed descendant sets are unchanged, so certs stay valid
    cover = H.query(h, shapes[5], certs, H.Stats())
    target = next(c for c, v in cover.items() if v == H.UNRESOLVED)
    h.refine(target)
    st = H.Stats()
    cover2 = H.query(h, shapes[5], certs, st)
    assert st.reused > 0 and st.bound_checks + st.point_tests > 0
    assert R.compare(h, cover2, shapes[5])[0] == 0


def test_stale_certificate_control():
    h = H.Hierarchy(K, lambda c: True)
    s, certs = Shape("d", disk=((3, 1), 40)), {}
    H.query(h, s, certs, H.Stats())
    s.disk, s.version = ((6, 2), 40), s.version + 1
    stale = H.query(h, s, certs, H.Stats(), check_version=False)
    assert R.compare(h, stale, s)[0] > 0, "ignoring versions must give wrong answers"
    fresh = H.query(h, s, {}, H.Stats())
    assert R.compare(h, fresh, s)[0] == 0


def test_false_pruning_hexagon_mutant():
    h = H.Hierarchy(K, lambda c: True)
    l, cnode = 3, (0, 0, 3)
    v = H.gbt.pi_pow(l)
    nbr = H.gbt.DIGITS[1]
    vv = H.gbt.e_mul(nbr, v)
    p = next(x for x in H.offsets(l) if N((x[0] - vv[0], x[1] - vv[1])) < N(x))
    # hexagon edge (bisector) toward neighbour centre vv: N(vv) - 2 B(x, vv) >= 0
    hp = HalfPlane(-2 * (Fr(vv[0]) - Fr(vv[1], 2)), -2 * (Fr(vv[1]) - Fr(vv[0], 2)), Fr(N(vv)))
    shape = Shape("bisector", planes=[hp])
    assert hp.f(p) < 0 and all(hp.f(q) >= 0 for q in H.hexagon(cnode))
    assert hp.f(p) == N(vv) - 2 * B(p, vv)
    mutant = H.query(h, shape, {}, H.Stats(), mode="refine", region="hexagon")
    assert R.compare(h, mutant, shape)[0] > 0, "hexagon assumption falsely prunes"
    correct = H.query(h, shape, {}, H.Stats(), mode="refine")
    assert R.compare(h, correct, shape) == (0, 0)


def test_baseline_matches_exhaustive():
    for s in R.scene(H.Hierarchy(K, R.refine_rule)):
        verdict, st, nb = H.baseline(DOM, s)
        assert all(verdict[p] == s.contains(p) for p in DOM) and nb == st.bound_checks


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print("PASS", t.__name__)
    print(f"PASS all {len(TESTS)} HEX-C1 test groups")
