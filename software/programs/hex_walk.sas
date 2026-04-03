; hex_walk.sas — IVM Hex Grid Traversal
; Demonstrates walking the hexagonal lattice using Quadray addition.
; Each of the 6 IVM neighbour directions is one basis Quadray.
; We start at the origin and walk East → NE → NW → West → SW → SE → back.
;
; IVM step vectors (normalized Quadrays, one non-zero component each):
;   East      : (1,0,0,0)
;   NorthEast : (0,1,0,0)
;   NorthWest : (0,0,1,0)
;   West      : (0,0,0,1)  [complement of East]
;   SouthWest : sub East from current via QADD with negatives
;
; For simplicity, we load each step as R[0..3] then QLOAD into QR4 (step),
; then QADD QR0 (position) + QR4 (step), then HEX to read pixel coords.

; ── Current position: start at origin ────────────────────────
        LD  R0, 0, 0
        LD  R1, 0, 0
        LD  R2, 0, 0
        LD  R3, 0, 0
        QLOAD QR0, R0    ; QR0 = position = [0,0,0,0]

; ── Step East: add (1,0,0,0) ─────────────────────────────────
        LD  R0, 1, 0
        LD  R1, 0, 0
        LD  R2, 0, 0
        LD  R3, 0, 0
        QLOAD QR4, R0    ; QR4 = step vector

        QADD  QR0, QR4   ; position += step
        QNORM QR0        ; canonical form
        HEX   R8, QR0    ; R8=hex_q, R9=hex_r
        LOG   R8
        LOG   R9
        QLOG  QR0

; ── Step NorthEast: add (0,1,0,0) ────────────────────────────
        LD  R0, 0, 0
        LD  R1, 1, 0
        LD  R2, 0, 0
        LD  R3, 0, 0
        QLOAD QR4, R0

        QADD  QR0, QR4
        QNORM QR0
        HEX   R8, QR0
        LOG   R8
        LOG   R9
        QLOG  QR0

; ── Step NorthWest: add (0,0,1,0) ────────────────────────────
        LD  R0, 0, 0
        LD  R1, 0, 0
        LD  R2, 1, 0
        LD  R3, 0, 0
        QLOAD QR4, R0

        QADD  QR0, QR4
        QNORM QR0
        HEX   R8, QR0
        LOG   R8
        LOG   R9
        QLOG  QR0

; ── Compute spread between QR0 (current) and QR2 (East step) ────
        LD  R0, 1, 0
        LD  R1, 0, 0
        LD  R2, 0, 0
        LD  R3, 0, 0
        QLOAD QR5, R0    ; QR5 = (1,0,0,0) — East reference

        SPREAD R10, QR0, QR5  ; R10=numerator, R11=denominator
        LOG    R10
        LOG    R11

        SNAP             ; manifold check
