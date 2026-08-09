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

## 2026-08-08 — VBUS channel failed; capture parked on a replacement part

**Read this first. Everything below is currently unrunnable.** The module's
**bus-voltage (VBUS) channel has failed**, while I2C and the shunt channel
remain good. A replacement is roughly a week out, so Phase B physical
acquisition is parked until then. Nothing else in the project is blocked by
this: INA226 uses the Pico 2, while the Wukong and RP2350-Zero tracks are
untouched.

> **Correction.** An earlier version of this block — and commit `136ce1c`,
> already pushed — said the *SCL path* failed and the module could not read
> currents. That was wrong on both counts: the link works and current readings
> are fine. The fault is confined to the bus-voltage channel. Corrected
> 2026-08-08 on John's account of the bench.

**The part is unusable for this capture even so, and that is not a judgement
call.** The contract requires a `bus_mV` column on every row and applies a
bus-voltage tolerance per class (`ina226_coarse_monitor_v2.json`); the v2
amendment exists precisely because that tolerance was unsatisfiable for
`current_limited_stall`. A module that cannot measure bus voltage cannot
satisfy the contract on any class. Jumpers were also swapped several times and
the failure followed the module rather than the wiring, so this is not a cable
fault — do not repeat the wire-swap hunt on this module.

**A hypothesis, explicitly untested.** The channel that died is the one
directly exposed to rail transients from switching an inductive load. That is
suggestive, not evidence — the back-EMF damage theory was investigated on
08-06/07 and *not* supported, and one failure is not a mechanism. It is a
further cheap reason to fit the flyback diode during the rebuild, and a thing
to watch if the replacement loses the same channel.

The SDA/SCL asymmetry below is unrelated to this failure. It is retained
because it is diagnostic for the *next* wiring fault:

- **SDA is driven at both ends**, so a marginal SDA wire produces the confusing
  partial signature recorded below: address ACKs succeed while longer register
  reads fail.
- **SCL is driven only by the master**, so a genuinely open SCL produces
  *total* failure — no ACK at all. If the address scan still ACKs, SCL is not
  fully open and the fault is somewhere else.

**Decision, 2026-08-08 (John):** order the spare INA226 and solder the sensor
power path. Rev B PCB and the power-ready interlock stay deferred. Rationale
and the ordering constraint (same R100 variant, or the contract's
`shunt_equation` check rejects every session) are in
[`BENCH_BOM.md`](BENCH_BOM.md) §2.

**Conflicting record resolved 2026-08-08.** `BENCH_BOM.md` §2 was right all
along — *"failed its VBUS channel 2026-08-07 with I2C and shunt both perfect"*
— and this block was the one that was wrong. The two records now agree.

**What this costs us as evidence.** The 08-06/07 "300/300 reads, zero failures"
soak was a genuine recovery, but note what it actually exercised: the I2C link
and register reads. It is an **I2C-health soak, not a channel-health soak**,
and the channel that later died is one it never checked. So it did not fail to
predict the failure so much as never test for it.

Two consequences for the replacement:

1. Treat a passing I2C soak as a necessary precondition for starting the
   30-session capture, never as evidence the part will survive it. Prefer
   losing a session mid-block to a dead part over discovering it after sealing.
2. **Add a bus-voltage sanity check to the pre-capture gate** — a known supply
   voltage read back within tolerance. The current soak would pass a module
   with exactly this fault, which is the gap that let it through.

## 2026-08-06/07 — a failing SDA jumper masqueraded as a dead module

Read this before anything below it; several statements further down are now
stale — and see the 08-08 block above, which supersedes its "resolved" state.

**Resolved.** The module is healthy: 300/300 reads at 400 kHz, zero failures,
`MFG=0x5449 DIE=0x2260`, shunt offset back to −5 µV. **The cause was a single
bad SDA jumper wire.** Replacing it fixed everything.

**The diagnostic trap, because it cost hours and will recur.** When the
failures began, both SDA and SCL showed pull-ups, so a disconnected SDA was
ruled out — wrongly. **A pull-up probe is a DC, high-impedance test; a wire can
pass it while being far too resistive or intermittent to carry signalling.**
The wire only revealed itself much later by going fully open (`GP8=00000000`
while `GP9=11111111`).

Symptoms it produced, all of which look like damaged silicon:

