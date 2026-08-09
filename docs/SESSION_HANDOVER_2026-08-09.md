# Session handover — 2026-08-09

**Written as work landed.** Previous:
[`SESSION_HANDOVER_2026-08-08.md`](SESSION_HANDOVER_2026-08-08.md), whose
"Plan for 2026-08-09" is now executed — items 1, 2 and 3 are done, item 4 was
dropped, item 5 remains.

## One-line state

**Both open silicon-evidence gaps are closed.** The Karatsuba candidate — the
production default since 2026-07-23 — now satisfies all five pre-registered
swap criteria, and the LUCAS 200-step claim that had sat unbacked since
2026-07-17 is evidenced.

## What landed

| Commit | What |
|---|---|
| `a6e462d` | Sweep complete: criteria 1-3 met; stale-metrics trap found and fixed |
| `125aabf` | Criterion 4 met; the swap turned out to have shipped on 07-23 |
| `95a188f` | TENSEGRITYLINK gap recorded as the top bench item |
| `d0d8c3c` | Four-act campaign plan |
| `26a646d` | Four SD traps recorded |
| `78cb516` | **§3.2l.1 — TENSEGRITYLINK four acts proven on the candidate, 10/10** |
| `714ce8c` | All five swap criteria met |
| `0ac49ae` | `spu_host` `connect()` fixed for already-booted boards |
| `317a0f4` | **§3.2e.7 — LUCAS 200-step zero-drift proven, 10/10** |
| `7c59b57` | This handover |
| `0f8e639` | Bench-supply characterisation procedure (DMM-only, no INA226 needed) |
| `8451aae` | Sweep + four-act drivers promoted into `tools/` |
| `f9bba1c` | Bench supply characterised — power path fixed, current column unresolved |
| `23be6ca` | **Phase 6 closed; claim level raised to ladder rung 6** |
| `9af013e` | INA226 bench work parked until the spare arrives |
| `139ce31` | **Service composition policy adopted** |
| `fe29773` | Boundary section pointed at the policy |
| `1159013` | Composition oracle + reference trace |
| `8e46808` | Trace registered in `run_all_tests.py` (184 → 185) |
| `ab2e640` | **Composition policy RTL, exhaustive oracle parity** |
| `42ee3eb` | Policy updated with RTL status |

## Karatsuba — evidence chain complete

| # | Criterion | Status |
|---|---|---|
| 1 | Every candidate build meets 25 MHz | MET — worst 31.46 MHz (+6.46) |
| 2 | Routing reliability within +1 of reference | MET at the limit — PROBE 1 non-convergence vs 0 |
| 3 | LUTX ≤ +1 %, FFX ≤ ref, DSP equal | MET — LINK +32, PROBE −44, both −176 FFX, DSP ±0 |
| 4 | Formal + regression at the swap commit | MET at `a6e462d` — 3/3 sby, zphi 46/46, tensegrity 48/48 |
| 5 | Four-act bench, N ≥ 10 + positive control | MET — 10/10, §3.2l.1 |

No criterion was amended after seeing results. **No Fmax claim is available in
either direction** and none is made: seed spread is ~9-21 MHz against an arm
median difference of ~2 MHz.

The **PROBE candidate cell is n=9**, missing seed 1, which did not converge
(`build/zk_pnr_campaign/20260808_194219/NONCONVERGED_PROBE_ZK1_S1.md`). Quote
it that way.

## What was actually wrong today — three false alarms and one real misread

Three things presented as broken hardware and were not:

1. **Card reader** — never enumerated; unrelated to the bench.
2. **SD supply and rate** — a bare 3V3 adapter, briefly run at 5 V (recorded in
   §3.2l.1 as a limitation), then `FR_DISK_ERR` at the 8 MHz post-init rate
   while the 400 kHz init passed. Runs at 1 MHz.
