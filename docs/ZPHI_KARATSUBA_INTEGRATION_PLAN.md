# Z[phi] Karatsuba Integration and A/B Evaluation Plan

Date: 2026-07-21

Status: Phases 0-5 complete as of 2026-07-23. The three-product multiplier
is now the production default in both tensegrity consumers
(integrated and routed, not silicon-verified); the four-product reference
remains selectable for rollback. Phase 6 (silicon confirmation) is the
only remaining phase.

This plan turns the standalone result in
`docs/ZPHI_KARATSUBA_MULTIPLIER.md` into a controlled production evaluation.
It does not authorize a source swap, a latency claim for the complete guard,
or a new silicon claim by itself.

## 1. Objective

Evaluate whether `spu13_zphi_mul_serial_karatsuba` can replace
`spu13_zphi_mul_serial` in the bounded tensegrity admission path while
preserving exact results and transaction semantics and improving measured
latency without a material physical-design regression.

The candidate changes one local schedule:

```text
four-product reference: 4 busy cycles
three-product candidate: 3 busy cycles
```

The end-to-end guard improvement must be measured. It must not be described as
25 percent unless a complete integration measurement actually reports that
number.

## 2. Production integration surface

Both production instances are in scope:

| Consumer | Instance | Shape | Function |
|---|---|---:|---|
| `spu13_tensegrity_intersection.v` | `u_zphi_mul` | 72 x 34 -> 108 | Exact segment contact, collinearity, and overlap micro-program |
| `spu13_tensegrity_guard.v` | `u_eq_zphi_mul` | 39 x 39 -> 80 | Exact force-density equilibrium cross-products |

The selection must propagate through:

```text
spu_a7_tensegrity_probe_top
  -> spu13_tensegrity_guard
       -> equilibrium multiplier
       -> spu13_tensegrity_intersection
            -> intersection multiplier

spu_a7_tensegrity_link_top
  -> spu13_tensegrity_sidecar
       -> spu13_tensegrity_guard
            -> both multiplier instances above
```

Testing only the 72 x 34 standalone candidate is insufficient. The 39 x 39
equilibrium instance, loader/watchdog behavior, and both Artix tops are part of
the acceptance surface.

## 3. Non-negotiable invariants

1. The production default stays on `spu13_zphi_mul_serial` through Phases 0--4.
2. No arithmetic width, signed interpretation, truncation, saturation, or
   reduction rule changes.
3. `start`, `busy`, `done`, operand capture, ignored-start-while-busy, and
   registered-output behavior remain interface-compatible.
4. TGR1 parsing, CRC, double-buffered commit, fault codes, state codes,
   rollback, and recovery behavior remain bit-identical.
5. Existing watchdog limits may not be increased to make the candidate pass.
6. Existing tests may be strengthened, but not weakened, skipped, or given
   looser expected values.
7. The known-good reference implementation remains selectable after any
   production default switch so rollback is one parameter change.
8. Generated build products and formal work directories remain untracked.
9. No power, energy, whole-system throughput, or silicon claim is made from
   simulation or place-and-route alone.
10. No hardware action is required before Phase 6.

## 4. Predeclared physical-design go/no-go gates

Matched reference and candidate builds must use the same source revision,
device, top, clock constraint, toolchain, and seed. Evaluate both
`TENSEGRITYPROBE` and `TENSEGRITYLINK` with seeds 1, 7, and 13.

The candidate may become the production default only if all of these pass:

| Gate | Requirement |
|---|---|
| Functional | Every reference and candidate regression passes with identical terminal results and evidence fields |
| Local schedule | Every accepted candidate multiply completes in three busy cycles and the reference in four |
| Integrated latency | Candidate fixture and transaction cycle counts are never greater than reference; at least one intersection case and one equilibrium case are strictly lower |
| DSP | No DSP increase in either Artix top |
| BRAM | No BRAM increase in either Artix top |
| LUT | Candidate post-route LUT use is no more than 2 percent above the matched reference for either top |
| FF | Candidate post-route FF use is no greater than the matched reference for either top |
| Timing | All matched builds close 25 MHz, with no new unconstrained-clock or incomplete-timing warnings |
| Seed stability | For every matched seed, candidate Fmax is at least 95 percent of the reference Fmax |
| Watchdogs | Existing parser and verifier watchdog limits pass unchanged |
| Reproducibility | Commands, tool versions, commit, metrics, and report hashes are recorded |

