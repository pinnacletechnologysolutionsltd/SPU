; equilibrium_test.sas — ISA v1.2 Vector Equilibrium demo
;
; Loads all 6 cuboctahedron edge-midpoint vectors into QR0–QR5.
; These are all distinct permutations of (1,1,0,0) in Quadray space.
; Their hex projections sum to exactly (0,0) — Vector Equilibrium.
;
; Proof:
;   QR0 (1,1,0,0) → hex=(+1,+1)
;   QR1 (1,0,1,0) → hex=(+1, 0)
;   QR2 (1,0,0,1) → hex=( 0,-1)
;   QR3 (0,1,1,0) → hex=( 0,+1)
;   QR4 (0,1,0,1) → hex=(-1, 0)
;   QR5 (0,0,1,1) → hex=(-1,-1)
;   Σ hex = (0,0) ✓ — cuboctahedron is the IVM zero-point (Vector Equilibrium)
;
; Expected results:
;   EQUIL ✓  — hex sum=(0,0), manifold balanced
;   JINV     — R0 surd sign flips, Q = a²-3b² unchanged (Janus symmetry)
;   IDNT     — QR2 resets to canonical [1,0,0,0]
;   ANNE     — QR0 anneals (halves toward origin)

; ── Load 6 cuboctahedron vertices ────────────────────────────────────────────

; QR0 = (1,1,0,0)
LD  R0, 1, 0
LD  R1, 1, 0
LD  R2, 0, 0
LD  R3, 0, 0
QLOAD QR0, R0

; QR1 = (1,0,1,0)
LD  R0, 1, 0
LD  R1, 0, 0
LD  R2, 1, 0
LD  R3, 0, 0
QLOAD QR1, R0

; QR2 = (1,0,0,1)
LD  R0, 1, 0
LD  R1, 0, 0
LD  R2, 0, 0
LD  R3, 1, 0
QLOAD QR2, R0

; QR3 = (0,1,1,0)
LD  R0, 0, 0
LD  R1, 1, 0
LD  R2, 1, 0
LD  R3, 0, 0
QLOAD QR3, R0

; QR4 = (0,1,0,1)
LD  R0, 0, 0
LD  R1, 1, 0
LD  R2, 0, 0
LD  R3, 1, 0
QLOAD QR4, R0

; QR5 = (0,0,1,1)
LD  R0, 0, 0
LD  R1, 0, 0
LD  R2, 1, 0
LD  R3, 1, 0
QLOAD QR5, R0

; ── Log all 6 axes before check ──────────────────────────────────────────────
QLOG QR0
QLOG QR1
QLOG QR2
QLOG QR3
QLOG QR4
QLOG QR5

; ── EQUIL — assert hex sum of all active QR = (0,0) ─────────────────────────
EQUIL

; ── JINV — test Janus bit on scalar ──────────────────────────────────────────
; Load a laminar surd, flip its surd sign, verify Q unchanged
LD   R0, 2, 1           ; R0 = 2 + 1·√3  Q=1 ✓
LOG  R0
JINV R0                 ; R0 = 2 - 1·√3  Q = 4-3 = 1 ✓ (Q symmetric)
LOG  R0
SNAP                    ; Davis Gate: both pre/post Janus must be laminar

; ── IDNT — reset QR2 to canonical unity ──────────────────────────────────────
IDNT QR2                ; QR2 ← [1,0,0,0]
QLOG QR2

; ── ANNE — anneal QR0 one step toward VE ─────────────────────────────────────
ANNE QR0                ; halve each component
QLOG QR0
