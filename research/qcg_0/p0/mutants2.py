"""Mutant suite X-13..X-24 (contract §8)."""
import arms_a, classes, conform, campaign, gen, refs, test_lu
from account import Ledger
from events import P4096
from ledger import Q
from mutkit import a_bad, killed, patched
import poly


def x13():
    ot = poly.tshift

    def swapped(c, t):                                               # mis-valued: inner loop ascending
        c = list(c)
        d = len(c) - 1
        for j in range(0, d):
            for i in range(j, d):
                c[i] = c[i] + t * c[i + 1]
        return c

    def extra(c, t):                                                 # miscounted: one uncounted-by-contract extra operation
        r = ot(c, t)
        r[0] + r[0]
        return r
    with patched(poly, "tshift", swapped):
        a = a_bad(arms_a.TS)["mismatches"] > 0
    with patched(poly, "tshift", extra):
        b = killed(test_lu.lu_dc_ts)
    return a and b, "LU-TS, LU-DC and EQ-3"


def x14():
    return classes.jet_exact(3, 3)["code"] == "APPROX_NOT_EXACT" and classes.jet_exact(4, 3)["status"] == "OK", "PH3 position at order 2"


def x15():
    ok = conform.w31_cell_a() == []
    with patched(Ledger, "check", lambda self, v, kind, sub: None):          # wrap/truncate instead of refusal
        bad = conform.w31_cell_a() != []
    return ok and bad, "certified W31 Cell A first refusals (sequential and Cell B tables pending)"


def x16():
    import arms
    ok = all(conform.refusal_atomic(c) for c in (arms_a.Horner, arms_a.PH, arms_a.C2))
    orig = arms.Arm.request

    def leaky(self, qid, t, req="BUNDLE"):                               # partial mutation of committed state on a refusal
        r = orig(self, qid, t, req)
        if r["status"] == "REFUSED":
            k = next(iter(self.state))
            v = self.state[k]
            self.state[k] = [x for x in v] + [v[0]] if isinstance(v, list) else v
        return r
    with patched(arms.Arm, "request", leaky):
        bad = not conform.refusal_atomic(arms_a.PH)
    return ok and bad, "state hash, fresh-run equality and identical repeat after a W31 refusal"


def x17():
    c = refs.load("QUINTIC_FIXTURE_VALUES.json")["controls"]["harmonic_order4"]
    return classes.operator_exact(c["forward_backward_residual_multiplier"])["code"] == "APPROX_NOT_EXACT", "harmonic operator control"


def x18():
    g = gen.make(refs.load("P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json")["cases"]["PH3_ns_h_form"]["polynomials"], Ledger(P4096, "X18"))
    t = Q.imp(0, 1, g.L, "t")
    d, tg, ck = g.request("DIRECTION", t), g.request("TANGENT", t), g.request("CURVATURE", t)
    return (d["status"] == "OK" and [x.pair() for x in d["outputs"]] == [[1, 1], [0, 1]]
            and tg["code"] == ck["code"] == "NONREGULAR"), "phi_ns at t = 0"


def x19():
    rows, _ = campaign.cell_a(P4096)
    byn = {r["arm"]: r for r in rows}
    same = all(byn["C1"][k] == byn["B-PH"][k] for k in ("P", "Q", "peaks", "attempt"))
    bump = dict(byn["C1"], Q=dict(byn["C1"]["Q"], M=byn["C1"]["Q"]["M"] + 1))
    return same and any(bump[k] != byn["B-PH"][k] for k in ("P", "Q")), "EQ-1"


def x20():
    rows, _ = campaign.cell_a(P4096)
    fd = next(r for r in rows if r["arm"] == "B-FD")
    return all(s == "NOT_APPLICABLE" for s in fd["statuses"]) and fd["Q"]["M"] == 0, "Cell A: FD status"


def x21():
    a = arms_a.Horner(P4096, refs.source("PH5"))
    a.prepare()
    a.state["sg"][2] = Q(3, 1, a.L)                                      # perturbed cache, generator unchanged
    out = a.request(0, (1, 2))["outputs"]["values"]
    from fractions import Fraction as F
    xp, yp, s2 = (F(*out[2]), F(*out[3]), F(*out[4]))
    return xp * xp + yp * yp != s2, "oracle-side identity x'^2 + y'^2 = sigma^2"


def x22():
    return conform.reversal_twice(), "symbolic: reversal twice restores the hodograph"


def x23():
    a = classes.retiming_class([(0, 1), (1, 1)], [(1, 1), (1, 1)])            # phi = t/(1+t)
    b = classes.retiming_class([(0, 1), (0, 1), (1, 1)], None, "primitive")   # phi = t^2, primitive form
    return a["code"] == "OUT_OF_DOMAIN" and b["code"] == "NOT_PRIMITIVE_RETIMING", "non-polynomial and non-primitive retiming"


def x24():
    bad = conform.controls_e1()
    return bad == [], "E1a (C4) and E1b (3-4-5) controls"


MUTANTS2 = {"X-13": x13, "X-14": x14, "X-15": x15, "X-16": x16, "X-17": x17, "X-18": x18, "X-19": x19, "X-20": x20,
            "X-21": x21, "X-22": x22, "X-23": x23, "X-24": x24}
