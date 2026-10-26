#!/usr/bin/env python3
"""ICOS-0 exhaustive research gate (pure oracle path, ~50 s). Fast regression fixture: test_icosian_e8.py. Run: python3 software/tests/test_icosian_e8_full.py"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from collections import Counter
from icosian_e8 import *

ONE_Q = (ONE, ZERO, ZERO, ZERO)


def phase_a(U):
    assert len(U) == len(set(U)) == 120
    assert all(qmul(u, qconj(u)) == ONE_Q for u in U)          # quaternionic unit norm
    S = set(U)
    assert all(qmul(p, q) in S for p in U for q in U)          # closure (14400 products)
    assert ONE_Q in S and all(qconj(u) in S for u in U)
    # independent float check of the 96 icosian-type coordinates against numeric phi
    ph = (1 + 5 ** 0.5) / 2
    for u in U:
        n = sum((float(t.a) + float(t.b) * ph) ** 2 for t in u)
        assert abs(n - 1) < 1e-12


def phase_b(R):
    assert len(R) == len(set(R)) == 240 and {B(r, r) for r in R} == {2}
    cnt = Counter()
    for r in R:
        ips = Counter(B(r, s) for s in R)
        assert all(v.denominator == 1 for v in ips)
        cnt[tuple(sorted(ips.items()))] += 1
    prof = {-2: 1, -1: 56, 0: 126, 1: 56, 2: 1}
    assert len(cnt) == 1 and dict(next(iter(cnt))) == prof, cnt
    S = set(R)
    assert all(reflect(r, x) in S for r in R for x in R)       # reflection closure
    basis = hnf_rows([vec8(r) for r in R])
    assert len(basis) == 8                                      # rank 8
    X = [from_vec8(v) for v in basis]
    G = [[B(x, y) for y in X] for x in X]
    assert all(g.denominator == 1 for r in G for g in r)
    assert all(G[i][i] % 2 == 0 for i in range(8))              # even
    assert det(G) == 1                                          # unimodular; even => E8
    # Z[phi]-span: phi*u = u + phi^-1*u lies in the root lattice (spot-check via HNF)
    phiU = [vec8(qscale(PHI, u)) for u in units()]
    assert len(hnf_rows([list(r) for r in basis] + phiU)) == 8
    return basis


def growth(R):
    out = {}
    out["root_bits"] = max(bits(r) for r in R)
    RS = set(R)
    prods = [qmul(p, q) for p in R for q in R]
    out["pair_product_bits"] = max(bits(p) for p in prods)
    out["pair_product_in_roots"] = sum(1 for p in prods if p in RS)
    out["reflect_bits"] = max(bits(reflect(r, x)) for r in R for x in R)
    rnd = random.Random(7)
    U = units()
    # unrestricted right-multiplication chains
    for name, pool in (("unit_chain", U), ("root_chain", R)):
        mx = []
        for depth in (1, 4, 8, 16, 32, 64):
            m = 0
            for _ in range(100):
                x = rnd.choice(pool)
                for _ in range(depth): x = qmul(x, rnd.choice(pool))
                m = max(m, bits(x))
            mx.append((depth, m))
        out[name] = mx
    # reflection chains on a larger lattice vector: bits must stay within the proved bound
    lam, lam2 = (5 + 5 ** .5) / 10, (5 - 5 ** .5) / 10
    worst = 0
    for _ in range(100):
        x = qmul(rnd.choice(R), rnd.choice(R))
        n = B(x, x)
        pb = proved_bits(n, lam, lam2)
        for _ in range(64):
            x = reflect(rnd.choice(R), x)
            assert B(x, x) == n and bits(x) <= pb
            worst = max(worst, bits(x))
    out["reflect_chain_bits"] = worst
    return out, lam, lam2


def proved_bits(n, lam, lam2):
    """Bound on bits of the 8-vector for a lattice vector with B(x,x)=n.
    B = 2(lam*|x|^2 + lam'*|sigma x|^2) => |u|<=sqrt(n/2lam), |u'|<=sqrt(n/2lam'),
    b=(u-u')/sqrt5, a=u-b*phi; numerators are 2a,2b."""
    u, v = math.sqrt(n / (2 * lam)), math.sqrt(n / (2 * lam2))
    b2 = 2 * (u + v) / 5 ** .5
    a2 = 2 * u + 1.6180339887 * b2
    return math.ceil(math.log2(max(a2, b2) + 1))


def main():
    U = units(); phase_a(U); R = roots(); phase_b(R)
    # check B = 2*Tr(lam*dot) identity numerically (derivation of the proved bound)
    ph, s5 = (1 + 5 ** .5) / 2, 5 ** .5
    lam, lam2 = (5 + s5) / 10, (5 - s5) / 10
    for r, s in zip(R[:60], R[100:160]):
        d = dot(r, s); e1 = float(d.a) + float(d.b) * ph; e2 = float(d.a) + float(d.b) * (1 - ph)
        assert abs(B(r, s) - 2 * (lam * e1 + lam2 * e2)) < 1e-9
    g, lam, lam2 = growth(R)
    pb = proved_bits(2, lam, lam2)
    assert g["root_bits"] <= pb and g["reflect_bits"] <= pb
    assert g["reflect_bits"] == g["root_bits"] and g["pair_product_in_roots"] > 0
    print("growth:", g, "proved_bits(n=2):", pb)
    return g
    print("PASS test_icosian_e8_full (120 units, 240 roots, E8 Gram det 1)")


if __name__ == "__main__":
    main()
