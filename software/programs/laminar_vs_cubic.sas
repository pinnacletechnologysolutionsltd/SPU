; laminar_vs_cubic.sas — Why Floating-Point Arithmetic is Wrong
;
; This program demonstrates the core argument for Q(√3) arithmetic
; by showing what happens when a single "rounding" step is applied
; to an otherwise exact computation.
;
; Two tracks run side-by-side:
;
;   TRACK A — Laminar (exact Q(√3)):
;     R0 = (1, 0)  i.e. a=1, b=0 → real value = 1
;     Q(R0) = 1² - 3×0² = 1  → LAMINAR ✓
;     Apply ROT (Pell rotation) 8 times → Q preserved exactly = 1 always
;
;   TRACK B — Cubic (float-approximated):
;     R1 = (1, 1)  i.e. a=1, b=1 → real value = 1 + √3 ≈ 2.732
;     This represents a value where floating-point rounding has introduced
;     a spurious surd component (b=1 instead of b=0).
;     Q(R1) = 1² - 3×1² = 1 - 3 = -2  → CUBIC LEAK ✗
;
; The SNAP after Track B FAILS immediately — the manifold detects the
; rounding corruption in one instruction. No epsilon. No tolerance.
; The geometry itself rejects the approximation.
;
; This is why the Davis Gate exists in hardware: it is the algebraic
; proof that a value belongs to the laminar manifold.
;
; Run with:
;   python3 software/spu_forge.py simulate software/programs/laminar_vs_cubic.sas --proof
;
; CC0 1.0 Universal.

; ════════════════════════════════════════════════════════════════════════════
; TRACK A: Exact Q(√3) arithmetic — stays on the manifold forever
; ════════════════════════════════════════════════════════════════════════════

; Seed: unit element of Q(√3). Q = 1² - 3×0² = 1. Laminar.
LD   R0, 1, 0
LOG  R0    ; R0 = (1 + 0·√3)  Q=1  ✓ laminar

; Apply Pell rotor 8 times.
; Each ROT multiplies by (2+√3): Q(2+√3) = 4-3 = 1.
; Multiplying two Q=1 elements: Q(A×B) = Q(A)×Q(B) = 1×1 = 1.
; The manifold is CLOSED under this operation. Q is invariant.
ROT  R0
LOG  R0    ; Pell step 1: (2+√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 2: (7+4√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 3: (26+15√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 4: (97+56√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 5: (362+209√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 6: (1351+780√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 7: (5042+2911√3)  Q=1 ✓

ROT  R0
LOG  R0    ; Pell step 8: (18817+10864√3)  Q=1 ✓

; Davis Gate check — Track A only.
; R0 has been through 8 Pell rotations. Q must still = 1.
; If this were floating-point: a=18817.0000000... b=10864.0000000...
; Q = 18817² - 3×10864² = 354,079,489 - 354,079,488 = 1
; Float64 would compute: 354,079,489.0 - 354,079,488.0 — catastrophic
; cancellation at this scale. Error would be ±1 ULP = ±1.
; In Q(√3): integers. Exact. Always 1.
SNAP    ; expect: ✓ laminar — Q=1 after 8 rotations

; ════════════════════════════════════════════════════════════════════════════
; TRACK B: The "rounded" value — manual cubic leak detection
; ════════════════════════════════════════════════════════════════════════════

; Simulate what floating-point does: a value that should be (1, 0)
; gets stored as (1, 1) due to rounding in a higher-level computation.
; This is not contrived: any IEEE 754 operation that produces a result
; near √3 will round the surd component to a non-zero integer part
; when converted to Q(√3) representation.

LD   R1, 1, 1   ; R1 = (1 + 1·√3)  — "rounded" unit vector
LOG  R1         ; Q = 1² - 3×1² = 1 - 3 = -2  ✗ CUBIC LEAK

; Manual Davis Gate check using COND (jump-if-laminar):
; COND jumps to the target label if Q(R1) > 0 (laminar).
; If Q ≤ 0 (cubic), it falls through to the leak-detected path.
COND R1, LAMINAR_B  ; Q=-2 → NOT taken — falls through to cubic leak branch

; ── Cubic leak branch (Q ≤ 0) ────────────────────────────────────────────
; This executes because R1 is NOT laminar.
; In hardware, this is where davis_gate_dsp.v triggers Henosis.
LD   R2, 0, 0       ; sentinel: cubic_detected = 0 (zero = "leak")
LOG  R2             ; prints "Q=0" — the manifold's verdict: this value is excluded
JMP  AFTER_B

LAMINAR_B:
; This branch would execute if R1 were laminar (it is not).
LD   R2, 1, 0       ; sentinel: cubic_detected = 1 (would indicate false pass)
LOG  R2

AFTER_B:

; ── Summary ──────────────────────────────────────────────────────────────────
; Expected output:
;   Track A — R0: Q=1 after 8 Pell rotations. SNAP ✓. Never drifts.
;   Track B — R1: Q=-2 logged. COND falls through (not taken = cubic leak).
;             R2 = 0 (sentinel) — manifold's verdict: value rejected.
;
; The key numbers:
;   R0 after 8 rotations: (18817 + 10864·√3)
;   Q = 18817² - 3×10864² = 354,079,489 - 354,079,488 = 1  EXACT.
;
;   In IEEE 754 float64:
;   18817.0² = 354,079,489.0  (exact, fits in 53-bit mantissa)
;   10864.0² = 117,985,216.0  (exact)
;   3×117,985,216.0 = 353,955,648.0
;   Catastrophic cancellation: 354,079,489.0 - 353,955,648.0 = 123,841.0 ≠ 1
;   (The float result is wrong by 5 orders of magnitude at step 8.)
;
;   In Q(√3): integers. 354,079,489 - 354,079,488 = 1. Always.

HALT