If any gate fails, retain the candidate as a documented research result and
keep the four-product implementation as production default. Do not tune a gate
after seeing the result; change the design or open a separately versioned
evaluation.

## 5. Phased execution

### Phase 0 -- Freeze and reproduce the existing candidate

Purpose: establish the starting point without changing production RTL.

Run:

```bash
iverilog -g2012 -o build/zphi_karatsuba_tb.vvp \
  hardware/rtl/core/spu13/spu13_zphi_mul_serial.v \
  hardware/rtl/core/spu13/spu13_zphi_mul_serial_karatsuba.v \
  hardware/tests/spu13/spu13_zphi_mul_serial_karatsuba_tb.v
vvp build/zphi_karatsuba_tb.vvp
sby -f hardware/tests/spu13/spu13_zphi_mul_serial_karatsuba_formal.sby
```

Required evidence:

- full-width directed extrema and deterministic random equivalence pass;
- reduced-width exhaustive sequential proof passes;
- wider signed width-plumbing proof passes;
- reference multiplier test remains green.

Recorded 2026-07-21 result: all three candidate checks above pass. This is a
reproduction result, not authorization to skip the later phases.

### Phase 1 -- Harden transaction semantics and latency measurement

Purpose: pin the interface behavior that production state machines depend on.

Add tests or formal properties for:

- operands captured only on an accepted idle `start`;
- external operand changes while busy do not affect the transaction;
- starts while busy are ignored;
- `busy` stays asserted through evaluation;
- `done` is exactly one cycle with stable registered outputs;
- return to idle and a second independent transaction;
- reset clears an in-flight transaction consistently with the reference;
- exact three-cycle/four-cycle completion relationship;
- 72 x 34, 39 x 39, and default 72 x 34 parameter shapes.

Deliverable: strengthened test/formal harnesses and a passing targeted run.
Production modules remain untouched.

### Phase 2 -- Add reversible implementation plumbing

Purpose: make A/B evaluation possible without source-file swapping.

Add a consistently named parameter:

```text
USE_ZPHI_KARATSUBA = 0
```

Requirements:

- add it to `spu13_tensegrity_intersection` and select the multiplier with a
  generate block;
- add it to `spu13_tensegrity_guard`, apply it to the equilibrium multiplier,
  and pass it to the intersection engine;
- pass it through `spu13_tensegrity_sidecar`;
- pass it through `spu_a7_tensegrity_probe_top` and
  `spu_a7_tensegrity_link_top`;
- add the candidate source to both tensegrity synthesis scripts;
- teach `build_a7.sh` an explicit `ZPHI_KARATSUBA=0|1` input for the two
  tensegrity spins;
- include both the implementation value and `A7_SEED` in artifact names, logs,
  and metrics so neither an A/B build nor a later seed can overwrite its mate;
- reject values other than 0 or 1;
- retain default 0 throughout Phases 2--4.

Do not use a preprocessor source substitution. Both implementations must be
present in the same source graph and selected by an elaboration parameter.

Deliverable: reference-mode builds are behaviorally and structurally
unchanged apart from selection plumbing; candidate mode elaborates without
changing the default.

### Phase 3 -- Run the complete simulation regression matrix

Purpose: prove the candidate inside every consumer before physical-design work.

Run the standalone reference and candidate tests:

- `spu13_zphi_mul_serial_tb.v`;
- `spu13_zphi_mul_serial_karatsuba_tb.v`;

Run both `USE_ZPHI_KARATSUBA=0` and `=1` through the integration tests:

- `spu13_tensegrity_intersection_tb.v`;
- `spu13_tensegrity_guard_tb.v`;
- `spu_a7_tensegrity_probe_tb.v`;
- `spu13_tensegrity_sidecar_tb.v`;
- `spu13_tensegrity_transport_tb.v`.

Run the hardware-independent oracle and demo checks once:

- `software/tests/test_tensegrity_balancer.py`;
- `software/tests/test_tensegrity_demo.py`.

Finally, run the full `python3 run_all_tests.py` regression in
default/reference mode.

Instrument testbenches to report deterministic cycle counts for:

- each intersection fixture;
- each of the seven guard fixtures;
- valid sidecar admission;
- mechanical-negative admission;
- corrupt-payload rollback;
- clear/reset recovery.

Candidate and reference must produce identical decisions and evidence. Store
the cycle table as a generated build artifact; do not hand-copy favourable
numbers into a source document.

