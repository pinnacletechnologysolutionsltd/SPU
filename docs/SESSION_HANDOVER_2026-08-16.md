# Session handover — 2026-08-16

Worked the 08-15 handover's open list top to bottom, then took the SPU-4
product direction forward. Closed items 0, 0b, 0c and 3. Froze the customer
ABI **and proved it in silicon the same day**, ran a bench session that sealed
two results, closed the register→ALU loop, amended the capture contract to v3
while that was still legitimate, and settled outreach timing.

**READ §9 FIRST.** Focus is now narrowed to one programme — the SPU-4 edge
node. Everything else is parked by name. Sections 1–8 are the record of how we
got here; §9 is what to do next.

*Written incrementally as work landed, per the 08-01 lesson.*

## 1. Repository state

- `master`, clean, **in sync with origin** — 13 commits from 08-15 that had
  never been pushed went out today, plus today's work.
- Regression **198 PASS / 0 FAIL** (was 193 at session start).
- **A bench session ran.** Two silicon results sealed, three probes on a board
  for the first time, one real defect found. See §8.
- Board-build check: **21 targets** — 18 `sha`, 2 `builds`, 1 `utilisation`.
  Self-test passes on both comparing modes. Coverage is now complete: 27 Tang
  scripts = 21 checked + 5 retired + 1 deliberately excluded.

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
| `8040917` | Manifest coverage gap closed — four targets were never added |
| `62971fe` | **`0xB0` resolved** — opaque payload with a mandatory magic |
| `d996b28` | **`spu4_abi_probe`** — the ABI reaches a board top |
| `9e3e513` | **§3.2j re-anchored in silicon** — 10/10, 4/4 control |
| `405dfcf` | **Tier 1** — register → ALU → register loop closed |
| `27d63d7` | **ABI proven in silicon** — bounded-latency gate closed |

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

## 6b. Board-build coverage gap closed, and `0xB0` resolved

**The 08-15 sweep reported widening the check to 21 targets; four scripts were
never added.** All four build and reproduce bit-exactly:

| Target | LUT4 | Board status |
|---|---|---|
| `blinky_uart` | 140 (0.6%) | has silicon |
| `rotc_tagged_probe` | 570 (2.5%) | **never run** — recorded as "awaiting board run" since 07-09 |
| `satellite_aggregator_probe` | 7,855 (34%) | **never run** |
| `whisper_v1_probe` | — (119–126 MHz) | **never run** |

Coverage is now 26 scripts = 20 checked + 5 retired + 1 excluded.
`blinky_uart` at 140 LUT4 is the cheapest known-good bench image and is a
better positive control for a capture path than the `som_bmu_probe` the §3.2j
procedure currently names.

**`0xB0` resolved (`62971fe`)**, open since 2026-07-08. The protocol
documented it as "Sentinel Telemetry, 8 nodes" while the firmware decoded
RPLU2 telemetry behind a `SPUC` magic — an opcode whose meaning depended on
which bitstream answered, violating the protocol's *own* compatibility rule 1.

Traced in RTL rather than argued from docs: `spu_spi_slave.v` imposes **no
structure at all**, streaming an opaque 512-bit port that each top drives
differently. **The decisive finding is that the 8-node layout is not reachable
on any current bitstream** — `spu_system.v` is referenced only from archived
scripts, no live `.ys`, no testbench. The doc led with the interpretation
nobody can build.

So the documentation was over-specified, not the RTL wrong. `0xB0` is now
documented as 64 opaque bytes with a **mandatory magic in bytes 0–3** and a
payload registry. New compatibility rule 5 generalises it.

*Prompted by reading Dmitry Grinberg's RISC-V critique, whose §7 is exactly
this failure — the same bytes meaning different things depending on the
implementation. It was the most directly quotable flaw in the repo.*

## 6c. The ABI now reaches a board — `spu4_abi_probe` (`d996b28`)

§5 froze the customer ABI. It then **reached nothing**: no `.ys`, no board top,
no manifest entry, verified only against its own testbench. That is the same
shape as the three defects it was written to prevent. **An ABI that has never
been synthesised is a paper contract.**

`spu13_tang25k_spu4_abi_probe` drives `spu4_customer_wrapper` through its real
handshake and prints:

```
ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7
```

**`L` is the measured latency in clocks** — `0xB7` = 183, matching the
simulated 180–183 range and inside the 200-clock bound. Bounded latency is an
*open* product gate in `SPU4_PRODUCT_CLAIMS.md`; printing it off the board
closes it with hardware evidence rather than a simulation figure.

`S` is **decoded and reported, not predicted** — whether the Φ-fold fires for
this fixture is an RTL fact, and asserting a guess would be a fabricated
expectation. The TB asserts only the bits the contract fixes.

