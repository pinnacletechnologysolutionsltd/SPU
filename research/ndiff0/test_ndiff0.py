"""Controls for the NDIFF-0 probe. Each detector is shown to accept the good case AND reject a mutant."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
from field import *
from curve import *
from closure import *
import cost, oracle
import eisenstein as Z

c = sample_curve()
t0 = S3(F(1, 4), F(1, 4))
H, R = S3(F(1, 2)), S3(0, F(1, 2))


def agree(curve, a_o, b_o):
    f = oracle.curve_facts(a_o, b_o, oracle.pairs(curve.h), (F(1), F(1)), (F(-1, 2), F(0)), (t0.p, t0.q))
    out = cost.ph_eval(curve, t0, 1)
    return all((out[k].p, out[k].q) == f[k] for k in ("Q", "dQ", "speed2"))


# oracle comparison: accepts good, rejects a perturbed generator
a_o, b_o = oracle.pairs(c.a), oracle.pairs(c.b)
assert agree(c, a_o, b_o)
bad = list(a_o)
bad[0] = (bad[0][0] + F(1, 7), bad[0][1])
assert not agree(c, bad, b_o)
# gate: accepts a synthetic win, rejects a tie and a loss
base = {"rat_mul": 10, "rat_add": 10}
assert cost.gate({"rat_mul": 9, "rat_add": 10}, [base])
assert not cost.gate({"rat_mul": 10, "rat_add": 10}, [base]) and not cost.gate({"rat_mul": 9, "rat_add": 12}, [base])
# sqrt_s3 / psqrt
assert sqrt_s3(S3(7, 4)) is not None and sqrt_s3(R3) is None and sqrt_s3(S3(2, 1)) is None
sq = sqrt_s3(S3(7, 4)); assert sq * sq == S3(7, 4)
assert psqrt(pmul(c.sigma, c.sigma)) is not None and psqrt(padd(pmul(c.sigma, c.sigma), (ONE,))) is None
# closure: good case accepted (60 deg primitive), bad rejected (30 deg), mutated hodograph rejected
r60, (xp, yp) = rotation(c, H, R); assert r60["primitive"] and r60["general"]
r30, _ = rotation(c, R, H); assert not r30["primitive"] and r30["general"] and r30["ph_property"]
assert not hod_matches(c, padd(xp, (ONE,)), yp)
rs, _ = scaling(c, R3); assert rs["ph_property"] and not rs["primitive"] and rs["general"]
rt, g = reparam_t2(c); assert rt["general"] and rt["position_is_X_of_t2"] and rt["h_valuation_odd"] and not rt["regular_at_0"]
# op counts are data independent
cnt = {tuple(sorted(cost.run_counted(cost.ph_eval, c, t, 1)[1].items())) for t in (S3(0), S3(3, 5), S3(F(1, 9), F(-2, 7)))}
assert len(cnt) == 1
# Eisenstein: correct norm matches the Cartesian image, the wrong-sign form does not
pts = [Z.E(a, b) for a in range(-3, 4) for b in range(-3, 4)]
good = lambda u: (u.cart()[0][0] ** 2 + 3 * u.cart()[1][1] ** 2) == u.norm()
assert all(good(u) for u in pts) and not all(u.a ** 2 + u.a * u.b + u.b ** 2 == u.norm() for u in pts)
print("PASS test_ndiff0 (controls accept good cases and reject mutants)")