3. **`ERR no SD card` / `file not found`** — the fixtures live under `TGR/`,
   and the RP2350's microSD bus (`spi1`, GP10-13) is independent of the J11
   link (`spi0`, GP0-3), so link health says nothing about SD.

And one real misread, mine: **`tgrstatus version=0` is the signature of an
unconfigured FPGA, not a healthy idle sidecar.** I reasoned from the RTL that
`header_version` resets to 0 and called it expected. A configured idle sidecar
reports `version=1`. The bitstream had never been loaded this session; every
zeroed readback was saying so. **Check the FPGA is configured before
interpreting any SPI readback** — an unconfigured device answers plausibly with
zeros, and `status raw=00 00 00 00` versus `5A 00 10 00` is the tell.

## Traps and fixes worth carrying

- **`spu_host` `connect()`** raised against any already-booted board, so
  `lucas_demo.py` only worked immediately after a reset. Fixed in `0ac49ae`.
- **Stale metrics survive a killed build.** A cancelled P&R leaves the previous
  campaign's metrics file under the same name; seed-completeness cannot see it.
  The analyser now filters on the campaign's `started_utc`. This silently
  inflated PROBE candidate to n=10 before it was caught.
- **Retiring a gate needs a search for what cites it.** §3.2l said the four-act
  work was "gated on the power-ready interlock" while the interlock's removal
  was recorded only in the roadmap and BOM. It sat unblocked for five days.

## Delegation — batch claim audits dropped

Two GTP tranches, two failures, both caused by contract design rather than
execution: v1 under-reported (23 claims presented as the population), v2
over-claimed (141 of 208 rows `BACKED` while naming no ledger section).
Replaced by ledger discipline at the point of writing — see **Claim discipline**
in `AGENTS.md`. Both contracts are marked CLOSED in `spu_strategy/`.

**The rule that came out of it:** delegate what a script can check, keep what
needs a judgement call. GTP compute remains well suited to P&R sweeps, long
formal runs, and pipelining searches — work whose output is verifiable from
artifacts rather than from a report.

## Composition track — policy to RTL in one session

The architecture's self-imposed blocker is cleared. `CURRENT_STATUS.md`'s
service-composition boundary deferred shared datapaths behind two
preconditions; the first is now met and the second is half met.

| Piece | State |
|---|---|
| Policy | adopted — `SERVICE_COMPOSITION_POLICY.md` |
| Software oracle | `software/lib/composition_policy.py` |
| Reference trace | 50 checks, in the regression |
| RTL | `spu13_composition_policy.v` — 396 checks, exhaustive parity |
| **Silicon trace** | **missing — shared datapaths stay deferred** |

**The central rule is compose verdicts, not values.** The three services are
different rings with no meaning-preserving map between them, so an algebra
service emits a bounded dimensionless verdict and only that composes with a
decision. The useful consequence: **no cross-domain adapter is needed for
anything currently contemplated.** The §4 adapter contract exists for the case
that is not yet contemplated and binds if anyone reaches for it.

It is also the strongest argument against implicit conversion available here —
every field is exact, so an adapter would be the **only** lossy step in the
pipeline, destroying the central claim at the one place nobody looks.

**Three decisions settled by John**, one against the draft's recommendation:
separate annotation frame keyed on result generation; **thresholds fixed in
RTL** rather than host-configurable; `hold` and `escalate` kept distinct. The
fixed-threshold choice turned out to cost nothing to re-prove, because it
pushed the design toward reusing SOM1 flag bit 3 — the classifier's own
ambiguity call, already proven in silicon — instead of inventing a new
constant.

**Two enforcement details worth keeping:** the oracle's `compose()` returns the
very bytes object it was handed, so rule 3.1 is checked by identity rather than
equality and a re-encoded lookalike cannot pass as untouched evidence; and the
RTL reads no quadrances at all, so policy §1 holds by construction rather than
by review.

## Open

