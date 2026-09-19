; fibonacci_pulse.sas — Fibonacci Heartbeat
; Generates the Fibonacci sequence in Q(√3) as a pure integer ladder.
; R0=F(n-1), R1=F(n), R2=scratch.
; Mirrors the 8,13,21 Phi-Gated timing of the hardware Piranha Pulse.
;
; Each ADD step: R2 = R0 + R1, then slide the window forward.

        LD  R0, 1, 0     ; R0 = (1 + 0·√3) = 1  [F1]
        LD  R1, 1, 0     ; R1 = (1 + 0·√3) = 1  [F2]

        LOG R0
        LOG R1

BEAT:
        ADD R2, R0       ; R2 = R2 + R0  (R2 starts 0, so R2 = R0)
        ADD R2, R1       ; R2 = R2 + R1  → R2 = F(n-1) + F(n) = F(n+1)
        ; Slide window: R0 ← R1, R1 ← R2
        LD  R0, 0, 0     ; clear R0
        ADD R0, R1       ; R0 = R1
        LD  R1, 0, 0     ; clear R1
        ADD R1, R2       ; R1 = R2
        LD  R2, 0, 0     ; clear R2 for next iteration

        LOG R1           ; emit current Fibonacci number
        JMP BEAT         ; use --steps to pick how many terms