- address scan succeeds while every `readfrom_mem` fails — SDA is bidirectional
  and driven by both ends, so a short ACK survives where a longer transfer does
  not;
- failure rate swinging between ~10 % and 100 % across minutes;
- identical failures at 400/200/100/50 kHz, on hardware *and* soft I2C, and on a
  second pin pair (I2C1 GP6/GP7);
- unaffected by a module power-cycle or by disconnecting the entire power side;
- one nonsense analog reading (`shunt_uV = 6095` with the supply off) that was
  simply a corrupted transaction.

**Rule for next time: if the address ACKs but register reads fail, replace the
SDA wire before concluding anything about the part.** Swap the wire, don't
reseat it — several failures today clustered on specific jumpers.

**Not established:** the earlier back-EMF/damage theory has no evidence behind
it. A flyback diode across the motor remains sensible practice for an inductive
load, but it is hygiene, not a fix for an observed fault.

### What is already done and needs no repeating

- MicroPython v1.28.0 flashed on the Pico 2; `ina226_logger.py` installed as
  `main.py`, hash-verified. Full chain proven: identity check, 100 Hz stream,
  cadence 9–11 ms against the 8–12 ms gate.
- **Two `power_log.py` defects found and fixed**, each of which would have
  silently rejected every one of the 30 sessions at seal:
  stale-serial-buffer rows producing a bogus first cadence interval, and
  motor-noise line-splitting that yields a corrupted `t_ms` which still parses.
  The second is now caught at capture time with a nonzero exit.
- **Contract v2** (`ina226_coarse_monitor_v2.json`) supersedes v1; v1 left
  byte-identical for provenance. Manifest needs a one-time re-`init`.
- Runbook corrected: missing `VBS` row, `VIN−` is a positive node, star-ground
  requirement, unstable `/dev/ttyACM*` numbering.

### Bench numbers measured before the failure (for the rebuild)

| Quantity | Value |
|---|---|
| Open-circuit bus | 3100 mV |
| Breadboarded power path | 0.96 Ω, degrading to 1.44 Ω within one session |
| Free-running motor | 95–98 mA |
| `elevated_load` (hands-off mechanical) | 240 mA |
| Stall, supply in CC | 307.4 mA — **supply displayed 280 mA** |
| Block-0 ascending-means gate | **passed**: 98.3 → 240.8 → 307.4 mA |

The supply's ~10 % current-limit error must be re-measured, not read off the
dial, before the manifest re-`init`.

### Resume sequence

1. Logic-only soak (300 reads at 400 kHz) — the gate is **zero** failures, not
   "the scan works." A single successful scan proves almost nothing; that is
   what hid the bad SDA wire for hours.
