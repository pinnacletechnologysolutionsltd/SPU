#!/usr/bin/env python3
"""Icosahedral rotation group A5 in the quadray basis — derivation + oracle.

Constructive derivation (no literature matrices, no floating point):
  1. Exact Q(phi) arithmetic: a + b*phi with a,b rational, phi^2 = phi + 1.
  2. Icosahedron vertices: the 12 cyclic permutations of (0, +-1, +-phi).
     This orientation shares exactly the ROTC catalog's A4 subgroup
     (coordinate 3-cycles + 180-degree coordinate-axis flips).
  3. A rotation is determined by the image of a flag (vertex, adjacent
     vertex): R = [w1 w2 w1xw2] [v1 v2 v1xv2]^-1. The 12*5 flag images
     yield all 60 rotations; closure to exactly 60 is then a checked
     theorem, not an assumption.
  4. Convert to quadray BCD 3x3 via M = E^-1 R E, the same embedding
     verified bit-exact against the RTL for ROTC angles 0-35.

Machine-checked findings (2026-07-10):
  - Quadray entries lie in (1/2)Z[phi], NOT Z[phi]: the Cartesian halves
    survive the quadray basis. Doubled matrices N = 2M have entries only
    in {0, +-1, +-2, +-phi, +-phi^-1, +-sqrt5} — PSCALE/add-chain
    material, no general Z[phi] multiply needed.
  - The /2 is fallible on raw integer inputs (mod-2 kernel is 16/64
    residue classes over F4^3, uniform across all 48 new rotations).
  - DOUBLING THEOREM: because A5 is finite and composition-closed with
    uniform denominator 2 (N_a N_b = 2 N_ab identically), doubling the
    input ONCE at load time makes every step of every A5 chain exact —
    the pre-division sums are always even even when intermediate vectors
    are odd. This is the opposite of the thirds /3 precondition, which
    does not compose (ROTC paper section 5) because the thirds catalog
    is not composition-closed.
  - Galois conjugation phi -> 1-phi maps this A5 onto the dual-orientation
    icosahedron's A5 (sharing exactly A4); PCHIRAL bridges the two.
"""
import random
from fractions import Fraction as Fr
from itertools import product


class Qp:
    """a + b*phi with a,b Fraction; phi^2 = phi + 1."""
    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a = Fr(a)
        self.b = Fr(b)

    def __add__(s, o): return Qp(s.a + o.a, s.b + o.b)
    def __sub__(s, o): return Qp(s.a - o.a, s.b - o.b)
    def __neg__(s):    return Qp(-s.a, -s.b)

    def __mul__(s, o):
        return Qp(s.a * o.a + s.b * o.b, s.a * o.b + s.b * o.a + s.b * o.b)

    def conj(s):       return Qp(s.a + s.b, -s.b)            # phi -> 1 - phi
    def norm(s):       return s.a * s.a + s.a * s.b - s.b * s.b

    def inv(s):
        n = s.norm()
        c = s.conj()
        return Qp(c.a / n, c.b / n)

    def __truediv__(s, o): return s * o.inv()
    def __eq__(s, o):  return s.a == o.a and s.b == o.b
    def __hash__(s):   return hash((s.a, s.b))
    def is_zero(s):    return s.a == 0 and s.b == 0

    def __repr__(s):
        if s.b == 0:
            return str(s.a)
        if s.a == 0:
            return f"{s.b}phi" if s.b != 1 else "phi"
        return f"{s.a}{'+' if s.b > 0 else ''}{s.b}phi"


ZERO, ONE, PHI = Qp(0), Qp(1), Qp(0, 1)


def vec_sub(u, v): return tuple(x - y for x, y in zip(u, v))
def dot(u, v):     return sum((x * y for x, y in zip(u, v)), ZERO)


def cross(u, v):
    return (u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0])


def mmul(X, Y):
    return tuple(tuple(sum((X[i][k] * Y[k][j] for k in range(3)), ZERO)
                       for j in range(3)) for i in range(3))


def mvec(X, v):
    return tuple(sum((X[i][k] * v[k] for k in range(3)), ZERO)
                 for i in range(3))


