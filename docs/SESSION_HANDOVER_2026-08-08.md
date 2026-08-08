# Session handover — 2026-08-08

**Written incrementally during the session, not at the end.** The 2026-08-01
handover went stale within hours of being written; this one is updated as work
lands. Anything below marked *in flight* was still running when the section was
written — check the artifact, not this file, for its outcome.

Previous: [`SESSION_HANDOVER_2026-08-04-EVENING.md`](SESSION_HANDOVER_2026-08-04-EVENING.md).
The 08-07 SU3 work landed in commits `8b58629`…`616bc44` and is summarised in
[`hardware_evidence.md`](hardware_evidence.md) §3.2e.6, not here.

## One-line state

The SU3 track is closed; INA226 Phase B is parked on a dead module; the
Karatsuba swap is down to one P&R sweep, running overnight against a
pre-registered gate.

## What landed

| Commit | Time | What |
|---|---|---|
| `136ce1c` | 19:43 | INA226 failure recorded; stale Padé "contained" status corrected |
| `a6f1bf0` | 20:02 | **Corrects `136ce1c`** — failure is VBUS, not SCL; records spare + soldered harness |
| `8d722fd` | 20:25 | Runbook: bus-voltage channel check, flyback diode, electrical freeze rule |
| `d1fe2c1` | 22:46 | Pre-registered Karatsuba swap criteria |
| `d56c9a9` | 22:48 | AGENTS.md corrected against the Padé divided clock and the SU3 re-proof |

`136ce1c` was pushed before it was known to be wrong; `a6f1bf0` corrects it in
place rather than rewriting history.

## INA226 — parked, ~1 week

**The module is dead: its bus-voltage (VBUS) channel failed, while I2C and the
shunt channel remained good.** Jumpers were swapped several times and the fault
followed the module, so this is not the cable fault of 08-06/07. It is still
unusable for the capture: the contract requires a `bus_mV` column on every row,
so a module that cannot measure bus voltage fails on every class regardless of
how good its current readings are.

**Decisions (John, 2026-08-08):** order a spare INA226; solder the sensor power
path. Rev B PCB and the power-ready interlock stay deferred — the damage class
they address has not recurred since the 100 Ω resistors went in, while the
failures actually costing sessions are connector- and module-side.

**The gate had a hole, now closed.** The 08-06/07 "300/300 reads at 400 kHz"
soak exercises the I2C link and register access only. It never touched the
channel that died and would pass a module carrying exactly this fault. The
runbook now requires a two-point bus-voltage check against a DMM before any
campaign — see [`INA226_CAPTURE_RUNBOOK.md`](INA226_CAPTURE_RUNBOOK.md) §3.

**Before the part arrives:** finish the whole electrical rebuild — soldered
harness, star ground, flyback, series R < 0.1 Ω (it was 0.96 Ω degrading to
1.44 Ω), true current limit measured with a DMM rather than the supply's
display, which read 280 mA against a true 307.4 mA. The runbook's freeze rule
now makes this explicit: **nothing may change after block 0**, because the
contract has no partial-redo path.

**Ordering constraint:** the same R100 variant. The contract hard-codes
`rshunt_mohm: 100`, `shunt_lsb_uV: 5/2`, `current_lsb_uA: 25`, address `0x40`.
A different shunt fails the `shunt_equation` check on every row.

## Karatsuba — the swap is down to one sweep

**Re-verified from scratch, not from the write-up:** all three SymbiYosys tasks
pass (`small` 4×3 exhaustive, `width_plumbing` 8×6, `reset_semantics`), and
`TB_FILTER=spu13_zphi` is 46/46.

**The roadmap's "two remaining cheap proof gaps" are closed** and have been
since `6edcf9b` on 07-20. One task covers both: `width_plumbing` runs the
second width pair *and* drives a second operand tuple at `cycle >= 6`. The
paragraph at `som_product_roadmap_2026-07.md:709` reads as though they are
open; a later status line already supersedes it.

