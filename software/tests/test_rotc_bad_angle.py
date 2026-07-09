#!/usr/bin/env python3
"""ROTC bad-angle fault test — VM side of the "don't corrupt the manifold"
fix (2026-07-09). Angles beyond ROTC_MAX_VERIFIED_ANGLE (11 since
2026-07-10; was 5 until the axis-permutation conjugates 6-11 got their
VM oracle + cross-verified RTL pass) must raise RotcUnverifiedAngleError
and leave the destination register completely untouched, matching the
RTL fault in spu13_core.v (see the ROTC_MAX_VERIFIED_ANGLE localparam
there for the matching hardware gate, and
hardware/tests/spu13/spu13_core_rotc_opcode_tb.v for the RTL-side proof
of the same property).

Why angles 12+ are refused rather than computed:
  - Angles 12-33 (removed 2026-07-09): were literal F=G=H=0 placeholder
    entries that would have silently zeroed the destination's B/C/D.
  - Angles 34-63: never had entries at all.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spu_vm import SPUCore, OPCODES, RotcUnverifiedAngleError

passed = 0
failed = 0


def ok(cond, msg):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


def word(op: str, r1=0, r2=0, a=0, b=0) -> int:
    oc = OPCODES[op]
    return ((oc & 0xFF) << 56) | ((r1 & 0xFF) << 48) | ((r2 & 0xFF) << 40) \
         | ((a & 0xFFFF) << 24) | ((b & 0xFFFF) << 8)


def make_core():
    return SPUCore(verbose=False, max_steps=50)


def qldi_a_b(a, b, c, d):
    # QLDI packs two signed 8-bit immediates per 16-bit half:
    # a-field = (A<<8)|B, b-field = (C<<8)|D. Matches spu_vm_test.py's usage.
    return ((a & 0xFF) << 8) | (b & 0xFF), ((c & 0xFF) << 8) | (d & 0xFF)


print("=== ROTC bad-angle fault (VM side) ===")

# Valid boundary: angle 11 must NOT raise (gate moved 5 → 11 on 2026-07-10
# when the axis-permutation conjugates got their cross-verified oracle pass).
core = make_core()
a_field, b_field = qldi_a_b(3, 6, 9, 12)
core.load([
    word("QLDI", r1=1, a=a_field, b=b_field),
    word("ROTC", r1=2, r2=1, a=11),
])
raised = False
try:
    core.run()
except RotcUnverifiedAngleError:
    raised = True
ok(not raised, "angle 11 (boundary, valid) does not raise")

# Angle 6 computes (permutation conjugate about B) and, unlike 0-5,
# rewrites the A component too — regression-pin one full result.
# Source (3,-6,9,-12), all multiples of 3 so the thirds division is
# exact; expected (12,-6,-3,-9) from the exact-Fraction oracle.
core = make_core()
a_field, b_field = qldi_a_b(3, -6, 9, -12)
core.load([
    word("QLDI", r1=1, a=a_field, b=b_field),
    word("ROTC", r1=2, r2=1, a=6),
])
core.run()
got = core.qregs[2]
ok((got.a.a, got.b.a, got.c.a, got.d.a) == (12, -6, -3, -9)
   and (got.a.b, got.b.b, got.c.b, got.d.b) == (0, 0, 0, 0),
   "angle 6 computes the B-axis conjugate incl. new A component")

# Angle 12: old placeholder was F=G=H=0 (silent zero) -- must fault.
core = make_core()
a_field, b_field = qldi_a_b(99, 98, 97, 96)
core.load([word("QLDI", r1=2, a=a_field, b=b_field)])
core.run()
poison_before = repr(core.qregs[2])
raised = False
core.load([word("ROTC", r1=2, r2=2, a=12)])
try:
    core.run()
except RotcUnverifiedAngleError:
    raised = True
ok(raised, "angle 12 raises RotcUnverifiedAngleError")
ok(repr(core.qregs[2]) == poison_before,
   "angle 12 leaves destination register QR2 completely untouched (no silent zero)")

# Angle 63: top of the 6-bit field -- must fault, not KeyError or crash.
core = make_core()
a_field, b_field = qldi_a_b(1, 1, 1, 1)
core.load([word("QLDI", r1=3, a=a_field, b=b_field)])
core.run()
raised = False
core.load([word("ROTC", r1=3, r2=3, a=63)])
try:
    core.run()
except RotcUnverifiedAngleError:
    raised = True
ok(raised, "angle 63 raises RotcUnverifiedAngleError (not KeyError/crash)")

print(f"\n{passed} passed, {failed} failed")
if failed:
    print("FAIL")
    sys.exit(1)
else:
    print("PASS")
    sys.exit(0)
