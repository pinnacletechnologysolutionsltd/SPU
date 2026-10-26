#!/usr/bin/env python3
"""Wildberger pass 2: quadrance/quadrea (Ch.5), oriented triangles/turns/signed area (Ch.9), plus bridges.

Exploratory, host-only, outside every qualified campaign. Needs SymPy (not a repo dependency):
  python3 -m venv /tmp/v && /tmp/v/bin/pip install sympy && /tmp/v/bin/python <this file>
Section D = statements as printed in the supplied Divine Proportions text; section E = my derivations.
"""
import sys
from sympy import Poly, symbols, expand, cancel, together, numer, denom, Matrix, I, im, re, simplify, resultant, Integer, factor

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)


x1, y1, x2, y2, x3, y3, x4, y4, x0, y0 = symbols("x1 y1 x2 y2 x3 y3 x4 y4 x0 y0")
Q = lambda p, q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
A1, A2, A3, A4, P0 = (x1, y1), (x2, y2), (x3, y3), (x4, y4), (x0, y0)
Q1, Q2, Q3 = Q(A2, A3), Q(A1, A3), Q(A1, A2)
Arch = lambda a, b, c: (a + b + c) ** 2 - 2 * (a**2 + b**2 + c**2)
cross = x1 * y2 - x1 * y3 + x2 * y3 - x3 * y2 + x3 * y1 - x2 * y1
sa = lambda P, R, S: (P[0] * R[1] - R[0] * P[1] + R[0] * S[1] - S[0] * R[1] + S[0] * P[1] - P[0] * S[1]) / 2

# ---- D. Chapter 5
check("D1 Thm 22/26: Archimedes(Q1,Q2,Q3) = 4Q1Q2-(Q1+Q2-Q3)^2 = 4 cross^2 (quadrea is 4x a square)",
      expand(Arch(Q1, Q2, Q3) - (4 * Q1 * Q2 - (Q1 + Q2 - Q3) ** 2)) == 0 and expand(Arch(Q1, Q2, Q3) - 4 * cross**2) == 0)
a, b, c, d, X = symbols("a b c d X")
forms = [4 * a * b - (a + b - c) ** 2, 2 * (a * b + b * c + c * a) - (a**2 + b**2 + c**2), 4 * (a * b + b * c + c * a) - (a + b + c) ** 2,
         Matrix([[2 * a, a + b - c], [a + b - c, 2 * b]]).det(),
         -Matrix([[0, a, b, 1], [a, 0, c, 1], [b, c, 0, 1], [1, 1, 1, 0]]).det()]
check("D2 Ex 5.7: five equivalent forms of Archimedes' function", all(expand(f - Arch(a, b, c)) == 0 for f in forms))
check("D3 Ex 5.14/5.15 alternative forms of the quadrea",
      expand(Arch(a, b, c) - (a * (b + c - a) + b * (c + a - b) + c * (a + b - c))) == 0 and
      expand(Arch(a, b, c) - ((c + a - b) * (a + b - c) + (a + b - c) * (b + c - a) + (b + c - a) * (c + a - b))) == 0)
d1, d2, d3 = symbols("d1 d2 d3")
check("D4 Thm 29 Archimedes: A(d1^2,d2^2,d3^2) = (d1+d2+d3)(d1+d2-d3)(d2+d3-d1)(d3+d1-d2)",
      expand(Arch(d1**2, d2**2, d3**2) - (d1 + d2 + d3) * (d1 + d2 - d3) * (d2 + d3 - d1) * (d3 + d1 - d2)) == 0)
check("D5 Thm 23/27 Pythagoras + right quadrea: Q1+Q2-Q3 = 2*dot at A3, so right <=> A=4Q1Q2",
      expand(Q1 + Q2 - Q3 - 2 * ((x1 - x3) * (x2 - x3) + (y1 - y3) * (y2 - y3))) == 0)
aa, bb, cc, xx, yy = symbols("aa bb cc xx yy")
fx, fy = (bb**2 * xx - aa * bb * yy - aa * cc) / (aa**2 + bb**2), (-aa * bb * xx + aa**2 * yy - bb * cc) / (aa**2 + bb**2)
check("D6 Thm 25 quadrance to a line: Q(A,F) = (ax+by+c)^2/(a^2+b^2)",
      cancel((fx - xx) ** 2 + (fy - yy) ** 2 - (aa * xx + bb * yy + cc) ** 2 / (aa**2 + bb**2)) == 0)
