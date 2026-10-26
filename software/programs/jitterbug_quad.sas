; jitterbug_quad.sas — Full Quadray Jitterbug Morph
; Loads 3 canonical IVM vertices (permutations of (2,1,1,0)) into QR0-QR2.
; Each QROT step applies the Pell rotor to all components, then normalizes.
; Hex projection shows the pixel address moving through the lattice.
;
; The 12 cuboctahedron vertices in Quadray are all permutations of (2,1,1,0).
; We demonstrate with 3 representative vertices.
;
; Expected: all vertices scale together (same Q ratio), all SNAP pass.

; ── Vertex 0: (2,1,1,0) ─────────────────────────────────────
        LD  R0, 2, 0    ; a = 2
        LD  R1, 1, 0    ; b = 1
        LD  R2, 1, 0    ; c = 1
        LD  R3, 0, 0    ; d = 0
        QLOAD QR0, R0   ; QR0 = [2,1,1,0]

; ── Vertex 1: (2,1,0,1) ─────────────────────────────────────
        LD  R0, 2, 0
        LD  R1, 1, 0
        LD  R2, 0, 0
        LD  R3, 1, 0
        QLOAD QR1, R0   ; QR1 = [2,1,0,1]

; ── Vertex 2: (1,2,1,0) ─────────────────────────────────────
        LD  R0, 1, 0
        LD  R1, 2, 0
        LD  R2, 1, 0
        LD  R3, 0, 0
        QLOAD QR2, R0   ; QR2 = [1,2,1,0]

; ── Jitterbug loop ───────────────────────────────────────────
JITTER:
        QROT  QR0           ; Pell step + normalize
        QROT  QR1
        QROT  QR2
        QLOG  QR0           ; show state + hex pixel
        QLOG  QR1
        QLOG  QR2
        SNAP                ; Davis Gate on all scalar registers
        JMP   JITTER        ; use --steps to bound
