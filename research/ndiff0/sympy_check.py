"""SymPy cross-check (research oracle only; run with .venv/bin/python -I -B). Not a dependency of anything else."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sympy as sp
from fractions import Fraction as F
from curve import sample_curve
from closure import rotation, scaling, reparam_t2
from field import S3
import phase3

t = sp.symbols("t")
r3 = sp.sqrt(3)
sy = lambda z: sp.Rational(z.p.numerator, z.p.denominator) + sp.Rational(z.q.numerator, z.q.denominator) * r3
poly = lambda cs: sum(sy(c) * t**k for k, c in enumerate(cs))
eq0 = lambda e: sp.simplify(sp.expand(e)) == 0

c = sample_curve()
a, b = poly(c.a), poly(c.b)
xp, yp = sp.expand(a**2 - b**2), sp.expand(2 * a * b)
X = sp.integrate(xp, t) + sy(c.X[0]); Y = sp.integrate(yp, t) + sy(c.Y[0])
assert eq0(X - poly(c.X)) and eq0(Y - poly(c.Y)), "positions"
assert eq0(sp.diff(X, t) - poly(c.xp)) and eq0(sp.diff(Y, t) - poly(c.yp)), "hodograph"
sig = sp.expand(a**2 + b**2)
assert eq0(sp.diff(X, t)**2 + sp.diff(Y, t)**2 - sig**2) and eq0(sig - poly(c.sigma)), "speed"
Q = X**2 + Y**2
assert eq0(sp.diff(Q, t) - 2 * (X * sp.diff(X, t) + Y * sp.diff(Y, t)))
from run import SAMPLES
import cost
n = 0
for t0 in SAMPLES:
    for order in (1, 2):
        for name, fn in cost.STRATEGIES.items():
            o = fn(c, t0, order)
            s0 = sy(t0)
            chk = {"P": (X, Y), "T": (sp.diff(X, t), sp.diff(Y, t)), "Q": (Q,), "dQ": (sp.diff(Q, t),),
                   "speed2": (sp.diff(X, t)**2 + sp.diff(Y, t)**2,)}
            if order == 2:
                chk["P2"] = (sp.diff(X, t, 2), sp.diff(Y, t, 2))
            for k, es in chk.items():
                got = o[k] if isinstance(o[k], tuple) else (o[k],)
                for g, e in zip(got, es):
                    assert eq0(sy(g) - e.subs(t, s0)), (name, k, order, t0)
                    n += 1
print(f"SYMPY {sp.__version__}: positions, hodograph, speed identity, {n} strategy outputs match")

# closure facts: a constant lies in Q(sqrt3) iff its minimal polynomial over Q(sqrt3) has degree 1
K = sp.QQ.algebraic_field(r3)
deg = lambda e: sp.degree(sp.minimal_polynomial(e, t, domain=K), t)  # degree over Q(sqrt3); 1 iff e in Q(sqrt3)
need = {"cos15deg (30deg rot)": sp.cos(sp.pi / 12), "sqrt2 (90deg rot, scale 2)": sp.sqrt(2),
        "3^(1/4) (scale sqrt3)": sp.root(3, 4), "sqrt(2+sqrt3) (scale Pell)": sp.sqrt(2 + r3),
        "sqrt(3) (scale 3: control, IN domain)": sp.sqrt(3), "cos30deg (control, IN domain)": sp.cos(sp.pi / 6)}
for k, e in need.items():
    print(f"  {k:40s} degree over Q(sqrt3) = {deg(e)}  ->", "in Q(sqrt3)" if deg(e) == 1 else "OUTSIDE Q(sqrt3)")
# the generalised forms: hodograph identities symbolically
th = sp.tan(sp.pi / 12)  # 30deg rotation: tan(15deg) = 2 - sqrt3
tt = sp.nsimplify(th); rr = 1 / (1 + tt**2)
A, B = a - tt * b, b + tt * a
cs, sn = r3 / 2, sp.Rational(1, 2)
assert eq0(rr * (A**2 - B**2) - (cs * xp - sn * yp)) and eq0(rr * 2 * A * B - (sn * xp + cs * yp))
print("  30deg rotation: h=1/(1+tan^2(15deg)) with (a-tb, b+ta) reproduces rotated hodograph symbolically; tan15 =", sp.simplify(tt))
two_t = 2 * t
assert eq0(two_t * (a.subs(t, t**2)**2 - b.subs(t, t**2)**2) - sp.diff(X.subs(t, t**2), t))
print("  t->t^2: 2t*hodograph(t^2) == d/dt X(t^2) symbolically")
print("PASS sympy_check")
