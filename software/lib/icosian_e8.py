"""ICOS-0: exact icosian construction of E8 over Z[phi] (software oracle).

Independent of BQ-0, A31 and the Lucas/Phinary modular oracles: exact Fractions,
no sqrt3, no fixed width. Reference: Moody & Patera, "Quasicrystals and
icosians" (1993); Conway & Sloane, SPLAG ch. 8.

Z[phi] element a+b*phi is ZP(a,b), phi^2=phi+1. A quaternion is a 4-tuple of ZP.
Units: 8 (+-1,+-i,+-j,+-k) + 16 (+-1+-i+-j+-k)/2 + 96 even permutations of
(+-phi,+-1,+-1/phi,0)/2  = 120 (binary icosahedral group).
E8 form: for x,y, dot(x,y)=a+b*phi (4-dim Euclidean dot in Q(sqrt5)); then
B(x,y)=2*(a+b). B = 2*Tr(lam*dot), lam=(5+sqrt5)/10 totally positive, so B is
positive definite on the 8-dim Z-lattice. Roots: U and phi^-1*U (B=2 each).
"""
from fractions import Fraction as Fr
from itertools import permutations, product


class ZP:
    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a, self.b = Fr(a), Fr(b)

    def __add__(s, o): return ZP(s.a + o.a, s.b + o.b)
    def __sub__(s, o): return ZP(s.a - o.a, s.b - o.b)
    def __neg__(s): return ZP(-s.a, -s.b)
    def __mul__(s, o): return ZP(s.a*o.a + s.b*o.b, s.a*o.b + s.b*o.a + s.b*o.b)
    def __eq__(s, o): return (s.a, s.b) == (o.a, o.b)
    def __hash__(s): return hash((s.a, s.b))
    def __repr__(s): return "ZP(%s,%s)" % (s.a, s.b)


ZERO, ONE, PHI, IPHI = ZP(), ZP(1), ZP(0, 1), ZP(-1, 1)  # IPHI = 1/phi = phi-1
HALF = Fr(1, 2)


def qmul(p, q):
    a, b, c, d = p; e, f, g, h = q
    return (a*e - b*f - c*g - d*h, a*f + b*e + c*h - d*g,
            a*g - b*h + c*e + d*f, a*h + b*g - c*f + d*e)


def qconj(p): return (p[0], -p[1], -p[2], -p[3])
def qscale(z, p): return tuple(z * t for t in p)
def qhalf(p): return tuple(ZP(t.a * HALF, t.b * HALF) for t in p)


def _parity(p):
    return sum(1 for i in range(4) for j in range(i + 1, 4) if p[i] > p[j]) % 2


def units():
    u = []
    for i in range(4):
        for s in (1, -1):
            u.append(tuple(ZP(s) if k == i else ZERO for k in range(4)))
    for sg in product((1, -1), repeat=4):
        u.append(qhalf(tuple(ZP(s) for s in sg)))
    base = (PHI, ONE, IPHI, ZERO)
    for p in permutations(range(4)):
        if _parity(p):
            continue
        for sg in product((1, -1), repeat=3):
            it = iter(sg)
            v = [None] * 4
            for pos, val in zip(p, base):
                v[pos] = val if val == ZERO else (val if next(it) > 0 else -val)
            u.append(qhalf(tuple(v)))
    return u


def dot(x, y):
    r = ZERO
    for s, t in zip(x, y):
        r = r + s * t
    return r


def B(x, y):
    d = dot(x, y)
    return 2 * (d.a + d.b)


def roots():
    U = units()
    return U + [qscale(IPHI, u) for u in U]


def reflect(r, x):
    k = B(x, r) // 1  # B(r,r)=2, so s_r(x)=x-B(x,r)*r
    assert k.denominator == 1
    return tuple(t - ZP(k) * s for t, s in zip(x, r))


def vec8(x):
    """Integer 8-vector (2a_i,2b_i); raises if a coordinate is not in (1/2)Z[phi]."""
    v = []
    for t in x:
        for c in (2 * t.a, 2 * t.b):
            assert c.denominator == 1
            v.append(int(c))
    return v


def from_vec8(v): return tuple(ZP(Fr(v[2*i], 2), Fr(v[2*i+1], 2)) for i in range(4))
def bits(x): return max(abs(c).bit_length() for c in vec8(x))


def hnf_rows(rows):
    """Integer row-echelon basis of the Z-span of rows (Euclid on columns)."""
    rows = [list(r) for r in rows if any(r)]
    basis, n = [], len(rows[0])
    for col in range(n):
        while True:
            nz = [r for r in rows if r[col]]
            if len(nz) <= 1:
                break
            nz.sort(key=lambda r: abs(r[col]))
            p = nz[0]
            for r in nz[1:]:
                q = r[col] // p[col]
                for k in range(n):
                    r[k] -= q * p[k]
        nz = [r for r in rows if r[col]]
        if nz:
            basis.append(nz[0]); rows.remove(nz[0])
        rows = [r for r in rows if any(r)]
    return basis


def det(M):
    M = [[Fr(c) for c in r] for r in M]; n = len(M); d = Fr(1)
    for i in range(n):
        p = next((r for r in range(i, n) if M[r][i]), None)
        if p is None: return Fr(0)
        if p != i: M[i], M[p] = M[p], M[i]; d = -d
        d *= M[i][i]
        for r in range(i + 1, n):
            f = M[r][i] / M[i][i]
            M[r] = [x - f * y for x, y in zip(M[r], M[i])]
    return d
