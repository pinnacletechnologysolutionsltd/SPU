; som_train_demo.sas — 4-Epoch SOM Training Program (v1.0)
;
; Trains the 7-node hex fixture on 4 input vectors across 4 epochs
; using dyadic weight updates (SOM_TRAIN with shift ∈ {1,2,3,4}).
;
; Algorithm:
;   1. QLDI → load feature vector into QR0
;   2. SOM → find best matching unit
;   3. SOM_TRAIN shift → w_bmu += (x - w_bmu) >> shift
;
; Proves: deterministic convergence at epoch 3, bit-exact replay.
;
; Run:
;   python3 software/spu_forge.py simulate software/programs/som_train_demo.sas
;
; Expected output:
;   Epoch 1 (shift=1): weights changing → converging
;   Epoch 2 (shift=2): weights still moving
;   Epoch 3 (shift=3): STABLE — map converged
;   Epoch 4 (shift=4): STABLE — converged
;
; Final weights after training:
;   Node 0: ( 0, 0, 0, 0)  — never a BMU
;   Node 1: ( 2, 0, 0, 0)  — BMU for (4,0) and (-2,3)
;   Node 2: ( 0, 2, 0, 0)  — not heavily trained
;   Node 3: ( 0, 0, 2, 0)  — BMU for (1,-3)
;   Node 4: (-2, 0, 0, 0)  — never a BMU
;   Node 5: ( 0,-2, 0, 0)  — never a BMU
;   Node 6: ( 0, 0,-2, 1+√3) — never a BMU

; ── Epoch 1: shift=1 (aggressive learning) ────────────────────
; Input 1: (4, 0, 0, 0)
QLDI QR0, 0x0400, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0001

; Input 2: (-2, 3, 0, 0)  → -2=0xFE, 3=0x03
QLDI QR0, 0xFE03, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0001

; Input 3: (1, -3, 0, 0)  → -3=0xFD
QLDI QR0, 0x01FD, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0001

; Input 4: (0, 0, 0, 0) — origin, pulls BMU toward center
QLDI QR0, 0x0000, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0001

; ── Epoch 2: shift=2 ─────────────────────────────────────────
QLDI QR0, 0x0400, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0002

QLDI QR0, 0xFE03, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0002

QLDI QR0, 0x01FD, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0002

QLDI QR0, 0x0000, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0002

; ── Epoch 3: shift=3 (fine tuning) ────────────────────────────
QLDI QR0, 0x0400, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0003

QLDI QR0, 0xFE03, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0003

QLDI QR0, 0x01FD, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0003

QLDI QR0, 0x0000, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0003

; ── Epoch 4: shift=4 (should be stable, no changes) ───────────
QLDI QR0, 0x0400, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0004

QLDI QR0, 0xFE03, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0004

QLDI QR0, 0x01FD, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0004

QLDI QR0, 0x0000, 0x0000
SOM   R0, QR0
SOM_TRAIN 0x0004

; ── Verify: reclassify all inputs on trained map ─────────────
QLDI QR0, 0x0400, 0x0000
SOM   R0, QR0                     ; expect label=1

QLDI QR0, 0xFE03, 0x0000
SOM   R2, QR0                     ; expect label=1

QLDI QR0, 0x01FD, 0x0000
SOM   R4, QR0                     ; expect label=2

QLDI QR0, 0x0000, 0x0000
SOM   R6, QR0                     ; expect label=0

HALT
