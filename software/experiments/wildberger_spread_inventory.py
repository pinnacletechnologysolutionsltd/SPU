#!/usr/bin/env python3
"""Wildberger first-pass inventory: spread polynomials, Pell traces, Lorentzian velocity addition.

Exploratory, host-only, outside every qualified campaign. Requires SymPy (not a repo dependency):
  python3 -m venv /tmp/v && /tmp/v/bin/pip install sympy && /tmp/v/bin/python <this file>
Every check is an exact symbolic/rational identity; nothing is numeric.
"""
import sys
from sympy import (symbols, Rational as R, sqrt, expand, simplify, cancel, chebyshevt, chebyshevu,
                   Matrix, Poly, Integer, together, rem, reduced)

s, x, u, v, a, b = symbols("s x u v a b")
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def S(n, var=s):
    """Spread polynomial by Wildberger's recurrence S_n = 2(1-2s)S_{n-1} - S_{n-2} + 2s."""
    p, q = Integer(0), var
    if n == 0:
        return p
    for _ in range(n - 1):
        p, q = q, expand(2 * (1 - 2 * var) * q - p + 2 * var)
    return q


# ---- A. spread polynomials (field: Z[s]; S_n has integer coefficients)
check("A1 S_n == (1 - T_n(1-2s))/2, n<=16", all(expand(S(n) - (1 - chebyshevt(n, 1 - 2 * s)) / 2) == 0 for n in range(17)))
check("A2 S_n in Z[s], S_n(0)=0, S_n(1)=n%2", all(all(c.is_integer for c in Poly(S(n), s).all_coeffs()) and S(n).subs(s, 0) == 0
                                                  and S(n).subs(s, 1) == n % 2 for n in range(1, 13)))
check("A3 composition S_m(S_n(s)) == S_mn(s), m,n<=6",
      all(expand(S(m).subs(s, S(n)) - S(m * n)) == 0 for m in range(1, 7) for n in range(1, 7)))
check("A4 S_m o S_n == S_n o S_m (commutative family)", expand(S(3).subs(s, S(5)) - S(5).subs(s, S(3))) == 0)
sa, ca, sb, cb = symbols("sa ca sb cb")
A_, B_ = sa**2, sb**2
sab = (sa * cb + ca * sb) ** 2  # sin^2(alpha+beta)
sdiff = (sa * cb - ca * sb) ** 2
q = lambda X: expand((X - A_ - B_ + 2 * A_ * B_) ** 2 - 4 * A_ * B_ * (1 - A_) * (1 - B_))
red = lambda e: reduced(e, [ca**2 - (1 - sa**2), cb**2 - (1 - sb**2)], ca, cb, sa, sb)[1]
check("A5 spreads of alpha+-beta are the two roots of (x-a-b+2ab)^2=4ab(1-a)(1-b)",
      red(q(sab)) == 0 and red(q(sdiff)) == 0)

# ---- B. Pell / Lucas trace correspondence
eps = 2 + sqrt(3)
def pw(n): return expand(eps**n)
def ab_n(n):
    e = pw(n); return e.coeff(sqrt(3), 0), e.coeff(sqrt(3), 1)
check("B1 eps^n = T_n(2) + U_{n-1}(2) sqrt3, n<=16", all(ab_n(n) == (chebyshevt(n, 2), chebyshevu(n - 1, 2)) for n in range(1, 17)))
check("B2 Pell norm a^2-3b^2 = 1", all(ab_n(n)[0]**2 - 3 * ab_n(n)[1]**2 == 1 for n in range(1, 17)))
check("B3 trace t_n = eps^n+eps^-n = 2a_n obeys V_n: t_n=4t_{n-1}-t_{n-2}",
      all(2 * ab_n(n)[0] == 4 * 2 * ab_n(n - 1)[0] - 2 * ab_n(n - 2)[0] for n in range(2, 17)))
