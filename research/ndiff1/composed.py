"""Composition-at-evaluation control: evaluate the BASE curve, then apply the chain pointwise (no maintenance).

Pointwise rules (counted): rot: P,T rotated (4 mul+2 add each), Q/speed2/dQ/sigma invariant.
scale k: P,T *k, k2=k*k, Q,dQ,speed2 *k2, sigma*k.   t2 at level param s: T*=2s, dQ*=2s, speed2*=(2s)^2, sigma*=2s.
"""
from rep import *
import cost


def comp_eval(base, chain, ev, t0, arg):
    levels = [t0]
    for op, _ in reversed(chain):
        levels.append(levels[-1] * levels[-1] if op == "t2" else levels[-1])
    levels.reverse()  # levels[j] = parameter at the output level of step j+1 ... levels[0] = base parameter
    out = ev(base, levels[0], 1)
    P, T, sp2, Q, dQ, sig = out["P"], out["T"], out["speed2"], out["Q"], out["dQ"], out.get("sigma")
    for j, (op, nm) in enumerate(chain):
        if op == "rot":
            cs, sn = arg(op, nm)
            P = (cs * P[0] - sn * P[1], sn * P[0] + cs * P[1])
            T = (cs * T[0] - sn * T[1], sn * T[0] + cs * T[1])
        elif op == "scale":
            k = arg(op, nm)
            k2 = k * k
            P, T, sp2, Q, dQ = (k * P[0], k * P[1]), (k * T[0], k * T[1]), k2 * sp2, k2 * Q, k2 * dQ
            sig = k * sig if sig is not None else None
        else:
            s2 = levels[j + 1].scale(2)
            T, dQ, sp2 = (s2 * T[0], s2 * T[1]), s2 * dQ, (s2 * s2) * sp2
            sig = s2 * sig if sig is not None else None
    out = {"P": P, "T": T, "speed2": sp2, "Q": Q, "dQ": dQ}
    if sig is not None:
        out["sigma"] = sig
    return out
