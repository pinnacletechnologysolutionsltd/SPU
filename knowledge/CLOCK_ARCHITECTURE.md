# SPU-13 Clock Architecture

**Two clock domains. One fast computation engine. One rational heartbeat.**

This document exists because the 61.44 kHz Piranha Pulse is not the compute clock,
and engineers reading the RTL for the first time will reasonably ask: *"Why is your
processor running at 61 kilohertz?"* It isn't. Here is what is actually happening.

---

## 1. The Two Domains

The SPU-13 system operates across two clock domains with fundamentally different roles:

| Domain | Signal | Frequency | Role |
|--------|--------|-----------|------|
| **Fast (TDM)** | `clk_fast` | 24 MHz | All computation — ALU, SDRAM burst, sequencer |
| **Sovereign (Piranha)** | `clk_piranha` | ~61.4 kHz | External sync — Artery inhale, RP2350 frame boundary |

The Piranha Pulse is the **frame boundary** — the moment at which external data is
committed to the manifold and results are ready to be read. It is analogous to the
vertical sync signal in display hardware: it defines when a frame is complete, not
how fast the GPU is running.

---

## 2. Clock Derivation

### 2.1 The 24 MHz Core Clock

The Tang Primer 25K's 50 MHz crystal is divided by the onboard rPLL:

```
50 MHz crystal
    │  IDIV_SEL = 1   → reference = 25 MHz
    │  FBDIV_SEL = 23 → VCO = 25 × 24 = 600 MHz
    │  ODIV_SEL = 25  → output = 600 / 25 = 24 MHz
    ▼
clk_fast = 24.000 MHz  (pll_lock → rst_n released)
```

This drives the SPU-13 core, the SDRAM controller, and the Sierpinski clock divider.

### 2.2 The Sierpinski Clock (spu_sierpinski_clk.v)

The Sierpinski clock counts 0→33 (a 34-cycle Fibonacci-sum frame) and fires
three single-cycle pulses at the Fibonacci positions within each frame:

```
Cycle:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 ... 33
phi_8:                               ↑
phi_13:                                          ↑
phi_21:                                                                ↑
```

**Why 8, 13, 21?** These are consecutive Fibonacci numbers. Their ratios:

```
13/8  = 1.6250   (φ² = 2.618...)
21/13 = 1.6154   (φ  = 1.6180...)
34/21 = 1.6190   (φ  = 1.6180...)
```

The dispatch points divide the frame at golden-ratio positions. The electromagnetic
switching profile of the chip follows the same geometric distribution as the field
elements being computed.

**The `heartbeat` output** is the OR of all three phi pulses — it fires **3 times
per 34-cycle frame**.

### 2.3 Actual Piranha Frequency

With `clk_fast = 24 MHz` driving the Sierpinski clock:

```
Frame rate    = 24,000,000 Hz / 34 cycles = 705,882 Hz
Heartbeat     = 3 pulses × 705,882 Hz    = 2,117,647 Hz  ≈ 2.118 MHz
```

**This is the actual hardware rate of `clk_piranha` as currently implemented.**

### 2.4 The 61.44 kHz Target

The 61.44 kHz figure (= 60 × 1024 Hz) appears in the comments and documentation as
the **design target for the sovereign domain** — the rate at which the RP2350 streams
104-byte Whisper frames and the rate at which the Artery FIFO is expected to be
drained.

61.44 kHz cannot be exactly derived from 24 MHz via an integer divider:

```
24,000,000 / 61,440 = 390.625  (not an integer)
```

The closest integer dividers:

| Divider | Frequency | Error |
|---------|-----------|-------|
| ÷390 | 61,538.5 Hz | +0.16% |
| **÷391** | **61,381.1 Hz** | **−0.09%** |
| ÷392 | 61,224.5 Hz | −0.35% |

**Resolution (two options):**

**Option A — Pre-divide before Sierpinski (recommended for hardware):**
Add a simple ÷391 counter between `clk_fast` and the Sierpinski clock input.
The Sierpinski then runs at 61,381 Hz, and `heartbeat` fires at:
```
61,381 Hz × 3 / 34 × 34 = 61,381 Hz  (once per frame, one pulse of the three)
```
Wait — if the input to Sierpinski is already the piranha-rate clock (61.4 kHz),
the Sierpinski sub-divides *within* each piranha frame to produce phi_8/13/21
at intra-frame golden-ratio positions:
```
phi_8  fires at 8/34 of the frame  = 23.5% through each 61.4 kHz period
phi_13 fires at 13/34 of the frame = 38.2% through each 61.4 kHz period
phi_21 fires at 21/34 of the frame = 61.8% through each 61.4 kHz period
```
The phi pulses become intra-frame dispatch triggers, and the 34 input-clock
cycles *within each piranha period* drive a 34-step sub-sequencer.

**Option B — Use rPLL second output:**
GOWIN GW5A rPLL supports dual outputs. A second output can be tuned
independently:
```
VCO = 600 MHz, ODIV_B = ? → target 61,440 Hz
600,000,000 / 61,440 = 9765.625  (exceeds ODIV max of 128)
```
This requires a post-PLL divider chain anyway — Option A is simpler.