M = Matrix([[2, 3], [1, 2]])
check("B4 tr(M^n) = t_n for M=[[2,3],[1,2]] (det 1)", all((M**n).trace() == 2 * ab_n(n)[0] for n in range(1, 13)))
check("B5 S_n(-1/2) = (1 - a_n)/2 = (2 - t_n)/4", all(S(n).subs(s, R(-1, 2)) == (1 - ab_n(n)[0]) / 2 for n in range(1, 13)))
check("B6 doubling a_2n=2a_n^2-1, b_2n=2a_n b_n  (S_2 = 4s(1-s) in the trace coordinate)",
      all(ab_n(2 * n) == (2 * ab_n(n)[0]**2 - 1, 2 * ab_n(n)[0] * ab_n(n)[1]) for n in range(1, 8)))
check("B7 Pell octave r^8 = (18817,10864) = three doublings of (2,1)", ab_n(8) == (18817, 10864))
check("B8 product-to-sum t_{m+n} = t_m t_n - t_{m-n}",
      all(2 * ab_n(m + n)[0] == 4 * ab_n(m)[0] * ab_n(n)[0] - 2 * ab_n(m - n)[0] for m in range(1, 7) for n in range(1, m + 1)))
check("B9 a_n alone determines b_n only up to sign: b^2=(a^2-1)/3", all(ab_n(n)[1]**2 == (ab_n(n)[0]**2 - 1) / 3 for n in range(1, 13)))
# Q(sqrt5): phi has norm -1 so phi^2 (norm +1, trace 3) is the Chebyshev analogue; Lucas L_n = Dickson D_n(1,-1)
phi = (1 + sqrt(5)) / 2
L = lambda n: expand(phi**n + (-1 / phi)**n).simplify()
check("B10 L_2k = 2 T_k(3/2) and S_k(-1/4) = (1 - L_2k/2)/2", all(simplify(L(2 * k) - 2 * chebyshevt(k, R(3, 2))) == 0
      and S(k).subs(s, R(-1, 4)) == (1 - L(2 * k) / 2) / 2 for k in range(1, 9)))
check("B11 odd Lucas is not 2T_k(3/2) (L_3=4 vs 18): phi has norm -1, so L_n is Dickson D_n(1,-1), not Chebyshev",
      L(3) == 4 and 2 * chebyshevt(3, R(3, 2)) == 18 and all(L(n) == L(n - 1) + L(n - 2) for n in range(2, 12)))

# ---- C. Lorentzian velocity addition (c=1)
oplus = lambda p, r: (p + r) / (1 + p * r)
rho = lambda w: (1 + w) / (1 - w)
check("C1 rho(u+v) = rho(u) rho(v)  (Mobius parameter map diagonalises addition)", cancel(rho(oplus(u, v)) - rho(u) * rho(v)) == 0)
check("C2 Mobius matrix [[1,u],[u,1]]: product has the same form, parameter u+v/(1+uv)",
      cancel(Matrix([[1, u], [u, 1]]) * Matrix([[1, v], [v, 1]]) - (1 + u * v) * Matrix([[1, oplus(u, v)], [oplus(u, v), 1]])) == Matrix.zeros(2))
check("C3 inverse map v=(rho-1)/(rho+1); velocity and rho are rational in each other", cancel((rho(v) - 1) / (rho(v) + 1) - v) == 0)
v0 = sqrt(3) / 3
check("C4 rho = 2+sqrt3 <=> v = 1/sqrt3 (v^2=1/3 rational, v in Q(sqrt3) only)", simplify(rho(v0) - eps) == 0)
vn = v0
okn = True
for n in range(2, 9):
    vn = simplify(oplus(vn, v0))
    a_, b_ = ab_n(n)
    okn &= simplify(vn - (a_ - 1 + b_ * sqrt(3)) / (a_ + 1 + b_ * sqrt(3))) == 0
check("C5 n-fold (+) of 1/sqrt3 = (eps^n-1)/(eps^n+1), n<=8, exact in Q(sqrt3)", okn)
sig = lambda w2: -w2 / (1 - w2)
vv = v
okS = True
for n in range(2, 7):
    vv = cancel(oplus(vv, v))
    Sn = S(n).subs(s, sig(v**2))
    okS &= cancel(vv**2 + Sn / (1 - Sn)) == 0
