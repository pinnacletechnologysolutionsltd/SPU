# SPU Sovereign Observer Stack — Design Philosophy

## The Core Principle

The SPU-13 cluster is a computation engine. It does not make decisions about
itself — it produces *observables*. The job of deciding what those observables
mean, and what to do about them, always lives in software above the hardware.

This is not a limitation. It is the correct division of responsibility, and it
mirrors how serious adaptive systems work: avionics flight control, adaptive mesh
refinement in CFD solvers, real-time adaptive codecs. **Hardware observes fast.
Software decides correctly.**

---

## The Four-Layer Observer Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 — Strategic Inference (minutes/hours)              │
│  Companion SBC (RPi 5, Jetson) or remote host               │
│  Rewrites thresholds, detects recurring patterns,           │
│  adapts the observer policy itself                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — Tactical Reasoning (milliseconds)                │
│  RP2350 Hazard3 RISC-V cores                                │
│  Classifies simulation phase, chooses response mode,        │
│  issues RPLU bank switches and PLC control words            │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — Signal Conditioning (microseconds)               │
│  RP2350 PIO / DMA                                           │
│  Polls SPI telemetry, filters noise, maintains              │
│  running statistics on laminar_index and residuals          │
├─────────────────────────────────────────────────────────────┤
│  Layer 1 — Hardware Observation (nanoseconds)               │
│  SPU-13 FPGA fabric                                         │
│  Computes laminar_index, turbulence_alert, ratio residuals, │
│  satellite telemetry — raises signals, never decides        │
└─────────────────────────────────────────────────────────────┘
```

---

## What Lives on the RP2350 (Layers 2 & 3)

The RP2350 has two Hazard3 RISC-V cores and two ARM Cortex-M33 cores (only
Hazard3 in the open-source variant). It has 520KB SRAM. This is enough for a
real-time observer with genuine decision-making capability — not just a timer.

### Layer 2 — Signal Conditioning (Core 0 / PIO)

Runs deterministically, never blocks:

```c
// Exponential moving average on laminar_index
// α = 0.1 gives ~10 sample smoothing — enough to reject single-cycle spikes
ema = (alpha * new_sample) + ((1.0f - alpha) * ema);

// Derivative: rate of change of stress
slope = ema - prev_ema;  // positive = worsening, negative = recovering
```

Also maintained:
- Rolling window of the last 64 `laminar_index` samples
- Min/max tracking per Piranha epoch (61.44 kHz frame)
- Histogram of residual distribution across 8 satellites

### Layer 3 — Tactical Reasoning (Core 1 / Hazard3)

This is a **finite state machine with learned thresholds**, not a simple
comparator. The states correspond to simulation phases:

```
IDLE          → Cluster at rest, no active manifold
LAMINAR       → Stable computation, smooth flow mode
TRANSITION    → laminar_index slope positive, watching
TURBULENT     → Sustained stress, turbulent mode active
RECOVERING    → Slope negative, waiting for hysteresis before reverting
SINGULARITY   → Ratio residual invalid, safety hold engaged
```

The key insight: **each state has different response logic**. In TRANSITION
state, the software doesn't immediately switch — it looks at slope *and*
satellite distribution. If only 2 out of 8 satellites are showing stress, it may
be a localised mathematical region, not a global field instability. A dumb
threshold comparator cannot make that distinction. The state machine can.

**Practical implementation options (in order of complexity):**

| Approach | Complexity | RP2350 fit | Accuracy |
|:---|:---|:---|:---|
| Fixed threshold FSM | Low | Yes (< 4KB) | Good for known workloads |
| EMA + slope detector | Low | Yes (< 8KB) | Better — rejects transients |
| Kalman filter on laminar_index | Medium | Yes (< 16KB) | Best noise rejection |
| Decision tree (trained offline) | Medium | Yes (< 32KB) | Generalises to new workloads |
| TinyML / quantised neural net | High | Marginal (needs < 200KB) | Best generalisation |

Start with **EMA + slope detector**. It is already half-written in
`rplu_mode_control.md`. The Kalman filter is the natural upgrade once you have
real measurement data from Phase 3.

---

## What "LLM Inference" Actually Means Here

To be precise: not a GPT-scale language model. The RP2350 has 520KB RAM — that
rules out anything above a few hundred thousand parameters.

What it *does* mean, practically:

### Option A — Symbolic Pattern Matching on a Companion Host

A Raspberry Pi 5 or similar SBC reads the UART telemetry log produced by the
RP2350 and runs a small Python script that applies pattern matching to detect
recurring simulation signatures:

```python
# "Every time axis 7 residual exceeds 0.3, turbulence follows within 50ms"
# → pre-emptively trigger TURBULENT mode 40ms earlier next time
```

This is essentially what an LLM does when it reads logs and suggests config
changes — except here it is doing it autonomously and feeding the result back
into the RP2350's threshold table over UART.

### Option B — Quantised Small Model (Phi-3 Mini / Gemma 2B)

Running on the companion host (not the RP2350 itself). The model is given a
structured prompt containing the last N telemetry frames and asked:

```
"Current simulation phase: structural stress analysis.
 laminar_index trend: rising at 0.8 units/ms.
 Satellite 3 residual: 0.41 (threshold 0.30).
 Last RPLU switch: 2.3 seconds ago.
 Recommendation?"
```

The model returns a structured JSON action: `{"rplu_mode": 1, "plc_scan": true,
"reason": "pre-emptive switch before singularity on satellite 3"}`.

The companion host parses this and writes the action to the RP2350 over UART.

### Why This Is Not Woo

The key is that the LLM/model is **not in the control loop** — it operates at
Layer 4, on timescales of minutes, rewriting the *policy* (thresholds, state
machine transitions) rather than issuing direct hardware commands. The RP2350
Layer 3 FSM always has the final authority on real-time decisions.

This mirrors how model-based reinforcement learning works in industrial control:
the learned model updates the controller policy offline; the controller runs
deterministically online.

---

## The "Fibonacci Depth" Insight

When the RPLU is operating in turbulent mode, the effective address used most
often in the Fibonacci bank tells you *how deep* into the Q(√5) field the
computation needed to go. Index 5 = F(5) = 5 ≈ simple, index 40 = F(40) =
102,334,155 ≈ deep recursive surd.

The RP2350 can track the distribution of `rplu_cfg_addr` values during turbulent
episodes. Over time this builds a **mathematical stress signature** for your
specific simulation — which is exactly the kind of structured observation a Layer
4 model can reason over to predict future stress *before* `turbulence_alert`
fires.

This transforms the Fibonacci bank from a static lookup table into a **passive
measurement instrument**.

---

## Practical Roadmap

```
Phase 1 (now):     Fixed threshold FSM in C on RP2350.
                   EMA filter on laminar_index.
                   Log all transitions to UART with timestamps.

Phase 2 (smoke test complete):
                   Calibrate thresholds from Phase 1 logs.
                   Add slope detection. Add satellite distribution check.
                   Promote to Kalman filter if noise warrants it.

Phase 3 (after 50+ hours of runtime):
                   Feed logs to companion host.
                   Run pattern-matching script to detect recurring signatures.
                   Auto-update threshold table on RP2350 via UART.

Phase 4 (optional, if application demands it):
                   Quantised decision tree trained on Phase 3 dataset.
                   Running on companion SBC.
                   Feeds updated FSM parameters to RP2350 nightly.
```

At no point does any of this require a cloud API, a large model, or anything
that cannot run fully offline on hardware you already own.
