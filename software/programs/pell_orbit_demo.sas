; pell_orbit_demo.sas — SPU-13 Sovereign VM demo program
;
; Exercises the full emulator stack with correct opcode semantics.
;
; Opcode reference:
;   LD  Rn, p, q        — Rn <- p + q*sqrt(3)
;   ROT Rn              — Rn <- pell_rotate(Rn) = (2p+3q, p+2q)
;   ADD Rn, Ra, Rb      — Rn <- R[Ra] + R[Rb]
;   MUL Rn, Ra, Rb      — Rn <- R[Ra] * R[Rb]
;   QLOAD QRn, base     — QRn <- (R[base], R[base+1], R[base+2], R[base+3])
;   QROT  QRd, QRs      — QRd <- pell_rotate(QRs)
;   QADD  QRd, QRs      — QRd <- QRd + QRs
;   QNORM QRn           — QRn <- normalize(QRn)
;   SPREAD Rn, QRa, QRb — R[n]=num, R[n+1]=denom of spread(QRa,QRb)
;   SNAP                — Davis Gate: assert all non-zero R[i] are laminar
;   JINV Rn             — negate surd component: (p,q) -> (p,-q)
;   ANNE QRn            — QRn <- QRn >> 1
;   IDNT QRn            — QRn <- [1,0,0,0]
;
; Run:
;   python3 spu_vm.py programs/pell_orbit_demo.sas
;   python3 spu_vm.py programs/pell_orbit_demo.sas --proof
;   python3 spu_vm.py programs/pell_orbit_demo.sas --quiet --gasket-trace --sdf-trace

; ── Phase 1: Scalar Pell orbit ─────────────────────────────────────────────
; r0 = 1+0*sqrt(3)  norm = 1 (Pell seed)
LD  R0, 1, 0
; Each ROT: rn+1 = (2p+3q, p+2q). Norm invariant = 1.
; (1,0) -> (2,1) -> (7,4) -> (26,15) -> (97,56)
ROT R0
ROT R0
ROT R0
ROT R0
LOG R0

; ── Phase 2: Scalar arithmetic ─────────────────────────────────────────────
LD  R1, 2, 1           ; (2,1) norm=1
LD  R2, 7, 4           ; (7,4) norm=1
; R3 = R1 + R2 = (9,5)  norm = 81-75 = 6 > 0  laminar
ADD R3, 1, 2
; R4 = R1 * R1 = (2*2+3*1, 2*1+1*2) = (7,4)  norm = 49-48 = 1
MUL R4, 1, 1
LOG R1
LOG R3
LOG R4

; ── Checkpoint 1 ───────────────────────────────────────────────────────────
SNAP

; ── Phase 3: Quadray load from register window ─────────────────────────────
; Set up window R8..R11 = (1,0,0,0) for canonical QR axis
LD R8,  1, 0
LD R9,  0, 0
LD R10, 0, 0
LD R11, 0, 0
QLOAD QR0, R8           ; QR0 = (1,0,0,0)
QNORM QR0
QLOG  QR0

; Second axis: (0,1,0,0)
LD R8,  0, 0
LD R9,  1, 0
QLOAD QR1, R8           ; QR1 = (0,1,0,0)
QNORM QR1
QLOG  QR1

; ── Phase 4: Quadray Pell rotation ─────────────────────────────────────────
; IDNT reloads QR0 = (1,0,0,0) — Henosis may have zeroed it since last load.
; This is expected: the Davis Gate zeroed an unbalanced manifold via Henosis.
IDNT  QR0              ; fresh canonical axis — (1,0,0,0) guaranteed
QROT  QR0              ; rotate QR0 in-place: (1,0,0,0) → (2+√3, 0, 0, 0)
QLOG  QR0              ; should show [(2 + 1·√3), 0, 0, 0]

; ── Phase 5: Quadray addition ──────────────────────────────────────────────
IDNT  QR3              ; QR3 = (1,0,0,0)
QADD  QR3, QR1         ; QR3 = QR3 + QR1 = (1,1,0,0)
QNORM QR3
QLOG  QR3

; ── Checkpoint 2 ───────────────────────────────────────────────────────────
SNAP

; ── Phase 6: Spread ────────────────────────────────────────────────────────
IDNT QR4               ; canonical (1,0,0,0)
LD R8,  0, 0
LD R9,  1, 0
LD R10, 0, 0
LD R11, 0, 0
QLOAD QR5, R8           ; (0,1,0,0)
SPREAD R20, QR4, QR5       ; spread(QR4,QR5) -> R20=num, R21=denom
LOG R20
LOG R21

; ── Phase 7: Janus round-trip ──────────────────────────────────────────────
; R1=(2,1): JINV -> (2,-1)  norm=4-3=1 still laminar
LOG  R1
JINV R1
LOG  R1
JINV R1                ; back to (2,1)
LOG  R1

; ── Checkpoint 3 ───────────────────────────────────────────────────────────
SNAP

; ── Phase 8: Annealing ─────────────────────────────────────────────────────
IDNT QR6               ; (1,0,0,0)
QLOG QR6
ANNE QR6               ; (0,0,0,0)  [1>>1 = 0]
QLOG QR6

; ── Final checkpoint ───────────────────────────────────────────────────────
SNAP
