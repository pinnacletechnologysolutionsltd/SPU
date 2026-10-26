# Takeover Checkpoint

> **Superseded for SOM state on 2026-09-11.** The terminal SOM classification
> and current authorization state are in
> [`SOM_RESEARCH_CLOSURE_2026-09-11.md`](SOM_RESEARCH_CLOSURE_2026-09-11.md).
> The remainder of this 2026-09-10 checkpoint is retained as campaign history,
> not as an authorization to resume localization, repair, or benchmarking.

Date: 2026-09-10

## 1. Current objective

Preserve the stopped completion-arm earliest-divergence tranche and await a
new owner gate. The authorized localization did not reach physical execution.

## 2. Current classification

**E — DIAGNOSTIC PERTURBATION INVALIDATES INFERENCE.**
Artifact A reproduces the historical scaled case-0 oracle result exactly;
artifact B returns a different valid result for the identical query with the
same frozen J4 identity. No causal attribution within artifact B is authorized
or established. The sole diagnostic implementation passed frozen-query
simulation (14/14), but its default-disabled synthesis was materially different
from artifact B (31,113 versus 29,084 cells; 2,024 versus 1,054 DFFRE cells).
The validity job stopped before diagnostic P&R or packing, so no diagnostic
artifact or physical boundary observation exists.

## 3. Proven facts

* SIMULATION: original and bench25 consumer profiles each pass 50/50 checks,
  including 11 consecutive accepted queries, exact result parity, one fresh
  completion per query, held-`done` rejection, and `L=006` on every query.
* REPOSITORY GATE: all registered components passed before hardware use:
  Verilog 163/163, C++ 12/12, Python 52/52; total 227 PASS / 0 FAIL.
* ARTIX GOVERNANCE GATE: the owner-authorized script-supported equivalent
  `A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all`
  completed synthesis, place-and-route, and packing with exit status 0. Final
  post-route `clk_fast` Fmax is 39.86 MHz against the frozen 25.00 MHz
  constraint. Packed bitstream SHA-256 is
  `36d5b92720d966cfc983570f6a06008e0d0e674d1a582206ba310acaee86310a`.
* SYNTH/P&R: fresh route passes 25 MHz at 35.02 MHz routed Fmax; worst setup
  path 28.55 ns, setup slack +11.45 ns, zero timing errors. No hold/min
  violation was emitted, so reportable hold margin is `>0 ns`; this nextpnr
  build does not emit a positive numeric hold margin. One accepted warning says
  the divider-to-BUFG local entry did not use dedicated routing; the routed
  BUFG output uses the accepted global-clock correction.
* PHYSICAL: SRAM loading succeeded and fresh boot output included
  `SOM:H N=0 Q=00000000 S=04 L=000 I=1020` (preceded by BL616 NUL framing).
* PHYSICAL: the completion-arm run transmitted raw vector `[109,39,21,11]`
  and returned the valid line
  `SOM:D N=3 Q=04433EA4 S=06 L=006 I=1020`. The result is exact parity for
  that transmitted vector. Its original comparison against node 2 / 63,278,740
  was invalid because that expectation belongs to the scaled vector.
* PHYSICAL REPRODUCIBILITY: predecessor artifact A, packed-image SHA-256
  `6b7022f236813695931464e2be946724a0d1775c1633f30c5540d861f3f8e8f6`,
  was independently SRAM-loaded three times. Each load produced fresh
  hydration, and its sole case-0 query returned exactly
  `SOM:D N=3 Q=04433EA4 S=06 L=007 I=1020`. No malformed, duplicate, missing,
  or unexpected terminal response was observed.
* PHYSICAL MODEL INTEGRITY: read-only J4 captures before and after those three
  executions were byte-identical and both matched frozen fold 0, SHA-256
  `7cd242bf445a9cf0b9688f398bb00c3a369ed74cf9133bbfdc863d929e0b0e52`.
* PHASE-0 ORACLE: the frozen record distinguishes raw `features`
  `[109,39,21,11]` from classifier `scaled` values
  `[6949,16056,21000,19412]`. Against the exact frozen J4 model, the trusted
  oracle gives four distances `[1036781750, 888500962, 1238907313, 71515812]`
  and winner node 3 / `0x04433EA4` for the raw vector. This exactly equals all
  three reproducibility results.