Deliverable: a machine-readable A/B cycle report and green regression matrix.

### Phase 4 -- Matched Artix-7 synthesis and place-and-route

Purpose: close the remaining physical-design acceptance gate without hardware.

After Phase 2 adds unique variant artifact names, run the equivalent of:

```bash
for seed in 1 7 13; do
  ZPHI_KARATSUBA=0 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegrityprobe synth
  ZPHI_KARATSUBA=0 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegrityprobe pnr
  ZPHI_KARATSUBA=1 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegrityprobe synth
  ZPHI_KARATSUBA=1 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegrityprobe pnr

  ZPHI_KARATSUBA=0 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegritylink synth
  ZPHI_KARATSUBA=0 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegritylink pnr
  ZPHI_KARATSUBA=1 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegritylink synth
  ZPHI_KARATSUBA=1 A7_SEED="$seed" A7_FREQ=25 \
    bash hardware/boards/artix7/build_a7.sh 100t tensegritylink pnr
done
```

The build implementation must ensure `synth` and `pnr` for each seed refer to
the same uniquely named JSON, for example a suffix equivalent to `_ZK0_S1`.
Do not launch this loop until that naming is verified with a dry-run or shell
trace.

Collect for every build:

- source commit and dirty/clean state;
- Yosys and nextpnr versions;
- seed and requested frequency;
- LUT, FF, CARRY4, DSP48E1, and BRAM counts;
- critical path/Fmax and timing pass/fail;
- unconstrained-path and incomplete-timing warnings;
- JSON, log, and timing-report SHA-256 hashes.

Deliverable: one generated comparison table evaluated against the predeclared
gates in Section 4. Do not select only the best seed.

### Phase 5 -- Controlled production default switch

Purpose: adopt the candidate only after the complete non-hardware evidence
surface passes.

This must be a separate, easily revertible commit. In that commit:

- change only the production default to the candidate;
- retain the reference implementation and explicit selector;
- rerun the full regression;
- regenerate both tensegrity Artix builds;
- update the contract and current-status documents;
- describe the result as integrated and routed, not silicon-verified;
- record the precise end-to-end cycle improvement, not the local 25 percent
  figure unless they are equal by measurement.

If a downstream regression appears, revert the default-switch commit without
removing the candidate or its evidence.

**Phase 5, 2026-07-23.** `USE_ZPHI_KARATSUBA` defaults to `1` in
all three tensegrity RTL consumers and in `build_a7.sh`'s own selector
default (both had to change — the build script always explicitly overrides
the RTL default via `chparam`, so the RTL-only flip would have been a no-op
for real builds). Full regression: 173/173.

"Regenerate both tensegrity Artix builds" is satisfied by the existing
`TENSEGRITYPROBE_ZK1_S1` / `TENSEGRITYLINK_ZK1_S1` Phase 4 P&R evidence
directly, not by a fresh re-synthesis check. Those were built with
`ZPHI_KARATSUBA=1 A7_SEED=1 A7_FREQ=25`, parameters that exactly match
what the new default now resolves to — that parameter match, established
and independently audited during Phase 4, is what makes them valid
evidence for the default build; it does not require reproducing the same
bytes again afterward. Attempting exactly that reproduction (a synthesis-
only rerun at the post-switch commit) surfaced a real environment
property worth recording: **synthesis is not bit-reproducible run-to-run
here** — a fresh `synth` invocation with byte-identical RTL source
produced a netlist with a different cell count (12655 vs 12736 in the
main module), most likely from yosys version drift between sessions, not
from any source or parameter difference (confirmed via `git diff` — only
the now-irrelevant parameter-default text differs, which `chparam`
overrides regardless). That rerun also overwrote the original
`TENSEGRITYPROBE_ZK1_S1.json` / `TENSEGRITYLINK_ZK1_S1.json` synthesis
snapshots with non-matching content — the P&R evidence itself
(`.pnr.json`/`.nextpnr.log`/`.timing_summary.json`, confirmed untouched
by file timestamp) is unaffected and remains exactly what Phase 4's
independent audit verified, but the standalone synthesis JSON can no
longer be hash-confirmed against its own original after the fact.
Lesson for any future phase: do not rerun `synth` against an existing
`_ZK{n}_S{seed}` artifact name to "double check" it — it will overwrite
the file being checked, and this environment's yosys does not reproduce
identical output on a second invocation regardless.