**A prior sweep exists and is not usable.** A 2×2×3 sweep ran on 07-22/23
(`build/metrics/artix7_100t_TENSEGRITY*_ZK*_S*.json`). Its PROBE candidate arm
spans three commits — `5449055`, `8aaaeaa`, `15b3118` — and LUTX moved
22797 → 22726 between them, so the RTL genuinely changed mid-arm. Seed variance
also swamps the arm difference: within LINK reference alone, seeds 1/7/13 gave
46.45 / 46.54 / 38.02 MHz.

**Sweep now running** (*in flight*): 2 spins × 2 arms × 10 seeds = 40 P&R runs,
all at commit `616bc44`, 3-way parallel, campaign
`build/zk_pnr_campaign/20260808_194219/`.

- Synthesis is done once per (spin, arm) and fed to every seed. This is
  **checked, not assumed**: a determinism gate re-synthesises a cell at a
  different seed and aborts the run if the JSON hash differs. It passed.
- Routing effort is heavy-tailed **in both arms** — a reference build took
  3935 s and a candidate build 500 s. One candidate build (`PROBE ZK1 S1`) is
  diverging rather than converging (overuse 30 → 56 → 68 across 340 iterations)
  and was deliberately left running.

**Interim, PROBE only, reference arm complete at n=10:**

| Cell | n | min | median | max | worst margin vs 25 MHz | all PASS |
|---|---|---|---|---|---|---|
| PROBE reference | 10 | 41.78 | 47.82 | 50.79 | +16.78 | yes |
| PROBE candidate | 6+ | 43.47 | 46.17 | 47.21 | +18.47 | yes |

Area (PROBE): **LUTX −44, FFX −176, DSP ±0** — the candidate is smaller on the
current RTL, a reversal of the 07-22 figures.

**No Fmax claim is available in either direction**, and this was stated before
the data existed: seed spread is ~9 MHz against an arm median difference of
~1.6 MHz.

**The gate is pre-registered** in
[`ZPHI_KARATSUBA_SWAP_CRITERIA.md`](ZPHI_KARATSUBA_SWAP_CRITERIA.md), committed
at 19/40 builds with the whole LINK arm unseen. Two judgement calls were
settled by John before the data: the full four-act bench bar stands, and a
non-converging seed does not block the swap but must be stated wherever
distributions are quoted.

## Plan for 2026-08-09

Ordered by what unblocks the most. Items 1 and 3 need no bench; item 2 does.

### 1. ~~Close out the P&R sweep~~ — DONE overnight, results below

**Campaign finished 2026-08-08T18:57Z, 40/40 runs, one deliberate failure**
(`PROBE ZK1 S1`, killed, `rc=143`). Wall clock ~11 h; the two longest LINK
routes took 16449 s and 14500 s.

**A stale-metrics trap was caught and fixed — check this before trusting any
rerun.** A killed build leaves the *previous* campaign's metrics file on disk
under the same name, so the first analyser pass silently absorbed the 07-31
`PROBE ZK1 S1` build (commit `15b3118`) and reported `n=10 complete` for a cell
that has 9. Seed-number completeness cannot see this; the seed is present, just
two weeks stale. The analyser now filters on the campaign's `started_utc` and
declares what it drops. The contamination warning fired correctly and is what
caught it. Corrected figures: PROBE candidate min 34.37 → **37.36**, worst
margin 9.37 → **12.36**.

| Cell | n | min | median | max | spread | worst margin | all PASS |
|---|---|---|---|---|---|---|---|
| LINK reference | 10 | 39.28 | 42.53 | 50.11 | 10.83 | +14.28 | yes |
| LINK candidate | 10 | 31.46 | 44.75 | 52.42 | 20.96 | +6.46 | yes |
| PROBE reference | 10 | 41.78 | 47.82 | 50.79 | 9.01 | +16.78 | yes |
| **PROBE candidate** | **9** (missing seed 1) | 37.36 | 44.58 | 47.21 | 9.85 | +12.36 | yes |

Area, deterministic per arm: **LINK** LUTX +32 (+0.13 %), FFX −176, DSP ±0.
**PROBE** LUTX −44, FFX −176, DSP ±0.

