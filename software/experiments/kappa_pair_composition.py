#!/usr/bin/env python3
"""One pair-composition law (a,b)o(c,d) = (ac + k*bd, ad + bc) for Euclid (k=-1), Pell (k=3), surd5 (k=5).

Exploratory, host-only. Python models are written from reading the RTL (spu_cross_rotor.v, surd_cpu_products.v,
rational_surd5_mul.v); the RTL itself is NOT simulated here. SymPy section optional (generic-k identities).
"""
import random
import sys
from fractions import Fraction as F

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)


def compose(k, z, w):
    (a, b), (c, d) = z, w
    return (a * c + k * b * d, a * d + b * c)


def s(x, bits):
    x &= (1 << bits) - 1
    return x - (1 << bits) if x >> (bits - 1) else x


rng = random.Random(20261023)

# ---- generic-k identities (SymPy)
try:
    import sympy as sp
    k, a, b, c, d, e, f, x, y = sp.symbols("k a b c d e f x y")
    R = lambda p, q: sp.Matrix([[p, k * q], [q, p]])
    zc = compose(k, (a, b), (c, d))
    check("K1 matrix R(a,b)R(c,d) = R((a,b)o(c,d)) for generic k", sp.expand(R(a, b) * R(c, d) - R(*zc)) == sp.zeros(2))
    N = lambda p, q: p**2 - k * q**2
    check("K2 norm N=a^2-k b^2 is multiplicative, N = det R", sp.expand(N(*zc) - N(a, b) * N(c, d)) == 0 and sp.expand(R(a, b).det() - N(a, b)) == 0)
    v = R(a, b) * sp.Matrix([x, y])
    check("K3 R preserves the form x^2-k y^2 up to the factor N(a,b)  (exact when N=1)", sp.expand(v[0]**2 - k * v[1]**2 - N(a, b) * (x**2 - k * y**2)) == 0)
    check("K4 composition is commutative and associative",
          sp.expand(sp.Matrix(compose(k, (a, b), (c, d))) - sp.Matrix(compose(k, (c, d), (a, b)))) == sp.zeros(2, 1) and
          sp.expand(sp.Matrix(compose(k, compose(k, (a, b), (c, d)), (e, f))) - sp.Matrix(compose(k, (a, b), compose(k, (c, d), (e, f))))) == sp.zeros(2, 1))
    u, w = sp.symbols("u w")
    ratio = sp.cancel(compose(k, (1, u), (1, w))[1] / compose(k, (1, u), (1, w))[0])
    check("K5 ratio law u=b/a: u(z o z') = (u+u')/(1+k u u')  [k=-1: book Ex 9.2 turn; k=3: velocity addition with c^2=1/3]",
          sp.simplify(ratio - (u + w) / (1 + k * u * w)) == 0)
    vel = lambda uu, ww: (uu + ww) / (1 + uu * ww)  # book (23.10), c=1
    check("K6 for k>0 put V=sqrt(k) u: law becomes (V+V')/(1+V V') = Lorentzian addition (c=1); light speed is u=1/sqrt(k)",
          sp.simplify(((ratio * sp.sqrt(k)).subs({u: u / sp.sqrt(k), w: w / sp.sqrt(k)})) - vel(u, w)) == 0)
except ImportError:
    print("(SymPy absent: generic-k identities skipped)")

# ---- RTL models vs the generic law
def cross_rotor(A, B, Ra, Rb):  # spu_cross_rotor.v: 4 mults, 3*bb as (x<<1)+x, bits [43:12] of the 64-bit sums
    nA = s(A * Ra + 3 * B * Rb, 64)
    nB = s(A * Rb + B * Ra, 64)
    return s((nA >> 12), 32), s((nB >> 12), 32)


ok = True
for _ in range(20000):
    A, B, Ra, Rb = (s(rng.getrandbits(32), 32) for _ in range(4))
    nA, nB = compose(3, (A, B), (Ra, Rb))
    ok &= cross_rotor(A, B, Ra, Rb) == (s(s(nA, 64) >> 12, 32), s(s(nB, 64) >> 12, 32))
check("R1 spu_cross_rotor model == generic law k=3 followed by the [43:12] bit-slice (random 32-bit inputs, incl. wraparound)", ok)

eps, orbit = (2, 1), [(1, 0)]
for _ in range(7):
    orbit.append(compose(3, orbit[-1], eps))
ok = all(cross_rotor(4096 * i, 4096 * j, 4096 * p, 4096 * q) == (4096 * compose(3, (i, j), (p, q))[0], 4096 * compose(3, (i, j), (p, q))[1])
         for (i, j) in [(1, 0), (0, 1), (5, -2)] for (p, q) in orbit)
check("R2 Q12 Pell steps 0-7: slice is exact when operands are integer multiples of 4096 (orbit r^0..r^7)", ok)


def products_unaligned(av, bv, cv, ev):  # surd_cpu_products.v, aligned=0: z0=a*c, z1=b*e, z2=a*e, z3=b*c ; raw_a = z0 + (z1<<1) + z1
    def corrected(x, y):  # unsigned 64x64 product corrected to signed, as in the RTL (sign_y = !aligned = 1)
        t = x * y
        if x >> 63:
            t -= y << 64
        if y >> 63:
            t -= x << 64
        return s(t, 128)
    u = lambda v: v & (2**64 - 1)
    z0, z1, z2, z3 = (corrected(u(av), u(cv)), corrected(u(bv), u(ev)), corrected(u(av), u(ev)), corrected(u(bv), u(cv)))
    return z0 + (z1 << 1) + z1, z2 + z3


