; quadrance_test.sas — Davis Gate Validation
; Tests that Q(√3) arithmetic maintains laminar (Q > 0) across all ops.
; This is the software equivalent of the spu_davis_gate.v hardware check.
;
; R0: laminar element    Q = 4 - 3 = 1  > 0  ✓
; R1: degenerate element Q = 0 - 3 = -3 < 0  ✗ (should trigger SNAP fail)
; R2: product — must also be laminar

        LD  R0, 2, 1     ; R0 = (2 + 1·√3)  → Q = 4 - 3 = 1  (laminar)
        LD  R1, 0, 1     ; R1 = (0 + 1·√3)  → Q = 0 - 3 = -3 (cubic!)
        LD  R2, 4, 2     ; R2 = (4 + 2·√3)  → Q = 16 - 12 = 4 (laminar)

        LOG R0           ; show R0
        LOG R1           ; show R1 — will display negative quadrance
        LOG R2           ; show R2

        SNAP             ; ← will report CUBIC LEAK for R1

        ; Demonstrate that MUL stays closed in Q(√3)
        MUL R0, R2       ; R0 = R0 × R2
        LOG R0           ; R0 = (2+√3)(4+2√3) = (8+12)+(4+4)√3 = (20 + 8√3)

        SNAP             ; R0 should still be laminar after multiply
