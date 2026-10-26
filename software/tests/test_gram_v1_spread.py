#!/usr/bin/env python3
"""SIM-CAP1 gram_v1 SPREAD: Python VM conformance against an independent oracle.

research/sim_cap1_spread/GRAM_V1_CONTRACT_FROZEN.md. The oracle (gram_v1_oracle.py) is plain (p, q) integer-pair
arithmetic sharing no code with the VM spread path.
"""

import itertools
import os
import re
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from gram_v1_oracle import smul, bilinear, oracle  # noqa: E402
from spu_vm import (QuadrayVector, RationalSurd, SPUCore, assemble_source,
                    capability_manifest, DegenerateMetricError)

CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)


def qv(lanes):
    return QuadrayVector(*[RationalSurd(p, q) for p, q in lanes])


def lanes(*ints):
    return [(i, 0) for i in ints]


def run_spread(v, w, semantics, rd=10):
    core = SPUCore(max_steps=8, verbose=False, metric_semantics=semantics)
    core.qregs[0], core.qregs[1] = qv(v), qv(w)
    core.regs[rd] = RationalSurd(7, 7)
    core.regs[(rd + 1) % 26] = RationalSurd(9, 9)
    core.load(assemble_source(f"SPREAD R{rd}, QR0, QR1"))
    return core


def spread_result(v, w, semantics="gram_v1", rd=10):
    core = run_spread(v, w, semantics, rd)
    core.step()
    r, r1 = core.regs[rd], core.regs[(rd + 1) % 26]
    return (r.a, r.b), (r1.a, r1.b)


PAIRS = [  # (a, b, legacy N/D, gram N/D)
    ((1, 1, 1, 0), (1, 0, 0, 0), (8, 9), (8, 9)),
    ((1, 0, 0, 0), (0, 1, 0, 0), (9, 9), (8, 9)),
    ((2, 0, 0, 0), (0, 0, 1, 1), (48, 48), (32, 48)),
    ((3, 1, 0, 0), (1, 2, 0, 5), (1319, 1344), (1200, 1344)),
]

for a, b, leg, gram in PAIRS:
    check(spread_result(lanes(*a), lanes(*b), "legacy_dot") == ((leg[0], 0), (leg[1], 0)), f"legacy {a} {b}")
    check(spread_result(lanes(*a), lanes(*b)) == ((gram[0], 0), (gram[1], 0)), f"gram {a} {b}")
    check(oracle(lanes(*a), lanes(*b)) == ((gram[0], 0), (gram[1], 0)), f"oracle {a} {b}")

# default profile is legacy_dot and bit-identical for the pinned historical case
check(SPUCore(verbose=False).metric_semantics == "legacy_dot", "default semantics")
check(spread_result(lanes(1, 0, 0, 0), lanes(1, 0, 0, 0), "legacy_dot") == ((8, 0), (9, 0)), "legacy self 8/9")

# self-spread and collinear: zero numerator under gram_v1
check(spread_result(lanes(1, 0, 0, 0), lanes(1, 0, 0, 0)) == ((0, 0), (9, 0)), "self-spread 0/9")
check(spread_result(lanes(1, 0, 0, 0), lanes(2, 0, 0, 0)) == ((0, 0), (36, 0)), "collinear 0/36")
check(spread_result(lanes(1, 0, 0, 0), lanes(2, 0, 0, 0), "legacy_dot") == ((32, 0), (36, 0)), "legacy collinear 32/36")

# symmetry, 24 coordinate permutations, coordinate-gauge invariance, surd operands
va = [(3, 1), (1, -2), (0, 5), (-4, 1)]
vb = [(1, 1), (2, 0), (0, -3), (5, 2)]
base = spread_result(va, vb)
check(base == oracle(va, vb), "surd pair vs oracle")
check(spread_result(vb, va) == base, "symmetry")
for perm in itertools.permutations(range(4)):
    check(spread_result([va[i] for i in perm], [vb[i] for i in perm]) == base, f"permutation {perm}")
for t in [(7, 0), (-3, 2), (0, 5)]:
    sh = lambda x: [(p + t[0], q + t[1]) for p, q in x]
    check(spread_result(sh(va), vb) == base, f"gauge shift on first {t}")
    check(spread_result(va, sh(vb)) == base, f"gauge shift on second {t}")
# rational inputs: second route through the three-quadrance form (same fraction)
for a, b, _, _ in PAIRS:
    A, Bv = lanes(*a), lanes(*b)
    Q1 = oracle(A, A) is None
    bvv = sum((a[i] - a[j]) ** 2 for i in range(4) for j in range(i + 1, 4))
    bww = sum((b[i] - b[j]) ** 2 for i in range(4) for j in range(i + 1, 4))
    q3 = sum(((a[i] - b[i]) - (a[j] - b[j])) ** 2 for i in range(4) for j in range(i + 1, 4))
    via_q = F(4 * bvv * bww - (q3 - bvv - bww) ** 2, 4 * bvv * bww)
    n, d = spread_result(A, Bv)
    check(F(n[0], d[0]) == via_q, f"three-quadrance route {a} {b}")