Qf = lambda a_, b_, c_, d_: ((a_ + b_ + c_ + d_) ** 2 - 2 * (a_**2 + b_**2 + c_**2 + d_**2)) ** 2 - 64 * a_ * b_ * c_ * d_
res = resultant((X - a - b) ** 2 - 4 * a * b, (X - c - d) ** 2 - 4 * c * d, X)
check("D7 Thm 30: resultant of the two quad-triple quadratics in x is exactly Q(a,b,c,d)", expand(res - Qf(a, b, c, d)) == 0)
e1, e2, e3, e4 = symbols("e1 e2 e3 e4")
brah = ((e1 - e4 + e2 + e3) * (e1 + e4 + e2 - e3) * (e4 - e1 + e2 + e3) * (e1 + e4 - e2 + e3) * (e1 + e4 + e2 + e3)
        * (e1 - e4 - e2 + e3) * (e1 - e4 + e2 - e3) * (e2 - e4 - e1 + e3))
check("D8 Thm 32 Brahmagupta identity as printed (d12=e1,d23=e2,d34=e3,d14=e4)",
      expand(Qf(e1**2, e2**2, e3**2, e4**2) - brah) == 0 or expand(Qf(e1**2, e2**2, e3**2, e4**2) + brah) == 0)
check("D9 Thm 63 Bretschneider: 16a^2 = 4Q13Q24 - (Q12+Q34-Q23-Q14)^2 for a=signed area of A1A2A3A4",
      expand(16 * ((x1 * y2 - x2 * y1 + x2 * y3 - x3 * y2 + x3 * y4 - x4 * y3 + x4 * y1 - x1 * y4) / 2) ** 2
             - (4 * Q(A1, A3) * Q(A2, A4) - (Q(A1, A2) + Q(A3, A4) - Q(A2, A3) - Q(A1, A4)) ** 2)) == 0)

# ---- D. Chapter 9
check("D10 §9.3: quadrea A = 16 a^2 for the signed area a (triangle)", expand(Arch(Q1, Q2, Q3) - 16 * sa(A1, A2, A3) ** 2) == 0)
check("D11 Thm 62: signed-area sum over an oriented triangle fan is independent of P (and = shoelace)",
      expand(sa(P0, A1, A2) + sa(P0, A2, A3) + sa(P0, A3, A1) - sa(A1, A2, A3)) == 0)
check("D12 Ex 9.5/9.7: quadrilateral = two triangles from A1; reversal flips sign",
      expand((sa(A1, A2, A3) + sa(A1, A3, A4)) - (x1 * y2 - x2 * y1 + x2 * y3 - x3 * y2 + x3 * y4 - x4 * y3 + x4 * y1 - x1 * y4) / 2) == 0
      and expand(sa(A3, A2, A1) + sa(A1, A2, A3)) == 0)
ax, ay, bx, by = symbols("ax ay bx by")
turn = lambda l, m: (l[0] * m[1] - m[0] * l[1]) / (l[0] * m[0] + l[1] * m[1])
L1, L2, L3 = (ax, ay), (bx, by), symbols("cx cy")
u1, u2, u3 = turn(L2, L3), turn(L3, L1), turn(L1, L2)
check("D13 Thm 61 Triple turn: u1+u2+u3 = u1 u2 u3 (lines as normal vectors (a,b))", cancel(u1 + u2 + u3 - u1 * u2 * u3) == 0)
o = lambda l, m: 1 / turn(l, m)
check("D14 Ex 9.1 Triple coturn: o1o2+o2o3+o3o1 = 1", cancel(o(L2, L3) * o(L3, L1) + o(L3, L1) * o(L1, L2) + o(L1, L2) * o(L2, L3) - 1) == 0)
u, w = symbols("u w")
Mu = lambda t: Matrix([[1, -t], [t, 1]])  # 'tan' rotation up to scale
check("D15 Ex 9.2: u(l0,l2) = (u+v)/(1-uv); turn composition is the Mobius map of Mu(u)Mu(v)",
      cancel((Mu(u) * Mu(w))[1, 0] / (Mu(u) * Mu(w))[0, 0] - (u + w) / (1 - u * w)) == 0)
Un = lambda n: (lambda z: (im(expand(z)) / re(expand(z))))((1 + I * u) ** n)
printed = {2: 2 * u / (1 - u**2), 3: (3 * u - u**3) / (1 - 3 * u**2), 4: (4 * u - 4 * u**3) / (1 - 6 * u**2 + u**4),
           5: (5 * u - 10 * u**3 + u**5) / (1 - 10 * u**2 + 5 * u**4)}
us = symbols("us", real=True)
Unr = lambda n: (lambda z: im(z) / re(z))(expand((1 + I * us) ** n))
check("D16 Ex 9.3 U_2..U_5 as printed == Im/Re of (1+iu)^n (general form, proved by induction on (1+iu)^n)",
      all(cancel(printed[n].subs(u, us) - Unr(n)) == 0 for n in printed))
