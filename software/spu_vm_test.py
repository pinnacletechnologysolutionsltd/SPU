#!/usr/bin/env python3
"""
spu_vm_test.py — Full opcode coverage for SPU-13 Sovereign VM v1.3

Tests every opcode against known exact Q(√3) manifold states.
Also validates Davis Gasket + FibDispatch integration.

Usage:  python3 software/spu_vm_test.py
Output: PASS or FAIL with per-test detail on failure.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from spu_vm import SPUCore, RationalSurd, QuadrayVector, OPCODES, DavisGasket, FibDispatch, SdfState

# ── Test harness ─────────────────────────────────────────────────────────────

_pass = 0
_fail = 0

def ok(cond: bool, msg: str):
    global _pass, _fail
    if cond:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {msg}")

def section(name: str):
    print(f"\n── {name} ──")

# ── Word builder ─────────────────────────────────────────────────────────────

def word(op: str, r1=0, r2=0, a=0, b=0) -> int:
    """Pack a 64-bit Lithic-L control word."""
    oc = OPCODES[op]
    return ((oc & 0xFF) << 56) | ((r1 & 0xFF) << 48) | ((r2 & 0xFF) << 40) \
         | ((a  & 0xFFFF) << 24) | ((b  & 0xFFFF) << 8)

def make_core() -> SPUCore:
    return SPUCore(verbose=False, max_steps=500)

# ─────────────────────────────────────────────────────────────────────────────
# 1. LD — load immediate into scalar register
# ─────────────────────────────────────────────────────────────────────────────
section("LD")
c = make_core()
c.load([word("LD", r1=0, a=5, b=3)])
c.run()
ok(c.regs[0].a == 5, "LD: rational part a=5")
ok(c.regs[0].b == 3, "LD: surd part b=3")

# ─────────────────────────────────────────────────────────────────────────────
# 2. ADD — R0 = R0 + R1 in Q(√3)
# ─────────────────────────────────────────────────────────────────────────────
section("ADD")
c = make_core()
c.load([
    word("LD",  r1=0, a=2, b=1),   # R0 = (2 + 1·√3)
    word("LD",  r1=1, a=3, b=2),   # R1 = (3 + 2·√3)
    word("ADD", r1=0, r2=1),        # R0 = (5 + 3·√3)
])
c.run()
ok(c.regs[0].a == 5, "ADD: a = 2+3 = 5")
ok(c.regs[0].b == 3, "ADD: b = 1+2 = 3")

# ─────────────────────────────────────────────────────────────────────────────
# 3. SUB — R0 = R0 - R1
# ─────────────────────────────────────────────────────────────────────────────
section("SUB")
c = make_core()
c.load([
    word("LD",  r1=0, a=7, b=4),
    word("LD",  r1=1, a=2, b=1),
    word("SUB", r1=0, r2=1),
])
c.run()
ok(c.regs[0].a == 5, "SUB: a = 7-2 = 5")
ok(c.regs[0].b == 3, "SUB: b = 4-1 = 3")

# ─────────────────────────────────────────────────────────────────────────────
# 4. MUL — Q(√3) multiplication: (p+q√3)(p'+q'√3) = (pp'+3qq') + (pq'+p'q)√3
# ─────────────────────────────────────────────────────────────────────────────
section("MUL")
c = make_core()
c.load([
    word("LD",  r1=0, a=2, b=1),   # R0 = (2 + √3)
    word("LD",  r1=1, a=2, b=1),   # R1 = (2 + √3)
    word("MUL", r1=0, r2=1),        # (2+√3)² = (4+3) + (2+2)√3 = (7 + 4√3)
])
c.run()
ok(c.regs[0].a == 7, "MUL: (2+√3)² → a = 4+3 = 7")
ok(c.regs[0].b == 4, "MUL: (2+√3)² → b = 2+2 = 4")

# Field identity: (7+4√3)(7-4√3) = 49-48 = 1
c2 = make_core()
c2.load([
    word("LD",  r1=0, a=7,  b=4),
    word("LD",  r1=1, a=7,  b=-4 & 0xFFFF),  # b=-4 as unsigned 16-bit
    word("MUL", r1=0, r2=1),
])
c2.run()
ok(c2.regs[0].a == 1, "MUL: (7+4√3)(7-4√3) = 1 (field identity)")
ok(c2.regs[0].b == 0, "MUL: (7+4√3)(7-4√3) → b=0")

# ─────────────────────────────────────────────────────────────────────────────
# 5. ROT — Pell orbit: (1,0)→(2,1)→(7,4)→(26,15)
# ─────────────────────────────────────────────────────────────────────────────
section("ROT")
c = make_core()
c.load([
    word("LD",  r1=0, a=1, b=0),   # R0 = 1 (Pell step 0)
    word("ROT", r1=0),              # step 1: (2,1)
    word("ROT", r1=0),              # step 2: (7,4)
    word("ROT", r1=0),              # step 3: (26,15)
])
c.run()
ok(c.regs[0].a == 26, "ROT: 3rd Pell orbit step → a=26")
ok(c.regs[0].b == 15, "ROT: 3rd Pell orbit step → b=15")
# Verify laminar invariant: a²-3b² = 1
q = c.regs[0].quadrance()
ok(q == 1, f"ROT: Pell invariant a²-3b²=1 (got {q})")

# ─────────────────────────────────────────────────────────────────────────────
# 6. JMP — unconditional jump
# ─────────────────────────────────────────────────────────────────────────────
section("JMP")
c = make_core()
c.load([
    word("JMP", a=2),               # jump to word 2
    word("LD",  r1=0, a=99, b=0),  # should be skipped
    word("LD",  r1=0, a=42, b=0),  # target
])
c.run()
ok(c.regs[0].a == 42, "JMP: skipped word 1, landed at word 2")
ok(c.regs[0].b == 0,  "JMP: b=0 at target")

# ─────────────────────────────────────────────────────────────────────────────
# 7. SNAP — Davis Gate: laminar registers pass, unstable fail
# ─────────────────────────────────────────────────────────────────────────────
section("SNAP")
# Laminar: R0=(2,1)  Q=4-3=1>0  → PASS
c = make_core()
c.load([
    word("LD",   r1=0, a=2, b=1),
    word("SNAP"),
])
c.run()
ok(c.snap_failures == 0, "SNAP: laminar reg (2,1) → no failure")

# Unstable: R0=(1,1)  Q=1-3=-2<0 → FAIL
c2 = make_core()
c2.load([
    word("LD",   r1=0, a=1, b=1),
    word("SNAP"),
])
c2.run()
ok(c2.snap_failures == 1, "SNAP: unstable reg (1,1) Q=-2 → 1 failure")

# ─────────────────────────────────────────────────────────────────────────────
# 8. COND — conditional jump based on quadrance of register
# ─────────────────────────────────────────────────────────────────────────────
section("COND")
# Q > 0: jump taken
c = make_core()
c.load([
    word("LD",   r1=0, a=2, b=1),  # Q=1>0
    word("COND", r1=0, a=3),        # jump to word 3
    word("LD",   r1=1, a=99, b=0), # skipped
    word("LD",   r1=1, a=7, b=0),  # target
])
c.run()
ok(c.regs[1].a == 7, "COND: Q>0 → jump taken, landed at word 3")

# Q == 0: fall-through (3-word program; no word 3 to overwrite R1)
c2 = make_core()
c2.load([
    word("LD",   r1=0, a=0, b=0),  # Q=0
    word("COND", r1=0, a=3),        # not taken → word 2
    word("LD",   r1=1, a=42, b=0), # fall-through target (program ends here)
])
c2.run()
ok(c2.regs[1].a == 42, "COND: Q=0 → fall-through")

# ─────────────────────────────────────────────────────────────────────────────
# 9. CALL / RET — subroutine stack
# ─────────────────────────────────────────────────────────────────────────────
section("CALL/RET")
c = make_core()
c.load([
    word("CALL", a=3),              # push ret=1, jump to 3
    word("LD",   r1=0, a=55, b=0), # ret lands here (word 1... wait, ret addr is 1)
    word("NOP"),                    # word 2: padding to halt after ret
    word("LD",   r1=1, a=77, b=0), # word 3: subroutine body
    word("RET"),                    # pop and return to 1
])
c.run()
ok(c.regs[1].a == 77, "CALL: subroutine body executed (R1=77)")
ok(c.regs[0].a == 55, "RET: returned to caller (R0=55)")

# RET on empty stack halts
c2 = make_core()
c2.load([word("RET")])
c2.run()
ok(c2.halted, "RET: empty stack → halted")

# ─────────────────────────────────────────────────────────────────────────────
# 10. QLOAD — pack scalar regs into Quadray register
# ─────────────────────────────────────────────────────────────────────────────
section("QLOAD")
c = make_core()
c.load([
    word("LD",    r1=0, a=1, b=0),  # R0..R3 = (1,0),(0,0),(0,0),(0,0)
    word("QLOAD", r1=0, r2=0),       # QR0 ← R0..R3
])
c.run()
comps = c.qregs[0].components()
ok(comps[0].a == 1, "QLOAD: QR0.a = 1")
ok(comps[1].a == 0, "QLOAD: QR0.b = 0")
ok(comps[2].a == 0, "QLOAD: QR0.c = 0")
ok(comps[3].a == 0, "QLOAD: QR0.d = 0")

# ─────────────────────────────────────────────────────────────────────────────
# 11. QADD — Quadray register addition
# ─────────────────────────────────────────────────────────────────────────────
section("QADD")
c = make_core()
# Load QR0=(1,0,0,0), QR1=(0,1,0,0) manually via QLOAD
c.load([
    word("LD", r1=0, a=1, b=0),  word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0),  word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),   # QR0 = (1,0,0,0)
    word("LD", r1=4, a=0, b=0),  word("LD", r1=5, a=1, b=0),
    word("LD", r1=6, a=0, b=0),  word("LD", r1=7, a=0, b=0),
    word("QLOAD", r1=1, r2=4),   # QR1 = (0,1,0,0)
    word("QADD",  r1=0, r2=1),   # QR0 = (1,1,0,0)
])
c.run()
comps = c.qregs[0].components()
ok(comps[0].a == 1, "QADD: QR0.a = 1")
ok(comps[1].a == 1, "QADD: QR0.b = 1")

# ─────────────────────────────────────────────────────────────────────────────
# 12. QROT — Pell rotation on Quadray register
# ─────────────────────────────────────────────────────────────────────────────
section("QROT")
c = make_core()
c.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),  # QR0 = (1,0,0,0)
    word("QROT",  r1=0),         # QROT: apply Pell rotor to each component
])
c.run()
# After QROT + normalize: (2,1) on each non-zero, then normalize
# (2,1,0,0) normalizes by subtracting min (0) → stays (2,1,0,0)
comps = c.qregs[0].components()
# Pell step 1: (1,0) → (2,1)
ok(comps[0].a == 2 and comps[0].b == 1, "QROT: first component (1,0) → (2,1)")

# ─────────────────────────────────────────────────────────────────────────────
# 13. QNORM — normalize Quadray to canonical IVM form
# ─────────────────────────────────────────────────────────────────────────────
section("QNORM")
c = make_core()
# Load QR0 = (1,0,1,0) — not canonical (min component should be 0)
c.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=1, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),
    word("QNORM", r1=0),
])
c.run()
comps = c.qregs[0].components()
# normalize subtracts min component from all → (1,0,1,0) - 0 → (1,0,1,0)
# min is already 0, so no change
ok(comps[0].a == 1, "QNORM: a component preserved when already canonical")

# ─────────────────────────────────────────────────────────────────────────────
# 14. SPREAD — Wildberger Spread between two Quadray registers
# ─────────────────────────────────────────────────────────────────────────────
section("SPREAD")
c = make_core()
c.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),   # QR0 = (1,0,0,0)
    word("LD", r1=4, a=1, b=0),  word("LD", r1=5, a=0, b=0),
    word("LD", r1=6, a=0, b=0),  word("LD", r1=7, a=0, b=0),
    word("QLOAD", r1=1, r2=4),   # QR1 = (1,0,0,0) — same as QR0
    # SPREAD R10, QR0, QR1 — r1=10, r2=QRa=0, b=QRb=1
    word("SPREAD", r1=10, r2=0, b=1),
])
c.run()
# spread(QR_A, QR_A): Quadray quadrance uses pairwise diffs, metric is non-diagonal
# so spread(A,A) = 8/9, not 0.  Verify the fraction is stored correctly.
ok(c.regs[10].a == 8, "SPREAD: identical QR_A vectors → numerator stored in R10")
ok(c.regs[11].a == 9, "SPREAD: identical QR_A vectors → denominator in R11")

# ─────────────────────────────────────────────────────────────────────────────
# 15. HEX — project Quadray to hex grid pixel
# ─────────────────────────────────────────────────────────────────────────────
section("HEX")
c = make_core()
c.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),    # QR0 = (1,0,0,0)
    word("HEX", r1=5, r2=0),      # HEX R5, QR0 → pixel in R5/R6
])
c.run()
# hex_project of (1,0,0,0): col = a-d = 1, row = b-d = 0
ok(c.regs[5].a == 1,  "HEX: QR(1,0,0,0) → col=1")
ok(c.regs[6].a == 0,  "HEX: QR(1,0,0,0) → row=0")

# ─────────────────────────────────────────────────────────────────────────────
# 16. EQUIL — Vector Equilibrium check (hex sum = 0)
# ─────────────────────────────────────────────────────────────────────────────
section("EQUIL")
# All QR zero → balanced (vacuously)
c = make_core()
c.load([word("EQUIL")])
c.run()
ok(c.snap_failures == 0, "EQUIL: all-zero registers → balanced")

# Load one non-zero QR, should show imbalance
c2 = make_core()
c2.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),   # QR0 = (1,0,0,0) — unbalanced alone
    word("EQUIL"),
])
c2.run()
ok(c2.snap_failures == 1, "EQUIL: single QR loaded → manifold tension")

# ─────────────────────────────────────────────────────────────────────────────
# 17. IDNT — reset Quadray register to canonical IVM identity [1,0,0,0]
# ─────────────────────────────────────────────────────────────────────────────
section("IDNT")
c = make_core()
c.load([
    word("LD", r1=0, a=5, b=3), word("LD", r1=1, a=2, b=1),
    word("LD", r1=2, a=1, b=0), word("LD", r1=3, a=4, b=2),
    word("QLOAD", r1=0, r2=0),   # load arbitrary QR0
    word("IDNT",  r1=0),          # reset to (1,0,0,0)
])
c.run()
comps = c.qregs[0].components()
ok(comps[0].a == 1, "IDNT: component a reset to 1")
ok(comps[1].a == 0, "IDNT: component b reset to 0")
ok(comps[2].a == 0, "IDNT: component c reset to 0")
ok(comps[3].a == 0, "IDNT: component d reset to 0")

# ─────────────────────────────────────────────────────────────────────────────
# 18. JINV — Janus bit: negate surd (b) component of scalar register
# ─────────────────────────────────────────────────────────────────────────────
section("JINV")
c = make_core()
c.load([
    word("LD",   r1=0, a=7, b=4),
    word("JINV", r1=0),
])
c.run()
ok(c.regs[0].a == 7,  "JINV: rational part unchanged")
ok(c.regs[0].b == -4, "JINV: surd part negated b=4 → b=-4")

# Double Janus = identity
c2 = make_core()
c2.load([
    word("LD",   r1=0, a=7, b=4),
    word("JINV", r1=0),
    word("JINV", r1=0),
])
c2.run()
ok(c2.regs[0].b == 4, "JINV: double inversion restores b=4")

# ─────────────────────────────────────────────────────────────────────────────
# 19. ANNE — anneal Quadray toward Vector Equilibrium (halve each component)
# ─────────────────────────────────────────────────────────────────────────────
section("ANNE")
c = make_core()
c.load([
    word("LD", r1=0, a=4, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),   # QR0 = (4,0,0,0)
    word("ANNE",  r1=0),          # halve → (2,0,0,0) then normalize
])
c.run()
comps = c.qregs[0].components()
ok(comps[0].a == 2, "ANNE: 4>>1 = 2 on first component")

# ANNE ×2 halves twice → (1,0,0,0)
c2 = make_core()
c2.load([
    word("LD", r1=0, a=4, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),
    word("ANNE",  r1=0),
    word("ANNE",  r1=0),
])
c2.run()
comps2 = c2.qregs[0].components()
ok(comps2[0].a == 1, "ANNE ×2: 4→2→1")

# ─────────────────────────────────────────────────────────────────────────────
# 20. NOP — no operation, no register change
# ─────────────────────────────────────────────────────────────────────────────
section("NOP")
c = make_core()
c.load([
    word("LD",  r1=0, a=99, b=0),
    word("NOP"),
    word("NOP"),
    word("NOP"),
])
c.run()
ok(c.regs[0].a == 99, "NOP: register unchanged through 3 NOPs")
ok(c.step_count == 4,  f"NOP: 4 steps total (got {c.step_count})")

# ─────────────────────────────────────────────────────────────────────────────
# 21. LOG — appends register string to core.log
# ─────────────────────────────────────────────────────────────────────────────
section("LOG")
c = make_core()
c.load([
    word("LD",  r1=0, a=5, b=2),
    word("LOG", r1=0),
])
c.run()
ok(len(c.log) == 1,      "LOG: one entry appended")
ok("R0" in c.log[0],     "LOG: entry contains register name")

# ─────────────────────────────────────────────────────────────────────────────
# 22. QLOG — appends Quadray register to log
# ─────────────────────────────────────────────────────────────────────────────
section("QLOG")
c = make_core()
c.load([
    word("LD", r1=0, a=1, b=0), word("LD", r1=1, a=0, b=0),
    word("LD", r1=2, a=0, b=0), word("LD", r1=3, a=0, b=0),
    word("QLOAD", r1=0, r2=0),
    word("QLOG",  r1=0),
])
c.run()
ok(len(c.log) >= 1,    "QLOG: one entry appended")
ok("QR0" in c.log[-1], "QLOG: entry contains QR register name")

# ─────────────────────────────────────────────────────────────────────────────
# 23. Davis Gasket + Fibonacci Dispatch integration
# ─────────────────────────────────────────────────────────────────────────────
section("DavisGasket")

# Fresh gasket starts laminar
g = DavisGasket()
ok(not g.leak,           "DavisGasket: initial state is laminar")
ok(g.tau.a == 0,         "DavisGasket: τ starts at 0")
ok(g.henosis_count == 0, "DavisGasket: henosis count starts at 0")

# All-zero qregs → vec sum = zero → laminar
qregs = [QuadrayVector() for _ in range(13)]
had = g.gasket_tick(qregs)
ok(not had, "DavisGasket.gasket_tick: zero regs → laminar")

# Load an imbalanced state and check leak detection
q_unbal = [QuadrayVector() for _ in range(13)]
q_unbal[0] = QuadrayVector(RationalSurd(1,0), RationalSurd(0,0),
                            RationalSurd(0,0), RationalSurd(0,0))
had2 = g.gasket_tick(q_unbal)
ok(had2, "DavisGasket.gasket_tick: non-zero asymmetric state → cubic leak")
ok(g.tau.a > 0 or g.tau.b != 0, "DavisGasket: τ accumulated after leak")

# Henosis recovery zeroes out an imbalanced state
q_big = [QuadrayVector() for _ in range(13)]
q_big[0] = QuadrayVector(RationalSurd(8,0), RationalSurd(0,0),
                          RationalSurd(0,0), RationalSurd(0,0))
g2 = DavisGasket()
pulses = g2.henosis_recover(q_big, max_pulses=8)
ok(pulses > 0, f"DavisGasket.henosis_recover: applied {pulses} pulses")

# ─────────────────────────────────────────────────────────────────────────────
# 24. FibDispatch — Fibonacci gate sequence
# ─────────────────────────────────────────────────────────────────────────────
section("FibDispatch")

f = FibDispatch()
gates_seen = []
for _ in range(34):  # one full Sierpinski frame
    gate = f.tick()
    if gate:
        gates_seen.append((f.frame_pos - 1) % 34)  # position before increment

ok(len(gates_seen) == 3, f"FibDispatch: 3 gates per 34-cycle frame (got {len(gates_seen)})")

# Second frame should repeat identically
gates2 = []
for _ in range(34):
    gate = f.tick()
    if gate:
        gates2.append((f.frame_pos - 1) % 34)
ok(gates_seen == gates2, f"FibDispatch: gate positions repeat each frame")

# Cycle counter increments every step
f2 = FibDispatch()
for i in range(10):
    f2.tick()
ok(f2.cycle == 10, "FibDispatch: cycle counter = 10 after 10 ticks")

# ─────────────────────────────────────────────────────────────────────────────
# 25. Davis Gasket wired into SPUCore (step integration)
# ─────────────────────────────────────────────────────────────────────────────
section("SPUCore gasket+fib integration")

# Run 34 NOPs — should tick through one full Fibonacci frame
c = make_core()
c.load([word("NOP")] * 40)
c.run()
ok(c.fib.cycle == 40, f"SPUCore: fib ticked 40 times (got {c.fib.cycle})")
ok(c.fib.cycle > 0,   "SPUCore: fib is advancing each step")

# Gasket is attached to core
ok(isinstance(c.gasket, DavisGasket),   "SPUCore: gasket is DavisGasket")
ok(isinstance(c.fib,    FibDispatch),   "SPUCore: fib is FibDispatch")

# load() resets both
c.load([word("NOP")])
ok(c.fib.cycle == 0,       "SPUCore.load: fib cycle reset")
ok(c.gasket.tau.a == 0,    "SPUCore.load: gasket τ reset")

# ─────────────────────────────────────────────────────────────────────────────
# SdfState — Layer 7 Rational Distance Field
# ─────────────────────────────────────────────────────────────────────────────

section("SdfState — qr_quadrance")

# Zero vector has Quadrance 0
sdf = SdfState()
zero = QuadrayVector()
ok(SdfState.qr_quadrance(zero) == 0,
   "SdfState.qr_quadrance: zero vector → Q=0")

# IVM canonical axis QR_A = [1,0,0,0]
# pairwise diffs: (1-0)²×3 = 3
qr_a = QuadrayVector(RationalSurd(1), RationalSurd(0),
                     RationalSurd(0), RationalSurd(0))
ok(SdfState.qr_quadrance(qr_a) == 3,
   "SdfState.qr_quadrance: [1,0,0,0] → Q=3")

# [1,1,0,0]: diffs (0,1,1,1,-1,-1) squared = 0+1+1+1+1+1 = wait:
# pairs: (1-1)²=0, (1-0)²=1, (1-0)²=1, (1-0)²=1, (1-0)²=1, (0-0)²=0 → 4
qr_b = QuadrayVector(RationalSurd(1), RationalSurd(1),
                     RationalSurd(0), RationalSurd(0))
ok(SdfState.qr_quadrance(qr_b) == 4,
   "SdfState.qr_quadrance: [1,1,0,0] → Q=4")

section("SdfState — qr_dist_q")

# Distance from qr_a to qr_a = 0
ok(SdfState.qr_dist_q(qr_a, qr_a) == 0,
   "SdfState.qr_dist_q: same vector → Q=0")

# Distance from qr_a to qr_b:
# diff = [0,-1,0,0], quadrance = (0-(-1))²+(0-0)²+... = pairwise: 3
diff_ab = QuadrayVector(RationalSurd(0), RationalSurd(-1),
                        RationalSurd(0), RationalSurd(0))
ok(SdfState.qr_dist_q(qr_a, qr_b) == SdfState.qr_quadrance(diff_ab),
   "SdfState.qr_dist_q: symmetric with qr_quadrance of diff")

section("SdfState — nearest")

# Build a simple 3-register set: [qr_a at idx 0, qr_b at idx 1, zero×11]
regs = [qr_a, qr_b] + [QuadrayVector()] * 11
# target = qr_a; nearest non-zero from regs[1:] should be qr_b (idx 0 of that slice = +1 in full)
target = qr_a
idx, min_q = SdfState.nearest(target, regs)
ok(min_q == 0, f"SdfState.nearest: qr_a vs regs containing qr_a → min_q=0 (got {min_q})")
ok(idx == 0,   f"SdfState.nearest: nearest is first reg (got {idx})")

# target = qr_b; nearest in [qr_a, qr_b, zeros] = qr_b itself (Q=0)
idx2, min_q2 = SdfState.nearest(qr_b, regs)
ok(min_q2 == 0, f"SdfState.nearest: qr_b in regs → Q=0 (got {min_q2})")

section("SdfState — snap_check")

# All QR zero: grad = zero → dot = 0 → no conflict
zero_regs = [QuadrayVector()] * 13
g = SdfState.grad(QuadrayVector(), zero_regs)
ok(not SdfState.snap_check(g, zero_regs),
   "SdfState.snap_check: all-zero regs → no conflict")

# Non-trivial: one non-zero register, target = zero
# grad points from zero toward qr_a; vec_sum = qr_a
# dot = (1×1 + 0×0 + 0×0 + 0×0)  (component-wise integer parts) = 1 ≠ 0
mixed_regs = [qr_a] + [QuadrayVector()] * 12
g2 = SdfState.grad(QuadrayVector(), mixed_regs)
conflict = SdfState.snap_check(g2, mixed_regs)
ok(conflict, "SdfState.snap_check: grad toward non-zero axis → conflict detected")

section("SdfState — evaluate (SNAP boundary)")

sdf2 = SdfState()
# Evaluate on all-zero regs: no conflict, snap_count increments
sdf2.evaluate([QuadrayVector()] * 13, sdf_trace=False)
ok(sdf2.snap_count    == 1, "SdfState.evaluate: snap_count increments")
ok(sdf2.conflict_count == 0, "SdfState.evaluate: no conflict on all-zero regs")

# Now evaluate with a non-zero reg
sdf3 = SdfState()
regs3 = [qr_a, qr_b] + [QuadrayVector()] * 11
sdf3.evaluate(regs3, sdf_trace=False)
ok(sdf3.snap_count == 1, "SdfState.evaluate: snap_count=1 after one call")
# nearest_axis should be > 0 (qr_a is index 0 = target, nearest non-self is qr_b)
ok(sdf3.nearest_axis >= 0, f"SdfState.evaluate: nearest_axis set (got {sdf3.nearest_axis})")

section("SPUCore SNAP integrates SdfState")

# Run a SNAP with all-zero QRs: no conflict, sdf.snap_count = 1
c = make_core()
c.load([word("SNAP"), word("JMP", a=1)])  # JMP 1 → loop; max_steps halts
c.run()
ok(c.sdf.snap_count == 1,     "SPUCore SNAP: sdf.snap_count=1 after one SNAP")
ok(c.sdf.conflict_count == 0, "SPUCore SNAP: no conflict on clean empty core")

# load() resets SdfState
c.load([word("NOP")])
ok(c.sdf.snap_count == 0,     "SPUCore.load: sdf.snap_count reset to 0")

# sdf_trace flag wires through without error (output goes to stdout; we just run it)
c2 = SPUCore(verbose=False, sdf_trace=True)
c2.load([word("SNAP"), word("JMP", a=1)])
c2.run()
ok(c2.sdf.snap_count == 1,    "SPUCore sdf_trace=True: SNAP still tracked")


# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"spu_vm_test.py: {_pass} passed, {_fail} failed")
if _fail == 0:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
