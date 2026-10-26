"""Q(sqrt3) with a declared operation-count model, plus exact polynomial helpers.

Cost model (frozen before any result is read):
  surd mul  = 4 rational mul + 2 rational add + 1 rational const-mul (schoolbook)
  surd add  = 2 rational add;   kmul (surd * small rational) = 2 rational const-mul
  Hodograph/Eisenstein field mul is counted the same way (4 mR + 2 aR + 1 kR).
Only mul/add/kmul are counted; negation, comparison and copies are free.
"""
from fractions import Fraction as F
from collections import Counter
from math import isqrt

OPS = Counter()


class S3:
    __slots__ = ("p", "q")

    def __init__(s, p=0, q=0):
        s.p, s.q = F(p), F(q)

    def __add__(a, b):
        OPS["add"] += 1
        return S3(a.p + b.p, a.q + b.q)

    def __sub__(a, b):
        OPS["add"] += 1
        return S3(a.p - b.p, a.q - b.q)

    def __mul__(a, b):
        OPS["mul"] += 1
        return S3(a.p * b.p + 3 * a.q * b.q, a.p * b.q + a.q * b.p)

    def __neg__(a):
        return S3(-a.p, -a.q)

    def scale(a, k):
        OPS["kmul"] += 1
        return S3(a.p * k, a.q * k)

    def __eq__(a, b):
        return a.p == b.p and a.q == b.q

    def __hash__(a):
        return hash((a.p, a.q))

    def __repr__(a):
        return f"({a.p}+{a.q}r3)"

    def bits(a):
        return max(x.numerator.bit_length() for x in (a.p, a.q)), max(x.denominator.bit_length() for x in (a.p, a.q))


ZERO, ONE, R3 = S3(0), S3(1), S3(0, 1)


def rsqrt(f):
    if f < 0:
        return None
    n, d = isqrt(f.numerator), isqrt(f.denominator)
    return F(n, d) if n * n == f.numerator and d * d == f.denominator else None


def sqrt_s3(x):
    """Return y in Q(sqrt3) with y*y == x (either sign), or None. Uncounted: a decision procedure."""
    m = rsqrt(x.p * x.p - 3 * x.q * x.q)
    if m is None:
        return None
    for mm in (m, -m):
        u2 = rsqrt((x.p + mm) / 2)
        if u2 is None:
            continue
        if u2 == 0:
            v2 = rsqrt((x.p - mm) / 6)
            if v2 is not None:
                return S3(0, v2)
            continue
        y = S3(u2, x.q / (2 * u2))
        if (y.p * y.p + 3 * y.q * y.q, 2 * y.p * y.q) == (x.p, x.q):
            return y
    return None


def reset():
    OPS.clear()


def snapshot():
    c = dict(OPS)
    m, a, k = c.get("mul", 0), c.get("add", 0), c.get("kmul", 0)
    return {"surd_mul": m, "surd_add": a, "surd_kmul": k,
            "rat_mul": 4 * m, "rat_add": 2 * m + 2 * a, "rat_kmul": m + 2 * k}


# polynomials: tuples of field elements, low degree first
def padd(a, b, sub=False):
    n = max(len(a), len(b))
    a, b = list(a) + [ZERO] * (n - len(a)), list(b) + [ZERO] * (n - len(b))
    return tuple(x - y if sub else x + y for x, y in zip(a, b))


def pmul(a, b):
    out = [ZERO] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = out[i + j] + x * y
    return tuple(out)


def pint(a):
    return (ZERO,) + tuple(c.scale(F(1, k + 1)) for k, c in enumerate(a))


def pder(a):
    return tuple(c.scale(k) for k, c in enumerate(a) if k) or (ZERO,)


def horner(a, t):
    r = a[-1]
    for c in reversed(a[:-1]):
        r = r * t + c
    return r


def pbits(a):
    nb = [c.bits() for c in a]
    return max(n for n, _ in nb), max(d for _, d in nb)