**Post-P&R, closing `SPU4_ABI.md` open item 1:** 1,044/23,040 LUT4 = 4.5%,
500 ALU, 381 DFF, **160.26 MHz** against 12 MHz, bitstream `1e70739d…`,
reproduced 2×. **That is the PROBE, not the wrapper alone** — it includes the
UART engine, FSM and LEDs. For scale `spu4_probe` is 982/462/336, so the ABI
probe is slightly *larger* despite excluding the sequencer, decoder and
regfile: the capture and result registers that buy G2 and G3 cost about what
the programmable path cost.

### It found an ABI gap on the first integration

The first version printed `L=FFF S=00` forever. The reset synchroniser added
for G6 is a two-flop chain, so `rst_n` going high does **not** release the
datapath for two more clocks — the probe's cycle-one `start` was swallowed.
**That requirement was nowhere in `SPU4_ABI.md`.**

Now documented under G6 with the symptom, because it is silent and reads as a
*dead* wrapper rather than a *mis-driven* one. Stated as a requirement rather
than fixed in RTL: latching an early `start` would mean accepting an operation
while the datapath is still in reset, which is worse. A `ready` output is a
v1.1 candidate — an appended port, which the compatibility promise allows.

Twelve hours of simulation did not surface this. The first real integration did,
in one run. That is the argument for building the probe.

### Correction

`SPU4_ABI.md` open item 2 previously said to batch the ABI silicon run into
`spu4_probe`. **Wrong** — §3.2j is pre-registered with both bitstreams built
and staged, and touching `spu4_probe` would void it. `spu4_abi_probe` is its
own target.

## 7. Bench session — two silicon results, one real defect

Ran on the Tang 25K, Sipeed FTDI debugger (JTAG if0, C3 UART if1). **No
southbridge, no external supply** — every probe is `sys_clk` + `led` +
`uart_tx`.

### §3.2j.2 — re-anchored, 10/10 (`9e3e513`)

```
SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF      41 bytes, 10/10 loads, 250 lines
SPU4:P A=0000 B=0155 C=0155 D=0155           36 bytes, 4/4 positive control
```

Re-anchors T7.4 **and** the width fix in one session, which is why the width
fix was taken first. Control run 3× before and once **after** the trials.
`9599f5e4…` rebuilt from `511f3f3` reproduces the July hash bit-exactly, which
also upgrades §3.2j's source anchor to **CONFIRMED**. Raw captures committed at
`docs/bench_captures/2026-08-16-spu4-reanchor/`.

### §3.2j.3 — the ABI on silicon, and a product gate closed (`27d63d7`)

```
ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7   10/10 loads, 250 lines
```

**`L=0B7` = 183 clocks, measured on hardware.** Simulation said 180–183 against
a 200 bound. `SPU4_PRODUCT_CLAIMS.md`'s bounded-latency gate moves **OPEN →
SILICON (scoped)** — scope stated: one operand fixture, one board, one session.

### §3.2j.4 — three first-ever board runs

| Probe | Result |
|---|---|
| `satellite_aggregator_probe` | PASS — `SAGG:P W:2 I:9 E:00` |
| `whisper_v1_probe` | PASS — `WHSP:P F:1 E:00` |
| **`rotc_tagged_probe`** | **MUTE — genuine, not a bench fault** |

`rotc_tagged_probe` builds, reproduces `5fa8b4b8…`, closes 120–135 MHz, and
emits nothing. `blinky_uart` returned 14 lines on the same path seconds later.
Recorded as "awaiting board run" since 2026-07-09; the board run now says the
image is silent. **This is the open bring-up item, and it needs no hardware to
start** — a probe that builds and stays mute is usually a testbench-vs-top
wiring difference.

### §3.2j.5 — the bench path wedges, and how to tell

**The Sipeed FTDI's channel B stops passing UART after ~20 MPSSE loads on
channel A.** `blinky_uart`, working minutes earlier, went silent while JTAG
stayed healthy and the device stayed enumerated. **Replugging fixes it**; that
power-cycles the board, so reload before capturing.

Four probes read as failures before `blinky` showed the path was dead. The same
check later proved `rotc_tagged_probe`'s silence was real. **Keeping a
known-good discriminator is what separates those two cases** — without it they
are identical.

## 8. Tier 1 — the register loop closed (`405dfcf`)

`spu4_standalone_top` gains `OPERAND_SRC`: `0` PIN (default, unchanged), `1`
REG (register file feeds the ALU — the closed loop), `2` SELF (the ALU's
always-present `mode_autonomous`, previously hardwired off).

Proven by **poisoning**: REG mode's pins are driven `0x7FFF` and the result must
still follow the register. PIN gives `0x0155`, REG gives `0x0000` from R0's
reset quadray, and the test asserts they **disagree**.