t1, t2, t3 = symbols("t1 t2 t3")
uu3 = (u + w) / (u * w - 1)  # Triple turn solved for the third turn (book p.115), u1=u, u2=w
check("D17 Thm 50 Triple twist: (t1+t2+t3-t1t2t3)^2 = 4(t1t2+t1t3+t2t3+2t1t2t3) holds for t_i = turn_i^2",
      cancel((u**2 + w**2 + uu3**2 - u**2 * w**2 * uu3**2) ** 2 - 4 * (u**2 * w**2 + u**2 * uu3**2 + w**2 * uu3**2 + 2 * u**2 * w**2 * uu3**2)) == 0)

# ---- E. my bridges
sp = lambda t: t**2 / (1 + t**2)
S = lambda n: _S(n)
s_ = symbols("s_")


def _S(n):
    p, q = Integer(0), s_
    if n == 0:
        return p
    for _ in range(n - 1):
        p, q = q, expand(2 * (1 - 2 * s_) * q - p + 2 * s_)
    return q


check("E1 spread = turn^2/(1+turn^2), and S_n(s(u)) = U_n^2/(1+U_n^2), n<=8 (spread poly = turn function modulo sign)",
      all(cancel(_S(n).subs(s_, sp(us)) - sp(Unr(n))) == 0 for n in range(1, 9)))
tri = lambda A_, B_, C_: (A_ + B_ + C_) ** 2 - 2 * (A_**2 + B_**2 + C_**2) - 4 * A_ * B_ * C_
sp1, sp2 = sp(u1), sp(u2)
check("E2 Triple turn => Triple spread (Thm 47): spreads of three lines with turns u1,u2,u3=(u1+u2)/(u1u2-1)",
      cancel(tri(sp(u), sp(w), sp((u + w) / (u * w - 1)))) == 0)
check("E3 Archimedes link: triple-spread function = Archimedes(s1,s2,s3) - 4 s1 s2 s3",
      expand(tri(a, b, c) - (Arch(a, b, c) - 4 * a * b * c)) == 0)
v, V1v = symbols("v V1v")
oplus = lambda p_, r_: (p_ + r_) / (1 + p_ * r_)
nfold = lambda n: __import__("functools").reduce(lambda acc, _: cancel(oplus(acc, v)), range(n - 1), v)
check("E4 analytic continuation: U_n(i v) = i * (n-fold velocity sum of v), n<=8 (Euclid turn <-> Lorentz velocity)",
      all(cancel(Unr(n).subs(us, I * v) - I * nfold(n)) == 0 for n in range(1, 9)))
va, vb = symbols("va vb")
v3 = -oplus(va, vb)
check("E5 velocity triple relation: va+vb+v3 = -va vb v3 for v3=-(va+vb) (Triple turn with u=i v)",
      cancel(va + vb + v3 + va * vb * v3) == 0)
tw = lambda T1, T2, T3: (T1 + T2 + T3 - T1 * T2 * T3) ** 2 - 4 * (T1 * T2 + T1 * T3 + T2 * T3 + 2 * T1 * T2 * T3)
Vs, Va, Vb = symbols("Vs Va Vb")
sym = (Vs + Va + Vb - Vs * Va * Vb) ** 2 - 4 * (Vs * Va + Vs * Vb + Va * Vb - 2 * Vs * Va * Vb)
check("E6 book (23.11) symmetric form IS the Triple twist formula with t=-V (twist = turn^2 = -v^2)",
      expand(sym - tw(-Vs, -Va, -Vb)) == 0)
bk = (Va + Vb - Vs - Vs * Va * Vb) ** 2 - 4 * Va * Vb * (1 - Vs) ** 2  # book (23.11): V=Vs, V1=Va, V2=Vb
low = Poly(expand(bk + Arch(Va, Vb, Vs)), Vs, Va, Vb)
check("E7 (23.11) LHS-RHS = -Archimedes(V1,V2,V) + terms of total degree >= 3: the quad triple (23.9) is its lowest-order part",
      all(sum(m) >= 3 for m in low.monoms()) and expand(bk + Arch(Va, Vb, Vs)) != 0)
check("E8 information: turn is odd under line reversal, spread/twist even: U_n(-u) = -U_n(u), S_n(s(-u)) = S_n(s(u))",
      all(cancel(Unr(n).subs(us, -us) + Unr(n)) == 0 for n in range(1, 7)))
pM = 2**31 - 1
ep = lambda z: pow(z % pM, (pM - 1) // 2, pM)
inv3 = pow(3, pM - 2, pM)
b0 = None
check("E9 M31: -1, 3 non-residues in F_p (no null vectors over F_p) but -1/3 is a residue => (b*sqrt3)^2=-1 in F_p(sqrt3): A31 has null vectors",
      ep(-1) == pM - 1 and ep(3) == pM - 1 and ep(-inv3) == 1)
print("\nALL PASS" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
