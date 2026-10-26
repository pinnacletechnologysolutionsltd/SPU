"""
test_regen_asm.py — Stage A assembler legality tests
(contract_regen_stageA_2026-08-20.md §4.2).

Valid / too-short / too-long / orphan / unterminated blocks, ineligible
mnemonics inside a block, and the REGEN P1_A = K encoding.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'tools'))

from spu13_asm import assemble, AssemblyError

FAILS = 0


def expect_ok(label, src, want_p1a=None):
    global FAILS
    words, _ = assemble(src, fold=False)
    if want_p1a is not None:
        last = words[-1]
        assert (last >> 24) & 0xFFFF == want_p1a, \
            f"REGEN P1_A = {(last >> 24) & 0xFFFF}, expected {want_p1a}"
    print(f"PASS: {label} ({len(words)} words)")
    return words


def expect_err(label, src, needle):
    global FAILS
    try:
        assemble(src, fold=False)
        print(f"FAIL: {label} did not raise")
        FAILS += 1
    except AssemblyError as e:
        if needle.lower() in str(e).lower():
            print(f"PASS: {label} ({e})")
        else:
            print(f"FAIL: {label} raised wrong error: {e}")
            FAILS += 1


VALID = """.block K=2
QLDI QR0, 1, 2, 3, 4
QLDI QR1, 4, 3, 2, 1
.regen"""
expect_ok("valid K=2 block assembles; REGEN P1_A=2", VALID, want_p1a=2)

K4 = """.block K=4
QLDI QR0, 1, 0, 0, 0
QSUB QR1, QR0, QR0
ROTC QR2, QR1, 1
IDNT QR3
.regen"""
expect_ok("valid K=4 block (QLDI+QSUB+ROTC+IDNT) assembles", K4, want_p1a=4)

expect_err("K=2 with 1 op -> too-short", """.block K=2
QLDI QR0, 1, 0, 0, 0
.regen""", "K=2")

expect_err("K=2 with 3 ops -> too-long", """.block K=2
QLDI QR0, 1, 0, 0, 0
QLDI QR1, 1, 0, 0, 0
QLDI QR2, 1, 0, 0, 0
.regen""", "K=2")

expect_err("K=4 with 3 eligible ops -> too-short", """.block K=4
QLDI QR0, 1, 0, 0, 0
QSUB QR1, QR0, QR0
ROTC QR2, QR1, 1
.regen""", "K=4")

expect_err("K=4 with 5 eligible ops -> too-long", """.block K=4
QLDI QR0, 1, 0, 0, 0
QSUB QR1, QR0, QR0
ROTC QR2, QR1, 1
IDNT QR3
DELTA QR4, 1, 2, 4
.regen""", "K=4")

expect_err("orphan .regen", """QLDI QR0, 1, 0, 0, 0
.regen""", "orphan")

expect_err("unterminated .block", """.block K=2
QLDI QR0, 1, 0, 0, 0
QLDI QR1, 1, 0, 0, 0""", "unterminated")

expect_err("ineligible LD inside block", """.block K=1
LD R0, 1, 0
.regen""", "not block-eligible")

expect_err("nested .block", """.block K=2
QLDI QR0, 1, 0, 0, 0
.block K=1
QLDI QR1, 1, 0, 0, 0
.regen""", "nested")

# REGEN with a labelled target inside the block must not break label counting
LAB = """start:
.block K=2
QLDI QR0, 1, 0, 0, 0
QLDI QR1, 1, 0, 0, 0
.regen
JMP start"""
expect_ok("label before block + JMP back assembles", LAB)

# blocks may appear multiple times; counters reset per .regen
TWO = """.block K=1
QLDI QR0, 1, 0, 0, 0
.regen
.block K=1
QLDI QR1, 1, 0, 0, 0
.regen"""
words = expect_ok("two consecutive K=1 blocks", TWO)
assert (words[-1] >> 24) & 0xFFFF == 1 and (words[1] >> 24) & 0xFFFF == 1, \
    "both REGENs carry P1_A=1"
print("PASS: both REGENs carry P1_A=1")

if FAILS:
    print(f"\ntest_regen_asm: FAIL ({FAILS} errors)")
    sys.exit(1)
print("\ntest_regen_asm: PASS")
