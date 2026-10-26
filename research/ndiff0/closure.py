"""Phase 3: closure of (i) the PH property, (ii) primitive generators (h=1), (iii) generalised (h,a,b), all in Q(sqrt3).

Why (ii) reduces to a scalar test: if (A+iB)^2 = u*(a+ib)^2 with u a constant, unique factorisation in K(i)[t]
forces A+iB = kappa*(a+ib), kappa^2 = u. For h*(a+ib)^2 with a non-square h(t), no kappa exists.
"""
from field import *
from curve import PH
import cost


def sinv(x):
    n = x.p * x.p - 3 * x.q * x.q
    return S3(x.p / n, -x.q / n)


def cpoly(k):
    return (k,)


def psqrt(f):
    """Exact square root of a polynomial over Q(sqrt3) (up to sign), or None. Analysis tool, uncounted."""
    m, top = (len(f) - 1) // 2, sqrt_s3(f[-1])
    if (len(f) - 1) % 2 or top is None:
        return None
    s = [ZERO] * (m + 1)
    s[m] = top
    inv2 = sinv(top + top)
    for k in range(1, m + 1):
        acc = f[2 * m - k]
        for i in range(1, k):
            acc = acc - s[m - i] * s[m - k + i]
        s[m - k] = acc * inv2
    r = tuple(s)
    sq = pmul(r, r)
    return r if all(x == y for x, y in zip(sq, f)) and len(sq) == len(f) else None


def same(p, q):
    n = max(len(p), len(q))
    return all(x == y for x, y in zip(list(p) + [ZERO] * (n - len(p)), list(q) + [ZERO] * (n - len(q))))


def ph_in_domain(xp, yp):
    return psqrt(padd(pmul(xp, xp), pmul(yp, yp))) is not None


def hod_matches(gen, xp, yp):
    return same(gen.xp, xp) and same(gen.yp, yp)


def rotation(c, cs, sn):
    xp = padd(pmul(cpoly(cs), c.xp), pmul(cpoly(sn), c.yp), True)
    yp = padd(pmul(cpoly(sn), c.xp), pmul(cpoly(cs), c.yp))
    r = {"ph_property": ph_in_domain(xp, yp), "primitive": False, "general": False}
    if cs == S3(-1):
        cphi, sphi = ZERO, ONE
    else:
        cphi = sqrt_s3(S3((1 + cs.p) / 2, cs.q / 2))
        sphi = sn * sinv(cphi + cphi) if cphi is not None else None
    if cphi is not None:
        g = PH(padd(pmul(cpoly(cphi), c.a), pmul(cpoly(sphi), c.b), True), padd(pmul(cpoly(sphi), c.a), pmul(cpoly(cphi), c.b)))
        r["primitive"] = hod_matches(g, xp, yp)
    t = sn * sinv(ONE + cs) if cs != S3(-1) else None
    if t is not None:
        rr = sinv(ONE + t * t)
        g = PH(padd(c.a, pmul(cpoly(t), c.b), True), padd(c.b, pmul(cpoly(t), c.a)), pmul(cpoly(rr), c.h))
        r["general"] = hod_matches(g, xp, yp)
        r["general_gen_bits"] = pbits(g.a + g.b + g.h)
    else:
        g = PH(tuple(-x for x in c.b), c.a, c.h)
        r["general"] = hod_matches(g, xp, yp)
    return r, (xp, yp)


def scaling(c, lam):
    xp, yp = pmul(cpoly(lam), c.xp), pmul(cpoly(lam), c.yp)
    r = {"ph_property": ph_in_domain(xp, yp), "primitive": False, "general": False}
    root = sqrt_s3(lam)
    if root is not None:
        g = PH(pmul(cpoly(root), c.a), pmul(cpoly(root), c.b), c.h)
        r["primitive"] = hod_matches(g, xp, yp)
    g = PH(c.a, c.b, pmul(cpoly(lam), c.h))
    r["general"] = hod_matches(g, xp, yp)
    return r, (xp, yp)


def sub_t2(p):
    out = []
    for i, x in enumerate(p):
        out += [x] + ([ZERO] if i < len(p) - 1 else [])
    return tuple(out)


def reparam_t2(c):
    two_t = (ZERO, S3(2))
    xp, yp = pmul(two_t, sub_t2(c.xp)), pmul(two_t, sub_t2(c.yp))
    g = PH(sub_t2(c.a), sub_t2(c.b), pmul(two_t, sub_t2(c.h)), c.X[0], c.Y[0])
    r = {"ph_property": ph_in_domain(xp, yp), "general": hod_matches(g, xp, yp)}
    r["position_is_X_of_t2"] = same(g.X, sub_t2(c.X)) and same(g.Y, sub_t2(c.Y))
    r["primitive"] = False  # h=2t has odd t-valuation => not a square in K(i)[t]; checked below
    val = next(i for i, x in enumerate(pmul(two_t, c.h)) if x != ZERO)
    r["h_valuation_odd"] = val % 2 == 1
    r["regular_at_0"] = g.sigma[0] != ZERO
    return r, g
