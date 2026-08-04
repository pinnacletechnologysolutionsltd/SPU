# INA226 capture — session handoff

**Living document, deliberately undated.** Update it as the capture progresses
rather than writing a new one; the project's dated handovers have gone stale
within hours before.

**This is not the procedure.** The procedure is
[`INA226_CAPTURE_RUNBOOK.md`](INA226_CAPTURE_RUNBOOK.md) and there must be
exactly one copy of it. This document carries **state, gates and decisions**
only. If you find a command sequence here that also appears in the runbook,
delete it from here.

---

## Verified ready (checked 2026-08-04, re-check before starting)

| Check | State |
|---|---|
| `manifest.json` loads, 30 sessions | yes — fails only at *"b00-normal is not SHA-256 sealed"*, the correct pre-capture state |
| `contract.sha256` vs `ina226_coarse_monitor_v1.json` | **matches** `58b37ec5…` |
| `test_ina226_capture.py` | **PASS**, 28 checks |
| Captures on disk | **0** — all 30 `csv_sha256` are null |
| Tooling present | `ina226_capture_pipeline.py`, `bench_metrics/{ina226_logger,power_log}.py`, `som_voronoi_explain.py` |

Re-run the top three before wiring anything. They take seconds and they are the
difference between a clean dataset and a rejected one.

## Hardware state

- **100 Ω series resistors are installed inline on all four SPI lines**
  (CS/SCK/MOSI/MISO). This was the outstanding protective item; it caps fault
  current at ~33 mA/pin if backfeed occurs. **The power-ready interlock is
  deferred indefinitely on cost grounds** — the resistors plus power sequencing
  discipline cover the same damage class.
- **Device assignment: RP2350-Zero = SPI southbridge, Pico 2 = INA226 logger.**
  Two devices, two roles, so the Padé work and INA226 never contend and no
  re-flash is needed between them.
- Wukong J11 **bottom row only** (pins 7-10). The top row is backfeed-damaged
  and retired.

### Power sequencing — unchanged, still the rule that matters

FPGA powered **first**, RP2350 connected **after**. On the way down, RP2350
off/disconnected **first**. Never leave an RP2350 driving an unpowered FPGA —
that is what destroyed J11 pins 1-3.

## The block-0 gate

Capture block 0 (`normal`, `elevated_load`, `current_limited_stall`), then
**stop and check that mean current ascends across the three classes** before
committing to blocks 1-9.

| Block 0 result | Action |
|---|---|
| Means separate cleanly | Proceed to blocks 1-9. |
| Means overlap | **Stop.** The physical load conditions are not distinguishable and no downstream scoring will rescue them. Re-establish the loads and redo block 0. |

This gate exists because blocks 1-9 are ~27 more sessions of bench time. Do not
skip it to "get the data in".

## Traps that will cost you a session

All five are already fixed in the runbook; they are listed here because each
one voids work *after* it has been done, not before.

1. **Do not run `init`.** The manifest exists and `init` is a bare
   `write_bytes` with no existence check — it silently discards the manifest and
   all 30 hash slots.
2. The manifest is **`manifest.json`**, not `capture_manifest.json`.
3. **`--probe` must be exactly `tamiya_75026_v1`.** Enforced per row at
   `ina226_capture.py:294`, but only at `seal`/`verify` — i.e. after the motor
   has run. The only remedy is re-running the whole session.
4. **`source .venv/bin/activate`** — `pyserial` is not in the system Python.
5. **Supply limit 280 mA**, matching the actuator's continuous rating. Stall
   captures ≤1.5 s, then ≥30 s unblocked to cool.

## After the 30 captures

`seal` → `verify` (must report 30 sessions, 120 windows) → `run` the frozen
study → **run it a second time to a separate output directory and byte-compare
`ina226_coarse_monitor_result_v1.json`.** Only a map passing the predeclared
replay gate proceeds to Tang and Artix SOM1 hardware replay.

Never hand-edit a hash. Fix a rejected acquisition by repeating the whole
affected session under the same block/class condition, then seal again.

## Strategic frame — why this is the priority

Settled with the project owner 2026-08-04:

- **No further hardware spend.** `som_product_roadmap_2026-07.md:191-193`
  already says *"No other spend on this path"*, and nothing since has changed
  it. One INA226 and one actuator carry the whole Phase A→C chain.
- **No platform change.** The Artix-7 100T stays. The ECP5-45F was evaluated and
  rejected on numbers: LUCAS needs 120 DSP48E1 and the ECP5-45F has 72
  MULT18X18 total — the RPLU2 probe alone already uses 72/72. ECP5 is also 40 nm
  against Artix-7's 28 nm, so a routing-bound path gets *worse*, not better.
- **Build and refine on the FPGAs already in hand.** There is enough hardware
  to produce the evidence base.

Sequence agreed for what follows:

1. **Stabilise the repository** — the current work.
2. **Prove in silicon** — the eight working spins, plus closing the Padé defect.
3. **Develop the ecosystem** — tooling and demonstrations.
4. **Then campaign** — commercial outreach, articles, posts.

The campaign starts *after* 1-3, not alongside. INA226 is the lead commercial
wedge and Phase A of the SOM product roadmap, which is why it outranks the
remaining Padé work despite that being the more interesting puzzle.

## Open, not blocking this session

The Padé `seven_over_three` defect is contained (structured inverter reverted
to default-off) and under investigation in
`spu_strategy/gtp_contract_pade_localisation_2026-08-05.md`. It needs the
Wukong and the RP2350-Zero, not the Pico 2, so it does **not** contend with
INA226 capture. See `SESSION_HANDOVER_2026-08-04.md` for where that stands.
