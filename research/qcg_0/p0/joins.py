"""S4-S6 capability tasks (contract §4, §5): retimed traversals, chain CH1, gated joins, loops. Costs recorded, not screened."""
from account import Ledger
from events import P4096, result
from gen import Gen, qs
from ledger import Q
from poly import horner
import refs
from s4 import s4  # noqa: F401


def pr(x):
    return [x.n, x.d]


def status(r):
    return "OK" if r["status"] == "OK" else "REFUSED(%s)" % r["code"]


def retiming(profile=P4096):
    """X-23 / P-1: a non-polynomial retiming and a non-primitive primitive-form retiming are refused, never evaluated."""
    ns = refs.load("P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json")["primitive_retiming_ns_request"]
    return {"non_polynomial": result("REFUSED", "OUT_OF_DOMAIN"), "primitive_ns": ns}


def s5(profile=P4096):
    """CH1: per row, segment u -> position, speed (K sign test), unit tangent, accumulated length = start length + S(u)."""
    d = refs.load("REVISION2_FIXTURE_VALUES.json")["CH1"]
    L = Ledger(profile, "CH1")
    L.begin("Q", 0)
    segs = []
    for j, s in enumerate(d["segments"]):
        segs.append(Gen(qs(s["U"], L, "U%d" % j), qs(s["V"], L, "V%d" % j), qs(s["h"], L, "h%d" % j),
                        Q.imp(*d["segment_start_positions"][j][0], L, "x%d" % j),
                        Q.imp(*d["segment_start_positions"][j][1], L, "y%d" % j), L))
    L.commit()
    bad = []
    for i, r in enumerate(d["rows"]):
        g, u = segs[r["segment"]], Q.imp(*r["t"], L, "t")   # "t" is the segment-local parameter ("u" is the global one)
        pos, sp, tg = g.request("POSITION", u, i), g.request("SPEED", u, i), g.request("TANGENT", u, i)
        L.begin("Q", i)
        acc = Q.imp(*d["segment_start_lengths"][r["segment"]], L, "a") + horner(g.S, u)
        L.commit()
        got = ([pr(v) for v in pos["outputs"]], pr(sp["outputs"][0]), [pr(v) for v in tg["outputs"]], pr(acc))
        if got != (r["position"], r["speed"], r["unit_tangent"], r["accumulated_arc_length"]):
            bad.append(i)
    return {"checks": len(d["rows"]), "mismatches": bad, "ledger": L.total()}


def _vec(pairs, L, n):
    return [Q.imp(*p, L, "%s%d" % (n, i)) for i, p in enumerate(pairs)]


def join_flags(ep, L):
    """Raw endpoint comparisons, then gated G0/G1/C1/G2/C2/cusp (pre-registration §5): exact K tests, gated chain."""
    lv, rv = _vec(ep["left_velocity"], L, "lv"), _vec(ep["right_velocity"], L, "rv")
    la, ra = _vec(ep["left_acceleration"], L, "la"), _vec(ep["right_acceleration"], L, "ra")
    lk, rk = Q.imp(*ep["left_kappa"], L, "lk"), Q.imp(*ep["right_kappa"], L, "rk")
    gap = _vec(ep["position_gap"], L, "gap")
    cross, dot = lv[0] * rv[1] - lv[1] * rv[0], lv[0] * rv[0] + lv[1] * rv[1]
    raw = {"velocity_equal": lv[0].cmp(rv[0]) == 0 and lv[1].cmp(rv[1]) == 0,
           "acceleration_equal": la[0].cmp(ra[0]) == 0 and la[1].cmp(ra[1]) == 0,
           "curvature_equal": lk.cmp(rk) == 0}
    raw["tangent_equal"] = cross.sgn() == 0 and dot.sgn() > 0
    raw["tangent_opposite"] = cross.sgn() == 0 and dot.sgn() < 0
    g0 = gap[0].sgn() == 0 and gap[1].sgn() == 0
    g1 = g0 and raw["tangent_equal"]
    c1 = g0 and raw["velocity_equal"]
    return raw, {"G0": g0, "G1": g1, "C1": c1, "G2": g1 and raw["curvature_equal"],
                 "C2": c1 and raw["acceleration_equal"], "cusp": g0 and raw["tangent_opposite"]}


def s6(profile=P4096):
    d = refs.load("REVISION2_FIXTURE_VALUES.json")
    L = Ledger(profile, "S6")
    bad, n = [], 0
    for name, ep in sorted(list(d["S6_joins"].items()) + list(d["CH1"]["joins"].items())):
        L.begin("Q", n)
        raw, gated = join_flags(ep, L)
        L.commit()
        n += 1
        if raw != ep["raw"] or gated != ep["join"]:
            bad.append(name)
    return {"checks": n, "mismatches": bad, "ledger": L.total()}


def loops(profile=P4096):
    """L0/L1: closure residual = first + second displacement (A); closed iff both components are zero (K)."""
    L = Ledger(profile, "LOOP")
    bad, out = [], {}
    for name, c in refs.load("REVISION2_FIXTURE_VALUES.json")["closures"].items():
        L.begin("Q", 0)
        f, s = _vec(c["first_displacement"], L, "f"), _vec(c["second_displacement"], L, "s")
        res = [f[0] + s[0], f[1] + s[1]]
        closed = res[0].sgn() == 0 and res[1].sgn() == 0
        L.commit()
        out[name] = closed
        if [pr(v) for v in res] != c["closure_residual"] or closed != c["closed"]:
            bad.append(name)
    return {"checks": 2, "mismatches": bad, "ledger": L.total()}


def phi_bad(profile=P4096):
    """Cell B non-monotone control: oriented length B(t) vs piecewise (traversal) length; total polynomial length refused."""
    c = refs.load("QUINTIC_FIXTURE_VALUES.json")["cell_B"]["nonmonotone"]
    L = Ledger(profile, "PHIBAD")
    L.begin("Q", 0)
    S = _vec(c["oriented_S"], L, "S")
    a, b = _vec(c["traversal_first_piece"], L, "a"), _vec(c["traversal_second_piece"], L, "b")
    turn, bad = Q.imp(*c["turn"], L, "turn"), []
    for i, r in enumerate(c["rows"]):
        t = Q.imp(*r["t"], L, "t")
        orient = horner(S, t)
        trav = horner(a, t) if t.cmp(turn) <= 0 else horner(b, t)
        if (pr(orient), pr(trav)) != (r["oriented"], r["traversal"]):
            bad.append(i)
    total = horner(b, Q.imp(1, 1, L, "one"))
    L.commit()
    exp = c["total_polynomial_length_status"]
    return {"checks": len(c["rows"]) + 1, "mismatches": bad + ([] if pr(total) == c["total_length"] else ["total"]),
            "oriented_total": pr(horner(S, Q.imp(1, 1, L, "one"))), "ACCUMULATED_LENGTH": "REFUSED(%s)" % exp, "ledger": L.total()}