def mT(X):
    return tuple(zip(*X))


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def inv3(m):
    d = det3(m)
    cof = [[None] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            s = [[m[r][c] for c in range(3) if c != j]
                 for r in range(3) if r != i]
            v = s[0][0] * s[1][1] - s[0][1] * s[1][0]
            cof[i][j] = v if (i + j) % 2 == 0 else -v
    return tuple(tuple(cof[j][i] / d for j in range(3)) for i in range(3))


I3 = ((ONE, ZERO, ZERO), (ZERO, ONE, ZERO), (ZERO, ZERO, ONE))

checks = fails = 0


def check(cond, msg):
    global checks, fails
    checks += 1
    if cond:
        print(f"  PASS  {msg}")
    else:
        fails += 1
        print(f"  FAIL  {msg}")


# ---- icosahedron and its 60 rotations ---------------------------------------
VERTS = []
for s1, s2 in product((1, -1), repeat=2):
    a, b = Qp(s1), Qp(0, s2)
    VERTS += [(ZERO, a, b), (a, b, ZERO), (b, ZERO, a)]
VSET = set(VERTS)
FOUR = Qp(4)


def neighbors(v):
    return [w for w in VERTS if dot(vec_sub(v, w), vec_sub(v, w)) == FOUR]


v1 = VERTS[0]
v2 = neighbors(v1)[0]
BASE_INV = inv3(tuple(zip(v1, v2, cross(v1, v2))))

rotations = []
for w1 in VERTS:
    for w2 in neighbors(w1):
        rotations.append(mmul(tuple(zip(w1, w2, cross(w1, w2))), BASE_INV))

print("== construction ==")
check(len(set(rotations)) == 60, "60 pairwise-distinct rotations from 60 flags")
check(all(mmul(mT(R), R) == I3 and det3(R) == ONE
          and {mvec(R, v) for v in VERTS} == VSET for R in rotations),
      "every R: orthogonal, det +1, permutes the 12 vertices")
rset = set(rotations)
check(all(mmul(x, y) in rset for x in rset for y in rset),
      "closure: A5 x A5 stays inside the 60")
check(all(mT(R) in rset for R in rset), "inverse-closed (R^T in the set)")


def period(R):
    P = R
    for k in range(1, 11):
        if P == I3:
            return k
        P = mmul(P, R)
    return None


by_p = {}
for R in rotations:
    by_p.setdefault(period(R), 0)
    by_p[period(R)] += 1
check(by_p == {1: 1, 2: 15, 3: 20, 5: 24},
      f"conjugacy class sizes 1/15/20/24 by period: {by_p}")

traces = {}
for R in rotations:
    t = R[0][0] + R[1][1] + R[2][2]
    traces.setdefault(t, 0)
    traces[t] += 1
check(traces == {Qp(3): 1, Qp(-1): 15, Qp(0): 20, PHI: 12, Qp(1, -1): 12},
      "trace spectrum {3:1, -1:15, 0:20, phi:12, 1-phi:12}")

# ---- A4 overlap --------------------------------------------------------------
# A4 built independently: cyclic coordinate shifts x even sign flips.
SHIFT = ((ZERO, ONE, ZERO), (ZERO, ZERO, ONE), (ONE, ZERO, ZERO))
a4 = set()
for k in range(3):
    P = I3
    for _ in range(k):
        P = mmul(P, SHIFT)
    for signs in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)):
        S = tuple(tuple(Qp(signs[i]) if i == j else ZERO for j in range(3))
                  for i in range(3))
        a4.add(mmul(S, P))
check(len(a4) == 12 and a4 <= rset,
      "independently built A4 (shifts x even signs) sits inside A5")
integral = {R for R in rset
            if all(e.b == 0 and e.a.denominator == 1 for row in R for e in row)}
check(integral == a4, "integer-entry subset of A5 == A4 exactly")
new48 = [R for R in rotations if R not in a4]
check(len(new48) == 48, "48 genuinely new rotations beyond A4")

# ---- quadray conversion and field finding ------------------------------------
E = ((Qp(0), Qp(-2), Qp(-2)),
     (Qp(-2), Qp(0), Qp(-2)),
     (Qp(-2), Qp(-2), Qp(0)))
E_INV = inv3(E)


def quadray_of(R):
    return mmul(mmul(E_INV, R), E)


