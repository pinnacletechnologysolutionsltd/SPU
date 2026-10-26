#!/usr/bin/env python3
"""Exact Sign Certificates for PH Curves -- exploratory, host-only, exact Fractions.

Cost unit: one de Casteljau lerp (a*(1-s)+b*s) or one coefficient product.
Run: python3 software/experiments/exact_sign_certificates.py
"""
import random
from fractions import Fraction as F

ops = 0


def lerp(a, b, s=F(1, 2)):
    global ops
    ops += 1
    return a + (b - a) * s


def split(c):
    """de Casteljau midpoint split of Bernstein coefficients."""
    left, right, row = [c[0]], [c[-1]], list(c)
    while len(row) > 1:
        row = [lerp(row[i], row[i + 1]) for i in range(len(row) - 1)]
        left.append(row[0])
        right.append(row[-1])
    return left, right[::-1]


def elevate(c):
    global ops
    n = len(c) - 1
    out = [c[0]]
    for i in range(1, n + 1):
        ops += 1
        out.append(F(i, n + 1) * c[i - 1] + (1 - F(i, n + 1)) * c[i])
    return out + [c[-1]]


def bern_from_power(a):
    """Power basis a[0..n] -> Bernstein coefficients (exact)."""
    from math import comb
    n = len(a) - 1
    return [sum(F(comb(i, j), comb(n, j)) * a[j] for j in range(i + 1)) for i in range(n + 1)]


def pmul(p, q):
    r = [F(0)] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            r[i + j] += x * y
    return r


def padd(p, q):
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(n)]


def pder(p):
    return [i * p[i] for i in range(1, len(p))] or [F(0)]


def discover(c, cap=40):
    """Bisection search. Returns (tree_leaf_depths or None, ops, max_bits)."""
    global ops
    ops = 0
    leaves, bits = [], 0
    stack = [(c, 0)]
    while stack:
        cur, d = stack.pop()
        bits = max(bits, max(x.denominator.bit_length() + abs(x.numerator).bit_length() for x in cur))
        if min(cur) > 0:
            leaves.append(d)
        elif d >= cap or max(cur) <= 0:
            return None, ops, bits  # inconclusive / refuse
        else:
            stack.extend((h, d + 1) for h in split(cur))
    return leaves, ops, bits


def verify(c, tree):
    """Check a submitted tree (list of per-node split flags, DFS) -- no search."""
    global ops
    ops = 0
    it = iter(tree)
    stack = [c]
    while stack:
        cur = stack.pop()
        if next(it):
            stack.extend(split(cur))
        elif not min(cur) > 0:
            return False, ops
    return True, ops


def tree_flags(c, cap=40):
    flags, stack = [], [(c, 0)]
    while stack:
        cur, d = stack.pop()
        if min(cur) > 0:
            flags.append(False)
        elif d >= cap:
            return None
        else:
            flags.append(True)
            stack.extend((h, d + 1) for h in split(cur))
    return flags


def elev_discover(c, cap=200):
    global ops
    ops = 0
    m = 0
    while min(c) <= 0 and m < cap:
        c = elevate(c)
        m += 1
    return (m if min(c) > 0 else None), ops


def elev_verify(c, m):
    global ops
    ops = 0
    for _ in range(m):
        c = elevate(c)
    return min(c) > 0, ops


