"""Mutant suite X-1..X-12 (contract §8). Each entry returns (killed, detector). Code-level mutants patch the real implementation."""
from fractions import Fraction as F
import arms_a, arms_seq, conform, campaign, gen, joins, o1, poly, s4, refs, test_lu
from account import Ledger
from events import P4096
from ledger import Q, lit
from mutkit import a_bad, killed, patched, seq_bad


def x1():
    orig = Q.twice
    with patched(Q, "twice", lambda self: self):
        dropped = a_bad(arms_a.PH)["mismatches"]
    with patched(Q, "twice", lambda self: orig(orig(self))):
        doubled = a_bad(arms_a.PH)["mismatches"]
    return dropped > 0 and doubled > 0, "EQ-3 Cell A, N_kappa index 7"


def x2():
    orig = gen.Gen._req
    with patched(gen.Gen, "_req", lambda self, k, t: orig(self, "SIGNED_RATE" if k == "SPEED" else k, t)):
        speed = len(s4.s4()["mismatches"])
    with patched(gen.Gen, "_req", lambda self, k, t: orig(self, "DIRECTION" if k == "TANGENT" else k, t)):
        tang = len(s4.s4()["mismatches"])
    return speed > 0 and tang > 0, "P-1 reversal rows (h = -1) vs primitive reversal rows"


def x3():
    s, phi = refs.source("PH3"), refs.phi()["phi"]
    no_dphi = 0
    for t, vals in refs.cell_b_ref():                                  # omit phi': psi' = dx(f), no chain-rule factor
        p, f = o1.derive(o1.fr(s["U"]), o1.fr(s["V"])), o1.fr(phi)
        c = o1.comp(p["dx"], f)
        no_dphi += o1.ev(c, F(*t)) != F(*vals[2])
    case = refs.load("P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json")["cases"]["PH3h_sq_h_form"]
    L = Ledger(P4096, "X3")
    pol = dict(case["polynomials"])
    V = o1.fr(pol["V"])
    pol["h"] = [[x.numerator, x.denominator] for x in o1.der(V)]       # omit h o phi: h = phi' only
    g = gen.make(pol, L)
    omit_h = sum(g.request("POSITION", Q.imp(*r["parameter"], L, "t"), i)["outputs"][0].pair() != r["position"][0]
                 for i, r in enumerate(case["dyadic_S4_rows"]))
    return no_dphi > 0 and omit_h > 0, "Cell B rows (phi'); P-1 nonconstant-h rows"


def x4():
    d = joins.phi_bad()
    return d["oriented_total"] != [8, 3] and d["mismatches"] == [], "phi_bad: oriented total 0, piecewise total 8/3"


def x5():
    L = Ledger(P4096, "X5")
    g = gen.make({"U": [[1, 1]], "V": [[0, 1], [1, 1]], "h": [[1, 1], [-2, 1]], "x": [[0, 1]], "y": [[0, 1]]}, L)
    r = g.request("ACCUMULATED_LENGTH", Q.imp(1, 1, L, "t"))
    return r["status"] == "REFUSED" and r["code"] == "OUT_OF_DOMAIN", "mixed-sign h: single polynomial length refused"


def x6():
    d = refs.load("REVISION2_FIXTURE_VALUES.json")["S6_joins"]
    diff = [n for n in ("b7", "b9") if d[n]["raw"]["curvature_equal"] != d[n]["join"]["G2"]
            or d[n]["raw"]["velocity_equal"] != d[n]["join"]["C1"]]
    return len(diff) == 2 and joins.s6()["mismatches"] == [], "b7, b9: raw equality differs from the gated join"


def x7():
    orig = Q.twice
    with patched(Q, "twice", lambda self: (self.L.__setattr__("c", dict(self.L.c, M=self.L.c["M"] + 1)) or orig(self))):
        a = killed(test_lu.lu_s_val_d_g)
    om = Q.__mul__

    def valmul(self, o):                                              # value-based: a multiplier equal to 1/2 is a shift
        return self.half() if (o.n, o.d) == (1, 2) else om(self, o)
    with patched(Q, "__mul__", valmul):
        b = killed(test_lu.lu_s_val_d_g)
    return a and b, "LU-S, LU-VAL"


def x8():
    def skip(c, t):
        acc = c[-1]
        for i in range(len(c) - 2, -1, -1):
            acc = acc if c[i].n == 0 else acc * t + c[i]
        return acc
    with patched(poly, "horner", skip):
        return killed(test_lu.lu_h), "LU-H0"


def x9():
    def probe():
        L = Ledger(P4096, "T")
        L.begin("Q", 0)
        lit(3, L) * lit(5, L)
        return L.c["G_calls"] == 1
    on = Q._norm

    def skipgcd(self, n, d):
        r = on(self, n, d)
        if r.d == 1:
            self.L.c["G_calls"] -= 1
        return r
    with patched(Q, "_norm", skipgcd):
        dead = killed(probe)
    return dead and probe(), "LU-G: 3*5 = 15"


def x10():
    rows, _ = campaign.cell_a(P4096)
    zero = [dict(r, P={k: 0 for k in r["P"]}) for r in rows]
    one = [dict(r, P=r["P"] if r["arm"] == "B-Horner" else {k: 0 for k in r["P"]}) for r in rows]
    return conform.prep_targets(rows) == [] and conform.prep_targets(zero) != [] and conform.prep_targets(one) != [], "P-phase targets"


def x11():
    rows, _ = campaign.cell_a(P4096)
    ot = Q.twice
    with patched(Q, "twice", lambda self: (self.L.__setattr__("c", dict(self.L.c, D=self.L.c["D"] + 1)) or ot(self))):
        bad = conform.q_division_free(campaign.cell_a(P4096)[0])
    return conform.q_division_free(rows) == [] and bad != [], "Q-phase D = 0 for every arm"


def x12():
    of = poly.fdinit
    with patched(poly, "fdinit", lambda c, d: of(c, lit(2 * d.n, d.L, d.d))):
        bad = seq_bad(arms_seq.SeqF)
    return bad > 0, "sequential EQ-3 on the certified rows (cost-identical wrong grid)"


MUTANTS = {"X-1": x1, "X-2": x2, "X-3": x3, "X-4": x4, "X-5": x5, "X-6": x6, "X-7": x7, "X-8": x8, "X-9": x9, "X-10": x10,
           "X-11": x11, "X-12": x12}