**Against the pre-registered criteria:** 1 (timing) **MET** — every candidate
build clears 25 MHz. 2 (routing reliability) **MET at the limit** — PROBE
candidate 1 non-convergence against reference 0, which is the allowed +1; LINK
0 vs 0. 3 (area) **MET** on both spins. **4 and 5 remain**: re-run formal plus
`spu13_zphi` regression at the swap commit, and the four-act bench with N ≥ 10
and a positive control.

**No Fmax claim, exactly as pre-registered.** Ranges overlap heavily — LINK
candidate alone spans 31.5–52.4 MHz across seeds, dwarfing the ~2 MHz median
difference.

So the swap is no longer a measurement question. It is criterion 4 (cheap, desk)
and criterion 5 (one bench session).

### Original plan for item 1, retained for reference

The campaign should be finished overnight. Before reading any number, check
what actually completed:

    D=build/zk_pnr_campaign/20260808_194219
    wc -l < $D/pnr_status.txt          # expect 40, or 39 + a killed straggler
    grep -v 'rc=0' $D/pnr_status.txt   # any non-zero exit is a failed cell
    cat $D/provenance.txt

Then run the analyser (currently in the session scratchpad,
`zk_analyse.py`). It reports per-arm Fmax distributions, constraint margins and
area deltas, and it checks whether the differing `git_commit` stamps came from
commits that touched source — they did not, all three were docs-only.

**Judge against [`ZPHI_KARATSUBA_SWAP_CRITERIA.md`](ZPHI_KARATSUBA_SWAP_CRITERIA.md),
which was pre-registered before the LINK data existed. Do not amend it to fit
the result.** Expected outcome on the PROBE evidence: criteria 1-3 met, leaving
criterion 4 (re-run formal + regression at the swap commit) and criterion 5
(four-act bench, N ≥ 10 with a positive control) as the remaining work. If so,
the swap becomes a scheduling decision, not a measurement one.

**`PROBE ZK1 S1` was terminated at 03:31:00 on 2026-08-09** after diverging —
router overuse worsened monotonically from 30 at iteration 101 to 87 at
iteration 442. It recorded `rc=143`. It was killed because twenty LINK builds
were still queued at over an hour each, making that worker slot worth roughly
seven completed builds; the earlier plan to let it grind assumed ~2 hours of
work remained, not ~12.

Per criterion 2 it does not block the swap — the reference arm also produced
hour-long routes (`PROBE ZK0 S23`, 3935 s), so routing difficulty belongs to
the design under nextpnr rather than to the multiplier. But **the PROBE
candidate cell is n=9, missing seed 1, and must be quoted that way.** Full
record and the overuse trajectory:
`build/zk_pnr_campaign/20260808_194219/NONCONVERGED_PROBE_ZK1_S1.md`. The
analyser now prints a completeness line per cell so a missing build cannot pass
as a smaller sample.

### 2. LUCAS 200-step bench session (Wukong + RP2350-Zero)

Prerequisites are verified (see Open, below). This closes an **unbacked silicon
claim**, which is why it outranks the other carried bench items.

Power sequencing: FPGA powered first, RP2350 connected after; reverse on the
way down. J11 **bottom row only**. `usbreset 1209:c0ca` before every
DirtyJTAG load.

Deliverable: a `hardware_evidence.md` section in the §3.2e.6 format — Date,
Scope, build/load commands, bitstream SHA-256, **raw** proof lines,
Interpretation. Then either confirm `LUCAS_QUICKSTART.md` §5's transcript
against what the bench actually printed, or correct the document to match the
bench. Not the other way round.

### 3. Gemini claim-ledger audit — receive and verify

Contract issued 2026-08-08:
`spu_strategy/gtp_contract_claim_ledger_audit_2026-08-08.md`. When findings
land, run the contract's five acceptance gates before believing any of it:
citations resolve at HEAD, all three calibration items correct, ten random
`BACKED` rows re-checked, ten random `UNBACKED` rows re-checked for missed
backing, and `git status` clean with the campaign intact.

Remediation is a **separate** tranche, scoped after the size of the problem is
known.