check("C6 (n-fold velocity sum)^2 = -S_n(sigma)/(1-S_n(sigma)), sigma=-v^2/(1-v^2), n<=6 (generic v)", okS)
uu, ww = symbols("uu ww")
sa_, sb_ = sig(uu**2), sig(ww**2)
quad = lambda X: cancel(together((X - sa_ - sb_ + 2 * sa_ * sb_) ** 2 - 4 * sa_ * sb_ * (1 - sa_) * (1 - sb_)))
check("C7 sigma((u+w)^2),sigma((u-w)^2 via (+)) are the two roots of the SAME spread-combination quadratic",
      quad(sig(oplus(uu, ww)**2)) == 0 and quad(sig(oplus(uu, -ww)**2)) == 0)
# information: v^2 loses direction; one cannot form u(+)w from (u^2,w^2) without choosing a root
check("C8 (u+w)^2 vs (u-w)^2 differ generically -> squared state needs a root choice",
      cancel(oplus(uu, ww)**2 - oplus(uu, -ww)**2) != 0)

# ---- D. checks against the book's own statements (Divine Proportions, 2005 text supplied by the user)
check("D1 book Thm 56/Ex 8.5: S_3=s(3-4s)^2, S_5=s(5-20s+16s^2)^2, S_15=S_3(S_5) factorisation",
      expand(S(3) - s * (3 - 4 * s)**2) == 0 and expand(S(5) - s * (5 - 20 * s + 16 * s**2)**2) == 0 and
      expand(S(15) - s * (3 - 4 * s)**2 * (5 - 20 * s + 16 * s**2)**2 * (1 - 32 * s + 224 * s**2 - 448 * s**3 + 256 * s**4)**2) == 0)
check("D2 book Ex 8.13 S_12 spread-cyclotomic factorisation",
      expand(S(12) - 16 * s * (1 - s) * (3 - 4 * s)**2 * (1 - 2 * s)**2 * (1 - 4 * s)**2 * (1 - 16 * s + 16 * s**2)**2) == 0)
check("D3 book Ex 8.1/Thm 57: {S_{n-1}, s, S_n} spread triple, i.e. (S_{n-1}+S_n-s)^2 = 4 S_{n-1} S_n (1-s)",
      all(expand((S(n - 1) + S(n) - s)**2 - 4 * S(n - 1) * S(n) * (1 - s)) == 0 for n in range(1, 10)))
bk = lambda Vq, X, Y: (X + Y - Vq - Vq * X * Y) ** 2 - 4 * X * Y * (1 - Vq) ** 2   # book (23.11), p.242, as typeset: (1-V)^2
bk_sym = lambda Vq, X, Y: (Vq + X + Y - Vq * X * Y) ** 2 - 4 * (Vq * X + Vq * Y + X * Y - 2 * Vq * X * Y)  # book's symmetric form
Vsq = oplus(u, v) ** 2
check("D4 book (23.11): V=((u+w)/(1+uw))^2, V1=u^2, V2=w^2 satisfies (V1+V2-V-VV1V2)^2 = 4V1V2(1-V)^2", cancel(bk(Vsq, u**2, v**2)) == 0)
check("D5 book symmetric form equals (23.11) as polynomials, and holds on the same data",
      expand(bk(a, b, x) - bk_sym(a, b, x)) == 0 and cancel(bk_sym(Vsq, u**2, v**2)) == 0)
check("D6 book (23.9) Newtonian: (V1+V2-V)^2=4V1V2 for V=(u+w)^2", cancel((u**2 + v**2 - (u + v)**2) ** 2 - 4 * u**2 * v**2) == 0)
sg = lambda w2: -w2 / (1 - w2)
Esig = together((sg(a) - sg(b) - sg(x) + 2 * sg(b) * sg(x)) ** 2 - 4 * sg(b) * sg(x) * (1 - sg(b)) * (1 - sg(x)))
from sympy import numer, denom
check("D7 numerator of my sigma-coordinate spread-combination quadratic == book (23.11) polynomial EXACTLY (a=V, b,x=V1,V2)",
      expand(numer(Esig) - bk(a, b, x)) == 0 and expand(denom(Esig)) == expand(((b - 1) * (x - 1) * (a - 1)) ** 2))

print("\nALL PASS" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
