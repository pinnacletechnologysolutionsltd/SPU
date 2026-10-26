#!/usr/bin/env python3
"""Taylor-shift sign certificates vs Bernstein bisection vs Sturm (Wildberger §19 follow-up). Exploratory.

Question: P > 0 on [0,1] (exact, rational). Four methods, same fixtures, same depth cap (40), no tuning:
  M1 Bernstein midpoint bisection        (baseline from exact_sign_certificates.py; verify = replay of the tree)
  M2 Sturm chain                          (baseline from exact_sign_certificates.py)
  M3 Taylor-centre certificate            (P(c+t)=sum a_k t^k; leaf test a_0 > sum_{k>=1} |a_k| h^k on |t|<=h)
  M4 Descartes/VCA on integer coefficients (Taylor shift by 1 = additions only; test = all coeffs of (1+x)^n p(1/(1+x)) > 0)
Verification for M3/M4 is independent of the search: each certified leaf is recomputed from the ORIGINAL polynomial.
Cost counters: mul (true multiplications), add, shift (multiplication by a power of two). Bits = max bit length of any coefficient vector with its common denominator cleared (same metric for all methods).
Optional SymPy section checks the Taylor/translate identities symbolically (skipped if SymPy is absent).
"""
import os
import sys
from fractions import Fraction as F
from math import comb, lcm, gcd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exact_sign_certificates as base  # noqa: E402

CAP = 40


def vbits(xs):
    """Storage metric shared by all methods: bit length of the coefficient vector with its common denominator cleared."""
    L = 1
    for x in xs:
        if isinstance(x, F):
            L = lcm(L, x.denominator)
    return max(abs(int(x * L)).bit_length() for x in xs)


class C:
    def __init__(self):
        self.mul = self.add = self.sh = self.bits = 0

    def b(self, xs):
        self.bits = max(self.bits, vbits(xs))

    def __add__(self, o):
        r = C()
        r.mul, r.add, r.sh, r.bits = self.mul + o.mul, self.add + o.add, self.sh + o.sh, max(self.bits, o.bits)
        return r

    def fmt(self):
        return f"{self.mul}m/{self.add}a/{self.sh}s b{self.bits}"


def shift_by(a, c, ctr):
    """x -> x + c (Taylor shift), in place on a copy. c==1 costs additions only; c==0 free."""
    a, n = list(a), len(a) - 1
    if c == 0:
        return a
    for i in range(n):
        for j in range(n - 1, i - 1, -1):
            a[j] = a[j] + c * a[j + 1]
            ctr.add += 1
            ctr.mul += 0 if c == 1 else 1
    ctr.b(a)
    return a


# ---------------- M3: Taylor-centre certificate
def m3_crit(a, h, ctr):
    tot, hk = F(0), F(1)
    for k in range(1, len(a)):
        hk = hk * h
        tot += abs(a[k]) * hk
        ctr.mul += 2
        ctr.add += 1
    return a[0] > tot


def m3_construct(P):
    ctr, leaves = C(), []
    stack = [(F(1, 2), F(1, 2), shift_by(P, F(1, 2), ctr), 0)]
    while stack:
        c, h, a, d = stack.pop()
        if a[0] <= 0:
            return "REFUTED", None, ctr
        if m3_crit(a, h, ctr):
            leaves.append((c, h))
        elif d >= CAP:
            return "REFUSED", None, ctr
        else:
            for s in (-1, 1):
                stack.append((c + s * h / 2, h / 2, shift_by(a, s * h / 2, ctr), d + 1))
    return "CERT", leaves, ctr


def m3_verify(P, leaves):
    ctr, edge = C(), F(0)
    for c, h in sorted(leaves):
        if c - h != edge:
            return False, ctr
        edge = c + h
        if not m3_crit(shift_by(P, c, ctr), h, ctr):
            return False, ctr
    return edge == 1, ctr


# ---------------- M4: Descartes / VCA on integers
def to_int(P):
    L = 1
    for x in P:
        L = lcm(L, x.denominator)
    return [int(x * L) for x in P]