**Option C — RP2350 as sovereign clock source:**
The RP2350 PIO generates the Piranha Pulse via `spu_bio_resonance.pio` and
transmits it to the FPGA. The FPGA treats the incoming RP2350 signal as the
sovereign clock, eliminating the need for on-FPGA derivation. This is the
cleanest for cross-board synchronisation.

**Status: To be resolved on first board bring-up.** The architecture is correct;
the exact divider will be confirmed by measuring `clk_piranha` with a logic
analyser on first power-on.

---

## 3. The Sequencer Burst

The sequencer (`spu13_sequencer.v`) wakes on each `pulse_61k` (piranha tick)
and processes all 13 axes in a single burst at `clk_fast` speed:

```
Piranha tick arrives
    │
    ▼  24 MHz clk_fast burst begins
    │
    ├─ Cycles 0–12:   fetch_ptr 0→12    (13 cycles, one per axis)
    ├─ Cycles 1–2:    compute latency   (ALU pipeline, 2 cycles)
    ├─ Cycles 2–14:   commit_ptr 0→12   (write_en high, 13 cycles)
    │
    ▼  15 fast-clock cycles total
    │  = 0.625 µs at 24 MHz
    │
    │  19 idle fast-clock cycles
    │  = 0.792 µs of silence
    ▼
Next piranha tick
```

**Key numbers:**

| Quantity | Value |
|----------|-------|
| Fast clock (clk_fast) | 24 MHz |
| Burst duration | 15 cycles = 0.625 µs |
| Idle per frame | 19 cycles = 0.792 µs |
| Burst duty cycle | 15/34 = 44.1% |
| Axes processed per burst | 13 |
| Time per axis | 1/24 MHz = 41.7 ns |
| Piranha target | 61.44 kHz (≈ 16.3 µs between bursts) |

---

## 4. Clock Domain Crossing

Data flows from the slow Piranha domain to the fast TDM domain through a
formal 4-phase CDC gate (`spu_system.v`):

```
Phase A: Piranha domain writes Artery chords → inhale_staging[0:12]
          (one register per axis, one piranha period to stabilise)

Phase B: 2-FF synchroniser crosses inhale_primed into clk_fast domain

Phase C: On next H_INHALE (mem_burst_rd=1), snapshot fires:
          inhale_staging → int_mem   (atomic copy, one fast-clock cycle)

Phase D: snap_inhale_done=1 — H_EXHALE (mem_burst_wr) may resume
```

This prevents the race condition where H_EXHALE (running at 24 MHz) could
overwrite manifold data faster than the 61.4 kHz inhale could fill it.
The 2-FF synchroniser meets all metastability requirements for the 24 MHz / 61.4 kHz
crossing (MTBF >> system lifetime at these frequencies and this process node).

---

## 5. Why These Specific Frequencies

### 61.44 kHz = 60 × 1024 Hz

- **60**: Sixty frames per second — the display refresh target and the perceptual
  threshold for smooth motion. Also: 60-degree IVM geometry resonance.
- **1024 = 2¹⁰**: Binary-friendly sample count per frame, compatible with FFT-based
  spectral analysis of manifold state. Allows exactly 1024 Quadray measurements
  per display frame with no aliasing.

### 24 MHz = 24 × 10⁶

- Derived from 50 MHz crystal via integer-ratio rPLL (600 MHz VCO ÷ 25).
- 24 is highly composite (divisors: 1,2,3,4,6,8,12,24) — convenient for
  further subdivision.
- Gives 24,000,000 / 34 = 705,882 Hz frame rate. At 13 axes per burst:
  705,882 × 13 = **9,176,470 axis-operations per second** in the TDM core.

### 34-cycle Sierpinski frame

- 34 = F(9) in the Fibonacci sequence (1,1,2,3,5,8,13,21,**34**).
- The frame length itself is a Fibonacci number, so the ratio of dispatch
  position to frame length is always a ratio of consecutive Fibonacci numbers —
  converging to φ.
- 8 + 13 + 21 = 42 (sum of phi positions). 34 + 42 = 76. 76/34 ≈ 2.235 ≈ √5.
  The Fibonacci structure encodes √5 — the algebraic root of φ.

---

## 6. Summary for Hardware Engineers

```
50 MHz crystal
    │
    ▼  rPLL (÷2, ×24, ÷25)
24 MHz clk_fast  ─────────────────────── All computation
    │                                    • 13-axis TDM ALU
    │                                    • Sequencer burst (15 cycles)
    │                                    • SDRAM controller
    │
    ▼  Sierpinski ÷34 (or pre-÷391 for 61.44 kHz target)
~61.4 kHz clk_piranha  ────────────────── External synchronisation
    │                                    • Artery FIFO drain boundary
    │                                    • RP2350 frame boundary
    │                                    • Whisper TX frame start
    │
    ▼  Within each piranha period (34 sub-cycles):
phi_8, phi_13, phi_21  ─────────────────── Intra-frame dispatch triggers
                                           • Fibonacci positions in frame
                                           • Drive sequencer wake-up
                                           • Golden-ratio EM profile
```

**The 61.44 kHz is not the processor clock. It is the sovereign frame rate —
the rate at which a complete manifold state is produced and made available
to the outside world. The processor runs at 24 MHz and completes all 13 axes
in 15 cycles (0.625 µs) — well within the 16.3 µs piranha period.**

---

*Clock Architecture Document v1.0 — CC0 1.0 Universal*
