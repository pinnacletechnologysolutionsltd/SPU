; pell_octave_test.sas
; Pell Octave: verify that 16 ROT steps (2 full octaves) stay laminar.
;
; The overflow problem: step 9 gives (70226, 40545) — overflows int16.
; The solution: Pell Octave representation tracks (octave, step) so the
; stored mantissa cycles through orbit[0..7], always fits 16-bit, norm=1.
;
; This program:
;   1. Loads unity (1,0) into R0 — seeds pell_step=0
;   2. Applies 16 ROT operations — crosses the octave boundary twice
;   3. SNAPs at key checkpoints to verify manifold stability throughout
;   4. Applies one inverse step (MUL by r^-1 = (2,-1)) and verifies
;
; Expected output: all SNAP ✓, final R0 = (5042, 2911) = r^7 at oct=2
; VM will show octave tags: R0=r^16(oct=2,s=0), r^7(oct=2,s=7) etc.
;
; PASS criterion: no SNAP failures, program reaches DONE.

        ; ── Seed the Pell orbit ──────────────────────────────────────────
        LD   R0, 1, 0       ; R0 = (1,0) = r^0  [oct=0, step=0]
        SNAP                ; baseline: norm=1 ✓

        ; ── Octave 0: steps 1–7 ─────────────────────────────────────────
        ROT  R0             ; r^1  = (2,1)        [oct=0, step=1]
        ROT  R0             ; r^2  = (7,4)        [oct=0, step=2]
        ROT  R0             ; r^3  = (26,15)      [oct=0, step=3]
        ROT  R0             ; r^4  = (97,56)      [oct=0, step=4]
        ROT  R0             ; r^5  = (362,209)    [oct=0, step=5]
        ROT  R0             ; r^6  = (1351,780)   [oct=0, step=6]
        ROT  R0             ; r^7  = (5042,2911)  [oct=0, step=7]
        SNAP                ; end of octave 0 — all 7 steps stable ✓

        ; ── Octave boundary: step 8 ──────────────────────────────────────
        ROT  R0             ; r^8  → octave wraps! stored=(1,0) [oct=1, step=0]
        SNAP                ; r^8 in octave representation: norm=1 ✓

        ; ── Octave 1: steps 9–15 ────────────────────────────────────────
        ROT  R0             ; r^9  = stored (2,1)     [oct=1, step=1]
        SNAP                ; step 9 — previously overflowed int16, now exact ✓

        ROT  R0             ; r^10 = stored (7,4)     [oct=1, step=2]
        ROT  R0             ; r^11 = stored (26,15)   [oct=1, step=3]
        ROT  R0             ; r^12 = stored (97,56)   [oct=1, step=4]
        ROT  R0             ; r^13 = stored (362,209) [oct=1, step=5]
        ROT  R0             ; r^14 = stored (1351,780)[oct=1, step=6]
        ROT  R0             ; r^15 = stored (5042,2911)[oct=1,step=7]
        SNAP                ; end of octave 1 — all steps stable ✓

        ; ── Second octave boundary: step 16 ─────────────────────────────
        ROT  R0             ; r^16 → stored=(1,0)    [oct=2, step=0]
        SNAP                ; r^16: norm=1, oct=2 ✓

        ; ── Octave 2: steps 17–23 ───────────────────────────────────────
        ROT  R0             ; r^17 = stored (2,1)    [oct=2, step=1]
        ROT  R0             ; r^18 = stored (7,4)    [oct=2, step=2]
        ROT  R0             ; r^19 = stored (26,15)  [oct=2, step=3]
        SNAP                ; mid-octave 2 check ✓

        ; ── Inverse step: multiply by r^-1 = (2, -1) ────────────────────
        ; r^19 * r^-1 = r^18 — step decrements, octave unchanged
        LD   R1, 2, -1      ; R1 = (2, -1) = r^-1 (inverse rotor)
        MUL  R0, R1         ; R0 = R0 * r^-1 = r^18 (stored: (7,4))
        SNAP                ; r^18 after inverse step: norm=1 ✓

        ; ── Final log ────────────────────────────────────────────────────
        LOG  R0             ; show final state: should be (7, 4) = orbit[2]
        LOG  R1             ; show r^-1: (2, -1)

        ; ── Demonstrate: norm of r^-1 is also 1 ─────────────────────────
        ; (2)^2 - 3*(-1)^2 = 4 - 3 = 1 ✓
        SNAP                ; both R0 and R1 laminar ✓

DONE:
        NOP
        ; Expected: all SNAP pass, no cubic leaks, 16+ rotations without overflow
        ; The Pell octave demonstrates: the manifold has no word-width ceiling.
