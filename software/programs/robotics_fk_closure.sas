; robotics_fk_closure.sas — Forward Kinematics with Inverse Closure (v1.0)
;
; Demonstrates the key robotics primitive: ROTC chain with verified
; inverse closure.  Uses only hardware-verified opcodes:
;   QLDI (0x1D), ROTC (0x1C), HEX (0x16), IDNT (0x18)
;
; Corrected ROTC 0-5 Angle Catalog (June 2026):
;   Angle 0: identity     F=1,0,0        period=1  inverse=0
;   Angle 1: 60°          F=2/3,2/3,-1/3 period=6  inverse=4
;   Angle 2: P5 forward   F=0,1,0        period=3  inverse=5
;   Angle 3: 120° period2 F=-1/3,2/3,2/3 period=2  inverse=3 (self-inverse)
;   Angle 4: 300°/240°    F=2/3,-1/3,2/3 period=6  inverse=1
;   Angle 5: P5 reverse   F=0,0,1        period=3  inverse=2
;
; Run:
;   python3 software/spu_forge.py simulate software/programs/robotics_fk_closure.sas
;
; Hardware: ROTC is RTL testbench-verified for all 6 angles.
; VM-vs-RTL trace equivalence verified by test_rotc_vm_rtl_trace.py.

; ── Test 1: Single-joint FK + Inverse closure (Angle 1 → Angle 4) ──
; Load unit vector at A-axis
QLDI QR0, 0x0100, 0x0000          ; QR0 = (1, 0, 0, 0)
HEX   R0, QR0                       ; hex project → R0=q, R1=r

; Apply 60° rotation (angle 1)
ROTC  QR1, QR0, 0x0001             ; QR1 = ROTC(QR0, 60°) → (0, 2/3, 2/3, -1/3)
HEX   R2, QR1

; Apply inverse 240° rotation (angle 4) → should recover QR0
ROTC  QR2, QR1, 0x0004             ; QR2 = ROTC(QR1, 240°) → should equal QR0
HEX   R4, QR2

; ── Test 2: P5 cycle closure (Angle 2 → Angle 5) ──────────────────
; P5 forward: B→C, C→D, D→B (pure bit permutation, zero multiplies)
QLDI QR3, 0x0000, 0x0100          ; QR3 = (0, 0, 1, 0) — C=1
ROTC  QR4, QR3, 0x0002             ; P5 forward → D=1
HEX   R6, QR4

ROTC  QR5, QR4, 0x0005             ; P5 inverse → C=1 (recovered)
HEX   R8, QR5

; Verify closure: QR5 should equal QR3
; (0,0,1,0) == (0,0,1,0) → check manually

; ── Test 3: Two-joint FK chain (Angle 1 then Angle 4 = identity) ──
QLDI QR6, 0x0001, 0x0000          ; QR6 = (0, 1, 0, 0) — B=1
ROTC  QR7, QR6, 0x0001             ; joint 0: 60°
ROTC  QR8, QR7, 0x0004             ; joint 1: 240° (inverse of 60°)
HEX   R10, QR8                      ; should equal hex projection of QR6

; ── Test 4: Self-inverse angle 3 (120° period-2) ──────────────────
QLDI QR9, 0x0100, 0x0000          ; QR9 = (1, 0, 0, 0)
ROTC  QR10, QR9, 0x0003            ; 120° rotation
ROTC  QR11, QR10, 0x0003           ; 120° again → should recover
HEX   R12, QR11

; ── Test 5: 6-step period-6 orbit (angle 1 applied 6 times) ──────
; 6 applications of 60° = 360° → identity
; This demonstrates the Pell orbit closure property.
QLDI QR12, 0x0100, 0x0000         ; start at A-axis
ROTC  QR0, QR12, 0x0001            ; step 1
ROTC  QR0, QR0, 0x0001             ; step 2
ROTC  QR0, QR0, 0x0001             ; step 3
ROTC  QR0, QR0, 0x0001             ; step 4
ROTC  QR0, QR0, 0x0001             ; step 5
ROTC  QR0, QR0, 0x0001             ; step 6 → should equal QR12
HEX   R14, QR0                      ; should match hex of QR12

HALT

; Expected results:
;   Test 1: QR0 hex = (1,0), QR1 hex ≠ (1,0), QR2 hex = (1,0)  [closure]
;   Test 2: QR3 hex = (0,0) [C=1 proj], QR5 hex = QR3 hex       [P5 closure]
;   Test 3: QR6 hex, QR8 hex = QR6 hex                            [chain closure]
;   Test 4: QR11 hex = QR9 hex                                    [self-inverse]
;   Test 5: QR0 hex = QR12 hex = (1,0)                            [period-6 orbit]