- ~~**ROBOTICS spin synth re-check**~~ — **DONE 2026-08-09, PASSES.**
  `bash hardware/boards/artix7/build_a7.sh 100t robotics synth` completes clean:
  rc=0, **zero errors**, 100 warnings (in line with other spins), netlist
  `build/spu_a7_100t_ROBOTICS.json` written, 56,330 cells at `spu_a7_top` with
  47 DSP48E1, 8,483 FDCE, 2,514 CARRY4. The last carried bench prerequisite is
  cleared — the spin is ready for its next Wukong session, which was the point
  of the re-check. Note this is synthesis only; P&R and a board run are
  separate.
- **Composition/adapter policy** — the 08-07 service-composition boundary still
  defers shared datapaths until a cross-domain adapter policy and an
  oracle-backed composition trace exist. Nothing produces either; the repo
  blocks its own next integration step. Needs John's judgement on product
  claims.
- **INA226** — order the R100 spare; complete the electrical rebuild (soldered
  harness, star ground, flyback, series R < 0.1 Ω, true current limit by DMM)
  **before** the part arrives, because the runbook's freeze rule forbids
  changing the rig after block 0.
- ~~**Padé 50 MHz**~~ — **CLOSED 2026-08-10, negative result. Do not reopen as a
  timing tranche.** Both cuts were built and measured across five seeds each at
  a 50 MHz constraint. `PADE_PIPELINED` costs +9 evaluator cycles and was never
  on the critical path in any of ten builds. `PIPELINED_RNS_CHECK` did move the
  critical path off the cross-die haul — the mechanism worked, confirmed on
  every arm-B build — but Fmax 37.42 ± 4.60 → 40.54 ± 5.23 MHz is not
  significant at five seeds, and **0 of 10 closed 50 MHz** (best 46.55). Both
  ship at default 0, committed `0130c28`/`5b4b3ea`/`7dc14c8`. Separating a
  +3 MHz effect needs ~40 seeds per arm (~9 h of P&R), and the 2026-08-05 entry
  gate already showed routed Fmax does not predict functional reliability here.
  The spin stays at `A7_CLK_DIV_LOG2=1` / 25 MHz with half throughput, and that
  cost still must be quoted wherever the pipeline is presented.
  Findings: `spu_strategy/claude_findings_rns_gather_cut_2026-08-09.md`.
  The contract's own premise — "completion *is* the proof" — was **wrong** and
  is corrected in the evening section: nextpnr writes the netlist and FASM
  before the final timing check, then exits non-zero.

- **Composition silicon trace** — the last piece of policy §5. Needs
  `spu13_composition_policy.v` integrated into a spin, driven with real SOM1
  frames, outcomes recorded. Until it exists, shared datapaths stay deferred
  and "composed decision" is a design intention in public material, not a
  capability.
- ~~**Sweep tooling**~~ — **DONE `8451aae`.** `tools/zk_pnr_sweep.sh`,
  `tools/zk_analyse.py`, `tools/tgr_four_act.py`, listed in the AGENTS.md
  command table, repo root from `git rev-parse` rather than a hardcoded path.
  Promoted because §3.2l.1 cites the four-act driver's output directly and the
  swap criteria rest on the sweep — evidence-producing tools do not belong in a
  session scratchpad.

- **Bench supply characterisation** — procedure added `0f8e639`
  (`INA226_CAPTURE_RUNBOOK.md` §2, recording table in the handoff). Needs only a
  DMM and the actuator, so it is doable now, and it is a hard prerequisite for
  the manifest re-`init`: `init` freezes `--supply-limit-ma` into all thirty
  sessions. Five readings minimum per quantity; the 2026-08-06 figures
  (3100 mV, 307.4 mA against a 280 mA display) are single-shot priors to be
  replaced.

---

## Evening session, 2026-08-09 — Padé pipelining audited, RNS gather cut, A/B sweep

Written incrementally as work landed. **The tree is uncommitted** — 11 modified
files plus one new vector file, spanning four separate pieces of work. See
"staging plan" below before any commit.

