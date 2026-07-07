#!/usr/bin/env python3
"""Montgomery batch inversion for batched Padé evals — oracle + evaluation.

Verifies the A31 field oracle (software/lib/a31_field.py) against
algebraic identities and an independent linear-algebra inversion path,
proves the batch inversion bit-exact against per-element tower runs
(including deferred zero-divisor isolation), then measures the
MAC-vs-tower tradeoff on representative RPLU2 workload mixes using the
cycle costs documented in the RTL:

  tower inversion  ~76 cycles  (spu13_fp4_inverter.v, deterministic)
  shared multiply   ~3 cycles  (spu13_m31_multiplier.v via launch/wait FSM)

No floating point. All correctness checks assert bit-exact results.

Usage:
    python3 software/tests/test_pade_batch_inversion.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.a31_field import (
    A31_ONE,
    MULT_CYCLES,
    OpCount,
    P,
    TOWER_CYCLES,
    a31_add,
    a31_mul,
    a31_norm,
    a31_tower_inv,
    batch_tower_inv,
    horner,
    m31,
    pade_eval,
    pade_eval_batch,
)

random.seed(0x5B13)  # deterministic run — this is an oracle, not a fuzzer

CHECKS = 0
FAILURES = 0


def check(cond, msg):
    global CHECKS, FAILURES
    CHECKS += 1
    if cond:
        print(f"  ok  {msg}")
    else:
        FAILURES += 1
        print(f"  FAIL {msg}")


def rand_a31():
    return tuple(random.randrange(P) for _ in range(4))


def rand_unit():
    while True:
        z = rand_a31()
        if a31_norm(z) != 0:
            return z


def matrix_inv_apply(z):
    """Independent inverse: solve M_z · v = e0 over F_p by Gaussian
    elimination, where M_z is left-multiplication by z in the basis
    [1, √3, √5, √15]. Shares no code with the tower path."""
    basis = [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]
    cols = [a31_mul(z, e) for e in basis]
    aug = [[cols[j][i] for j in range(4)] + [1 if i == 0 else 0]
           for i in range(4)]
    for col in range(4):
        piv = next((r for r in range(col, 4) if aug[r][col]), None)
        if piv is None:
            return None
        aug[col], aug[piv] = aug[piv], aug[col]
        inv_p = pow(aug[col][col], P - 2, P)
        aug[col] = [v * inv_p % P for v in aug[col]]
        for r in range(4):
            if r != col and aug[r][col]:
                f = aug[r][col]
                aug[r] = [(a - f * b) % P for a, b in zip(aug[r], aug[col])]
    return tuple(aug[i][4] for i in range(4))


SQRT15 = pow(15, (P + 1) // 4, P)  # 15 is a QR mod M31; p = 3 mod 4


def rand_zero_divisor():
    """(√15 + √15-basis-element)·unit — nonzero, norm 0."""
    return a31_mul((SQRT15, 0, 0, 1), rand_unit())


# ── 1. Field axioms and basis table ───────────────────────────────────────

print("A31 basis identities:")
S3, S5, S15 = (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)
check(a31_mul(S3, S3) == (3, 0, 0, 0), "sqrt3 * sqrt3 = 3")
check(a31_mul(S5, S5) == (5, 0, 0, 0), "sqrt5 * sqrt5 = 5")
check(a31_mul(S15, S15) == (15, 0, 0, 0), "sqrt15 * sqrt15 = 15")
check(a31_mul(S3, S5) == S15, "sqrt3 * sqrt5 = sqrt15")
check(a31_mul(S3, S15) == (0, 0, 3, 0), "sqrt3 * sqrt15 = 3*sqrt5")
check(a31_mul(S5, S15) == (0, 5, 0, 0), "sqrt5 * sqrt15 = 5*sqrt3")

print("Ring axioms (200 random triples):")
ok_comm = ok_assoc = ok_dist = True
for _ in range(200):
    a, b, c = rand_a31(), rand_a31(), rand_a31()
    ok_comm &= a31_mul(a, b) == a31_mul(b, a)
    ok_assoc &= a31_mul(a31_mul(a, b), c) == a31_mul(a, a31_mul(b, c))
    ok_dist &= a31_mul(a, a31_add(b, c)) == a31_add(a31_mul(a, b),
                                                    a31_mul(a, c))
check(ok_comm, "multiplication commutes")
check(ok_assoc, "multiplication associates")
check(ok_dist, "multiplication distributes over addition")

# ── 2. Tower inversion ────────────────────────────────────────────────────

print("Conjugate Reduction Tower:")
ok_inv = True
for _ in range(100):
    z = rand_unit()
    inv, v = a31_tower_inv(z)
    ok_inv &= not v and a31_mul(z, inv) == A31_ONE
check(ok_inv, "z * tower_inv(z) = 1 (100 random units)")

ok_mat = True
for _ in range(20):
    z = rand_unit()
    ok_mat &= a31_tower_inv(z)[0] == matrix_inv_apply(z)
check(ok_mat, "tower matches independent Gaussian-elimination inverse (20)")

check(a31_tower_inv(A31_ONE) == (A31_ONE, False), "inv(1) = 1")
a = random.randrange(1, P)
check(a31_tower_inv((a, 0, 0, 0))[0] == (pow(a, P - 2, P), 0, 0, 0),
      "scalar inverse matches Fermat")

print("Zero divisors (FLAGS.V):")
zd = (SQRT15, 0, 0, 1)
check(a31_norm(zd) == 0 and a31_tower_inv(zd) == (None, True),
      "sqrt(15)+sqrt15-element is a zero divisor, tower raises FLAGS.V")
ok_zd = all(a31_tower_inv(rand_zero_divisor())[1] for _ in range(50))
check(ok_zd, "zero-divisor * unit stays singular (50 random)")

# ── 3. Montgomery batch inversion ─────────────────────────────────────────

print("Batch inversion:")
ok_batch = True
for k in [1, 2, 3, 5, 8, 13, 21, 40]:
    dens = [rand_unit() for _ in range(k)]
    invs, singular = batch_tower_inv(dens)
    ok_batch &= singular == []
    ok_batch &= invs == [a31_tower_inv(d)[0] for d in dens]
check(ok_batch, "batch bit-exact vs per-element tower (k=1..40)")

ctr = OpCount()
k = 13
batch_tower_inv([rand_unit() for _ in range(k)], ctr)
check(ctr.towers == 1 and ctr.mults == 3 * (k - 1),
      f"unit batch costs exactly 1 tower + 3(k-1) mults (k={k}: "
      f"{ctr.towers} towers, {ctr.mults} mults)")

dens = [rand_unit() for _ in range(10)]
bad = [2, 7]
for i in bad:
    dens[i] = rand_zero_divisor()
invs, singular = batch_tower_inv(dens)
check(singular == bad, "deferred check isolates the singular indices")
ok_iso = all(
    (invs[i] is None) if i in bad else invs[i] == a31_tower_inv(dens[i])[0]
    for i in range(10))
check(ok_iso, "unit entries stay bit-exact alongside singulars")

invs, singular = batch_tower_inv([rand_zero_divisor() for _ in range(4)])
check(singular == [0, 1, 2, 3] and invs == [None] * 4,
      "all-singular batch flags every lane")

# ── 4. Padé evaluation ────────────────────────────────────────────────────

print("Padé [4/4] evaluation:")
NUM = [rand_a31() for _ in range(5)]
DEN = [rand_a31() for _ in range(5)]

x = rand_a31()
check(pade_eval(NUM, [A31_ONE, (0,) * 4, (0,) * 4, (0,) * 4, (0,) * 4], x)[0]
      == horner(NUM, x), "den = 1 reduces to numerator Horner")
r, v = pade_eval(NUM, NUM, x)
check(not v and r == A31_ONE, "num = den evaluates to exactly 1")

lanes = [rand_a31() for _ in range(13)]  # one 13-axis manifold sweep
batch_res, singular = pade_eval_batch(NUM, DEN, lanes)
ok_pade = singular == [] and all(
    batch_res[i] == pade_eval(NUM, DEN, lanes[i])[0] for i in range(13))
check(ok_pade, "13-lane batch bit-exact vs 13 single evals")

sing_x = (0, 0, 0, 0)
den_zero_at_origin = [(0,) * 4] + DEN[1:]  # D(0) = 0 -> singular lane
batch_res, singular = pade_eval_batch(NUM, den_zero_at_origin,
                                      lanes[:4] + [sing_x] + lanes[4:])
check(singular == [4] and batch_res[4] is None and
      all(batch_res[i] is not None for i in range(9) if i != 4),
      "singular saddle flagged per-lane, others still evaluate")

# ── 5. MAC-vs-tower evaluation ────────────────────────────────────────────

print("\n== Cycle model: baseline vs Montgomery batch "
      f"(tower={TOWER_CYCLES}, mult={MULT_CYCLES} cycles) ==")
print(f"{'k':>5} {'base cyc':>9} {'batch cyc':>10} {'speedup':>8} "
      f"{'base MACs':>10} {'batch MACs':>11} {'MAC delta':>10}")

WORKLOADS = [
    (1, "single eval"),
    (2, "crossover"),
    (4, "quad step"),
    (13, "manifold sweep (13 lanes)"),
    (26, "2-step sweep"),
    (104, "trajectory (13 lanes x 8 steps)"),
    (512, "audio frame"),
]
speedup_13 = None
for k, label in WORKLOADS:
    xs = [rand_a31() for _ in range(k)]
    base = OpCount()
    for xi in xs:
        pade_eval(NUM, DEN, xi, base)
    batch = OpCount()
    pade_eval_batch(NUM, DEN, xs, batch)
    su = base.cycles() / batch.cycles()
    if k == 13:
        speedup_13 = su
    dmac = 100.0 * (batch.mults - base.mults) / base.mults
    print(f"{k:>5} {base.cycles():>9} {batch.cycles():>10} {su:>7.2f}x "
          f"{base.mults:>10} {batch.mults:>11} {dmac:>+9.1f}%  {label}")

asym = (9 * MULT_CYCLES + TOWER_CYCLES) / (12 * MULT_CYCLES)
print(f"\nAsymptote: {asym:.2f}x (per-eval floor 12 mults: 8 Horner + "
      f"~3 batch + 1 final; tower fully amortized)")
print("Sensitivity (k=13 speedup at mult = 2 / 3 / 4 cycles): "
      + " / ".join(
          f"{(9 * 13 * mc + 13 * TOWER_CYCLES) / ((9 * 13 + 3 * 12 + 0) * mc + TOWER_CYCLES):.2f}x"
          for mc in (2, 3, 4)))

check(speedup_13 is not None and speedup_13 > 2.0,
      "batch wins >2x on the 13-lane manifold sweep")

# ── Summary ───────────────────────────────────────────────────────────────

print(f"\n{CHECKS} checks, {FAILURES} failures")
if FAILURES == 0:
    print("ALL CHECKS PASS")
    sys.exit(0)
print("FAILURES PRESENT")
sys.exit(1)