### 4. If time remains — composition/adapter policy

The 08-07 service-composition boundary in `CURRENT_STATUS.md` defers shared
datapaths until a cross-domain adapter policy and an oracle-backed composition
trace exist, and nothing currently produces either. The repo blocks its own
next integration step. Needs John's judgement on product claims, not
file-reading.

### Not tomorrow, but this week

Order the spare INA226 (same R100 variant) and complete the electrical rebuild
— soldered harness, star ground, flyback, series R < 0.1 Ω, true current limit
by DMM — **before** the part arrives, so the runbook's freeze rule holds.

## Traps found this session

- **`collect_fpga_metrics.py` stamps `git_commit` with HEAD at *collection*
  time**, not the commit built from. Three docs commits during this sweep made
  it look like the campaign spanned four commits. Treat that field as "when the
  number was written". Real provenance is the synth JSON hash, recorded per arm
  in the campaign's `synth_hashes.txt`.
- **`spu_strategy/` is gitignored**, so the roadmap correction made this session
  is local-only and invisible to anyone cloning the repo.
- The sweep harness has **no per-build timeout**. A non-converging build holds a
  worker slot indefinitely.

## Open

- **Sweep results** — run
  `python3 <scratchpad>/zk_analyse.py` when it finishes. Driver and analyser are
  still in the session scratchpad, not the repo; they belong in `tools/` if this
  becomes a repeatable check.
- **Three commits unpushed** at time of writing: `8d722fd`, `d1fe2c1`,
  `d56c9a9`.
- ~~**SOM-SIDECAR dead-write-path fix**~~ — **CLOSED, no board time needed.**
  The fix is `d5a17e6` (07-16 06:54, `spu_spi_cfg.v` + Tang sidecar top). The
  silicon proof is `hardware_evidence.md` §3.2g.2, added by `28e5c81`
  (07-16 20:24), which explicitly describes the run as following the
  `spu_spi_cfg.v` command-acceptance repair. Verified structurally, not from
  the prose: `d5a17e6` is an ancestor of `28e5c81`, and `git diff d5a17e6
  28e5c81 -- hardware/rtl/peripherals/io/spu_spi_cfg.v` is **empty**, so the
  proven bitstream was built from the byte-identical fixed file. The roadmap's
  guess that the 07-*17* runs might cover it was close but a day late.
- **LUCAS 200-step ledger entry** — **prerequisites verified 2026-08-08, the
  session is ready to run.** Bitstream `build/spu_a7_100t_LUCAS.bit` (Aug 3,
  post-reset-fix, passed the 08-03 sweep); evaluator `tools/lucas_demo.py
  --steps 200`; firmware rebuilt by the documented cmake step at 250 kHz, far
  under the `clk_fast/6` ceiling; procedure in `LUCAS_QUICKSTART.md` §4-5.
  Note the diag SPI default was 2 MHz before `db55c94` (07-31) and is 250 kHz
  now — do not flash the stale Jul 17 `.uf2` left in
  `build/rp2350_lucas_demo/`; run the cmake step, which regenerates it.

  **It closes an evidence gap, not just a bookkeeping item — this is the SU3
  pattern again.** `LUCAS_QUICKSTART.md` §5 shows a transcript asserting
  *"silicon: bit-exact against ground truth for all 200 steps"*, but
  `hardware_evidence.md` has **no 200-step entry**: its LUCAS entries are
  §3.2e, §3.2e.1 and §3.2e.2, the last covering the four sidecar ops on 07-03,
  before the J11 remap. Line 2354 verifies PMUL/PINV, not the loop. The
  transcript is formally sample output in a walkthrough, so it is not a false
  claim — but a reader takes it as an achieved silicon result and nothing in
  the evidence base backs it. Treat the 200-step silicon claim as
  **unbacked pending this run**.

- **ROBOTICS spin synth re-check** — carried, needs the Wukong.
- **Composition/adapter policy** — the 08-07 service-composition boundary defers
  shared datapaths until a cross-domain adapter policy and an oracle-backed
  composition trace exist. Nothing is currently producing either; the repo
  blocks its own next integration step.
