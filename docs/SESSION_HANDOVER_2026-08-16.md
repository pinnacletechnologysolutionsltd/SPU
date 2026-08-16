# Session handover — 2026-08-16

Worked the 08-15 handover's open list top to bottom, then took the SPU-4
product direction forward. Closed items 0, 0b, 0c and 3. Froze the customer
ABI, pre-registered the next bench session, settled outreach timing, and
amended the capture contract to v3 while it was still legitimate to do so.

*Written incrementally as work landed, per the 08-01 lesson.*

## 1. Repository state

- `master`, clean, **in sync with origin** — 13 commits from 08-15 that had
  never been pushed went out today, plus today's work.
- Regression **196 PASS / 0 FAIL** (was 193 at session start; +1 dissonance
  width TB, +1 customer wrapper TB, +1 bench-metrics firmware test).
- Board-build check: **16 targets** — 13 `sha`, 2 `builds`, 1 `utilisation`.
  Self-test passes on both comparing modes.

| Commit | Change |
|---|---|
| `2c08d2a` | `southbridge` measured at 267% — capacity boundary in the ledger |
| `f885fce` | Last two failing spins measured; `six_step` is a router problem |
| `8598308` | **`dissonance` widened to 19 bits** — it read laminar at maximum fault |
| `b8f39c3` | Handover item 3 closed; six_step routing trend extended |
| `d5d91fb` | **Five over-capacity Tang spins retired as targets** |
| `c203852` | **Utilisation check mode**; `six_step_probe` quarantined on it |
| `e9a46c4` | Bench buy-now list cut to three; logic analyzer recovered |
| `460aeec` | `router2` NO GO recorded |
| `37c1339` | **SPU-4 customer ABI v1.0 frozen** |
| `c7b4b99` | This handover |
| `f7d8919` | §3.2j bench procedure pre-registered, both bitstreams staged |
| `69221d6` | Outreach wait decision; encoder sourcing alternatives |
| `2cd434c` | **`ina226_logger_v2`** with an encoder channel; silent row-drop fixed |
| `26faebe` | **Capture contract amended to v3** — the `pulses` covariate |

## 2. The dissonance defect was worse than recorded (`8598308`)

The 08-15 handover called it "a false laminar reading". Measured:

| Vector | True residual | Old reading |
|---|---|---|
| `A=B=C=D=0x8000` | **−131072**, the maximum reachable | **`0x00` — perfectly laminar** |
| `A=B=C=D=0x7FFF` | 131068 | `0x04` |

A saturating fault signal that reads clean under the largest possible fault,
failing silently in the unsafe direction. Fixed to **19 bits** — 18 holds the
range, but negating −131072 in 18-bit signed wraps back to itself, so the abs
step needs the extra bit.

Also **deduplicated** into `spu4_dissonance.v`. It was a copied block in two
files kept in step by a comment; they had already diverged once.

Cost +3 LUT4 / +2 ALU / 0 DFF. Bitstream `cbd6f83a…` → **`0061b02f…`**,
reproduced 3×. **Golden line unchanged**, so one bench run re-anchors both this
and T7.4.

**Worth keeping:** 2000 random vectors all PASSED against the buggy RTL.
`$random` never draws four same-sign extremes. Targeted corners caught this.

## 3. Tang capacity — measured, then decided (`2c08d2a`, `f885fce`, `d5d91fb`)

Every failing target now has a number (`hardware_evidence.md` §3.6g):

| Target | LUT4 / 23,040 | Disposition |
|---|---|---|
| `series_stream_probe` | **305%** | RETIRED |
| `southbridge` | **267%** | RETIRED |
| `rotc_probe` | 145% | RETIRED — *had real silicon at 13,352 LUT4* |
| `som_southbridge` | 127% | RETIRED |
| `som_probe` | 103% | RETIRED — best trim candidate |
| `six_step_probe` | **96% — fits** | quarantined, see §4 |
| `irotc_spi` | 52% | the lone routing anomaly |

Retired **by decision, not defect**. Scripts and RTL kept with `RETIRED`
headers; re-entry is trimming under 23,040 LUT4 and re-adding. Stale build
instructions were cleared from AGENTS.md, SPIN_CATALOG.md,
build_and_bringup_guide.md and rotc_robotics_bringup_plan.md — retiring a
target means removing the procedures that tell people to run it.

**Nothing evidential was withdrawn.** §3.2g stands, ROTC keeps A7 coverage,
Tang SOM survives via `som_sidecar`/`som_bmu_probe`/`som_hydrate_probe`.

**Growth nobody was watching:** `rotc_probe` 13,352 → 33,456 (2.5×);
`southbridge` known not to fit at 25.5k on 07-11, now 61,439. AGENTS.md was
still quoting "89% LUT" for it.

## 4. Utilisation gate — a third check mode (`c203852`)

`six_step_probe` fits, places in 484 s, and passes timing at 25.77 MHz, but
does not route. Retiring it would discard the only spin on the capacity
boundary; gating it on buildability would make the check permanently red.

