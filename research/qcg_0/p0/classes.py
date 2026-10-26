"""Class gates (contract §4 X-23, §6 X-14/X-17): retiming classification and jet exactness. Exact Fractions, uncounted (administrative)."""
from fractions import Fraction as F
from math import isqrt
from events import result


def _sqrt_poly(c):
    """Exact polynomial square root of c (Fractions, ascending) or None."""
    c = list(c)
    while len(c) > 1 and c[-1] == 0:
        c.pop()
    if len(c) % 2 == 0:
        return None
    m = (len(c) - 1) // 2
    top = c[-1]
    num, den = top.numerator, top.denominator
    if num <= 0:
        return None
    rn, rd = isqrt(num), isqrt(den)
    if rn * rn != num or rd * rd != den:
        return None
    q = [F(0)] * (m + 1)
    q[m] = F(rn, rd)
    for j in range(1, m + 1):
        s = c[2 * m - j] - sum(q[m - a] * q[m - j + a] for a in range(1, j) if 0 <= m - j + a <= m)
        q[m - j] = s / (2 * q[m])
    sq = [F(0)] * (2 * m + 1)
    for i, a in enumerate(q):
        for k, b in enumerate(q):
            sq[i + k] += a * b
    return q if sq == c else None


def retiming_class(phi, den=None, form="h"):
    """phi: ascending coefficient pairs of the numerator; den: denominator pairs (None = constant 1).
    A non-constant denominator is not a polynomial retiming (OUT_OF_DOMAIN). In the primitive form the retimed generator needs
    phi' = +/- q^2 (NOT_PRIMITIVE_RETIMING otherwise); in the h-form any polynomial phi is admissible."""
    if den is not None and len([p for p in den if F(*p) != 0]) > 1 and any(F(*p) != 0 for p in den[1:]):
        return result("REFUSED", "OUT_OF_DOMAIN")
    if form == "primitive":
        d = [F(*phi[i]) * i for i in range(1, len(phi))] or [F(0)]
        if _sqrt_poly(d) is None and _sqrt_poly([-x for x in d]) is None:
            return result("REFUSED", "NOT_PRIMITIVE_RETIMING")
    return result("OK")


def jet_exact(jet_len, declared_degree):
    """A jet of order below the declared degree is an approximation: any exactness-claiming request is refused."""
    if jet_len - 1 < declared_degree:
        return result("REFUSED", "APPROX_NOT_EXACT")
    return result("OK")


def operator_exact(residual_multiplier):
    """Harmonic E2 control: the step operator carries residual (-127/37748736) * I; nonzero residual is approximate, never exact."""
    r = F(*residual_multiplier)
    return result("OK") if r == 0 else result("REFUSED", "APPROX_NOT_EXACT")