qmats = {R: quadray_of(R) for R in rotations}
half_ok = all(e.a.denominator <= 2 and e.b.denominator <= 2
              for R in new48 for row in qmats[R] for e in row)
any_half = any(e.a.denominator == 2 or e.b.denominator == 2
               for R in new48 for row in qmats[R] for e in row)
check(half_ok and any_half,
      "quadray BCD entries lie in (1/2)Z[phi] and halves DO occur "
      "(pure-Z[phi] claim is false)")
check(all(all(e.b == 0 and e.a.denominator == 1
              for row in qmats[R] for e in row) for R in a4),
      "A4 members convert to integer BCD matrices (consistency)")

NUM_ALPHABET = set()
for x in (ZERO, ONE, Qp(2), PHI, Qp(-1, 1), Qp(-1, 2)):
    NUM_ALPHABET |= {x, -x}
check(all((e + e) in NUM_ALPHABET
          for R in new48 for row in qmats[R] for e in row),
      "doubled entries only in {0,+-1,+-2,+-phi,+-phi^-1,+-sqrt5} "
      "(PSCALE/add chains, no general PMUL)")

# ---- mod-2 structure ----------------------------------------------------------
RES = [Qp(0), Qp(1), Qp(0, 1), Qp(1, 1)]          # Z[phi]/2 = F4


def even(e):
    return e.a % 2 == 0 and e.b % 2 == 0


kernel_sizes = set()
for R in new48:
    N = tuple(tuple(e + e for e in row) for row in qmats[R])
    kernel_sizes.add(sum(1 for v in product(RES, repeat=3)
                         if all(even(o) for o in mvec(N, v))))
check(kernel_sizes == {16},
      "every new rotation: exactly 16/64 safe residue classes mod 2 "
      "(rank 1 over F4)")

# ---- doubling theorem -----------------------------------------------------------


def hw_step(N, w):
    """Hardware semantics: t = N*w must be componentwise even, else fault."""
    t = mvec(N, w)
    if not all(even(e) for e in t):
        return None
    return tuple(Qp(e.a / 2, e.b / 2) for e in t)


nums = {R: tuple(tuple(e + e for e in row) for row in qmats[R])
        for R in rotations}
random.seed(20260710)
all60 = list(rset)
faults = mism = 0
for _ in range(300):
    v0 = tuple(Qp(random.randint(-9, 9)) for _ in range(3))
    w = tuple(e + e for e in v0)
    exact = v0
    for R in (random.choice(all60) for _ in range(10)):
        w = hw_step(nums[R], w)
        if w is None:
            faults += 1
            break
        exact = mvec(qmats[R], exact)
    else:
        if w != tuple(e + e for e in exact):
            mism += 1
check(faults == 0 and mism == 0,
      "doubling theorem: 300 random 10-step A5 chains, doubled load, "
      "all divisions exact, values track exact rationals")

ctrl = sum(1 for _ in range(200)
           if hw_step(nums[random.choice(new48)],
                      tuple(Qp(random.randint(-9, 9)) for _ in range(3)))
           is None)
check(ctrl > 100, f"control: raw (undoubled) integer loads fault often "
      f"({ctrl}/200) — the /2 is genuinely fallible without conditioning")

# ---- Galois / PCHIRAL bridge ----------------------------------------------------


def conj_mat(R):
    return tuple(tuple(e.conj() for e in row) for row in R)


check(sum(1 for R in new48 if conj_mat(R) in rset) == 0,
      "phi -> 1-phi maps all 48 new rotations OUT of this A5 "
      "(onto the dual icosahedron's A5)")
check(len({conj_mat(R) for R in rset} & rset) == 12,
      "the conjugate A5 shares exactly A4 with this one")

# ---- canonical IROTC index space (spec: docs/IROTC_SPEC.md) -------------------
# Deterministic ordering: sort all 60 by (period, row-major numerator key),
# numerator key per entry = (a, b) integers of 2M in Z[phi]. Index 0 = identity.


def num_key(R):
    M = qmats[R]
    return tuple((int((e + e).a), int((e + e).b)) for row in M for e in row)


CANON = sorted(rotations, key=lambda R: (period(R), num_key(R)))
IDX = {R: i for i, R in enumerate(CANON)}

