"""Evaluation strategies over a PH curve and a conventional polynomial baseline; shared output set.

Outputs (order 1): P, T=P', speed2=|P'|^2, Q=|P|^2, dQ=d|P|^2/dt.  Order 2 adds P''.
PH-only extra output: exact speed sigma (not comparable: the baselines have no exact sqrt).
"""
from field import *


def _tail(x, y, xp, yp, sp2):
    Q = x * x + y * y
    dQ = (x * xp + y * yp).scale(2)
    return {"P": (x, y), "T": (xp, yp), "speed2": sp2, "Q": Q, "dQ": dQ}


def ph_eval(c, t, order=1):
    prim = len(c.h) == 1 and c.h[0] == ONE
    a, b = horner(c.a, t), horner(c.b, t)
    h = horner(c.h, t)
    hm = (lambda v: v) if prim else (lambda v: h * v)
    a2, b2, ab = a * a, b * b, a * b
    sig = hm(a2 + b2)
    xp, yp = hm(a2 - b2), hm(ab).scale(2)
    out = _tail(horner(c.X, t), horner(c.Y, t), xp, yp, sig * sig)
    out["sigma"] = sig
    if order == 2:
        assert prim, "order-2 PH path implemented for h=1 only"
        a1, b1 = horner(pder(c.a), t), horner(pder(c.b), t)
        out["P2"] = ((a * a1 - b * b1).scale(2), (a1 * b + a * b1).scale(2))
    return out


def poly_eval(c, t, order=1):
    xp, yp = horner(c.dX, t), horner(c.dY, t)
    out = _tail(horner(c.X, t), horner(c.Y, t), xp, yp, xp * xp + yp * yp)
    if order == 2:
        out["P2"] = (horner(pder(c.dX), t), horner(pder(c.dY), t))
    return out


def dual_horner(coeffs, t, order):
    """Jet-Horner at t0+eps (eps^(order+1)=0); eps-part of the variable is the constant 1, so no multiplies by it."""
    r = [coeffs[-1]] + [ZERO] * order
    for j, cf in enumerate(reversed(coeffs[:-1]), 1):
        for k in range(min(j, order), 0, -1):
            r[k] = r[k - 1] if k == j else r[k] * t + r[k - 1]
        r[0] = r[0] * t + cf
    return r


def jet_eval(c, t, order=1):
    jx, jy = dual_horner(c.X, t, order), dual_horner(c.Y, t, order)
    out = _tail(jx[0], jy[0], jx[1], jy[1], jx[1] * jx[1] + jy[1] * jy[1])
    if order == 2:
        out["P2"] = (jx[2].scale(2), jy[2].scale(2))
    return out


STRATEGIES = {"PH": ph_eval, "poly_horner": poly_eval, "jet_horner": jet_eval}


def run_counted(fn, c, t, order):
    reset()
    out = fn(c, t, order)
    return out, snapshot()


def out_bits(out):
    vals = [v for k, x in out.items() for v in (x if isinstance(x, tuple) else (x,))]
    nb = [v.bits() for v in vals]
    return max(n for n, _ in nb), max(d for _, d in nb)


def gate(ph, others):
    """Frozen gate: PH strictly fewer rational muls than every baseline and no more (mul+add)."""
    return all(ph["rat_mul"] < o["rat_mul"] and ph["rat_mul"] + ph["rat_add"] <= o["rat_mul"] + o["rat_add"] for o in others)
