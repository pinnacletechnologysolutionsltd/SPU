#!/usr/bin/env python3
"""IROTC poison-value proofs — VM side (mirrors test_rotc_bad_angle.py).

Both dispatch faults (IROTC_SPEC.md §4) must leave the destination
register bit-identically untouched and raise:

  IROTC_ERR_UNTAGGED  (IrotcUntaggedError)    — source tag UNTAGGED
  IROTC_ERR_BADIDX    (IrotcBadIndexError)    — sel[5:0] > 59
  IROTC_ERR_CATMIX    (IrotcCatalogMixError)  — source catalog-locked the
                        other way (main↔conjugate; the doubling theorem
                        does not compose across catalogs — found
                        2026-07-10, 101/200 random mixed chains would
                        silently truncate under the old 1-bit tag)

Also proven here: BADIDX outranks UNTAGGED (index decode precedes the
operand read, as in the ROTC angle gate), faults do not disturb the
destination's own tag state, the boundary index 59 computes, and SCALE2
re-conditioning (back to PHI_FRESH) legitimately unlocks a catalog switch.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spu_vm import (SPUCore, OPCODES, IrotcBadIndexError, IrotcUntaggedError,
                    IrotcCatalogMixError, PHI_FRESH, PHI_MAIN, PHI_CONJ)

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


def state(core, lane):
    q = core.qregs[lane]
    return (tuple((c.a, c.b) for c in q.components()), core.qr_doubled[lane])


print("=== IROTC poison proofs (VM side) ===")

# Boundary: index 59 on tagged data must compute, not fault.
core = SPUCore(verbose=False, max_steps=20)
af, bf = imm(0, 1, 2, -3)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=2, r2=1, a=59)])
raised = False
try:
    core.run()
except (IrotcBadIndexError, IrotcUntaggedError):
    raised = True
ok(not raised, "index 59 (boundary, valid) computes without fault")

# UNTAGGED: raw QLDI load (tag clear) then IROTC — destination poison-pinned.
core = SPUCore(verbose=False, max_steps=20)
core.load([word("QLDI", r1=1, a=af, b=bf),
           word("LOAD2X", r1=2, a=imm(9, 9, 9, 9)[0], b=imm(9, 9, 9, 9)[1])])
core.run()
before = state(core, 2)
raised = False
core.load([word("IROTC", r1=2, r2=1, a=5)])
try:
    core.run()
except IrotcUntaggedError:
    raised = True
ok(raised, "untagged source raises IrotcUntaggedError (IROTC_ERR_UNTAGGED)")
ok(state(core, 2) == before,
   "UNTAGGED fault leaves destination QR2 bit-identical, tag undisturbed")

# BADIDX: indices 60-63 all fault; destination poison-pinned.
core = SPUCore(verbose=False, max_steps=20)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("LOAD2X", r1=3, a=imm(7, -7, 7, -7)[0], b=imm(7, -7, 7, -7)[1])])
core.run()
before = state(core, 3)
bad = 0
for sel in (60, 61, 62, 63):
    core.load([word("IROTC", r1=3, r2=1, a=sel)])
    try:
        core.run()
    except IrotcBadIndexError:
        bad += 1
ok(bad == 4, "indices 60-63 all raise IrotcBadIndexError (IROTC_ERR_BADIDX)")
ok(state(core, 3) == before,
   "BADIDX faults leave destination QR3 bit-identical, tag undisturbed")

# BADIDX also faults on the conjugate catalog (sel[6] set).
core.load([word("IROTC", r1=3, r2=1, a=(1 << 6) | 60)])
raised = False
try:
    core.run()
except IrotcBadIndexError:
    raised = True
ok(raised, "conjugate-catalog bad index (sel[6]|60) still faults BADIDX")

# Precedence: bad index on an untagged source — BADIDX wins (index decode
# precedes the operand read at dispatch).
core = SPUCore(verbose=False, max_steps=20)
core.load([word("QLDI", r1=1, a=af, b=bf)])
core.run()
got = None
core.load([word("IROTC", r1=2, r2=1, a=63)])
try:
    core.run()
except (IrotcBadIndexError, IrotcUntaggedError) as e:
    got = type(e)
ok(got is IrotcBadIndexError,
   "BADIDX outranks UNTAGGED when both apply (dispatch decode order)")

# CATMIX: a main-catalog output may not enter the conjugate catalog (and
# vice versa); destination poison-pinned; SCALE2 re-conditions.
core = SPUCore(verbose=False, max_steps=20)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=2)])       # QR1 now PHI_MAIN
core.run()
ok(core.qr_doubled[1] == PHI_MAIN, "main-catalog IROTC output is PHI_MAIN")
core.load([word("LOAD2X", r1=2, a=imm(5, 5, 5, 5)[0], b=imm(5, 5, 5, 5)[1])])
core.run()
before = state(core, 2)
raised = False
core.load([word("IROTC", r1=2, r2=1, a=(1 << 6) | 3)])   # conj on MAIN data
try:
    core.run()
except IrotcCatalogMixError:
    raised = True
ok(raised, "conjugate IROTC on PHI_MAIN data raises IrotcCatalogMixError")
ok(state(core, 2) == before,
   "CATMIX fault leaves destination QR2 bit-identical, tag undisturbed")

core.load([word("IROTC", r1=2, r2=1, a=3)])   # same catalog: allowed
core.run()
ok(core.qr_doubled[2] == PHI_MAIN, "main-on-main chain step still computes")

# The mirror direction: conj-locked data refuses a main-catalog rotation.
core = SPUCore(verbose=False, max_steps=20)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=(1 << 6) | 2)])
core.run()
ok(core.qr_doubled[1] == PHI_CONJ, "conjugate-catalog IROTC output is PHI_CONJ")
raised = False
core.load([word("IROTC", r1=2, r2=1, a=3)])
try:
    core.run()
except IrotcCatalogMixError:
    raised = True
ok(raised, "main IROTC on PHI_CONJ data raises IrotcCatalogMixError")

# SCALE2 re-conditioning: MAIN → FRESH → conjugate catalog is legal again.
core = SPUCore(verbose=False, max_steps=20)
core.load([word("LOAD2X", r1=1, a=af, b=bf),
           word("IROTC", r1=1, r2=1, a=2),          # PHI_MAIN
           word("SCALE2", r1=1, r2=1),               # back to PHI_FRESH
           word("IROTC", r1=1, r2=1, a=(1 << 6) | 3)])
raised = False
try:
    core.run()
except (IrotcCatalogMixError, IrotcUntaggedError, AssertionError):
    raised = True
ok(not raised and core.qr_doubled[1] == PHI_CONJ,
   "SCALE2 re-conditioning (PHI_FRESH) legitimately unlocks catalog switch")

print(f"\n{passed} passed, {failed} failed")
if failed:
    print("FAIL")
    sys.exit(1)
print("PASS")
sys.exit(0)
