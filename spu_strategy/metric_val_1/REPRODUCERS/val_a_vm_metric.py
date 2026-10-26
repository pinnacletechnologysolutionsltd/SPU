"""Validation A: VM quadrance/spread vs an independent exact oracle in Q(sqrt3). Does not repair anything.
Oracle (derived here, not imported): Q(x)=4*sum(x^2)-(sum x)^2 ; B(x,y)=4*sum(xy)-sum(x)*sum(y) ; spread=1-B^2/(Q(x)Q(y))."""
import argparse, json, random, sys
from fractions import Fraction as F

ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--label", required=True)
a = ap.parse_args(); sys.path.insert(0, a.src + "/software")
import spu_vm as V

def emit(i, ok, d): print("RESULT " + json.dumps({"id": f"A[{a.label}].{i}", "ok": ok, "detail": d}, default=str))

class Q3:  # independent Q(sqrt3) element (x + y*sqrt3)
    def __init__(s, x=0, y=0): s.x, s.y = F(x), F(y)
    def __add__(s, o): return Q3(s.x + o.x, s.y + o.y)
    def __sub__(s, o): return Q3(s.x - o.x, s.y - o.y)
    def __mul__(s, o): return Q3(s.x * o.x + 3 * s.y * o.y, s.x * o.y + s.y * o.x)
    def __eq__(s, o): return s.x == o.x and s.y == o.y
    def iszero(s): return s.x == 0 and s.y == 0
    def __repr__(s): return f"({s.x}+{s.y}r3)"
def fromvm(r): return Q3(r.a, r.b)
def Qf(v): S = sum_(v); return sum_([c * c for c in v]) * Q3(4) - S * S
def sum_(l):
    t = Q3(0)
    for c in l: t = t + c
    return t
def Bf(u, v): return sum_([x * y for x, y in zip(u, v)]) * Q3(4) - sum_(u) * sum_(v)
def vmv(v): return V.QuadrayVector(*[V.RationalSurd(c.x.numerator, c.y.numerator) for c in v])
def mk(t): return [Q3(c[0], c[1]) if isinstance(c, tuple) else Q3(c) for c in t]
def spread_oracle(u, v):
    d = Qf(u) * Qf(v); return d - Bf(u, v) * Bf(u, v), d
def vm_spread(u, v):
    n, d = vmv(u).spread(vmv(v)); return fromvm(n), fromvm(d)
def same_ratio(n1, d1, n2, d2): return (n1 * d2) == (n2 * d1)

# A1/A2: self-spread must be 0 for non-null P; proportional vectors too
selfs = [(1, -1, 0, 0), (1, 0, 0, 0), (2, -1, -1, 0), (0, 1, 1, 0), (3, 1, 0, 0), (1, 1, -1, -1), (5, 0, 0, 0)]
rows = []
for t in selfs:
    u = mk(t); n, d = vm_spread(u, u); no, do = spread_oracle(u, u)
    rows.append({"P": t, "vm_num": repr(n), "vm_den": repr(d), "oracle_num": repr(no), "oracle_den": repr(do), "vm_self_spread_zero": n.iszero()})
emit("self_spread_zero", all(r["vm_self_spread_zero"] for r in rows), rows)
for t in [(1, -1, 0, 0), (1, 0, 0, 0)]:
    u = mk(t); k = [c * Q3(3) for c in u]; n, d = vm_spread(u, k)
    emit(f"proportional_{t}", n.iszero(), {"vm_num": repr(n), "vm_den": repr(d)})
# A3: orthogonal / non-orthogonal vs oracle (cross-multiplied; also compare VM denom to oracle Q*Q)
rng = random.Random(20261021); bad = 0; badden = 0; N = 400; ex = None
for _ in range(N):
    u = mk([tuple(rng.randint(-6, 6) for _ in range(2)) if rng.random() < .3 else rng.randint(-6, 6) for _ in range(4)])
    v = mk([tuple(rng.randint(-6, 6) for _ in range(2)) if rng.random() < .3 else rng.randint(-6, 6) for _ in range(4)])
    if Qf(u).iszero() or Qf(v).iszero(): continue
    n, d = vm_spread(u, v); no, do = spread_oracle(u, v)
    if not d == do: badden += 1
    if not same_ratio(n, d, no, do):
        bad += 1; ex = ex or {"u": [repr(c) for c in u], "v": [repr(c) for c in v], "vm": [repr(n), repr(d)], "oracle": [repr(no), repr(do)]}
emit("random_vs_oracle", bad == 0, {"cases": N, "numerator_mismatch": bad, "denominator_mismatch": badden, "first_counterexample": ex})
ex1 = mk((1, 0, 0, 0)); ex2 = mk((0, 1, 0, 0)); n, d = vm_spread(ex1, ex2); no, do = spread_oracle(ex1, ex2)
emit("tetra_axes_vs_oracle", same_ratio(n, d, no, do), {"vm": [repr(n), repr(d)], "oracle": [repr(no), repr(do)], "oracle_B": repr(Bf(ex1, ex2)), "oracle_Q": repr(Qf(ex1))})
orth = (mk((1, -1, 0, 0)), mk((0, 0, 1, -1)))
emit("orthogonal_pair_B_zero", Bf(*orth).iszero() and vm_spread(*orth)[0].iszero() == spread_oracle(*orth)[0].iszero(),
     {"oracle_B": repr(Bf(*orth)), "vm_spread_num": repr(vm_spread(*orth)[0]), "oracle_spread_num": repr(spread_oracle(*orth)[0])})
# A4: common-coordinate translation invariance (Q and B and spread are invariant in the oracle; test the VM)
bq = bs = 0
for _ in range(200):
    u = mk([rng.randint(-5, 5) for _ in range(4)]); v = mk([rng.randint(-5, 5) for _ in range(4)]); k, m = Q3(rng.randint(-4, 4)), Q3(rng.randint(-4, 4))
    if Qf(u).iszero() or Qf(v).iszero(): continue
    u2 = [c + k for c in u]; v2 = [c + m for c in v]
    if not fromvm(vmv(u2).quadrance()) == fromvm(vmv(u).quadrance()): bq += 1
    n1, d1 = vm_spread(u, v); n2, d2 = vm_spread(u2, v2)
    if not same_ratio(n1, d1, n2, d2): bs += 1
emit("vm_quadrance_translation_invariant", bq == 0, {"violations": bq})
emit("vm_spread_translation_invariant", bs == 0, {"violations": bs, "of": 200})
emit("vm_quadrance_equals_oracle_Q", all(fromvm(vmv(mk(t)).quadrance()) == Qf(mk(t)) for t in selfs), "pairwise quadrance == 4*sum(x^2)-S^2 (no factor 2)")
# A5: zero vector semantics (record; no exception expected?)
z = mk((0, 0, 0, 0)); p = mk((1, -1, 0, 0))
try: n, d = vm_spread(z, p); r = {"returns": [repr(n), repr(d)]}
except Exception as e: r = {"raises": type(e).__name__ + ": " + str(e)}
emit("zero_vector_semantics_recorded", True, r)
k = mk((2, 2, 2, 2))   # non-zero but Q=0 (null along (1,1,1,1))
try: n, d = vm_spread(k, p); r = {"returns": [repr(n), repr(d)], "oracle_Q": repr(Qf(k))}
except Exception as e: r = {"raises": type(e).__name__ + ": " + str(e)}
emit("null_vector_(1,1,1,1)_semantics_recorded", True, r)