Default is PIN, so **no bitstream moved** — verified, `spu4_probe` still builds
`0061b02f…` bit-exactly.

**Scope correction:** this does *not* make SPU-4 programmable.
`spu4_euclidean_alu` has **no opcode input and no second operand port**, and
the decoder's `alu_op` is connected to nothing. `QADD` cannot execute
regardless of routing; `QLDI` has no immediate→register path. Both need
arithmetic-core changes that re-anchor §3.2j.2.

**SPU-13 does not have this defect** — `spu13_nsa_core` loads operands from its
register bank by decoded source address.

**Recommendation on the next step:** do `QLDI` (a regfile write mux, does not
touch the ALU, and without it the closed loop can only start from R0's reset
value or the pins). Do **not** do `QADD` — narrow the stated ISA to what the
hardware does instead. Claiming an ISA you do not implement is the same failure
pattern this session spent the day removing.

## 9. FOCUS NARROWED — the SPU-4 edge node is the only programme

**John's call, 2026-08-16, closing the session.** No more spreading thin until
money and time allow. Everything below the programme is **parked by name** so
it stops competing for attention.

### What SPU-4 is, and what we are building

`knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 already designates it:
**micro-cell = edge node = SPU-4 only.** Not a small SPU-13. A self-contained
sensing node that classifies locally, checks its own ΣABCD, recovers via
Henosis locally, and reports upward only what it could not recover.

> **The deliverable: a self-contained deterministic anomaly-detection edge node
> on a $30 FPGA — sensor features in, exact classification out, with a
> continuously-checked invariant, proven end-to-end on real data.**

The classifier already exists as RTL and has never been used:
**`hardware/rtl/core/spu4/spu4_som_edge.v`** — a 4-node Kohonen BMU on rational
quadrance (`Q = p² + 3q²`, no sqrt, no division), register-backed, explicitly
sized for the SPU-4 edge budget. Its own header records the gap: *"not
instantiated by an SPU-4 core or board top, has no host weight-upload path, and
has not been synthesized or proven in silicon."*

Note the SOM that **is** cross-vendor silicon-proven is the SPU-13 seven-node
BRAM version, not this one. They are different modules and must not be
conflated in any claim.

### The programme — four of five steps need nothing we lack

| # | Step | Blocked on parts? |
|---|---|---|
| 1 | **Weight-upload path for `spu4_som_edge`** — it has none, and untrained hardware is a demo, not a product | **No** |
| 2 | **`spu4_edge_node_top`** — customer wrapper + som_edge + telemetry in one bitstream. The pieces have never been together | **No** |
| 3 | **Full-chain testbench** against the `software/lib/rational_som.py` oracle | **No** |
| 4 | **Board probe → silicon.** The Tang is connected and the bench path is understood | **No** |
| 5 | Feed it real INA226 data | Yes — parts ordered week of 08-17 |

**Start at step 1.** It is what turns `spu4_som_edge` from an experiment into a
component, it is pure RTL plus a testbench, and everything downstream needs it.

### Decide before step 1

`spu4_som_edge` defaults to **`NUM_FEATURES = 3`**. The capture contract
(`ina226_coarse_monitor_v3.json`) defines **four** features. The parameter
supports 4, but this is a deliberate call — get it wrong and the hardware and
the dataset disagree silently, which is the exact class of defect this session
spent the day removing.

### PARKED by name

SPU-13 tranches · GPU/rasterizer · PDM audio · Padé/RPLU2 · quantum · the
papers · `QADD` · ECP5 port · the `irotc_spi` router anomaly ·
`six_step_probe` trimming · A7 manifest targets · re-anchor decisions for
§3.2g.1 and §3.2k · `build_a7.sh:12` spin-name drift.

All promising. None of them this.

### Carried, because they are cheap and on the path

- **`QLDI`** — a regfile write mux, does not touch the ALU. Without it the
  register loop closed in §8 can only start from R0's reset value or the pins.
  Do this one; do **not** do `QADD`.
- **`rotc_tagged_probe` is MUTE** (§7). Real defect, needs no hardware to
  start, but it is *not* the wedge — pick it up only if the wedge stalls.
- **Order the three bench items** (§6) and set `ENC_PPR` before block 0.
- **John is reading `docs/SPU4_ABI.md`** to ratify or overturn the product
  decisions made in it on 2026-08-16. Those were mine and are properly his;
  v1.0 has no external dependents, so changes are free right now and expensive
  later.

### Outreach — DECIDED 2026-08-16: wait

No campaign until the real-sensor result exists. Artifact-led, not
education-led. Full record in the gitignored
`spu_strategy/outreach_decision_record_2026-08-16.md`; flagged here because a
decision living only in an ignored file is invisible to git and to a fresh
clone.

## 10. Corrections to earlier beliefs

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