So the gate changed instead. `"check": "utilisation"` synthesises, packs,
compares LUT4 against a ceiling, **skips placement and routing** — `--pack-only`
returns the number in ~2 s. Baseline 22,212/23,040 = 96.4%, ceiling 100%.
Growth below the ceiling is recorded but does not fail, so it shows in a
manifest diff at review time.

Had this existed, all five retirements would have tripped at 101%.

**Both routing levers are closed by measurement — do not re-try:**
- *Longer timeout*: arc rate decayed 5.83 → 1.39 arcs/s over 68 min, 65,740 of
  109,475 arcs unrouted at iteration 140k. Decaying, not converging.
- *`--router router2 --seed 7`*: 25,087 wires overused at routing iteration 2.

**Trimming is the only route left.**

**Correction:** I called `six_step` a second `irotc_spi`. It is not. It grew
13,576 → 22,212 LUT4 with **DFF unchanged at 1,518** — pure combinational
growth, so it is ordinary congestion at 96%. `irotc_spi` failing at 52% is
still a population of one.

## 5. SPU-4 customer ABI v1.0 — FROZEN (`37c1339`)

`docs/SPU4_ABI.md`, `hardware/rtl/core/spu4/spu4_customer_wrapper.v`,
`hardware/tests/spu4/spu4_customer_wrapper_tb.v` (19 checks).

The strategy put this module at the centre of the product architecture and it
**existed nowhere** — named only in a gitignored strategy doc while the claim
ledger pointed at `spu4_standalone_top`, a bring-up vehicle.

**That gap has now produced three defects, found by accident, weeks apart:**

1. `dissonance` absent from the named product interface (T7.4, 08-14)
2. The residual reading laminar at maximum fault (§3.2j.1, today)
3. **`uart_tx` and `node_tx[31:0]` are declared outputs with NO drivers.** Both
   read `z`. The "cluster link" is a comment placeholder. Every consumer,
   including the silicon probe, left them unconnected.

One failure repeated: *a product surface asserted in a document and never
exercised.*

Six guarantees, each with a check that fails if withdrawn — outputs all driven,
inputs captured at `start`, results registered and held, `start`-during-`busy`
ignored **and reported**, bounded latency, synchronised reset. **G6 encodes the
A7 lesson**: a raw async reset pad caused that three-week outage, and a customer
must not be able to reproduce it by wiring a button to `rst_n`.

**Latency is BOUNDED, NOT FIXED — 180–183 clocks over 124 operations, bound
200.** I wrote the check expecting *fixed*; it failed. The multiplier is serial,
so timing is operand-dependent. The TB pins both the bound and the 8-clock
spread.

**Excluded, with reasons:** the sequencer and program memory, because that path
is **not closed** — the regfile's read ports are dangling and `mode_auto` is
hardwired to 0, so register operands can never reach the ALU. Freezing an ABI
over that would freeze a defect.

**Additive only** — `spu4_standalone_top` is untouched, so no bitstream moves
and §3.2j's pending bench run stays valid.

Resource cost is a **synthesis estimate only**: 294 LUT, 119 ALU, 433 flops.
Not comparable to the probe's post-P&R figures.

## 6. Bench purchases — three items (`e9a46c4`)

John confirmed diodes and enamel wire are on hand. Buy-now is: **INA226 ×2
(R100), IR slotted optical encoder, 8-channel logic analyzer.**

**The encoder is co-blocking with the INA226, not a follow-on.** The capture
contract is `frozen_before_physical_capture_or_scoring`, 30 sessions, and its
four features are **current-only** — RPM appears nowhere. RPM must be recorded
*while* capturing; it cannot be retro-fitted. Ordering it after block 0 is
sealed forces a choice between discarding sessions and losing the ability to
condition on operating point — the exact flaw behind all three prior negatives.

**DECIDED and DONE 2026-08-16: the v3 contract amendment.**
`ina226_coarse_monitor_v3.json` adds a `pulses` column; validator, pipeline,
synthetic fixture and tests all moved. Legitimate only because
`sessions_sealed_when_amended: 0` — that latitude closes at block 0.

**`pulses` is a COVARIATE and must never become a feature.** Rotation
trivially separates `current_limited_stall`, so a model given it would score
well while proving nothing about current-based anomaly detection. The feature
list is unchanged at four current-derived values and the test suite asserts
`"pulses" not in contract["features"]`.

**No class-conditional pulse gate**, deliberately — it is not yet known
whether a current-limited stall on this rig stops rotation or merely slows it,
and a threshold invented before measuring would encode a guess as a validation
rule. Block 0 answers it.

Firmware is ready: `tools/bench_metrics/ina226_logger_v2.py` (GP6, raw edge
counts, `ppr` in the header), 17 host-side checks in the regression. **Set
`ENC_PPR` to the measured value of whatever encoder is actually used before
capturing.**

**The logic analyzer was a recovered omission** — the roadmap's 07-19 amendment
listed it; it never reached BENCH_BOM.

## 7. Open

