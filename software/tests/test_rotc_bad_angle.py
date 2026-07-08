#!/usr/bin/env python3
"""ROTC bad-angle fault test — VM side of the "don't corrupt the manifold"
fix (2026-07-09). Angles beyond ROTC_MAX_VERIFIED_ANGLE (5) must raise
RotcUnverifiedAngleError and leave the destination register completely
untouched, matching the RTL fault added in spu13_core.v (see the
ROTC_MAX_VERIFIED_ANGLE localparam there for the matching hardware gate,
and hardware/tests/spu13/spu13_core_rotc_opcode_tb.v for the RTL-side
proof of the same property).

Why angles 6+ are refused rather than computed:
  - Angles 6-11: the RTL applies a genuine axis permutation
    (spu_quadray_permute) that this VM never implemented -- VM and RTL
    would silently disagree if these were ever dispatched.
  - Angles 12-33 (removed 2026-07-09): were literal F=G=H=0 placeholder
    entries that would have silently zeroed the destination's B/C/D.
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

# Valid boundary: angle 5 must NOT raise.
core = make_core()
a_field, b_field = qldi_a_b(1, 2, 3, 4)
core.load([
    word("QLDI", r1=1, a=a_field, b=b_field),
    word("ROTC", r1=2, r2=1, a=5),
])
raised = False
try:
    core.run()
except RotcUnverifiedAngleError:
    raised = True
ok(not raised, "angle 5 (boundary, valid) does not raise")

# Angle 6: real RTL permutation logic the VM doesn't implement -- must fault.
core = make_core()
a_field, b_field = qldi_a_b(50, 51, 52, 53)
core.load([word("QLDI", r1=1, a=a_field, b=b_field)])
core.run()
poison_before = repr(core.qregs[1])
core2_program_ok = True
raised = False
core.load([word("ROTC", r1=1, r2=1, a=6)])
try:
    core.run()
except RotcUnverifiedAngleError:
    raised = True
ok(raised, "angle 6 raises RotcUnverifiedAngleError")
ok(repr(core.qregs[1]) == poison_before,
   "angle 6 leaves destination register QR1 completely untouched")

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
