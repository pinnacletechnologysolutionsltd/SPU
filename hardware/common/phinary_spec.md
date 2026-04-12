Phinary Packed Format and Chirality Spec

Overview
--------
This document specifies the packed phinary encoding used by SPU-4 research modules and the canonical folding/addition semantics ("phinary"). The goal is a single authoritative definition shared by RTL, VM, assembler and intrinsics plus a small golden reference implementation.

Bit layout / encoding
---------------------
- Packed word width: W bits (parameterizable).
- Integer component: lower INT_BITS bits (bits [INT_BITS-1:0]).
- Surd component: upper SURD_BITS = W - INT_BITS bits (bits [W-1:INT_BITS]).
- Packed value representation: Packed = (SURD << INT_BITS) | INT
  where SURD and INT are non-negative integers.

Defaults and constants
----------------------
- Default LAMINAR_THR = 10 (packed units).
  - The constant "10" (decimal) is an empirical folding constant used by
    ladder/seed logic. For the 4-bit toy adder (INT_BITS=2) the LAMINAR_THR = 10.
  - For parameterized designs, choose LAMINAR_THR as a packed-unit threshold
    appropriate to the width/scale of the adder; commonly 10 for toy tests,
    or a scaled value if required by higher-level semantics.

Addition / folding semantics (canonical)
----------------------------------------
Given two packed phinary words A and B (width W, INT_BITS):
1. Extract integer and surd components:
     int_A  = A & ((1<<INT_BITS)-1)
     int_B  = B & ((1<<INT_BITS)-1)
     surd_A = (A >> INT_BITS) & ((1<<SURD_BITS)-1)
     surd_B = (B >> INT_BITS) & ((1<<SURD_BITS)-1)
2. Compute partial sums:
     int_sum  = int_A + int_B
     surd_sum = surd_A + surd_B
3. Compose combined scalar:
     sum_val = (surd_sum << INT_BITS) + int_sum
4. Compare to threshold:
     if sum_val > LAMINAR_THR then overflow = true else overflow = false
5. On overflow (sum_val > LAMINAR_THR):
   - Canonical mode (chirality == 0):
       void_state := not void_state
       out        := (sum_val - LAMINAR_THR) & ((1<<W)-1)
   - Chiral mode (chirality == 1):
       new_int := (int_sum + 1) & ((1<<INT_BITS)-1)
       new_surd := surd_sum & ((1<<SURD_BITS)-1)
       out := (new_surd << INT_BITS) | new_int
       void_state unchanged
6. If no overflow: out := sum_val & ((1<<W)-1) and void_state unchanged.

Reset semantics
---------------
- void_state is a single-bit state tied to the adder instance. On reset it
  MUST be cleared to 0.

Implementation notes
--------------------
- All arithmetic is unsigned for packing/folding. Signed semantics (Q(√3))
  live at higher software/hardware layers; this packing is an orthogonal
  representation used by seed/ladder logic.
- Masking to W bits is required when writing outputs back to registers / nets.
- Use parameterized LAMINAR_THR = 10 (packed units) by default; adjust for
  board-specific scaling or higher-level semantics.

Golden vectors (4-bit toy, INT_BITS=2)
--------------------------------------
- Example: A=0b1111, B=0b1111
  int_sum = 3+3 = 6 ; surd_sum = 3+3 = 6
  tb_sumv = {surd_sum[1:0], int_sum[1:0]} = 0b1010 (decimal 10)
  since tb_sumv == 10 → no overflow (compare is >)
- Example thresholding and chirality behaviour demonstrated in the
  accompanying software golden reference (software/tools/phinary_ref.py).

Testing
-------
- The reference implementation (phinary_ref.py) is the canonical software
  oracle. Use it to generate unit tests for the RTL chiral_phinary_adder
  and chiral_phinary_adder_param modules.

Files
-----
- software/tools/phinary_ref.py  — Python golden reference & test vectors
- hardware/common/phinary_spec.md — this file (authoritative spec)

Notes
-----
- This spec intentionally keeps the packing/folding rules minimal and
  deterministic so they can be mirrored precisely in RTL and VM.
- Any change to LAMINAR_THR or bit ordering must be coordinated between
  RTL, VM and intrinsics before merging.