def m4_test(a, ctr):
    R = shift_by(a[::-1], 1, ctr)
    return all(x > 0 for x in R)


def m4_construct(P):
    ctr, n, leaves = C(), len(P) - 1, []
    a0 = to_int(P)
    stack = [(a0, 0, 0)]
    while stack:
        a, k, d = stack.pop()
        ctr.b(a)
        ctr.add += len(a)
        if a[0] <= 0 or sum(a) <= 0:
            return "REFUTED", None, ctr
        if m4_test(a, ctr):
            leaves.append((k, d))
        elif d >= CAP:
            return "REFUSED", None, ctr
        else:
            left = [x * 2 ** (n - j) for j, x in enumerate(a)]
            ctr.sh += n + 1
            right = shift_by(left, 1, ctr)
            stack.append((right, 2 * k + 1, d + 1))
            stack.append((left, 2 * k, d + 1))
    return "CERT", leaves, ctr


def m4_verify(P, leaves):
    ctr, n = C(), len(P) - 1
    a0, pos = to_int(P), F(0)
    for k, d in sorted(leaves, key=lambda t: F(t[0], 2 ** t[1])):
        if F(k, 2 ** d) != pos:
            return False, ctr
        pos = F(k + 1, 2 ** d)
        q = [x * 2 ** (d * (n - j)) for j, x in enumerate(a0)]
        ctr.sh += n + 1
        q = shift_by(q, k, ctr)
        if not m4_test(q, ctr):
            return False, ctr
    return pos == 1, ctr


# ---------------- fixtures (deterministic, fixed before running; not tuned)
def pp(*roots_sq, scale=1, eps=0):
    p = [F(scale)]
    for r in roots_sq:
        p = base.pmul(p, [r * r, -2 * r, F(1)])
    p[0] += eps
    return p


def fixtures():
    import random
    rng, out = random.Random(20261023), []
    for deg in (4, 6, 8):
        k = 0
        while k < 4:
            p = base.rand_pos_poly(deg, rng)
            if min(base.bern_from_power(p)) <= 0:
                out.append((f"rand deg{deg} #{k}", p, True))
                k += 1
    for e in (2, 8, 32):
        out.append((f"(t-1/3)^2+1e-{e}", [F(1, 9) + F(1, 10**e), F(-2, 3), F(1)], True))
    for e in (2, 8):
        out.append((f"(t-1/3)^2(t-2/3)^2(t-1/2)^2+1e-{e}", pp(F(1, 3), F(2, 3), F(1, 2), eps=F(1, 10**e)), True))
    out += [("(t-1/3)^2   [double zero]", pp(F(1, 3)), False), ("(t-1/3)^2(t-2/3)^2(t-1/2)^2 [3 double zeros]", pp(F(1, 3), F(2, 3), F(1, 2)), False),
            ("(t-1/3)(t-2/3)   [sign change]", base.pmul([F(-1, 3), F(1)], [F(-2, 3), F(1)]), False),
            ("(t-3/2)^2        [zero outside]", pp(F(3, 2)), True), ("t^2+1           [trivial]", [F(1), F(0), F(1)], True),
            ("t^2-t+1/4+1e-4 (min at 1/2)", [F(1, 4) + F(1, 10**4), F(-1), F(1)], True)]
    return out


def m1_bits(cb):
    bits, stack = 0, [(cb, 0)]
    while stack:
        cur, d = stack.pop()
        bits = max(bits, vbits(cur))
        if min(cur) <= 0 and max(cur) > 0 and d < CAP:
            stack.extend((h, d + 1) for h in base.split(cur))
    return bits


def m2_bits(P):
    return max(vbits(q) for q in base.sturm_chain(P)[0])