import hashlib
_catalog_blob = repr([num_key(R) for R in CANON]).encode()
CATALOG_SHA = hashlib.sha256(_catalog_blob).hexdigest()[:16]
PINNED_SHA = "aabef37c9c8b0317"
check(CANON[0] == I3, "canonical index 0 is the identity")
check(CATALOG_SHA == PINNED_SHA,
      f"canonical catalog checksum stable: {CATALOG_SHA}")

# ---- A4 overlap aliased to ROTC angles, verified against VM bypass semantics --
ROTC_PERM = {0: None, 21: (1, 0, 3, 2), 22: (2, 3, 0, 1), 23: (3, 2, 1, 0)}


def rotc_bypass_perm(angle):
    """4-tuple p with out[i] = in[p[i]], replicating spu_vm.py bypass path."""
    if angle in ROTC_PERM:
        return ROTC_PERM[angle] or (0, 1, 2, 3)
    sel = {2: 0, 5: 0, 15: 1, 16: 1, 17: 2, 18: 2, 19: 3, 20: 3}[angle]
    comps = list(range(4))
    pf = comps[sel:] + comps[:sel]
    if angle in (2, 15, 17, 19):
        bp = (pf[0], pf[3], pf[1], pf[2])
    else:
        bp = (pf[0], pf[2], pf[3], pf[1])
    inv = (-sel) % 4
    return tuple(bp[inv:] + bp[:inv])


def perm_to_bcd(p):
    """BCD 3x3 of a quadray component permutation on the zero-sum plane."""
    cols = []
    for j in range(3):
        vin = [ZERO, ZERO, ZERO, ZERO]
        vin[j + 1] = ONE
        vin[0] = -sum(vin[1:], ZERO)
        vout = tuple(vin[p[i]] for i in range(4))
        cols.append(vout[1:])
    return tuple(tuple(cols[j][i] for j in range(3)) for i in range(3))


ALIAS = {}          # IROTC index -> ROTC angle, for the 12 A4 members
alias_ok = True
for ang in (0, 2, 5, 15, 16, 17, 18, 19, 20, 21, 22, 23):
    Mb = perm_to_bcd(rotc_bypass_perm(ang))
    Rc = mmul(mmul(E, Mb), E_INV)
    if Rc not in IDX:
        alias_ok = False
        break
    ALIAS[IDX[Rc]] = ang
check(alias_ok and len(ALIAS) == 12,
      "all 12 ROTC bypass angles (0,2,5,15-23) alias into the IROTC index "
      "space via VM permutation semantics")
check(set(ALIAS.keys()) == {IDX[R] for R in a4},
      "alias set == the A4 (integer) members of the canonical list")

# ---- catalog emission (--emit) ------------------------------------------------
ANGLE_OF_TRACE = {Qp(3): "0°", Qp(-1): "180°", Qp(0): "±120°",
                  PHI: "±72°", Qp(1, -1): "±144°"}
ENTRY_COST = {}     # (a,b) of doubled entry -> (pscale, addsub)
for v, c in ((Qp(0), (0, 0)), (ONE, (0, 1)), (Qp(2), (0, 2)),
             (PHI, (1, 1)), (Qp(-1, 1), (1, 2)), (Qp(-1, 2), (1, 3))):
    for s in (v, -v):
        ENTRY_COST[(int(s.a), int(s.b))] = c


def emit_catalog():
    print("| idx | period | inverse | ROTC alias | angle | PSCALE | ADD/SUB |")
    print("|---:|---:|---:|---:|---:|---:|---:|")
    for i, R in enumerate(CANON):
        inv_i = IDX[mT(R)]
        t = R[0][0] + R[1][1] + R[2][2]
        ps = ad = 0
        for k in num_key(R):
            p, a = ENTRY_COST[k]
            ps += p
            ad += a
        alias = str(ALIAS[i]) if i in ALIAS else "—"
        print(f"| {i} | {period(R)} | {inv_i} | {alias} | "
              f"{ANGLE_OF_TRACE[t]} | {ps} | {ad} |")


if __name__ == "__main__" and "--emit" in __import__("sys").argv:
    emit_catalog()

print()
if fails == 0:
    print(f"{checks} checks, 0 failed")
    print("ICOSAHEDRAL CATALOG DERIVATION: ALL PASS")
else:
    print(f"{checks} checks, {fails} FAILED")
    raise SystemExit(1)
