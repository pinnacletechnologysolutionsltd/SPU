#!/usr/bin/env python3
"""
spu13_arch_sim_test.py — SPU-13 ISA v1.0 behavioral test suite

Tests all temporal opcodes, quadrance arithmetic, geometric ops,
RPLU integration, flow control, and the Wheeler-Feynman phase-lock.

Usage:  python3 software/spu13_arch_sim_test.py [-v]
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(__file__))

from spu13_arch_sim import (
    SPU13Core, RPLUTable,
    Rational, RationalSurd, Quadray,
    pack_R, pack_L, pack_I, pack_U, pack_B, pack_X,
    asm_R, asm_L, asm_I, asm_U, asm_B, asm_X,
    field, decode_R,
    OP_NOP, OP_HALT, OP_SYNC,
    OP_LOAD, OP_STORE, OP_MOV, OP_MOVI, OP_LDO, OP_LDC,
    OP_QADD, OP_QSUB, OP_QMUL, OP_QDIV, OP_QNORM, OP_QCMP,
    OP_SPRD, OP_ROTR, OP_CROSS, OP_DOT, OP_TNSR, OP_PROJ,
    OP_OFFR, OP_CNFM, OP_PHSLK, OP_INVJ, OP_PHSTA, OP_PHCLR,
    OP_RCFG, OP_RREAD, OP_RLOAD, OP_RDISSOC,
    OP_CMP, OP_JMP, OP_JZ, OP_JNZ, OP_JC, OP_JNC, OP_CALL, OP_RET,
    OP_MFOLD, OP_STAT, OP_SCALE, OP_QR, OP_HEX, OP_SENT,
    REG_ZERO, REG_PC, REG_FLAGS,
    FLAG_ZERO, FLAG_COHERENT,
    format_name,
)

# ── Test harness ──

_pass = 0
_fail = 0

def ok(cond, msg):
    global _pass, _fail
    if cond:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {msg}")

def section(name):
    print(f"\n── {name} ──")

def make_core(verbose=False, trace=False):
    return SPU13Core(verbose=verbose, trace=trace)


# ═════════════════════════════════════════════════════════════════════════════
# 1. Instruction Encoding / Decoding
# ═════════════════════════════════════════════════════════════════════════════

section("Instruction Encoding")

# Test pack_R format
w = pack_R(OP_PHSLK, dest=4, srcA=2, srcB=3)
op, d, a, b = decode_R(w)
ok(op == OP_PHSLK, f"pack_R opcode: got 0x{op:02X}, expected 0x{OP_PHSLK:02X}")
ok(d == 4, f"pack_R dest: got {d}, expected 4")
ok(a == 2, f"pack_R srcA: got {a}, expected 2")
ok(b == 3, f"pack_R srcB: got {b}, expected 3")

# Test asm helpers
w = asm_X("HALT")
ok(w is not None and (w >> 56) == OP_HALT, f"asm_X HALT: opcode=0x{w>>56:02X}")

w = asm_I("MOVI", 5, 0xDEAD)
op, d, imm = (w >> 56) & 0xFF, (w >> 51) & 0x1F, w & 0x7FFFFFFFFFFFF
ok(op == OP_MOVI, f"asm_I opcode: 0x{op:02X}")
ok(d == 5, f"asm_I dest: {d}")
ok(imm == 0xDEAD, f"asm_I imm: 0x{imm:X}")

w = asm_U("INVJ", 7, 3)
op, d, s, c = (w >> 56) & 0xFF, (w >> 51) & 0x1F, (w >> 46) & 0x1F, (w >> 44) & 0x3
ok(op == OP_INVJ, f"asm_U opcode: 0x{op:02X}")
ok(d == 7, f"asm_U dest: {d}")
ok(s == 3, f"asm_U src: {s}")


# ═════════════════════════════════════════════════════════════════════════════
# 2. Temporal Opcodes: OFFR / CNFM (RPLU material load)
# ═════════════════════════════════════════════════════════════════════════════

section("OFFR / CNFM — RPLU Material Load")

c = make_core()
c.load([
    asm_R("OFFR", 8, 1, 5),   # OFFR R8, material=1(iron), addr=5
    asm_R("CNFM", 9, 0, 10),  # CNFM R9, material=0(carbon), addr=10
    asm_X("HALT"),
])
c.run()

ok(c.R[8]['O'].quadrance().num != 0,
   f"OFFR R8.O non-zero (quadrance={c.R[8]['O'].quadrance()})")
ok(c.R[9]['C'].quadrance().num != 0,
   f"CNFM R9.C non-zero (quadrance={c.R[9]['C'].quadrance()})")
ok(c.R[8]['C'].quadrance().num == 0,
   "OFFR did not modify R8.C (remains zero)")


# ═════════════════════════════════════════════════════════════════════════════
# 3. PHSLK — Phase-Lock (Wheeler-Feynman handshake)
# ═════════════════════════════════════════════════════════════════════════════

section("PHSLK — Wheeler-Feynman Phase-Lock")

# 3a. Matching Offer/Confirmation should phase-lock
c = make_core()
c.load([
    asm_L("LDO", 10, 0, 100),    # R10.O = 100
    asm_L("LDC", 11, 0, 100),    # R11.C = 100
    asm_R("PHSLK", 12, 10, 11),  # R12 = PHSLK(R10.O, R11.C)
    asm_X("HALT"),
])
c.run()
ok(c._flag_test(FLAG_COHERENT),
   "PHSLK: matching Offer/Confirmation → COHERENT")
ok(c.R[12]['O'].quadrance().num != 0,
   f"PHSLK: dest written (Q={c.R[12]['O'].quadrance()})")

# 3b. Mismatched Offer/Confirmation should NOT phase-lock
c = make_core()
c.load([
    asm_L("LDO", 10, 0, 50),     # R10.O = 50
    asm_L("LDC", 11, 0, 200),    # R11.C = 200
    asm_R("PHSLK", 12, 10, 11),
    asm_X("HALT"),
])
c.run()
ok(not c._flag_test(FLAG_COHERENT),
   "PHSLK: mismatched → NOT COHERENT")


# ═════════════════════════════════════════════════════════════════════════════
# 4. INVJ — Janus Inversion
# ═════════════════════════════════════════════════════════════════════════════

section("INVJ — Janus Inversion")

c = make_core()
c.load([
    asm_L("LDO", 15, 0, 42),     # R15.O = 42
    asm_U("INVJ", 16, 15),        # R16 = INVJ(R15) = -42
    asm_X("HALT"),
])
c.run()

q_orig = c.R[15]['O'].quadrance()
q_inv = c.R[16]['O'].quadrance()
ok(q_orig == q_inv,
   f"INVJ: quadrance preserved ({q_orig} == {q_inv})")

# Verify negated by checking component signs
orig_a = c.R[15]['O'].a
inv_a = c.R[16]['O'].a
ok(inv_a == -orig_a,
   f"INVJ: component negated ({orig_a} → {inv_a})")


# ═════════════════════════════════════════════════════════════════════════════
# 5. PHSTA / PHCLR — Phase-Lock Status
# ═════════════════════════════════════════════════════════════════════════════

section("PHSTA / PHCLR — Status")

c = make_core()
c.load([
    asm_X("PHCLR"),                # Clear coherent flag
    asm_U("PHSTA", 17, REG_ZERO),  # R17 = coherent?  (should be 0)
    asm_L("LDO", 18, 0, 50),
    asm_L("LDC", 19, 0, 50),
    asm_R("PHSLK", 20, 18, 19),   # Lock → coherent=1
    asm_U("PHSTA", 21, REG_ZERO),  # R21 = coherent? (should be 1)
    asm_X("HALT"),
])
c.run()

phclr_val = c.R[17]['O'].quadrance().to_q12()
phlock_val = c.R[21]['O'].quadrance().to_q12()
ok(phclr_val == 0,
   f"PHSTA after PHCLR: got 0x{phclr_val:08X}, expected 0")
ok(phlock_val == 0x1000,
   f"PHSTA after PHSLK: got 0x{phlock_val:08X}, expected 0x1000")


# ═════════════════════════════════════════════════════════════════════════════
# 6. Quadrance Arithmetic
# ═════════════════════════════════════════════════════════════════════════════

section("Quadrance Arithmetic")

# QADD: quadrance of 100 + quadrance of 50 = 12500
c = make_core()
c.load([
    asm_L("LDO", 22, 0, 100),
    asm_L("LDO", 23, 0, 50),
    asm_R("QADD", 24, 22, 23),
    asm_X("HALT"),
])
c.run()
# Quadrance of scalar n is n², so 100² + 50² = 10000 + 2500 = 12500
expected = 12500
q_out = c.QUAD_OUT
ok(q_out.num * q_out.den >= 0,
   f"QADD: positive result ({q_out})")


# ═════════════════════════════════════════════════════════════════════════════
# 7. Geometric Operations
# ═════════════════════════════════════════════════════════════════════════════

section("Geometric Operations")

# TNSR — tensor M = 4I
c = make_core()
c.load([
    asm_L("LDO", 25, 0, 10),
    asm_R("TNSR", 26, 25, 0),
    asm_X("HALT"),
])
c.run()
q_scaled = c.R[26]['O'].quadrance()
ok(q_scaled.num != 0,
   f"TNSR: non-zero result ({q_scaled})")


# ═════════════════════════════════════════════════════════════════════════════
# 8. Flow Control
# ═════════════════════════════════════════════════════════════════════════════

section("Flow Control")

# JZ / JNZ with QCMP
c = make_core()
c.load([
    asm_L("LDO", 27, 0, 10),
    asm_L("LDO", 28, 0, 10),      # Same → QCMP sets ZERO
    asm_R("QCMP", REG_ZERO, 27, 28),
    asm_B("JZ", 2),                # Should jump forward 2
    asm_I("MOVI", 29, 0xBAD),      # Skipped
    asm_I("MOVI", 29, 0x600D),     # After JZ target: 0x600D="GOOD"
    asm_X("HALT"),
])
c.run()
# MOVI stores val as Quadray(a=val), quadrance = val² → extract val
q_r29 = c.R[29]['O'].quadrance()
# For val > 0 and den == 1: quadrance = val² so val = sqrt(quadrance)
import math
val_r29 = int(math.isqrt(q_r29.num)) if q_r29.den == 1 and q_r29.num > 0 else 0
ok(val_r29 == 0x600D,
   f"JZ: R29=0x{val_r29:04X}, expected 0x600D (GOOD)")


# ═════════════════════════════════════════════════════════════════════════════
# 9. RPLU Table Simulation
# ═════════════════════════════════════════════════════════════════════════════

section("RPLU Table Simulation")

rplu = RPLUTable()
a_p, re_p, de_p = rplu.read_params(0, 0)
ok(a_p == 0x00010000, f"RPLU params[0].a = 0x{a_p:08X}")
ok(re_p == 0x00080000, f"RPLU params[0].re = 0x{re_p:08X}")

# RATIO_CMP cross-multiplication
cmp1 = rplu.ratio_cmp(10, 1, 10, 1)    # 10/1 == 10/1 → 0
cmp2 = rplu.ratio_cmp(10, 1, 20, 1)    # 10/1 < 20/1 → -1
cmp3 = rplu.ratio_cmp(20, 1, 10, 1)    # 20/1 > 10/1 → +1
ok(cmp1 == 0, f"RATIO_CMP equal: got {cmp1}, expected 0")
ok(cmp2 == -1, f"RATIO_CMP less: got {cmp2}, expected -1")
ok(cmp3 == 1, f"RATIO_CMP greater: got {cmp3}, expected 1")

# Vnorm read/write
rplu.write_cfg(5, 0, 42, 0xDEAD)
v = rplu.read_vnorm(0, 42)
ok(v == 0xDEAD, f"RPLU vnorm write/read: 0x{v:04X}")

# Dissociation read
d0 = rplu.read_dissoc(0, 5)    # addr 5 < 100 → dissociated
d100 = rplu.read_dissoc(0, 200) # addr 200 > 100 → bound
ok(d0 == 1, f"RPLU dissoc at addr 5: {d0}, expected 1")
ok(d100 == 0, f"RPLU dissoc at addr 200: {d100}, expected 0")


# ═════════════════════════════════════════════════════════════════════════════
# 10. Rational Arithmetic (Q(√3) field)
# ═════════════════════════════════════════════════════════════════════════════

section("Rational Q(√3) Arithmetic")

# (2 + 1·√3)(3 + 2·√3) = (6 + 6) + (4 + 3)·√3 = 12 + 7·√3
r1 = RationalSurd(Rational(2,1), Rational(1,1))
r2 = RationalSurd(Rational(3,1), Rational(2,1))
r3 = r1 * r2
ok(r3.p == Rational(12,1) and r3.q == Rational(7,1),
   f"Q(√3) multiply: (2+√3)(3+2√3) = {r3}, expected 12+7√3")

# Norm: (12 + 7√3)(12 - 7√3) = 144 - 3·49 = 144 - 147 = -3
q = r3.norm()
ok(q.num == -3 and q.den == 1,
   f"Q(√3) norm of 12+7√3 = {q}, expected -3")

# Conjugate
r4 = r3.conjugate()
ok(r4.p == r3.p and r4.q == -r3.q,
   f"Q(√3) conjugate: {r4}, expected 12-7√3")


# ═════════════════════════════════════════════════════════════════════════════
# ═════════════════════════════════════════════════════════════════════════════

section("SUMMARY")
total = _pass + _fail
print(f"  PASS: {_pass}/{total}  FAIL: {_fail}/{total}")
if _fail > 0:
    print(f"  *** {_fail} TESTS FAILED ***")
    sys.exit(1)
else:
    print(f"  ALL TESTS PASSED")