def rand_pos_poly(deg, rng):
    """prod of (t-a)^2 factors (+small eps): positive, usually negative Bernstein coeffs."""
    p = [F(rng.randint(1, 5))]
    for _ in range(deg // 2):
        a = F(rng.randint(1, 15), 16)
        p = pmul(p, [a * a, -2 * a, F(1)])
    if deg % 2:
        p = pmul(p, [F(rng.randint(1, 4)), F(1)])
    p[0] += F(1, 64)
    return p


def exp1(rng):
    print("== 1. discovery vs verification (positive, initial Bernstein has negatives)")
    print("deg  neg  bisect:disc/ver/R/leaves/bits   elevate:m disc/ver/R")
    for deg in range(4, 9):
        rows = []
        while len(rows) < 20:
            c = bern_from_power(rand_pos_poly(deg, rng))
            if min(c) <= 0:
                rows.append(c)
        agg = [0, 0, 0, 0, 0, 0, 0]
        for c in rows:
            leaves, d_ops, bits = discover(c)
            fl = tree_flags(c)
            _, v_ops = verify(c, fl)
            m, e_d = elev_discover(c)
            _, e_v = elev_verify(c, m)
            for k, v in enumerate((d_ops, v_ops, len(leaves), bits, m, e_d, e_v)):
                agg[k] += v
        n = len(rows)
        print(f"{deg:>3}  {n:>3}  {agg[0]/n:8.0f}/{agg[1]/n:6.0f}/{agg[0]/agg[1]:.2f}/{agg[2]/n:5.1f}/{agg[3]/n:5.0f}"
              f"   m={agg[4]/n:5.1f} {agg[5]/n:8.0f}/{agg[6]/n:6.0f}/{agg[5]/agg[6]:.2f}")


def ph_data(rng):
    U = [F(rng.randint(-5, 5)) for _ in range(3)]
    V = [F(rng.randint(-5, 5)) for _ in range(3)]
    return U, V


def exp2(rng):
    print("== 2. PH W (deg<=2) vs generic r'xr'' numerator (deg 6), 300 random PH curves")
    stats = {"trivial": 0, "certified": 0, "sign-change/refused": 0, "identity-fail": 0}
    cw_t = cg_t = 0
    for _ in range(300):
        U, V = ph_data(rng)
        x1 = padd(pmul(U, U), [-c for c in pmul(V, V)])
        y1 = [2 * c for c in pmul(U, V)]
        cross = padd(pmul(x1, pder(y1)), [-c for c in pmul(y1, pder(x1))])
        W = padd(pmul(U, pder(V)), [-c for c in pmul(pder(U), V)])
        w2 = pmul(W, padd(pmul(U, U), pmul(V, V)))
        if [c for c in cross] != [2 * c for c in w2] + [F(0)] * (len(cross) - len(w2)):
            stats["identity-fail"] += 1
            continue

        def cost(poly):
            c = bern_from_power(poly)
            if min(c) > 0 or max(c) < 0:
                return 0, 1
            for s in (1, -1):
                r = discover([s * x for x in c], cap=20)
                if r[0] is not None:
                    return r[1], 2
            return r[1], 3
        (cw, kw), (cg, kg) = cost(W), cost(cross)
        if kw == 3 or kg == 3:
            stats["sign-change/refused"] += 1
        elif kw == 1 and kg == 1:
            stats["trivial"] += 1
        else:
            stats["certified"] += 1
            cw_t += cw
            cg_t += cg
    print(stats, f"| nontrivial certified: W ops={cw_t} generic ops={cg_t} ratio={cg_t/max(cw_t,1):.1f}")


def exp3(rng):
    print("== 3. repeated affine transforms: cross-product reuse via det, PH-form invalidation")
    U, V = ph_data(rng)
    x1 = padd(pmul(U, U), [-c for c in pmul(V, V)])
    y1 = [2 * c for c in pmul(U, V)]
    base = padd(pmul(x1, pder(y1)), [-c for c in pmul(y1, pder(x1))])
    n_steps, ph_lost, sign_ok, det_flip, singular = 200, 0, 0, 0, 0
    sign = 1
    xs, ys = x1, y1
    for _ in range(n_steps):
        a, b, c, d = (F(rng.randint(-4, 4)) for _ in range(4))
        det = a * d - b * c
        if det == 0:
            singular += 1
            continue
        nx = padd([a * z for z in xs], [b * z for z in ys])
        ny = padd([c * z for z in xs], [d * z for z in ys])
        cr = padd(pmul(nx, pder(ny)), [-z for z in pmul(ny, pder(nx))])
        want = [det * z for z in padd(pmul(xs, pder(ys)), [-z for z in pmul(ys, pder(xs))])]
        sign_ok += cr == want
        det_flip += det < 0
        # PH form preserved only for similarities: |A col1| = |A col2|, orthogonal
        if not (a * a + c * c == b * b + d * d and a * b + c * d == 0):
            ph_lost += 1
        xs, ys = nx, ny
    print(f"steps={n_steps} det-rule exact={sign_ok} orientation flips={det_flip} "
          f"singular-skipped={singular} PH-form invalidated={ph_lost} (I_PH={ph_lost/n_steps:.2f}, I_det=0.00)")


def exp4(rng):
    print("== 4. hard cases: P=(t-1/3)^2+eps, and exact double zero (nonneg, not strictly pos)")
    print("eps          depth-max  nodes-ops  bits   outcome")
    for k in (2, 4, 8, 16, 32):
        c = bern_from_power([F(1, 9) + F(1, 10 ** k), F(-2, 3), F(1)])  # min near t=1/3
        leaves, o, bits = discover(c, cap=200)
        print(f"1e-{k:<8} {max(leaves) if leaves else '-':>9} {o:>10} {bits:>5}   {'CERT' if leaves else 'INCONCLUSIVE'}")
    c = bern_from_power([F(1, 9), F(-2, 3), F(1)])
    leaves, o, bits = discover(c, cap=40)
    print(f"0 (exact)    {'-':>9} {o:>10} {bits:>5}   {'CERT' if leaves else 'REFUSED at cap 40 (zero at t=1/3)'}")


def sturm_chain(p):
    """Sturm chain of power-basis p; returns (chain, quotients, mults, bits)."""
    m = 0
    chain, quots = [p, pder(p)], []
    while len(chain[-1]) > 1 or chain[-1][0] != 0:
        a, b = list(chain[-2]), chain[-1]
        if len(b) == 1 and b[0] == 0:
            break
        q = [F(0)] * max(len(a) - len(b) + 1, 1)
        while len(a) >= len(b) and any(a):
            k = len(a) - len(b)
            f = a[-1] / b[-1]
            q[k] = f
            m += 1 + len(b)
            for i, y in enumerate(b):
                a[i + k] -= f * y
            while a and a[-1] == 0:
                a.pop()
        quots.append(q)
        if not a:
            break
        chain.append([-x for x in a])
        if len(a) == 1:
            break
    bits = max(x.denominator.bit_length() + abs(x.numerator).bit_length() for c in chain for x in c)
    return chain, quots, m, bits


def sturm_positive(p):
    """True iff p>0 on [0,1] (no roots there and p(0)>0). Evaluation costs counted."""
    chain, quots, m, bits = sturm_chain(p)
    def var(t):
        vals = [sum(c * t ** i for i, c in enumerate(q)) for q in chain]
        vals = [v for v in vals if v != 0]
        return sum(1 for a, b in zip(vals, vals[1:]) if (a < 0) != (b < 0))
    ev = 2 * sum(len(q) for q in chain)
    ok = (var(F(0)) - var(F(1)) == 0) and p[0] > 0 and sum(p) > 0
    ver = sum(len(q) * len(c) for q, c in zip(quots, chain[1:])) + ev  # multiply-back check + evaluations
    return ok, m + ev, ver, bits


def exp5(rng):
    print("== 5. Sturm vs bisection vs elevation (mults; lerp=1 mult), degree-4..8 positive")
    print("deg  bisect disc/ver  elev disc/ver   sturm disc/ver  sturm bits vs bisect bits")
    for deg in range(4, 9):
        rows = []
        while len(rows) < 20:
            q = rand_pos_poly(deg, rng)
            if min(bern_from_power(q)) <= 0:
                rows.append(q)
        agg = [0] * 8
        for q in rows:
            c = bern_from_power(q)
            _, d, bb = discover(c)
            _, v = verify(c, tree_flags(c))
            m, ed = elev_discover(c)
            _, ev = elev_verify(c, m)
            ok, sd, sv, sb = sturm_positive(q)
            assert ok
            for k, x in enumerate((d, v, ed, ev, sd, sv, sb, bb)):
                agg[k] += x
        n = len(rows)
        print(f"{deg:>3}  {agg[0]/n:6.0f}/{agg[1]/n:<6.0f}  {agg[2]/n:6.0f}/{agg[3]/n:<6.0f}  "
              f"{agg[4]/n:6.0f}/{agg[5]/n:<6.0f}   {agg[6]/n:5.0f} vs {agg[7]/n:3.0f}")
    print("near-zero (t-1/3)^2+eps, deg 2: Sturm disc mults / bits vs bisection")
    for k in (2, 8, 32):
        q = [F(1, 9) + F(1, 10 ** k), F(-2, 3), F(1)]
        ok, sd, sv, sb = sturm_positive(q)
        _, d, bb = discover(bern_from_power(q), cap=200)
        print(f"  eps=1e-{k:<3} sturm ok={ok} {sd}/{sv} bits={sb}   bisect {d} bits={bb}")
    q = [F(1, 9), F(-2, 3), F(1)]
    print("  eps=0      sturm ok =", sturm_positive(q)[0], "(decides in finite steps; bisection refuses)")


if __name__ == "__main__":
    rng = random.Random(20261023)
    for e in (exp1, exp2, exp3, exp4, exp5):
        e(rng)
        print()