### Correction to the pipelining contract's premise (above)

The line "a missed 50 MHz constraint is a hard nextpnr error … so completion
*is* the proof" is **wrong**. nextpnr writes `.pnr.json`/`.pnr.fasm` *before*
the final timing check, then exits non-zero with `0 warnings, 1 error`.
Artifact presence proves nothing; the exit code and the `ERROR: Max frequency`
line are the evidence. A side effect: `collect_fpga_metrics.py` never runs on a
failing build, so there is no `build/metrics/` entry for any of them.

### PADE_PIPELINED — audited, works, and is on the wrong signal

`spu_strategy/claude_audit_of_pade_pipelining_2026-08-09.md`. Verified
independently: latency 112→121 and 33→41 cycles, the five-seed Fmax table, that
the builds really had the option on, and area-after. The negative result stands.

But the registered handoff **is not on the critical path**. The routed path runs
from the shared multiplier's `s1` result registers, through the mod-3 residue
check, into `shared_rns_error_q` — 24.5 ns, 5.9 logic / 18.7 routing. The
+9-cycle option should be **shelved**, not landed.

### PIPELINED_RNS_CHECK — the actual cut, default 0

Implements Part A of `gtp_contract_rns_check_pipeline_2026-08-05.md` (that
tranche was stopped by its entry gate as a *reliability* fix; it is revived here
only as a *throughput* question — see the audit's Finding 6). Each lane's mod-3
compare is computed next to its own registers; 4 bits make the long trip instead
of 136. Scoped to `spu13_m31_multiplier_structured` and plumbed only through the
Padé sidecar → `spu_a7_top` → `build_a7.sh`. Cost measured: **+86 LUTX, +5 FFX.**

**Consumer audit, completed 2026-08-09 evening — safe everywhere it terminates:**

- `spu13_rplu2_pade_sidecar.v` — not done-relative, not state-gated, sticky flag,
  SPI-paced clear. Safe.
- `spu13_rplu2_sidecar.v:287` — earlier caution that this "folds rns_error into a
  stall decision" was **too pessimistic**. `rns_error` shares an `if` with
  `pipeline_stall` but only sets the `error` status pulse and the sticky
  `rns_error_seen`; it never suppresses a QR commit. Safe. One nuance: a
  final-multiply error is now reported one cycle *after* the commit rather than
  concurrent with it — ordering, not behaviour.
- `spu13_core.v` → `spu_a7_top.v:1086` — terminates in `spi_status_turbulence`,
  a status bit latched into `resp_buf[2]` and read over SPI. **Not** a Henosis
  trigger, not a datapath gate. Observability only.
- **Blocker for enabling it beyond the Padé sidecar:** `rplu_pipeline.v` takes
  `rns_error` from `spu13_m31_multiplier` and `spu13_m31_multiplier_seq_structured`,
  neither of which has the parameter. Adding it there is a cone edit, deferred.

### Artifact tagging fixed — and why it mattered

`build_a7.sh` now appends `_PP1` / `_RC1`, matching the existing `_PT1` rule.
Without it the 2026-08-09 pipelining run **overwrote its own baseline**, and
because `FP4_EVIDENCE=1` was set for seeds 2/3/5/7 but not seed 1, the seed-1
build wrote the **canonical production name**. The `.bit` survived only because
`pack` never ran; the `.json`/`.fasm`/`.pnr.json` under that name are now from
a pipelined, non-closing design. **Do not `pack` `spu_a7_100t_RPLU2PADE` until
it is rebuilt.**

### Baseline Fmax is a distribution, not a number

Five-seed baseline at `A7_FREQ=50 A7_CLK_DIV_LOG2=0`, current RTL:

| seed | 1 | 2 | 3 | 5 | 7 |
|---|---|---|---|---|---|
| Fmax (MHz) | 34.98 | 31.12 | 37.51 | 42.58 | 40.91 |
| routing (ns) | 22.5 | 26.4 | 20.9 | 17.2 | 18.1 |

Logic is pinned at 5.7–6.2 ns; **routing carries all 11.5 MHz of the spread.**
Any single-seed Fmax comparison on this design is noise.

### Sweep result — gather broken, 50 MHz not closed

Full findings: `spu_strategy/claude_findings_rns_gather_cut_2026-08-09.md`.

| seed | A Fmax | B Fmax | A routing | B routing |
|---:|---:|---:|---:|---:|
| 1 | 34.98 | 46.55 | 22.5 | 15.8 |
| 2 | 31.12 | 41.97 | 26.4 | 18.2 |
| 3 | 37.51 | 36.70 | 20.9 | 21.4 |
| 5 | 42.58 | 33.73 | 17.2 | 24.2 |
| 7 | 40.91 | 43.74 | 18.1 | 16.6 |

Fmax 37.42±4.60 → 40.54±5.23 (delta +3.12, SE 3.11); routing 21.02±3.68 →
19.24±3.51 (delta −1.78, SE 2.27). **Neither is significant**; 3 of 5 seeds
improved, 2 got worse. **0 of 10 builds closed 50 MHz** (best 46.55).

**The mechanism did work**, and this part does not rest on the statistic: the
critical-path sink moved from `u_rplu2_pade_sidecar`'s `shared_rns_error_q`
(across the die) to the new per-lane `rns_lane_q` **inside `u_shared_mult`**, on
every arm-B build checked. The 136-bit haul is off the critical path. What
remains is each lane's own 32-bit gather into `mod3_32`; the next cut would be
inside that function, not at a module boundary.

Do **not** quote the per-seed deltas: arm B's netlist differs (+86 LUTX, +5 FFX)
so the same seed is a different placement, and the arms are independent samples,
not matched pairs. Seed 1's +11.57 MHz is one draw, not a measurement.

Recommendation: land the cut at default 0 if wanted — nearly free, zero latency
cost, audited safe, regression-covered — but **do not present it as a speedup**.
Establishing a +3 MHz effect against this spread needs ~40 seeds per arm (~9 h
of P&R), and per the 2026-08-05 entry gate routed Fmax does not predict
functional reliability anyway.

### Test coverage — two real gaps closed

- `rplu_thimble_pade_tb.v` now runs **six oracle-derived non-trivial [4/4]
  vectors** (`pade_eval_vectors.mem`), all four lanes checked, 33/33 in both
  `PADE_PIPELINED` modes. All six re-derived independently against
  `a31_field.py:pade_eval`. Previously the bench's entire arithmetic coverage
  was "1/1 returns 1".
- As delivered, **five of the six never ran** — the loop used `wait_cycles`,
  which `pulse_start()` resets and counts up to 112, ending the loop after one
  iteration. Reported 8/8 was the tell (3 + 1×5, not 3 + 6×5). Fixed with a
  dedicated induction variable.
- `PARAM_VARIANTS` now covers `PIPELINED_RNS_CHECK` and `PADE_PIPELINED`.
  Regression **188/188**. Note the totals count benches, not checks, so this
  class of bug is invisible to the headline number.

### Staging plan (nothing committed yet)

Four independent commits, explicit paths only — never `git add -A`, shared tree:

1. `spu13:` RNS gather cut — `spu13_m31_multiplier_structured.v`,
   `spu13_rplu2_pade_sidecar.v`, `spu_a7_top.v`, `spu13_m31_multiplier_structured_tb.v`
2. `a7:` artifact tagging — `build_a7.sh`
3. `test:` evaluator coverage — `rplu_thimble_pade_tb.v`, `pade_eval_vectors.mem`,
   `spu13_rplu2_pade_sidecar_tb.v`, `spu13_spi_rplu2_pade_tb.v`, `run_all_tests.py`
4. `rplu_thimble_pade.v` (PADE_PIPELINED) — **hold**, pending the shelve decision.