* HISTORICAL INPUT: the archived passing query
  `Q1B2500003EB80000520800004BD40000` encodes the scaled vector. Its oracle
  distances are `[565720577, 1423732861, 63278740, 703046049]`, with winner
  node 2 / `0x03C58E94`. The reproducibility query
  `Q006D00000027000000150000000B0000` instead encodes the raw vector.
* CORRECTED PHYSICAL REPLAY (2026-09-10): after an independent artifact-A SRAM
  load and fresh hydration, exactly one historical scaled query
  `Q1B2500003EB80000520800004BD40000` returned
  `SOM:D N=2 Q=03C58E94 S=06 L=007 I=1020`. This is exact node/distance parity.
  Initial and closure J4 captures were byte-identical and matched frozen fold
  0, SHA-256
  `7cd242bf445a9cf0b9688f398bb00c3a369ed74cf9133bbfdc863d929e0b0e52`.
* COMPLETION-ARM SAME-INPUT CHECK (2026-09-10): independently loaded artifact
  B, SHA-256
  `7a57be49d6164d838cd9ba49b9e13a1feb64f250312378a425bf237622dc448b`,
  produced fresh hydration and exactly one valid terminal response to
  `Q1B2500003EB80000520800004BD40000`:
  `SOM:D N=0 Q=42FF6EEB S=06 L=006 I=1020`. Expected and artifact A are node 2
  / `0x03C58E94`. J4 was exact and byte-identical before/after. Classification:
  **DIVERGENCE**.

## 4. Closed issues

* The accepted 25 MHz global-clock distribution remains unchanged and timing
  clean. Do not reopen it without contradictory evidence.
* A stale level-held `done` cannot satisfy the next request in the corrected
  consumer simulation. Physical `L=006` confirms a non-stale completion was
  observed for the one executed case; broader physical acceptance did not run.
* No performance result or comparative advantage was established.
* Artifact identity is now correlated with the same-input result difference:
  A matches the oracle and B does not. This does not identify the causal RTL or
  physical mechanism within B.
* The reproducibility tranche's stable node 3 / `0x04433EA4` result is not a
  classifier parity failure for the query bytes it transmitted; it is the
  exact trusted-oracle result for those bytes.

## 5. Current blocker

Artifact B has a demonstrated same-input divergence, but D0-D5 remain
unresolved. The one authorized diagnostic implementation failed its
non-perturbation validity gate. The contract prohibits a second diagnostic
workaround, so further instrumentation, localization, repair, wider acceptance,
or performance work requires a new owner authorization.

## 6. Physical state

Last measured/owner-confirmed on 2026-09-10:

* Tang Primer 25K was unplugged for the mandatory closure integrity capture;
  do not infer that any SRAM image remains active.
* J4 model-flash module is attached to the Pico flash adapter. Its closure
  readback is exact frozen fold 0, SHA-256
  `7cd242bf445a9cf0b9688f398bb00c3a369ed74cf9133bbfdc863d929e0b0e52`.
* Tang UART during both corrected same-input executions was the onboard BL616
  `if01-port0` path at 115200 8N1.
* Pico 2 is running the flash-PMOD utility and enumerated as serial
  `9537D50959F3BE46`; no RP2350 performance firmware was loaded or executed.

Do not infer that this physical state remains current after takeover.

## 7. Frozen constraints

Classifier RTL/arithmetic, weights, J4 format, UART semantics, fixtures,
preprocessing, voting, thresholds, queue depth 1, timing target, transport
architecture, benchmark schedules, run lengths, and A/B/C/D/E gates are frozen.

## 8. Work in progress

NONE. The localization tranche stopped as E before hardware. Observation-only
diagnostic edits remain in the working tree as preserved failed evidence; they
must not be synthesized or loaded without a new owner contract.

Build directory:
`build/spu4_ina226_benchmark/bench25_completion_arm/`

The directory contains `command.txt`, `exit_status`, synthesis/P&R reports,
routed netlist, timing JSON, and packed `probe.fs`. Bitstream SHA-256:
`7a57be49d6164d838cd9ba49b9e13a1feb64f250312378a425bf237622dc448b`.

