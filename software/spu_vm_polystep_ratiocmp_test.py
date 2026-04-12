#!/usr/bin/env python3
"""
spu_vm_polystep_ratiocmp_test.py — Unit test for POLY_STEP + RATIO_CMP in SPU VM

Runs two small scenarios under the Python VM:
 1) POLY_STEP then copy registers and RATIO_CMP -> expect equality (result 0)
 2) Same but increment compare numerator -> expect left < right (result -1)

Exits 0 on PASS, non-zero on FAIL.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from spu_vm import SPUCore, OPCODES, RationalSurd


def word(op: str, r1=0, r2=0, a=0, b=0) -> int:
    oc = OPCODES[op]
    return ((oc & 0xFF) << 56) | ((r1 & 0xFF) << 48) | ((r2 & 0xFF) << 40) \
         | ((a  & 0xFFFF) << 24) | ((b  & 0xFFFF) << 8)


def make_core() -> SPUCore:
    return SPUCore(verbose=False, max_steps=500)


def run_equal_test() -> bool:
    c = make_core()
    prog = [
        word("LD", r1=2, a=0, b=0),               # R2 := x = 0 (Q32)
        word("POLY_STEP", r1=0, r2=2, a=0, b=0),  # POLY_STEP R0,R2 -> R0=num, R1=den
        word("LD", r1=10, a=0, b=0),              # R10 := 0
        word("ADD", r1=10, r2=0),                 # R10 := R0
        word("LD", r1=11, a=0, b=0),              # R11 := 0
        word("ADD", r1=11, r2=1),                 # R11 := R1
        word("RATIO_CMP", r1=0, r2=10),           # compare R0/R1 with R10/R11 -> expect 0
    ]
    c.load(prog)
    c.run()
    return c.regs[0].a == 0


def run_inequal_test() -> bool:
    c = make_core()
    prog = [
        word("LD", r1=2, a=0, b=0),               # R2 := x = 0 (Q32)
        word("POLY_STEP", r1=0, r2=2, a=0),       # POLY_STEP R0,R2 -> R0=num, R1=den
        word("LD", r1=10, a=0, b=0),              # R10 := 0
        word("ADD", r1=10, r2=0),                 # R10 := R0
        word("LD", r1=11, a=0, b=0),              # R11 := 0
        word("ADD", r1=11, r2=1),                 # R11 := R1
        word("LD", r1=12, a=1, b=0),              # R12 := 1
        word("ADD", r1=10, r2=12),                # R10 := R10 + 1  (increase compare numerator)
        word("RATIO_CMP", r1=0, r2=10),           # expect -1 (left < right)
    ]
    c.load(prog)
    c.run()
    return c.regs[0].a == -1


if __name__ == '__main__':
    ok1 = run_equal_test()
    ok2 = run_inequal_test()
    if ok1 and ok2:
        print("POLY_STEP+RATIO_CMP tests: PASS")
        sys.exit(0)
    else:
        print("POLY_STEP+RATIO_CMP tests: FAIL")
        if not ok1:
            print("  equality test failed")
        if not ok2:
            print("  inequality test failed")
        sys.exit(2)
