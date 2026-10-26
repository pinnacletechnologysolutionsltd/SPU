#!/usr/bin/env python3
"""ICOS-0 fast fixture: same assertions as test_icosian_e8_full.py, evaluated on
exact integer 8-vectors (entries 2a,2b per coordinate) with a cached Gram matrix.
The integer layer is differentially checked against the Fraction oracle on all
14400 unit products and all 57600 root inner products. Run: python3 software/tests/test_icosian_e8.py"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.dirname(__file__))
from collections import Counter
from icosian_e8 import *
from test_icosian_e8_full import proved_bits


def zm(A, Bc, C, D): return (A*C + Bc*D, A*D + Bc*C + Bc*D)   # (a+b phi)(c+d phi), x4 scale


def iqmul(p, q):
    z = lambda i, j: zm(p[2*i], p[2*i+1], q[2*j], q[2*j+1])
    t = lambda *terms: [sum(s * z(i, j)[k] for s, i, j in terms) for k in (0, 1)]
    out = []
    for terms in (((1, 0, 0), (-1, 1, 1), (-1, 2, 2), (-1, 3, 3)), ((1, 0, 1), (1, 1, 0), (1, 2, 3), (-1, 3, 2)),
                  ((1, 0, 2), (-1, 1, 3), (1, 2, 0), (1, 3, 1)), ((1, 0, 3), (1, 1, 2), (-1, 2, 1), (1, 3, 0))):
        for s in t(*terms):
            assert s % 2 == 0
            out.append(s // 2)
    return tuple(out)


def iB(v, w):
    sa = sb = 0
    for i in range(4):
        a, b = zm(v[2*i], v[2*i+1], w[2*i], w[2*i+1]); sa += a; sb += b
    assert (sa + sb) % 2 == 0
    return (sa + sb) // 2


def ibits(v): return max(abs(c).bit_length() for c in v)
def ireflect(r, x): k = iB(x, r); return tuple(a - k * b for a, b in zip(x, r))


def main():
    U, R = units(), roots()
    iU, iR = [tuple(vec8(u)) for u in U], [tuple(vec8(r)) for r in R]
    # differential: integer layer == oracle, exhaustively
    for p, ip in zip(U, iU):
        for q, iq in zip(U, iU):
            assert tuple(vec8(qmul(p, q))) == iqmul(ip, iq)
    G = [[iB(a, b) for b in iR] for a in iR]
    assert all(G[i][j] == B(R[i], R[j]) for i in range(240) for j in range(240))
    # Phase A (all 14400 unit products, via the verified integer layer)
    SU, one = set(iU), tuple(vec8((ONE, ZERO, ZERO, ZERO)))
    assert len(SU) == 120 and one in SU and all(iqmul(p, q) in SU for p in iU for q in iU)
    assert all(iqmul(u, tuple(vec8(qconj(U[k])))) == one for k, u in enumerate(iU))
    # Phase B
    assert len(set(iR)) == 240 and {G[i][i] for i in range(240)} == {2}
    prof = {-2: 1, -1: 56, 0: 126, 1: 56, 2: 1}
    assert all(dict(Counter(row)) == prof for row in G)
    idx = {v: i for i, v in enumerate(iR)}
    assert all(ireflect(r, x) in idx for r in iR for x in iR)
    basis = hnf_rows([list(v) for v in iR]); assert len(basis) == 8
    X = [from_vec8(v) for v in basis]
    Gm = [[B(x, y) for y in X] for x in X]
    assert all(g.denominator == 1 for r in Gm for g in r) and all(Gm[i][i] % 2 == 0 for i in range(8))
    assert det(Gm) == 1
    assert len(hnf_rows([list(r) for r in basis] + [vec8(qscale(PHI, u)) for u in U])) == 8
    # Phase C (same RNG call sequence as the full gate => identical numbers)
    g = {"root_bits": max(map(ibits, iR))}
    prods = [iqmul(p, q) for p in iR for q in iR]
    g["pair_product_bits"] = max(map(ibits, prods))
    g["pair_product_in_roots"] = sum(1 for p in prods if p in idx)
    g["reflect_bits"] = max(ibits(ireflect(r, x)) for r in iR for x in iR)
    rnd = random.Random(7)
    for name, pool in (("unit_chain", iU), ("root_chain", iR)):
        mx = []
        for depth in (1, 4, 8, 16, 32, 64):
            m = 0
            for _ in range(100):
                x = rnd.choice(pool)
                for _ in range(depth): x = iqmul(x, rnd.choice(pool))
                m = max(m, ibits(x))
            mx.append((depth, m))
        g[name] = mx
    lam, lam2 = (5 + 5 ** .5) / 10, (5 - 5 ** .5) / 10
    worst = 0
    for _ in range(100):
        x = iqmul(rnd.choice(iR), rnd.choice(iR)); n = iB(x, x); pb = proved_bits(n, lam, lam2)
        for _ in range(64):
            x = ireflect(rnd.choice(iR), x)
            assert iB(x, x) == n and ibits(x) <= pb
            worst = max(worst, ibits(x))
    g["reflect_chain_bits"] = worst
    assert g["root_bits"] <= proved_bits(2, lam, lam2) and g["reflect_bits"] == g["root_bits"]
    if "--print" in sys.argv: print(g)
    print("PASS test_icosian_e8 (fast integer layer; 120 units, 240 roots, E8 Gram det 1)")
    return g


if __name__ == "__main__":
    main()