Reproducibility evidence directory:
`build/spu4_ina226_benchmark/parity_repro_20260909/`

Its `exit_status` records
`COMPLETE R1_STABLE_REPRODUCIBLE_PARITY_FAILURE`. The directory contains the
exact procedure, capture harness and hash, initial/final J4 bytes, three boot
captures, three one-query raw/parsed captures, and explicit result manifest.
That historical classification is superseded by the demonstrated raw/scaled
fixture mismatch: its physical result is exact parity for its transmitted raw
query.

Corrected replay evidence directory:
`build/spu4_ina226_benchmark/scaled_replay_20260910/`

Its `exit_status` records `PASS_EXACT_SAME_INPUT_PARITY`. It contains the exact
procedure, artifact identity, initial/final J4 bytes, boot capture, raw and
parsed one-query capture, and result manifest.

Artifact-B same-input evidence directory:
`build/spu4_ina226_benchmark/completion_arm_same_input_20260910/`

Its `exit_status` records `DIVERGENCE`. It contains artifact-B identity,
initial/final J4 bytes, fresh boot capture, exactly one raw/parsed terminal
response, procedure, and result manifest.

Completion-arm localization evidence directory:
`build/spu4_ina226_benchmark/completion_arm_localization_20260910/`

`tranche_result.json` records classification
`E_DIAGNOSTIC_PERTURBATION_INVALIDATES_INFERENCE`. The nested
`diagnostic_validity_job/` has terminal marker `FAILED`, exit status 1, the
14/14 simulation log, source diff, and failed default-disabled synthesis
comparison. No diagnostic bitstream was produced and no physical query ran.

## 9. Authorized next action

NONE. A second diagnostic implementation, physical localization, repair,
wider acceptance, or performance measurement requires a separate owner gate.

## 10. Parked work

Canonical INA226 1/4/16/64 aligned/staggered performance benchmark; GPU/IVM;
SU(3)/photonics and product hardware.

## 11. Evidence pointers

* `AGENTS.md`
* `spu_strategy/spu4_ina226_performance_contract_2026-09-08.md`
* `docs/bench_captures/2026-09-09_spu4_completion_arm_boot.json`
* `docs/bench_captures/2026-09-09_spu4_completion_arm_fold0_acceptance.json`
* `docs/bench_captures/2026-09-09_spu4_j4_model_identity.json`
* `build/spu4_ina226_benchmark/bench25_completion_arm/exit_status`
* `build/spu4_ina226_benchmark/bench25_completion_arm/pnr.log`
* `build/spu4_ina226_benchmark/parity_repro_20260909/result.json`
* `build/spu4_ina226_benchmark/parity_repro_20260909/exit_status`
* `build/spu4_ina226_benchmark/parity_repro_20260909/command.txt`
* `build/spu4_ina226_benchmark/parity_repro_20260909/a7_gate_result.txt`
* `build/spu_a7_100t_RPLU2PADE.json.nextpnr.log`
* `build/metrics/artix7_100t_RPLU2PADE.md`
* `build/spu4_ina226_benchmark/earliest_divergence_20260909/phase0_oracle.json`
* `build/spu4_ina226_benchmark/earliest_divergence_20260909/result.json`
* `build/spu4_ina226_benchmark/earliest_divergence_20260909/exit_status`
* `build/spu4_ina226_benchmark/scaled_replay_20260910/command.txt`
* `build/spu4_ina226_benchmark/scaled_replay_20260910/result.json`
* `build/spu4_ina226_benchmark/scaled_replay_20260910/exit_status`
* `build/spu4_ina226_benchmark/completion_arm_same_input_20260910/command.txt`
* `build/spu4_ina226_benchmark/completion_arm_same_input_20260910/result.json`
* `build/spu4_ina226_benchmark/completion_arm_same_input_20260910/exit_status`

## Takeover instruction

Read this checkpoint, `AGENTS.md`, and the referenced evidence before modifying
anything. Verify repository and physical assumptions rather than trusting
conversation history. Do not reinterpret the raw/scaled fixture mismatch as a
classifier failure. Treat the A/B difference as build-correlated, not
cause-localized, and do not perform localization, repair, wider acceptance, or
performance work without owner authorization.
