#!/usr/bin/env python3
"""IROTC chain tests — the doubling theorem exercised through real VM
instruction streams, plus every typestate transition that can break a
chain (IROTC_SPEC.md §3, roadmap Phase 2 step 5).

Proven here:
  - doubled load → 10-step chains, pure main and pure conjugate catalog,
    bit-exact against the exact-Fraction oracle at every step;
  - a thirds ROTC mid-chain clears the tag and the next IROTC faults
    UNTAGGED without corrupting its destination;
  - an octahedral ROTC (24-35, integer but not A₅) demotes MAIN→UNTAGGED,
    but passes FRESH data through still-licensed;
  - an A₄ bypass ROTC mid-chain preserves the state and the chain stays
    exact (alias interop);
  - QADD lattice: FRESH+MAIN stays licensed as MAIN; MAIN+CONJ clears.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spu_vm import (SPUCore, OPCODES, IrotcUntaggedError, IrotcCatalogMixError,
                    PHI_UNTAGGED, PHI_FRESH, PHI_MAIN, PHI_CONJ)

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


def imm(a, b, c, d):
    return ((a & 0xFF) << 8) | (b & 0xFF), ((c & 0xFF) << 8) | (d & 0xFF)


def bcd_pairs(qr):
    return tuple((c.a, c.b) for c in (qr.b, qr.c, qr.d))


def conj_mat(M):
    return tuple(tuple(e.conj() for e in row) for row in M)


random.seed(20260710)

# --- 10-step pure-catalog chains vs exact Fractions -------------------------
for conj in (0, 1):
    mism = faults = 0
    for _ in range(40):
        v = [random.randint(-9, 9) for _ in range(3)]
        idxs = [random.randrange(60) for _ in range(10)]
        af, bf = imm(0, v[0], v[1], v[2])
        prog = [word("LOAD2X", r1=1, a=af, b=bf)]
        prog += [word("IROTC", r1=1, r2=1, a=(conj << 6) | i) for i in idxs]
        core = SPUCore(verbose=False, max_steps=40)
        core.load(prog)
        try:
            core.run()
        except (IrotcUntaggedError, IrotcCatalogMixError, AssertionError):
            faults += 1
            continue
        # exact: w_final = 2 * (M10 ... M1) v
        exact = tuple(ico.Qp(x) for x in v)
        for i in idxs:
            M = ico.qmats[ico.CANON[i]]
            if conj:
                M = conj_mat(M)
            exact = ico.mvec(M, exact)
        exp = tuple((int((e + e).a), int((e + e).b)) for e in exact)
        if bcd_pairs(core.qregs[1]) != exp:
            mism += 1
    cat = "conjugate" if conj else "main"
    ok(faults == 0 and mism == 0,
       f"40 random 10-step {cat}-catalog chains: no faults, "
       f"bit-exact vs exact-Fraction oracle")

# --- thirds ROTC mid-chain: tag cleared, next IROTC faults, no corruption ---
core = SPUCore(verbose=False, max_steps=40)
af, bf = imm(0, 3, -6, 9)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=40),
           word("ROTC", r1=1, r2=1, a=1)])       # thirds — clears the tag
core.run()
ok(core.qr_doubled[1] == PHI_UNTAGGED,
   "thirds ROTC (angle 1) mid-chain clears the tag to UNTAGGED")
snap = tuple((c.a, c.b) for c in core.qregs[1].components())
raised = False
core.load([word("IROTC", r1=1, r2=1, a=41)])
try:
    core.run()
except IrotcUntaggedError:
    raised = True
ok(raised, "next IROTC after the thirds step faults UNTAGGED")
ok(tuple((c.a, c.b) for c in core.qregs[1].components()) == snap,
   "faulting IROTC leaves the register bit-identical (no corruption)")

# --- octahedral ROTC: demotes MAIN, passes FRESH -----------------------------
core = SPUCore(verbose=False, max_steps=40)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=38),      # PHI_MAIN
           word("ROTC", r1=1, r2=1, a=26)])      # octahedral, not in A₅
core.run()
ok(core.qr_doubled[1] == PHI_UNTAGGED,
   "octahedral ROTC (angle 26) demotes PHI_MAIN to UNTAGGED "
   "(sandwich products leave ½Z[φ])")
raised = False
core.load([word("IROTC", r1=1, r2=1, a=38)])
try:
    core.run()
except IrotcUntaggedError:
    raised = True
ok(raised, "IROTC after the octahedral step faults UNTAGGED")

core = SPUCore(verbose=False, max_steps=40)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("ROTC", r1=1, r2=1, a=26),       # octahedral on FRESH
           word("IROTC", r1=1, r2=1, a=38)])     # still licensed
raised = False
try:
    core.run()
except (IrotcUntaggedError, AssertionError):
    raised = True
ok(not raised and core.qr_doubled[1] == PHI_MAIN,
   "octahedral ROTC passes FRESH through (even stays even), "
   "chain continues licensed")

# --- A₄ bypass ROTC mid-chain: state preserved, chain exact ------------------
mism = 0
for idx, ang in sorted(ico.ALIAS.items()):
    v = [random.randint(-9, 9) for _ in range(3)]
    af2, bf2 = imm(0, v[0], v[1], v[2])
    pre, post = 37, 42                        # genuine period-5 rotations
    core = SPUCore(verbose=False, max_steps=40)
    core.load([word("LOAD2X", r1=1, a=af2, b=bf2),
               word("IROTC", r1=1, r2=1, a=pre),
               word("ROTC", r1=1, r2=1, a=ang),   # A₄ member via ROTC encoding
               word("IROTC", r1=1, r2=1, a=post)])
    try:
        core.run()
    except (IrotcUntaggedError, IrotcCatalogMixError, AssertionError):
        mism += 1
        continue
    exact = tuple(ico.Qp(x) for x in v)
    for i in (pre, idx, post):
        exact = ico.mvec(ico.qmats[ico.CANON[i]], exact)
    exp = tuple((int((e + e).a), int((e + e).b)) for e in exact)
    if bcd_pairs(core.qregs[1]) != exp or core.qr_doubled[1] != PHI_MAIN:
        mism += 1
ok(mism == 0,
   "all 12 A₄ aliases via ROTC encoding mid-IROTC-chain: state preserved, "
   "chain bit-exact")

# --- QADD lattice -------------------------------------------------------------
core = SPUCore(verbose=False, max_steps=40)
core.load([word("LOAD2X", r1=1, a=af, b=bf),      # QR1 FRESH
           word("LOAD2X", r1=2, a=af, b=bf),
           word("IROTC", r1=2, r2=2, a=45),        # QR2 MAIN
           word("QADD", r1=2, r2=1),               # MAIN + FRESH
           word("IROTC", r1=2, r2=2, a=46)])       # must still be licensed
raised = False
try:
    core.run()
except (IrotcUntaggedError, IrotcCatalogMixError, AssertionError):
    raised = True
ok(not raised and core.qr_doubled[2] == PHI_MAIN,
   "QADD of FRESH into MAIN keeps the MAIN license (lattice join)")

core = SPUCore(verbose=False, max_steps=40)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=45),               # QR1 MAIN
           word("LOAD2X", r1=2, a=af, b=bf),
           word("IROTC", r1=2, r2=2, a=(1 << 6) | 45),    # QR2 CONJ
           word("QADD", r1=2, r2=1)])                     # MAIN + CONJ
core.run()
ok(core.qr_doubled[2] == PHI_UNTAGGED,
   "QADD of MAIN into CONJ clears the tag (incompatible catalogs)")
raised = False
core.load([word("IROTC", r1=2, r2=2, a=1)])
try:
    core.run()
except IrotcUntaggedError:
    raised = True
ok(raised, "IROTC on the mixed sum faults UNTAGGED")

print(f"\n{passed} passed, {failed} failed")
if failed:
    print("FAIL")
    sys.exit(1)
print("IROTC CHAIN TESTS: PASS")
sys.exit(0)
