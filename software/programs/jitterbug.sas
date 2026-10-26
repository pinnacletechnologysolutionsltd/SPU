; jitterbug.sas — The Jitterbug Morph (Pell Sequence)
; Demonstrates the fundamental resonance rotation in Q(√3).
;
; ROT multiplies by the unit element (2+√3) — Q=1, laminar-preserving.
; This generates the Pell sequence: 1, (2+√3), (7+4√3), (26+15√3)...
; The Q(√3) analogue of the golden ratio Fibonacci spiral.
;
; All SNAP checks should pass — this is a fully laminar orbit.

        LD  R0, 1, 0    ; R0 = (1 + 0·√3) = 1  — seed

LOOP:
        ROT R0           ; R0 ← R0 × (2+√3)  — Pell step
        LOG R0           ; emit state
        SNAP             ; Davis Gate — must stay laminar
        JMP LOOP         ; use --steps to bound

