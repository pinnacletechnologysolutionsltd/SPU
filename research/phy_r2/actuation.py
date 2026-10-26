"""PHY-R2: exact cable actuation along a path of PHY-R1 metric equilibria.

Conventions (from PHY-R1 / the canonical oracle): force density q_e = T_e / l_e,
cables q > 0 (tension), struts q < 0 (compression); the unique self-stress is
cable 1, strut -3/2, scaled by a prestress level LAM > 0.

Two constitutive laws, both expressed through rest *quadrance* R = l0^2:
  Hooke:    T = k (l - l0)           q = k (1 - sqrt(R/Q))
            equilibrium  <=>  R = Q (1 - LAM q*/k)^2   with 1 - LAM q*/k > 0
  Squared:  E = (kappa/4) max(Q - R, 0)^2  ->  q = kappa (Q - R)   (no sqrt)
            equilibrium  <=>  R = Q - LAM q*/kappa
Cables are unilateral (q = 0 when slack); struts are bilateral.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction as Fr

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "phy_r1"))
import fixture                       # noqa: E402
import model                         # noqa: E402
from field import QF, sqrt_in_field  # noqa: E402

LAM = Fr(1)
HOOKE = {"C": Fr(4), "S": Fr(40)}         # stiffness k per member type
SQUARED = {"C": Fr(1, 2), "S": Fr(5)}     # kappa per member type


def path_metric(M1, t):
    """M(t) = (1 - t) I + t M1; unit diagonal is preserved for every t."""
    t = Fr(t)
    return tuple(tuple((1 - t) * int(i == j) + t * Fr(M1[i][j]) for j in range(3))
                 for i in range(3))


def member_quadrances(mach, M):
    X = mach.X
    return [model.quad([X[i][k] - X[j][k] for k in range(3)], M) for i, j, _ in mach.E]


def target_densities(mach):
    return [LAM * v for v in mach.certs[0]["stress"]]


# ---- rest parameters -------------------------------------------------------
def rest_hooke(Qs, mach):
    R = []
    for Q, qs, (_, _, t) in zip(Qs, target_densities(mach), mach.E):
        c = 1 - qs / HOOKE[t]
        if c <= 0:
            raise ValueError("INVALID_CABLE: needs non-positive rest length")
        R.append(c * c * Q)
    return R


def rest_squared(Qs, mach):
    R = []
    for Q, qs, (_, _, t) in zip(Qs, target_densities(mach), mach.E):
        r = Q - qs / SQUARED[t]
        if r <= 0:
            raise ValueError("INVALID_CABLE: needs non-positive rest quadrance")
        R.append(r)
    return R


# ---- induced force densities ----------------------------------------------
def densities_squared(Qs, Rs, E):
    out = []
    for Q, R, (_, _, t) in zip(Qs, Rs, E):
        v = SQUARED[t] * (Q - R)
        out.append(Fr(0) if (t == "C" and v <= 0) else v)
    return out


def densities_hooke(Qs, Rs, E):
    """Exact only when every R/Q is a rational square; otherwise None."""
    out = []
    for Q, R, (_, _, t) in zip(Qs, Rs, E):
        s = sqrt_in_field(QF(Fr(R) / Q, Fr(0), 1))
        if s is None:
            return None
        v = HOOKE[t] * (1 - s.a)
        out.append(Fr(0) if (t == "C" and v <= 0) else v)
    return out


def hooke_matches(Qs, Rs, mach) -> bool:
    """sqrt-free test that Hooke densities equal the target stress."""
    for Q, R, qs, (_, _, t) in zip(Qs, Rs, target_densities(mach), mach.E):
        c = 1 - qs / HOOKE[t]
        if c <= 0 or Fr(R) != c * c * Q:
            return False
    return True


# ---- equilibrium checks ----------------------------------------------------
def relational_equilibrium(mach, h, dens):
    """Omega(dens) G Omega(dens) == 0 from pairwise quadrances only."""
    import reference as R
    n = len(mach.X)
    G = R.centred_gram(mach.pair_quadrances(h))
    om = fixture.stress_matrix(dens, mach.E, n)
    resid = R._mm(R._mm(om, G), om)
    return all(v == 0 for row in resid for v in row)


def coordinate_equilibrium(points, dens, E, d):
    """Explicit node force sums in Q(sqrt d) materialised coordinates."""
    n = len(points)
    zero = QF.of(0, d)
    for node in range(n):
        f = [zero, zero, zero]
        for q, (i, j, _) in zip(dens, E):
            if node in (i, j):
                other = j if node == i else i
                f = [f[k] + q * (points[other][k] - points[node][k]) for k in range(3)]
        if any(not c.is_zero() for c in f):
            return False
    return True


def admit_path(mach, M1):
    """Endpoint admission + exact bounds valid on all of t in [0, 1]."""
    status, h = mach.transform(M1)
    if status != "COMMITTED":
        return ("REFUSED", h)
    q0 = member_quadrances(mach, path_metric(M1, 0))
    q1 = member_quadrances(mach, path_metric(M1, 1))
    # quadrances are affine in t, so their minimum on [0,1] is at an endpoint
    qmin = min(min(a, b) for a, b, (_, _, t) in zip(q0, q1, mach.E) if t == "C")
    for t_ in ("C", "S"):
        if 1 - LAM * (Fr(-3, 2) if t_ == "S" else 1) / HOOKE[t_] <= 0:
            return ("REFUSED", "INVALID_CABLE_HOOKE")
    if qmin - LAM / SQUARED["C"] <= 0:
        return ("REFUSED", "INVALID_CABLE_SQUARED")
    return ("ADMITTED", {"handle": h, "cable_qmin": qmin})
