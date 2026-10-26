"""Validation D: classify cycle / rotate / hex_project / thirds transforms against exact oracles."""
import argparse, itertools, json, random, sys
from fractions import Fraction as F
ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); a = ap.parse_args(); sys.path.insert(0, a.src + "/software")
import spu_vm as V
def emit(i, ok, d): print("RESULT " + json.dumps({"id": "D." + i, "ok": ok, "detail": d}, default=str))
Q = lambda x: 4 * sum(c * c for c in x) - sum(x) ** 2
def det3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
rng = random.Random(20261021)
# --- cycle(): (a,b,c,d)->(b,c,d,a) as map on the zero-sum 3-lattice; basis e_i - e_4
def vmcycle(t): return [c.a for c in V.QuadrayVector(*[V.RationalSurd(x, 0) for x in t]).cycle().components()]
basis = [(1, 0, 0, -1), (0, 1, 0, -1), (0, 0, 1, -1)]
img = [vmcycle(b) for b in basis]
coords = lambda w: (w[0], w[1], w[2])   # on zero-sum vectors the first three coordinates determine the vector
M = [coords(w) for w in img]
emit("cycle_preserves_Q", all(Q(vmcycle(x)) == Q(x) for x in [[rng.randint(-9, 9) for _ in range(4)] for _ in range(200)]), "pure permutation")
emit("cycle_det_on_zero_sum_lattice", det3(M) == -1, {"det": det3(M), "classification": "improper isometry (rotoreflection S4) if -1; proper rotation if +1"})
# proper 90-degree candidate: -(4-cycle)
emit("neg_cycle_det", det3([[-v for v in r] for r in M]) == 1, {"det_of_negated": det3([[-v for v in r] for r in M])})
# --- rotate(): per-component multiply by (2+sqrt3); compare Q ratio (exact Q(sqrt3))
class Q3:
    def __init__(s, x, y): s.x, s.y = F(x), F(y)
    def __mul__(s, o): return Q3(s.x*o.x+3*s.y*o.y, s.x*o.y+s.y*o.x)
    def __add__(s, o): return Q3(s.x+o.x, s.y+o.y)
    def __sub__(s, o): return Q3(s.x-o.x, s.y-o.y)
    def t(s): return (s.x, s.y)
def Qs(cs):
    S = Q3(0, 0)
    for c in cs: S = S + c
    sq = Q3(0, 0)
    for c in cs: sq = sq + c * c
    return Q3(4, 0) * sq - S * S
ratios = set(); inv_fail = 0
for _ in range(60):
    comps = [(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(4)]
    qv = V.QuadrayVector(*[V.RationalSurd(*c) for c in comps])
    before = Qs([Q3(*c) for c in comps])
    if before.t() == (0, 0): continue
    r = qv.rotate(); after = Qs([Q3(c.a, c.b) for c in r.components()])
    # ratio after/before in Q(sqrt3): solve via multiplication by conjugate
    cj = Q3(before.x, -before.y); den = before * cj; num = after * cj
    ratios.add((num.x / den.x, num.y / den.x))
emit("rotate_is_dilation_not_isometry", ratios == {(F(7), F(4))} , {"observed_Q_ratio_set": sorted(map(str, ratios)), "pell_unit_(2+r3)^2": "7+4r3",
     "doc_claim": "rotate() docstring: 'Quadrance is preserved'", "classification": "similarity/dilation if ratio != 1"})
# --- hex_project(): kernel and restricted-metric behaviour
def hp(t): return V.QuadrayVector(*[V.RationalSurd(x, 0) for x in t]).hex_project()
QH = lambda q, r: q*q + q*r + r*r
kern = [(0, 0, k, 0) for k in (1, 2, 5)] + [(k, k, 0, k) for k in (1, 3)]
emit("hex_project_kernel", all(hp(t) == (0, 0) and Q(t) > 0 for t in kern), {"kernel_examples_map_to_(0,0)_with_Q>0": [(t, Q(t)) for t in kern]})
# B-orthogonal complement of the kernel direction t_C: 4c = S  => ratio Q/Q_H constant?
sub = [t for t in itertools.product(range(-6, 7), repeat=4) if 3*t[2] == t[0]+t[1]+t[3] and hp(t) != (0, 0)]
rat = {F(Q(t), QH(*hp(t))) for t in sub if QH(*hp(t))}
emit("hex_project_metric_on_Bperp_subspace", len(rat) == 1, {"subspace_vectors": len(sub), "Q/QH_ratio_set": sorted(map(str, rat))})
allv = [t for t in itertools.product(range(0, 5), repeat=4) if QH(*hp(t))]
rat_all = {F(Q(t), QH(*hp(t))) for t in allv}
emit("hex_project_not_metric_off_subspace", len(rat_all) > 1, {"distinct_ratios_on_min0_box": len(rat_all)})
# --- thirds: out = (1/3)[[F,H,G],[G,F,H],[H,G,F]] (B,C,D), A fixed; check against VM circulant_rotate*3 and Q-preservation
COEF = {1: (2, 2, -1), 3: (-1, 2, 2), 4: (2, -1, 2)}
def oracle(x, ang):
    f, g, h = COEF[ang]; A, B, C, D = x
    return [F(A), F(f*B+h*C+g*D, 3), F(g*B+f*C+h*D, 3), F(h*B+g*C+f*D, 3)]
for ang, (f, g, h) in COEF.items():
    ok_q = ok_vm = True; nonint = 0
    for _ in range(200):
        x = [rng.randint(-9, 9) for _ in range(4)]; o = oracle(x, ang)
        ok_q &= (Q(o) == Q(x))
        vmres = V.QuadrayVector(*[V.RationalSurd(c, 0) for c in x]).circulant_rotate(V.RationalSurd(f), V.RationalSurd(g), V.RationalSurd(h))
        comps = [c.a for c in vmres.components()]
        ok_vm &= comps[1:] == [3 * v for v in o[1:]]
        nonint += any(v.denominator != 1 for v in o)
    emit(f"thirds_angle{ang}_isometry_of_Q", ok_q, {"Q_preserved_exact": ok_q})
    emit(f"thirds_angle{ang}_vm_matches_oracle_x3", ok_vm, {"note": "VM circulant_rotate returns undivided (x3) values for integer F,G,H", "noninteger_outputs_of_200": nonint})
    # integer condition: outputs integral iff A == 0 mod 3 (check on all small vectors)
    iff = all(all(v.denominator == 1 for v in oracle(x, ang)) == (x[0] % 3 == 0) for x in itertools.product(range(-4, 5), repeat=4) if sum(x) == 0)
    emit(f"thirds_angle{ang}_integral_iff_A_mod3_on_zero_sum", iff, "falsifiable claim from IMG-0A; rounding semantics of RTL div3 handled in val_e (static) -- RTL thirds run is NOT part of this tranche")