def run():
    rows, tot = [], {k: [0, 0, 0, 0, 0, 0] for k in ("M1", "M2", "M3", "M4")}  # certs, wrong, mul, add, shift, verifyops
    wrong = []
    for name, P, truth in fixtures():
        print(f"\n{name}  (truth: {'strictly positive' if truth else 'NOT strictly positive'})")
        cb = base.bern_from_power(P)
        leaves, d_ops, bits = base.discover(cb, cap=CAP)
        fl = base.tree_flags(cb, cap=CAP) if leaves else None
        v_ops = base.verify(cb, fl)[1] if fl else 0
        r1 = ("CERT" if leaves else "REFUSED/REFUTED", d_ops, v_ops, m1_bits(cb))
        ok2, sd, sv, sb = base.sturm_positive(P)
        r2 = ("CERT" if ok2 else "REFUTED", sd, sv, m2_bits(P))
        o3, l3, c3 = m3_construct(P)
        v3 = m3_verify(P, l3) if l3 else (None, C())
        o4, l4, c4 = m4_construct(P)
        v4 = m4_verify(P, l4) if l4 else (None, C())
        print(f"  M1 bisect  {r1[0]:<16} build {r1[1]} lerps (={2*r1[1]}a/{r1[1]}s)  replay-verify {r1[2]} lerps  bits {r1[3]}")
        print(f"  M2 sturm   {r2[0]:<16} build {r2[1]} mults (adds not instrumented, ~equal)  verify {r2[2]}  bits {r2[3]}")
        print(f"  M3 taylor  {o3:<16} build {c3.fmt()}  indep-verify {v3[1].fmt() if l3 else '-'} ok={v3[0]}  leaves={len(l3) if l3 else 0}")
        print(f"  M4 descart {o4:<16} build {c4.fmt()}  indep-verify {v4[1].fmt() if l4 else '-'} ok={v4[0]}  leaves={len(l4) if l4 else 0}")
        for m, out in (("M1", r1[0]), ("M2", r2[0]), ("M3", o3), ("M4", o4)):
            if (out == "CERT") != truth and not (out == "CERT" and False):
                if out == "CERT" and not truth:
                    wrong.append((name, m, "FALSE CERTIFICATE"))
                if out != "CERT" and truth:
                    tot[m][1] += 1
        tot["M1"][0] += r1[0] == "CERT"; tot["M2"][0] += ok2; tot["M3"][0] += o3 == "CERT"; tot["M4"][0] += o4 == "CERT"
        if o3 == "CERT":
            tot["M3"][2:6] = [tot["M3"][2] + c3.mul, tot["M3"][3] + c3.add, tot["M3"][4] + c3.sh, tot["M3"][5] + v3[1].mul + v3[1].add]
        if o4 == "CERT":
            tot["M4"][2:6] = [tot["M4"][2] + c4.mul, tot["M4"][3] + c4.add, tot["M4"][4] + c4.sh, tot["M4"][5] + v4[1].mul + v4[1].add]
        if ok2:
            tot["M2"][2:6] = [tot["M2"][2] + sd, tot["M2"][3], tot["M2"][4], tot["M2"][5] + sv]
        if r1[0] == "CERT":
            tot["M1"][2:6] = [tot["M1"][2], tot["M1"][3] + 2 * r1[1], tot["M1"][4] + r1[1], tot["M1"][5] + r1[2]]
    print("\n== summary over certified fixtures (certs, missed-positive refusals, mul, add, shift, verify-ops) ==")
    for m, v in tot.items():
        print(f"  {m}: certs={v[0]} missed_positive={v[1]} mul={v[2]} add={v[3]} shift={v[4]} verify_ops={v[5]}")
    print("  false certificates:", wrong or "none")
    return not wrong