2. Reconnect the power side: VIN+, VIN−, and **VBS to the VIN− node**.
3. Star-ground power path: motor return direct to the supply terminal.
4. Measure series R (open-circuit vs loaded); target < 0.1 Ω.
5. **Characterise the bench supply** — procedure now in
   [`INA226_CAPTURE_RUNBOOK.md`](INA226_CAPTURE_RUNBOOK.md) §2. Needs only a
   DMM and the actuator, **not** the INA226, so do it while the replacement
   part is in transit. Five readings minimum per quantity; record min/median/max
   below rather than a single figure. Then trim so the loaded rail sits near
   3000 mV and feed the measured limit into `init`.

   **Measured 2026-08-09. Voltage column resolved; current column is NOT.**

   | Quantity | Front panel | Measured | Note |
   |---|---|---|---|
   | Open-circuit voltage | 3.000 V | **3.06 V** | panel reads ~60 mV low (+2.0 %) |
   | Loaded, breadboarded path | 3.000 V | **2.80 V** | 260 mV droop — see below |
   | Loaded, soldered direct | 3.000 V | **3.05 V** | 10 mV droop |
   | Regulating current at CC clamp | 280 mA | **UNRESOLVED** | see "current column" below |

   **The power path was the whole problem, and it is fixed.** At ~96 mA
   free-running, the breadboarded path dropped 260 mV — an implied **~2.7 Ω**,
   nearly double the 1.44 Ω measured on 08-06 and 27x the <0.1 Ω target. Soldered
   directly to the supply terminals the same load drops 10 mV: **~0.10 Ω**, at
   target. The breadboard alone accounted for ~2.6 of the 2.7 Ω.

   That decides the capture budget. At 0.1 Ω the non-stall classes sit within
   ~25 mV of each other (`normal` 3.050 V, `elevated_load` ~3.036 V) against a
   ±5 % band of roughly ±150 mV. At 2.7 Ω, `elevated_load` would have landed
   ~400 mV out and failed the bus-voltage gate on physics alone, whatever
   nominal was declared.

   **Trim and nominal.** Set the panel to ~2.95 V to land a loaded rail near
   3.000 V, then declare `nominal_bus_mV = 3000` at `init`. `nominal_bus_mV` is
   a *choice made at init*, not a contract constant, and it must be set from the
   measured **loaded** rail — declaring 3000 against a rail that sits at 2900
   spends a third of the ±5 % budget before any noise.

   **Discard the old stall-voltage figures.** Block 0 measured the stall rail at
   1478-1501 mV; it now collapses to **680-800 mV**. Both are correct for their
   own rig: with 2.7 Ω in series much of the supply's voltage never reached the
   motor, and at 0.1 Ω the stalled winding draws harder before the clamp
   engages. **Stall bus voltage is rig-dependent**, so the 08-06 numbers describe
   a rig that no longer exists. It also confirms the v2 exemption independently:
   at 0.7 V the stall class is nowhere near ±5 % of nominal on any bench.

   ### The current column — unresolved, and why

   Two measurements of the same quantity disagree by 40 %:

   | Date | Instrument | Panel | Measured |
   |---|---|---|---|
   | 2026-08-06 | INA226 (R100) | 280 mA | 307.4 mA (+10 %) |
   | 2026-08-09 | DMM, current range | 280 mA | 185 mA (−34 %) |

   **The DMM is the prime suspect, not the supply.** It intermittently stops
   reading on its amp ranges — the classic signature of a blown or high-resistance
   fuse in the current path, which under-reads, in the direction observed. A
   failing meter explains both readings; a supply wandering 40 % between sessions
   explains only one. The ZK-5KX is probably stable at ~280-307 mA when set to
   280.

   **Do not write 185 mA into the manifest.** `init` freezes
   `--supply-limit-ma` across all thirty sessions and it cannot be corrected
   without re-running them.

   **Resolve it with the R100 shunt method**, which avoids the meter's current
   path entirely by using its voltage function — the one that has been
   self-consistent all session:

   1. Wire a known 0.1 Ω in series. **The dead INA226's R100 is intact** — its
      failure was confined to the bus-voltage channel — so it serves as a
      calibrated shunt.
   2. Measure the drop in millivolts during stall; current is `V / 0.1`.
      Expect ~28 mV at 280 mA.
   3. Five-plus readings, 1.5 s stalled / 30 s cooling.

   This has a second payoff: it is the same measurement principle the
   replacement INA226 uses, so it cross-validates the sensor path. If the new
   module later disagrees with this figure, you will know which to doubt.

   **A clamp below ~240 mA would break the study**, so this must be settled
   before block 0: `elevated_load` (~240 mA) and `current_limited_stall` would
   both sit against the clamp and the three classes would collapse to two. That
   failure would present as "the SOM cannot separate the classes" — the exact
   shape of the three prior negatives — when the real cause was the bench.
6. Re-`init` the manifest against **v2** with measured values.
7. Fresh block 0 — the three captures on disk were taken through the old
   breadboard path against the v1 manifest and must be discarded.

## Verified ready (checked 2026-08-04 — SUPERSEDED, see the block above)

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

**The Padé `seven_over_three` defect is RESOLVED (2026-08-05), superseding the
"contained, structured inverter default-off" state described here earlier.** A
bracketed campaign with a 50 MHz positive control (0/10 PASS) and canonical
brackets (20/20 PASS) showed the divided clock clean at 40/40 across four
candidate images; `A7_CLK_DIV_LOG2=1` with `A7_FREQ=25` is a shippable
timing-closed configuration, the FP4 structured inverter is back to default-on
(`95cdaf5`), and no RTL changed. Evidence:
`spu_strategy/gtp_findings_pade_divided_clock_2026-08-05.md`. What remains is
datapath pipelining toward a 50 MHz product target — an optimisation, not a
defect. It needs the Wukong and the RP2350-Zero, not the Pico 2, so it does
**not** contend with INA226 capture.
