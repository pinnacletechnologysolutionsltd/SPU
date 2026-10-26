"""Preparation primitives (contract §5). Results are truncated to their highest nonzero index (free, uncounted)."""
from math import comb, gcd
from ledger import Q, lit


def trim(p):
    p = list(p)
    while len(p) > 1 and p[-1].n == 0:
        p.pop()
    return p


def pmul(a, b):
    r = [None] * (len(a) + len(b) - 1)
    for i in range(len(a)):
        for j in range(len(b)):
            term = a[i] * b[j]
            r[i + j] = term if r[i + j] is None else r[i + j] + term
    return r


def _combine(a, b, sign):
    n = min(len(a), len(b))
    out = [a[i] + b[i] if sign > 0 else a[i] - b[i] for i in range(n)]
    longer = a if len(a) >= len(b) else b
    for i in range(n, len(longer)):          # unmatched coefficients copy (free); a longer subtrahend is negated (free)
        out.append(longer[i] if (longer is a or sign > 0) else -longer[i])
    return out


def padd(a, b):
    return _combine(a, b, +1)


def psub(a, b):
    return _combine(a, b, -1)


def pscale2(a):
    return [x.twice() for x in a]


def pder(a):
    if len(a) == 1:
        return [lit(0, a[0].L)]
    return [a[i] * lit(i, a[0].L) for i in range(1, len(a))]   # i is an index: M for every i, including 2


def pint(a):
    L = a[0].L
    return [lit(0, L)] + [a[i] / lit(i + 1, L) for i in range(len(a))]   # D for every i, including i+1 = 2


def pcomp(a, b):
    acc = [a[-1]]
    for i in range(len(a) - 2, -1, -1):
        acc = pmul(acc, b)
        acc[0] = acc[0] + a[i]
    return acc


def bern(a, name):
    """Power -> Bernstein with imported weights w[j][i] = C(j,i)/C(d,i); first term initialises, later terms add."""
    d, L = len(a) - 1, a[0].L
    out = []
    for j in range(d + 1):
        acc = None
        for i in range(j + 1):
            num, den = comb(j, i), comb(d, i)
            g = gcd(num, den)
            term = Q.imp(num // g, den // g, L, "w.%s.%d.%d" % (name, j, i)) * a[i]
            acc = term if acc is None else acc + term
        out.append(acc)
    return out


def derive_steps():
    """P1-P15 of contract §5 as (label, target, reads, fn) tuples; fn(env, L) -> value."""
    t = trim
    return [
        ("P1", "UU", ("U",), lambda e, L: t(pmul(e["U"], e["U"]))),
        ("P2", "VV", ("V",), lambda e, L: t(pmul(e["V"], e["V"]))),
        ("P3", "UV", ("U", "V"), lambda e, L: t(pmul(e["U"], e["V"]))),
        ("P4", "dx", ("UU", "VV"), lambda e, L: t(psub(e["UU"], e["VV"]))),
        ("P5", "dy", ("UV",), lambda e, L: t(pscale2(e["UV"]))),
        ("P6", "sg", ("UU", "VV"), lambda e, L: t(padd(e["UU"], e["VV"]))),
        ("P7", "X", ("dx",), lambda e, L: t(pint(e["dx"]))),
        ("P8", "Y", ("dy",), lambda e, L: t(pint(e["dy"]))),
        ("P9", "SS", ("sg",), lambda e, L: t(pint(e["sg"]))),
        ("P10", "U1", ("U",), lambda e, L: t(pder(e["U"]))),
        ("P11", "V1", ("V",), lambda e, L: t(pder(e["V"]))),
        ("P12", "NP1", ("U", "V1"), lambda e, L: t(pmul(e["U"], e["V1"]))),
        ("P13", "NP2", ("U1", "V"), lambda e, L: t(pmul(e["U1"], e["V"]))),
        ("P14", "Np", ("NP1", "NP2"), lambda e, L: t(psub(e["NP1"], e["NP2"]))),
        ("P15", "Nk", ("Np",), lambda e, L: t(pscale2(e["Np"]))),
    ]