ok = True
for _ in range(5000):
    av, bv, cv, ev = (s(rng.getrandbits(64), 64) for _ in range(4))
    ok &= products_unaligned(av, bv, cv, ev) == compose(3, (av, bv), (cv, ev))
check("R3 surd_cpu_products unaligned path == exact generic law k=3 on full 64-bit signed operands (130-bit result, no wrap)", ok)


def surd5(a, b):  # rational_surd5_mul.v: k=5 via q1q2*5, 32-bit saturating outputs
    pv, qv = compose(5, a, b)
    sat = lambda t: max(-2**31, min(2**31 - 1, t))
    return sat(pv), sat(qv)


ok_small = all(surd5((x1, y1), (x2, y2)) == compose(5, (x1, y1), (x2, y2))
               for x1, y1, x2, y2 in [tuple(rng.randint(-3000, 3000) for _ in range(4)) for _ in range(2000)])
ok_clamp = surd5((32767, 32767), (32767, 32767))[0] == 2**31 - 1 and surd5((32767, 32767), (32767, 32767))[0] != compose(5, (32767, 32767), (32767, 32767))[0]
check("R4 rational_surd5_mul model == generic law k=5 in range; saturates (not wraps, not widens) out of range", ok_small and ok_clamp)
big = 2**30
ex = compose(3, (big, 0), (big, 0))[0]
check("R5 one law, three overflow policies: for (2^30,0)^2, cross_rotor wraps to a wrong 32-bit slice, surd_cpu_products stays exact, surd5 saturates",
      cross_rotor(big, 0, big, 0)[0] != ex >> 12 and products_unaligned(big, 0, big, 0)[0] == ex and surd5((32767, 32767), (32767, 32767))[0] == 2**31 - 1)

# ---- what is genuinely different between k=-1 and k=3
solutions = [(a_, b_) for b_ in range(0, 4000) for a_ in [int((1 + 3 * b_ * b_) ** 0.5 + 0.5)] if a_ * a_ - 3 * b_ * b_ == 1]
pw, zz = [(1, 0)], (1, 0)
for _ in range(12):
    zz = compose(3, zz, (2, 1))
    pw.append(zz)
check("D1 integer solutions of a^2-3b^2=1 with b<4000 are exactly (2+sqrt3)^n: ONE generator (discrete, closed integer rotor group)",
      solutions == [p for p in pw if p[1] < 4000] and len(solutions) == len([p for p in pw if p[1] < 4000]))
check("D2 Euclid k=-1: the only integer pairs with N=1 are the 4 Gaussian units, so exact general rotations need N!=1 (scale) or rational pairs",
      sorted((a_, b_) for a_ in range(-50, 51) for b_ in range(-50, 51) if a_ * a_ + b_ * b_ == 1) == [(-1, 0), (0, -1), (0, 1), (1, 0)])
z = (3, 4)
nz = [(1, 0)]
for _ in range(6):
    nz.append(compose(-1, nz[-1], z))
check("D3 Euclid exact composition by a (3,4,5) turn carries norm 25^n (scale growth; normalising needs division): norms " + str([a_ * a_ + b_ * b_ for a_, b_ in nz[:4]]),
      all(a_ * a_ + b_ * b_ == 25**i for i, (a_, b_) in enumerate(nz)))
check("D4 Pell closure: N(eps^n)=1 for all n (no scale to track)", all(p[0]**2 - 3 * p[1]**2 == 1 for p in pw))
pM = 2**31 - 1
ep = lambda t: pow(t % pM, (pM - 1) // 2, pM)
check("D5 over F_p (p=2^31-1): -1 and 3 are non-residues, so a^2+b^2 and a^2-3b^2 are anisotropic for (a,b) in F_p^2\\{0} (both k=-1 and k=3)",
      ep(-1) == pM - 1 and ep(3) == pM - 1)
check("D6 ratio u=b/a of eps^n stays below the 'light speed' 1/sqrt3 (3u^2<1 since N=1), approaching it", all(F(3) * F(p[1], p[0]) ** 2 < 1 for p in pw if p[0]))
sm = lambda x, y: compose(3, x, y)  # Q(sqrt3) multiplication on (p,q)=p+q*sqrt3 (Fractions)
sa_ = lambda x, y: (x[0] + y[0], x[1] + y[1])
sn = lambda x, y: (x[0] - y[0], x[1] - y[1])
cplx = lambda z, w: (sn(sm(z[0], w[0]), sm(z[1], w[1])), sa_(sm(z[0], w[1]), sm(z[1], w[0])))  # k=-1 law over Q(sqrt3)
r30, acc = ((F(0), F(1, 2)), (F(1, 2), F(0))), ((F(1), F(0)), (F(0), F(0)))
cyc = [acc]
for _ in range(12):
    acc = cplx(acc, r30)
    cyc.append(acc)
check("D7 Euclid over the SPU field: 30-degree rotor (sqrt3/2, 1/2) is an exact norm-1 pair in Q(sqrt3)^2 and its 12th power is the identity "
      "(costs 4 surd products = 16 integer products per composition, vs 4 for a Pell pair)",
      cyc[12] == ((F(1), F(0)), (F(0), F(0))) and cyc[6] == ((F(-1), F(0)), (F(0), F(0))))
print("\nALL PASS" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
