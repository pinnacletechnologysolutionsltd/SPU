#!/usr/bin/env python3
"""IROTC VM-vs-exact-Fraction trace equivalence — all 60 A₅ indices,
both catalogs (sel[6] = 0 main, 1 Galois-conjugate), on tagged inputs.

Style of test_rotc_vm_rtl_trace.py, adapted for the φ-plane: the
independent oracle is the constructive derivation itself
(test_icosahedral_catalog.py), imported as a module — its 21 self-checks
run at import, so a broken derivation fails this test before any VM
comparison. The VM's generated table (software/lib/irotc_catalog.py) is
checksum-verified independently at first IROTC dispatch, closing the
three-way discipline: derivation / generated table / VM semantics.

Input path exercises real instructions: registers are injected undoubled
(the southbridge-arrival model), conditioned with SCALE2, then rotated.
Register model: φ-plane Z[φ] pair (a, b) = a + b·φ overlays the
RationalSurd (a, b) slots of the QR file (decision 2026-07-10).
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spu_vm import SPUCore, OPCODES, QuadrayVector, RationalSurd

print("== importing constructive derivation (oracle self-checks run now) ==")
import test_icosahedral_catalog as ico

passed = 0
failed = 0


def ok(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {msg}")
    else:
        failed += 1
        print(f"  FAIL  {msg}")


def word(op, r1=0, r2=0, a=0, b=0):
    oc = OPCODES[op]
    return ((oc & 0xFF) << 56) | ((r1 & 0xFF) << 48) | ((r2 & 0xFF) << 40) \
         | ((a & 0xFFFF) << 24) | ((b & 0xFFFF) << 8)


def inject(core, lane, comps, doubled=False):
    """Write Z[φ] pairs [(a,b) x4 for A,B,C,D] into a QR lane."""
    core.qregs[lane] = QuadrayVector(*(RationalSurd(a, b) for a, b in comps))
    core.qr_doubled[lane] = doubled


def pairs_of(qr):
    return tuple((c.a, c.b) for c in qr.components())


def qp_pair(e):
    """Exact Qp -> integer Z[φ] pair; fails loudly on non-integers."""
    assert e.a.denominator == 1 and e.b.denominator == 1, e
    return (int(e.a), int(e.b))


def expected_bcd(M, w_pairs, conj):
    """2 * (M or conj(M)) applied to undoubled w, as integer pairs."""
    if conj:
        M = tuple(tuple(e.conj() for e in row) for row in M)
    wv = tuple(ico.Qp(a, b) for a, b in w_pairs)
    out = ico.mvec(M, wv)
    return tuple(qp_pair(e + e) for e in out)


random.seed(20260710)
CASES_PER_INDEX = 3

for conj in (0, 1):
    mism = 0
    tag_lost = 0
    a_bad = 0
    for idx, R in enumerate(ico.CANON):
        M = ico.qmats[R]
        for _ in range(CASES_PER_INDEX):
            w = [(random.randint(-9, 9), random.randint(-9, 9))
                 for _ in range(3)]
            core = SPUCore(verbose=False, max_steps=20)
            # junk A proves the source A component is ignored
            inject(core, 1, [(77, -55)] + w, doubled=False)
            core.load([
                word("SCALE2", r1=1, r2=1),
                word("IROTC", r1=2, r2=1, a=(conj << 6) | idx),
            ])
            core.run()
            got = pairs_of(core.qregs[2])
            exp = expected_bcd(M, w, conj)
            if got[1:] != exp:
                mism += 1
            ea = (-(exp[0][0] + exp[1][0] + exp[2][0]),
                  -(exp[0][1] + exp[1][1] + exp[2][1]))
            if got[0] != ea:
                a_bad += 1
            if not core.qr_doubled[2]:
                tag_lost += 1
    cat = "conjugate" if conj else "main"
    ok(mism == 0,
       f"{cat} catalog: all 60 indices x {CASES_PER_INDEX} random tagged "
       f"inputs bit-exact vs exact-Fraction oracle ({mism} mismatches)")
    ok(a_bad == 0,
       f"{cat} catalog: A always recomputed from zero-sum, source A ignored")
    ok(tag_lost == 0,
       f"{cat} catalog: DOUBLED tag preserved across IROTC")

# --- A₄ alias interop: IROTC idx == ROTC alias-angle on shared registers ---
# The 12 integer-matrix members are reachable by either encoding
# (IROTC_SPEC.md §5); on zero-sum doubled data the results must be
# bit-identical and both must carry the tag through.
alias_mism = 0
alias_tag = 0
for idx, ang in sorted(ico.ALIAS.items()):
    for _ in range(CASES_PER_INDEX):
        w = [(random.randint(-9, 9), random.randint(-9, 9)) for _ in range(3)]
        av = (-(w[0][0] + w[1][0] + w[2][0]),
              -(w[0][1] + w[1][1] + w[2][1]))
        core = SPUCore(verbose=False, max_steps=20)
        inject(core, 1, [av] + w, doubled=False)
        core.load([
            word("SCALE2", r1=1, r2=1),
            word("IROTC", r1=2, r2=1, a=idx),
            word("ROTC", r1=3, r2=1, a=ang),
        ])
        core.run()
        if pairs_of(core.qregs[2]) != pairs_of(core.qregs[3]):
            alias_mism += 1
        if not (core.qr_doubled[2] and core.qr_doubled[3]):
            alias_tag += 1
ok(alias_mism == 0,
   "all 12 A4 aliases: IROTC idx and ROTC angle produce identical "
   "registers on zero-sum doubled data")
ok(alias_tag == 0,
   "all 12 A4 aliases: both encodings preserve the DOUBLED tag")

# --- conjugate catalog is a don't-care for aliased (rational) indices ------
dc_mism = 0
for idx in sorted(ico.ALIAS):
    w = [(random.randint(-9, 9), random.randint(-9, 9)) for _ in range(3)]
    core = SPUCore(verbose=False, max_steps=20)
    inject(core, 1, [(0, 0)] + w, doubled=False)
    core.load([
        word("SCALE2", r1=1, r2=1),
        word("IROTC", r1=2, r2=1, a=idx),
        word("IROTC", r1=3, r2=1, a=(1 << 6) | idx),
    ])
    core.run()
    if pairs_of(core.qregs[2]) != pairs_of(core.qregs[3]):
        dc_mism += 1
ok(dc_mism == 0,
   "sel[6] is a don't-care for the 12 aliased indices "
   "(conjugation fixes rational matrices)")

print(f"\n{passed} passed, {failed} failed")
if failed:
    print("FAIL")
    sys.exit(1)
print("IROTC VM TRACE EQUIVALENCE (60 indices x both catalogs): PASS")
sys.exit(0)
