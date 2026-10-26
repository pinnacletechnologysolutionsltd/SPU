"""Validation C: Quadray coordinate conventions. Independent Fraction arithmetic; VM used only for the min=0 normalize contract."""
import argparse, itertools, json, sys
from fractions import Fraction as F
ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); a = ap.parse_args(); sys.path.insert(0, a.src + "/software")
import spu_vm as V
def emit(i, ok, d): print("RESULT " + json.dumps({"id": "C." + i, "ok": ok, "detail": d}, default=str))
Q = lambda x: 4 * sum(c * c for c in x) - sum(x) ** 2

rng = range(0, 6)
hosts = [x for x in itertools.product(rng, repeat=4) if min(x) == 0]
frac = [x for x in hosts if sum(x) % 4]
emit("host_min0_centered_fractional", len(frac) > 0, {"hosts_min0_in_0..5": len(hosts), "centered_rep_fractional": len(frac), "example": frac[0],
     "centered": [str(F(c) - F(sum(frac[0]), 4)) for c in frac[0]], "rule": "integer zero-sum representative exists iff sum % 4 == 0"})
# the iff, checked on a wider box including negatives (translation by integer k changes sum by 4k)
ok = all((sum(x) % 4 == 0) == any(sum(y) == 0 for y in [tuple(c - k for c in x) for k in range(-12, 13)]) for x in itertools.product(range(-3, 4), repeat=4))
emit("zero_sum_rep_iff_sum_mod4", ok, "checked all x in [-3,3]^4 against translations k in [-12,12]")
# Q is translation invariant and equals 4*sum(c^2) for the centered (zero-sum, possibly fractional) representative
ok = True
for x in itertools.product(range(0, 5), repeat=4):
    c = [F(v) - F(sum(x), 4) for v in x]
    ok &= (Q(x) == 4 * sum(v * v for v in c)) and (Q(x) == Q([v + 7 for v in x]))
emit("Q_equals_4sum_centered_squares", ok, "Q(host)=4*sum(centered^2); RTL quadrance on zero-sum ints is 4*sum(c^2) -> same normalization")
# scaled conversion: x4 = 4x - S*(1,1,1,1) is integer zero-sum, Q(x4)=16 Q(x)
ok = all(Q([4 * v - sum(x) for v in x]) == 16 * Q(x) and sum(4 * v - sum(x) for v in x) == 0 for x in itertools.product(range(0, 5), repeat=4))
emit("lossless_conversion_needs_x4_scale", ok, "Q scales by 16 under (4x - S)")
# shells (fixes IMG-0A A3-13 harness defect: exclude Q==0, i.e. multiples of (1,1,1,1))
def shell(vs):
    qs = sorted({Q(v) for v in vs if Q(v) > 0}); m = qs[0]; return m, sum(1 for v in vs if Q(v) == m)
A3 = [v for v in itertools.product(range(-3, 4), repeat=4) if sum(v) == 0]
emit("A3_root_lattice_min_shell", shell(A3) == (8, 12), {"min_Q_count": shell(A3), "expected": (8, 12)})
reps = {tuple(c - min(v) for c in v) for v in itertools.product(range(-3, 4), repeat=4)}
emit("A3star_host_min_shell", shell(sorted(reps)) == (3, 8), {"min_Q_count": shell(sorted(reps)), "expected": (3, 8)})
# VM normalize() contract: min component 0, translation only
vm = V.QuadrayVector(*[V.RationalSurd(c, 0) for c in (3, 5, 4, 7)]).normalize()
emit("vm_normalize_min0", [c.a for c in vm.components()] == [0, 2, 1, 4], [c.a for c in vm.components()])
# surd components: min=0 'canonical' uses rs_min over Q(sqrt3); record, no judgment
v2 = V.QuadrayVector(V.RationalSurd(1, 1), V.RationalSurd(2, -1), V.RationalSurd(0, 1), V.RationalSurd(3, 0)).normalize()
emit("vm_normalize_surd_recorded", True, [(c.a, c.b) for c in v2.components()])