def identities():
    try:
        import sympy as sp
    except ImportError:
        print("\n(SymPy absent: identity section skipped)")
        return True
    ok = True
    x, y, t, c = sp.symbols("x y t c")
    d, e, f, a, b, c0, u, v = sp.symbols("d e f a b c0 u v")
    lhs = d * (x - u) ** 2 + e * (x - u) * (y - v) + f * (y - v) ** 2 + a * (x - u) + b * (y - v) + c0
    rhs = d * x**2 + e * x * y + f * y**2 + (a - 2 * d * u - e * v) * x + (b - 2 * f * v - e * u) * y + (d * u**2 + e * u * v + f * v**2 - a * u - b * v + c0)
    r = sp.expand(lhs - rhs) == 0
    print(("PASS" if r else "FAIL"), "S1 book Thm 118 translate-of-a-conic coefficient identity"); ok &= r
    x0, y0 = sp.symbols("x0 y0")
    q = d * x**2 + e * x * y + f * y**2 + a * x + b * y + c0
    w = sp.expand(q.subs({x: x + x0, y: y + y0}, simultaneous=True))
    r = sp.simplify(w.coeff(x, 1).coeff(y, 0) - sp.diff(q, x).subs({x: x0, y: y0})) == 0 and sp.simplify(w.coeff(y, 1).coeff(x, 0) - sp.diff(q, y).subs({x: x0, y: y0})) == 0
    print(("PASS" if r else "FAIL"), "S2 book Thm 119: linear Taylor coefficients (a+2d x0+e y0, b+e x0+2f y0) equal the partial derivatives"); ok &= r
    for n in (4, 6, 8):
        A = sp.symbols(f"A0:{n+1}")
        p = sum(A[k] * t**k for k in range(n + 1))
        sh = sp.Poly(sp.expand(p.subs(t, t + c)), t).all_coeffs()[::-1]
        r = all(sp.simplify(sh[k] - sp.diff(p, t, k).subs(t, c) / sp.factorial(k)) == 0 for k in range(n + 1))
        r2 = sp.expand(sp.Poly(sp.expand(p.subs(t, t + c)), t).as_expr().subs(t, t + 1) - p.subs(t, t + c + 1)) == 0
        print(("PASS" if r and r2 else "FAIL"), f"S3 n={n}: shift coefficients = P^(k)(c)/k!, and shifts compose"); ok &= r and r2
        rev = sp.expand(sum(A[k] * (1 + t) ** (n - k) for k in range(n + 1)))
        Pp = sp.Poly(rev, t).all_coeffs()[::-1]
        bern = [sum(sp.Rational(comb(i, j), comb(n, j)) * A[j] for j in range(i + 1)) for i in range(n + 1)]
        r = all(sp.simplify(Pp[n - i] - comb(n, i) * bern[i]) == 0 or sp.simplify(Pp[i] - comb(n, i) * bern[n - i]) == 0 for i in range(n + 1))
        print(("PASS" if r else "FAIL"), f"S4 n={n}: coeffs of (1+x)^n p(1/(1+x)) = binomial * Bernstein coefficients (M4 test == M1 test)"); ok &= r
    return ok


def contact_order():
    """Book §19.3 idea in 1-D: the first non-zero Taylor coefficient at a point is its order of contact (root multiplicity)."""
    cases = [("(t-1/3)^2 at 1/3", pp(F(1, 3)), F(1, 3), 2), ("(t-1/3)^2(t-2/3)^2(t-1/2)^2 at 1/3", pp(F(1, 3), F(2, 3), F(1, 2)), F(1, 3), 2),
             ("same at 2/3", pp(F(1, 3), F(2, 3), F(1, 2)), F(2, 3), 2), ("same at 1/2", pp(F(1, 3), F(2, 3), F(1, 2)), F(1, 2), 2),
             ("(t-1/3)^2+1e-8 at 1/3 (no zero)", [F(1, 9) + F(1, 10**8), F(-2, 3), F(1)], F(1, 3), 0)]
    ok = True
    print("\n== order of contact via one exact Taylor shift (needs the root; Sturm/gcd must supply it) ==")
    for name, P, c, want in cases:
        ctr = C()
        a = shift_by(P, c, ctr)
        m = next(k for k, x in enumerate(a) if x != 0)
        good = (m == want)
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'} {name}: first nonzero index {m}, leading coeff {a[m]}  ({ctr.fmt()})")
    return ok


if __name__ == "__main__":
    good = run()
    good &= contact_order()
    good &= identities()
    print("\nNO FALSE CERTIFICATES; identities PASS" if good else "\nPROBLEM: see above")
    sys.exit(0 if good else 1)