Precise end-to-end cycle improvement (not the
local 25%/3-vs-4-cycle figure): ranges from 0% (fixtures that terminate
before reaching multiplier work) to roughly 12.9% (best-case intersection
fixture), with whole-transaction sidecar admissions around 3.3-3.6% and
guard fixtures 1-7%. Full per-fixture figures:
`build/zphi_karatsuba_phase3_cycles.json`. Claim level: "Production-
integrated and routed three-product multiplier" (claim ladder row 5).
Phase 6 (silicon confirmation) remains open.

### Phase 6 -- Deferred hardware confirmation

This phase is not required to continue Phases 0--5.

The standalone UART `TENSEGRITYPROBE` can eventually be checked without an
external actuator or RP2350 link, provided the Artix board is powered normally
and no external device drives an unpowered bank. Require repeated
`TGR:P V:7 E:00` and record the bitstream hash.

The `TENSEGRITYLINK` confirmation must wait for the safe power-ready interlock
or an equivalently reviewed power-sequencing arrangement. Re-run the complete
admission, mechanical-negative, corrupt-payload rollback, and recovery sequence
three times. Do not use the damaged J11 top row.

Only after this phase may public material say the production Karatsuba-backed
tensegrity path is silicon-verified.

**Bitstream built and ready, 2026-07-24 — not yet loaded, not a silicon
claim.** A fresh `TENSEGRITYPROBE` bitstream exists for the standalone
UART check above: built from clean commit `8aaaeaa` (current
`origin/master` at build time), seed 2 (deliberately distinct from the
Phase 4 matrix's seeds 1/7/13, chosen so this build could not collide
with or overwrite any existing Phase 4 evidence file — see the Phase 5
note above for why that caution matters here), 25MHz, candidate
multiplier as production default (`ZPHI_KARATSUBA=1`). Route converged
cleanly: zero overuse, timing PASS on both clocks (`guard_clk` 43.47MHz,
`sys_clk` 70.86MHz, both against the 25MHz target), no unconstrained or
incomplete-timing warnings. Packed bitstream:
`build/spu_a7_100t_TENSEGRITYPROBE_ZK1_S2.bit` (3,825,936 bytes,
untracked per this repo's generated-artifact convention), SHA-256
`07c979daf0da76697c615527620eb2b96c85433438862368db43645550dd4cad`.
This bitstream has not been loaded onto hardware yet — building and
routing cleanly is necessary but not sufficient for Phase 6; the
`TGR:P V:7 E:00` repeated-readback confirmation over UART is the actual
remaining step, and only that step, once done, licenses a silicon claim.

## 6. Commit boundaries

Use small reviewable commits in this order:

1. strengthen standalone simulation/formal contracts;
2. add default-off selector plumbing;
3. add dual-mode integration regressions and cycle reporting;
4. add variant-safe build/metrics plumbing;
5. record A/B P&R evidence;
6. switch the production default, only if every gate passes;
7. record later silicon evidence separately.

Do not combine the selector, result evaluation, and default switch in one
commit. Preserve all unrelated working-tree changes.

## 7. Claim ladder for this work

| Completed phase | Allowed wording |
|---|---|
| 0--1 | Formally and simulation-verified three-product candidate |
| 2--3 | Integration-simulation-verified candidate, production default unchanged |
| 4 | Routed A/B candidate meeting (or failing) predeclared physical-design gates |
| 5 | Production-integrated and routed three-product multiplier |
| 6 | Silicon-verified production integration for the recorded fixtures |

Do not call the multiplier `Karatsuba-Ofman` unless the paper or public text
defines the precise three-product identity being used. In general project
communication, `three-product Z[phi] multiplier` is the clearest description.

## 8. Handoff instructions for another coding agent

Start at Phase 1. Read this file and `docs/ZPHI_KARATSUBA_MULTIPLIER.md` before
editing. Keep `USE_ZPHI_KARATSUBA=0` as the default. Implement and verify one
phase at a time, stop after each phase, and report:

```text
files changed
commands run
PASS/FAIL results
cycle-count changes
whether any acceptance gate changed
next proposed phase
```

The agent must not:

- switch the production default early;
- perform hardware flashing or power operations;
- loosen a watchdog or test;
- overwrite reference build artifacts with candidate artifacts;
- update public claim level beyond the last completed phase;
- push, publish, or contact third parties without explicit authorization.

The first implementation task is transaction-semantics hardening, not the
production source swap.