# Pell-unit cancellation witness: intermediates exceed int32 but the result fits
u, w = (708158977, 408855776), (708158977, -408855776)
check(smul(u, w) == (1, 0), "u*w is the Pell norm 1")
s = lambda c, x: (c * x[0], c * x[1])
z = (0, 0)
for wa, wb in [([s(3, u), z, z, z], [s(3, w), z, z, z]),
               ([z, s(3, u), z, z], [z, s(3, w), z, z]),
               ([s(-3, u), z, z, z], [s(3, w), z, z, z])]:
    check(all(abs(c) < 2**31 for pq in wa + wb for c in pq), "witness lanes fit int32")
    check(spread_result(wa, wb) == ((0, 0), (729, 0)), "Pell cancellation commits N=(0,0) D=(729,0)")
    check(oracle(wa, wb) == ((0, 0), (729, 0)), "oracle agrees on witness")

# Python is an unbounded oracle: no OVERFLOW even for huge lanes
big = [(2**40, 2**39), (3, 0), (0, 5), (7, 7)]
check(spread_result(big, vb) == oracle(big, vb), "unbounded Python result")

# degenerate operands: DEGENERATE_METRIC, atomic. Full VM state is compared before/after:
# only halted/fault_kind may change (registers, QRs, typestate tags, call stack, snap counter,
# PC, step count and log all preserved), including the rd=25 -> R0 wrap.
def vm_state(core):
    return {k: re.sub(r"0x[0-9a-f]+", "0x", repr(x)) for k, x in vars(core).items()}


for bad in [lanes(1, 1, 1, 1), lanes(0, 0, 0, 0), [(2, 3)] * 4]:
    for first in (True, False):
        for rd in (10, 25):
            v, wv = (bad, vb) if first else (vb, bad)
            core = run_spread(v, wv, "gram_v1", rd)
            core.call_stack, core.snap_failures = [19, 23], 2
            before = vm_state(core)
            try:
                core.step()
                check(False, "degenerate operand must fault")
            except DegenerateMetricError:
                pass
            after = vm_state(core)
            check(core.fault_kind == "DEGENERATE_METRIC" and core.halted, "fault kind + halted")
            check({k for k in before if before[k] != after[k]} == {"halted", "fault_kind"},
                  f"only halted/fault_kind may change (rd={rd})")
            check(core.pc == 0 and core.step_count == 0 and core.log == [], "pc/step/log unchanged")
            check((core.regs[rd].a, core.regs[rd].b) == (7, 7)
                  and (core.regs[(rd + 1) % 26].a, core.regs[(rd + 1) % 26].b) == (9, 9),
                  "destination pair unchanged on refusal")
# legacy keeps the historical zero-denominator behaviour (no fault)
check(spread_result(lanes(1, 1, 1, 1), lanes(1, 0, 0, 0), "legacy_dot")[1] == (0, 0), "legacy zero-metric: no fault")

# R25 -> R0 wrap of the second destination
check(spread_result(lanes(1, 0, 0, 0), lanes(0, 1, 0, 0), rd=25) == ((8, 0), (9, 0)), "rd=25 wrap result")

# --proof prints the three B values the result is computed from (same line format as the C++ VM)
import contextlib
import io
for pa, pb in [(lanes(1, 0, 0, 0), lanes(0, 1, 0, 0)), (lanes(3, 1, 0, 0), lanes(1, 2, 0, 5)), (va, vb)]:
    core = run_spread(pa, pb, "gram_v1")
    core.proof = True
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        core.step()
    want = "B(v,v)=({},{}) B(w,w)=({},{}) B(v,w)=({},{})".format(
        *bilinear(pa, pa), *bilinear(pb, pb), *bilinear(pa, pb))
    check(want in buf.getvalue(), f"python proof B line {want!r} in {buf.getvalue()!r}")
    (n, d) = oracle(pa, pb)
    check(f"N=({n[0]},{n[1]}) D=({d[0]},{d[1]})" in buf.getvalue(), "python proof N/D line")
# legacy proof is unchanged (no B line)
core = run_spread(lanes(1, 0, 0, 0), lanes(0, 1, 0, 0), "legacy_dot")
core.proof = True
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    core.step()
check("B(v,v)" not in buf.getvalue() and "dot" in buf.getvalue(), "legacy proof keeps its original form")

# manifest + construction-time validation; legacy marked unqualified
m = capability_manifest("full", "gram_v1")
check(m["metric_semantics"] == "gram_v1" and m["profile"] == "full", "manifest axes independent")
check(capability_manifest()["metric_semantics"] == "legacy_dot", "manifest default")
check("qualified: false" in capability_manifest()["metric_semantics_detail"]["spread_opcode_0x15"]["scope"], "legacy unqualified note")
try:
    SPUCore(metric_semantics="nope")
    check(False, "bad semantics must be rejected")
except ValueError:
    pass

core = SPUCore(metric_semantics="gram_v1")
for bad in ("legacy_dot", "nope"):
    try:
        core.metric_semantics = bad
        check(False, "metric_semantics must be read-only after construction")
    except AttributeError:
        pass
check(core.metric_semantics == "gram_v1", "selection unchanged after rejected writes")

print(f"PASS: gram_v1 SPREAD Python conformance ({CHECKS} checks)")