1. **§3.2j bench re-run — DECIDED: this is next session's work.**
   **Everything is prepared; next session is execution, not design.**
   Procedure: `docs/BENCH_PROCEDURE_2026-08-3_2j_SPU4_REANCHOR.md`, with Part 0
   pre-registration and Part 1 rig already filled in.

   Both bitstreams are **built, hash-verified and staged** in
   `build/bench_3_2j/` (gitignored, regeneration commands are in the procedure):

   | Role | File | SHA-256 |
   |---|---|---|
   | Trial | `TRIAL_head_0061b02f.fs` | `0061b02f…56d67c` |
   | **Positive control** | `POSCTL_pre_t74_9599f5e4.fs` | `9599f5e4…22664` |

   **The positive control is the part worth knowing about.** It is the
   *pre-T7.4* bitstream, rebuilt from commit `511f3f3` on 2026-08-16 —
   reproducing `9599f5e4…` **bit-exactly**, a fifth independent reproduction.
   It must emit the **36-char** line with no `R=` field. If both images produce
   the same line, the capture path is not reporting what is on the board and
   the session is void. That directly tests the failure this session is most
   exposed to — *did the new image actually load* — which a bench-works control
   cannot distinguish.

   Run controls **first**: if a control run afterwards fails, every trial before
   it is already in doubt. 10 trial loads, 3 control loads, reload between
   every run, report the rate. Re-anchors T7.4 *and* the width fix in one
   session because the golden line is unchanged. Gates T7.
2. **§3.2g.6 bench re-run** — needs the full A7 + RP2350 southbridge rig.
3. **Order the three bench items** (§6). The RPM contract question is settled —
   v3 is in. **Set `ENC_PPR` in the logger and confirm the encoder counts on
   the Pico before block 0**; an all-zero pulse column is indistinguishable
   from a stalled motor, so disconnection cannot be detected from the data.
4. **`six_step_probe`** — trimming is the only remaining route. Not urgent; the
   utilisation gate is watching it.
5. **Re-anchor decisions** for §3.2g.1 and §3.2k. John's call.
6. **A7 targets are still outside the manifest.** Chipdb exists; build time only.
7. **The two remaining `builds`-mode targets** could move to `utilisation` —
   optimisation, not a fix; both build fine.
8. Spin-name drift in `build_a7.sh:12` — cosmetic, still unfixed.

### Outreach — DECIDED 2026-08-16: wait

**No campaign starts until the real-sensor result exists** — not even a gentle
or educational one. John's call, reaffirming the 2026-08-04 sequencing.

Order: order the three bench items → §3.2j → capture campaign → *then*
artifact-led post → warm network → sniper email.

Reasoning, in one line each: nothing is blocked on audience (parts, §3.2j and
Gate A are what is blocked); you get one first impression and the Iris demo is
a classification benchmark rather than the wedge, so posting now means having
nothing to sell anyone who engages; content is the slowest path to revenue on
this project's own list, and if pressure sharpens the answer is paid
engineering work, not more content. Nothing is lost by waiting — the material
is generated as a side effect of working honestly and already carries numbers.

Also settled: **artifact-led, not education-led.** "Did anyone replicate it?"
is answerable; "did the education land?" is not.

**Full record — including the reconciliation of three conflicting outreach
documents and which one governs — is `outreach_decision_record_2026-08-16.md`
in the gitignored `spu_strategy/` directory.** Flagged here because a decision
that lives only in an ignored file is invisible to git, to handover
orientation, and to a fresh clone; that hazard already caused a duplicated
contract on 2026-08-04. Kept out of tracked `docs/` deliberately, since this
repo publishes its RTL and that file is commercial positioning.

**Revisit on a result, not on a new strategy document.**

### Not to be done
- **The `irotc_spi` router anomaly.** Population of one, nothing depends on it.
- **ECP5 port.** Right second vendor eventually, but John's 08-16 call is that
  boards/interlock/sensor suite come before any further FPGA hardware. Also
  note the 08-04 ECP5 rejection was an **SPU-13/LUCAS DSP** verdict, not an
  SPU-4 one — don't cite it either way.
- **Seeds or alternate routers on `six_step`.** Covered ground, twice.

## 8. Corrections to earlier beliefs

- I called `six_step_probe` a second `irotc_spi` routing anomaly. It is
  congestion from growth at 96%; DFF unchanged proves it. See §4.
- I recommended starting outreach now, citing the 08-13 strategy doc. A
  2026-08-04 decision says the campaign starts **after** stabilise → silicon →
  ecosystem, *not* alongside. The 08-13 doc may soften that to an "educational
  pilot", but I presented it as settled when it is not. **John's call.**
- I proposed ECP5 as SPU-4 vendor #2 without knowing an ECP5 migration had been
  evaluated and rejected on 08-04. That rejection is about SPU-13 DSP capacity
  and does not decide the SPU-4 question — but I should have known it existed.
- Two testbench races in my own wrapper TB made two checks pass vacuously
  against the previous operation's result registers. Found and fixed before
  commit; the fix is to poison the result registers first.
- I expected the wrapper's latency to be fixed. It is not — 180–183.
