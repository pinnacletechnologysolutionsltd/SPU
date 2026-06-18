; som_classify_demo.sas — SOM/BMU classifier demo (v1.0)
;
; Exercises the SOM_CLASSIFY opcode (0x2A) with the 7-node hex fixture
; built into spu_som_bmu.v.  The fixture is a tiny hex map with four
; cluster labels (0-3) and integer/surd weights.
;
; Matches the RTL testbench spu13_core_som_opcode_tb.v.
; VM-vs-RTL parity verified 2026-06-17.
;
; Run:
;   python3 software/spu_forge.py simulate software/programs/som_classify_demo.sas
;   python3 software/spu_forge.py simulate software/programs/som_classify_demo.sas --proof
;
; Hardware (Tang Primer 25K with SOM probe):
;   bash build_25k_spu13_som_probe.sh
;   openFPGALoader -b tangprimer25k -f build/spu13_som_probe.fs
;
; The 7-node hex fixture:
;   Node 0: (q= 0, r= 0) label=0  weights=( 0,  0,  0,  0)
;   Node 1: (q= 1, r= 0) label=1  weights=( 2,  0,  0,  0)
;   Node 2: (q= 1, r=-1) label=1  weights=( 0,  2,  0,  0)
;   Node 3: (q= 0, r=-1) label=2  weights=( 0,  0,  2,  0)
;   Node 4: (q=-1, r= 0) label=2  weights=(-2,  0,  0,  0)
;   Node 5: (q=-1, r= 1) label=3  weights=( 0, -2,  0,  0)
;   Node 6: (q= 0, r= 1) label=3  weights=( 0,  0, -2, 1+√3)
;
; Unit feature weights (all 1.0) — no feature scaling.

; ── Test 1: Feature (2,1,0,0) → label=1 (node 1 wins) ──────────
; QLDI encodes A,B in p1_a (packed bytes), C,D in p1_b.
; Format: QLDI QRd, 0xAB, 0xCD  where A,B,C,D are 8-bit signed ints.
; (2,1,0,0) → p1_a=0x0201, p1_b=0x0000
QLDI QR0, 0x0201, 0x0000        ; QR0 = (2, 1, 0, 0)
SOM   R0, QR0                     ; classify → label=1 (clear)

; ── Test 2: Feature (0,0,2,0) → label=2 (node 3 wins) ──────────
QLDI QR1, 0x0000, 0x0200        ; QR1 = (0, 0, 2, 0)
SOM   R2, QR1                     ; classify → label=2

; ── Test 3: Feature (-2,0,0,0) → label=2 (node 4 wins) ──────────
QLDI QR2, 0xFE00, 0x0000        ; QR2 = (-2, 0, 0, 0)  (FE=-2 signed)
SOM   R4, QR2                     ; classify → label=2

; ── Test 4: Feature (0,-2,0,0) → label=3 (node 5 wins) ──────────
QLDI QR3, 0x00FE, 0x0000        ; QR3 = (0, -2, 0, 0)  (FE=-2 signed)
SOM   R6, QR3                     ; classify → label=3

; ── Test 5: Feature (0,0,0,0) → label=0 (node 0 wins) ───────────
QLDI QR4, 0x0000, 0x0000        ; QR4 = (0, 0, 0, 0)
SOM   R8, QR4                     ; classify → label=0

; ── Test 6: Surd feature (0,0,-2,1+√3) → label=3? ───────────────
; Feature matches node 6's weights exactly → Q=0 → best match.
; But QLDI only loads integers.  For surd features, use QLOAD
; after loading the surd coefficient into R registers via LD.
; Skipping for now — QLDI doesn't support surd immediates.

; ── Test 7: Ambiguity boundary ───────────────────────────────────
; Feature exactly midway between node 0 (Q=5) and node 2 (Q=5):
; f=(1,1,0,0): node 0 Q=1+1=2, node 1 Q=1+1=2... wait, recalc.
; f=(1,0,0,0): node 0 Q=1, node 1 Q=1 → TIE! Node 0 wins by lower ID.
QLDI QR5, 0x0100, 0x0000        ; QR5 = (1, 0, 0, 0)
SOM   R10, QR5                    ; classify → label=0 (node 0 wins tie)

; ── Dump results ─────────────────────────────────────────────────
QLOG QR0
QLOG QR1
QLOG QR2
QLOG QR3
QLOG QR4
QLOG QR5

HALT

; Expected results:
;   R0  = 1  (label 1, clear)     — feature (2,1,0,0) → node 1
;   R1  = 0  (not ambiguous)
;   R2  = 2  (label 2)            — feature (0,0,2,0) → node 3
;   R3  = 0
;   R4  = 2  (label 2)            — feature (-2,0,0,0) → node 4
;   R5  = 0
;   R6  = 3  (label 3)            — feature (0,-2,0,0) → node 5
;   R7  = 0
;   R8  = 0  (label 0)            — feature (0,0,0,0) → node 0
;   R9  = 0
;   R10 = 0  (label 0, tie)       — feature (1,0,0,0) → node 0 wins tie
;   R11 = 0
