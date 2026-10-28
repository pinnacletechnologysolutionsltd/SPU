# ISA-V02-NUM-SOM-4 Phase B — RPLU2 numeric-domain guard and internal refusal indication

**Status:** implemented in `spu13_core.v` and verified at **core-level RTL simulation** scope. It is **not** SPI-visible, not H0-C1-compliant, not synthesized or timed, and not hardware-qualified. SOM, BTU, Padé and the A₃₁ refusal path are not qualified by this work. Governing contract: [`H0_NUMSOM4_B2_COMPLETION_CONTRACT_DRAFT.md`](H0_NUMSOM4_B2_COMPLETION_CONTRACT_DRAFT.md) (a local implementation contract, not a ratified ISA specification).
**Source identity:** tested on `dev/next` at `6556d22422549cac6848494dd640d1c224fc124a` plus the Phase B diff below. RTL is unchanged from `2a9a9f12760bb13fb47bcf192b66f44645f35ef9` (the later commits are documentation). Preserved evidence is added by the commit containing this file (`git log -1 -- docs/isa/ISA_V02_NUMSOM4_PHASEB_FINDINGS.md`).
**Toolchain:** isolated OSS CAD Suite release 2026-10-27 (archive SHA-256 `9fa347adb4a86e45472c55ee6fb286a91243228e856ccb408ff1bf0cfeef58ae`): Icarus Verilog 14.0 (devel) `s20260301-739-gd95f2401b-dirty`, Verilator 5.053 devel `v5.052-619-gbaed329fa`, system Python 3.10.12 and g++ 11.4.0. System tools (Icarus 11.0, Verilator 4.038) were not replaced; Icarus 11.0 cannot parse `spu13_jet_sparse_mac.v` (unpacked-array ports), so the regression gate needs the newer tools.
**Evidence classes:** *RTL observation* = simulation of the preserved probes; *host* = none used for the verdicts here. Nothing in this document is a physical-hardware result.

## 1. Implementation

Only `hardware/rtl/core/spu13/spu13_core.v` changed (diff SHA-256 `4e3b47a3c943f809dc8f9bf24dd628b5a45271d9b1df901fe196046614c5e767`, 80 lines; resulting file SHA-256 `213663307810a6af1a9b6e1d6901d502afad6a974a3ad3d01ac6177287f9d629`):

* **Guard.** In the `ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE` branch, at the edge where `rplu2_som_pending && !rplu2_busy` would launch, all eight original signed 32-bit P/Q halves of `qrf_rd_A..D` are checked against `[-9457, 9457]` inclusive, before the 18-bit extraction `rplu2_features` can be consumed.
* **Pass:** `rplu2_som_start` is asserted exactly as before. **Fail:** `rplu2_som_pending` is cleared, `rplu2_som_start` is not asserted, and a registered one-core-clock `rplu2_domain_refused` pulse is produced.
* **Completion.** `inst_done_r` keeps its single procedural owner; the public output is now `inst_done = inst_done_r | rplu2_domain_refused`, so the refusal pulse is aligned with `inst_done`. A new output port `rplu2_domain_refused` exposes it (tied low in the config-only and disabled RPLU2 branches). `inst_done` remains a generic handshake release and does not mean success.
* **Not changed:** comparator signedness or arithmetic, feature weights, SOM, BTU, Padé, SPI, ISA encodings, reason encodings, sidecars.

## 2. Directed verification (`hardware/tests/spu13/num_som_4_phaseB/`)

| File | Role |
|---|---|
| `numsom4b_probe.v` | core-level directed probe (H0 configuration); source-lane values injected through the register-file write port; driver enforces single-outstanding; `$fatal` on any failed check |
| `numsom4b_lock.v` | lockstep probe: previous `spu13_core` (extracted from git at `2a9a9f1`, renamed) versus the current core, every compared output every cycle |
| `run_num_som_4_phaseB.py`, `expected/probe.txt`, `expected/lock.txt` | runner and fixed expectations; no regenerate option; requires simulator exit status 0 |

SHA-256: `numsom4b_probe.v` `10beaecc61c93b7fa1cbea442de889f9c21fd8a460a95faab87c95f4251f3740`; `numsom4b_lock.v` `020d627cb447b793e1873fd6bb993ed9aef909f88d7fe3cb94356313678a3c6e`; `run_num_som_4_phaseB.py` `2d4f76765c61daa9ff058e40b4dc2401adec7b8c799a20c0cd63154e8ceb2225`; `expected/probe.txt` `84af07ff2023a749acf20c21aec399066412ef4ed4811731ee4bf2d1b6ef4993`; `expected/lock.txt` `a67015d6a167d764779747134fb595971dda72501160d886da16cf33e5a47324`.

```bash
python3 -I hardware/tests/spu13/num_som_4_phaseB/run_num_som_4_phaseB.py     # about 3.5 minutes; needs iverilog >= 12
```

The file names avoid `tb` and the directory is not among the runner's scanned source directories, so `run_all_tests.py` does not compile these probes.

**Probe: 450 checks, 0 failures.** Coverage: the zero vector; each of the eight coefficient positions (A.P, A.Q, B.P, B.Q, C.P, C.Q, D.P, D.Q) at +9457 and −9457 (launched) and ±9458 (refused); each position at signed 32-bit `MAX` and `MIN` (refused); each position at pre-narrowing aliases ±262149 whose low 18 bits are in range (refused); three valid mixed-sign operand sets. Per case: exactly one launch and one result for valid input; exactly one refusal for invalid input, with `rplu2_domain_refused` aligned with `inst_done`; no `rplu2_som_start`, `rplu2_result_valid` or `qr_commit_valid` on refusal; no QR register write for either outcome; previous commit telemetry unchanged after a refusal; the selected lane stable at guard and launch, and the launched features equal the checked operands. Also: a sequence refuse–launch–refuse with minimal gaps (2 refusals, 1 launch, 3 completions); reset during pending, on the guard edge, during the refusal-pulse cycle, at the launch cycle and 200 cycles into the pipeline (no refusal, completion or result afterwards, and normal refusal and launch recovered each time).

**Lockstep, 0 mismatches in all five configurations (160 operations each):**

| Configuration | Stream | Result |
|---|---|---|
| H0 (RPLU2 pipeline) | QLDI/QSUB/ROTC only | 0 mismatches |
| H0 (RPLU2 pipeline) | plus 64 in-domain `0x2A` | 0 mismatches, 0 refusals |
| RPLU2 config-only | plus `0x2A` with arbitrary 32-bit source data | 0 mismatches |
| Legacy core SOM | plus `0x2A` with arbitrary 32-bit source data | 0 mismatches |
| No RPLU2, no SOM | plus `0x2A` with arbitrary 32-bit source data | 0 mismatches |

**Controls.** A built-in negative control (output that would match, then `$fatal`) is rejected. Two mutated guards (bound 9458; the D.Q check removed) are each detected as simulator failures. Developing the first mutant exposed an unbounded wait loop in the probe (it hung for 21 minutes); all waits are now bounded and the global timeout is 1 ms of simulated time.

## 3. Observed instruction-overlap hazard (negative evidence; unsupported behavior)

These are **observations of unsupported behavior, not an accepted execution mode.** They are not repaired in Phase B and show why the single-outstanding rule must be enforced by the future H0-C1 transaction controller.

| Experiment | Observation |
|---|---|
| QLDI at gap 2–5 after a refused `0x2A` | refusal and QLDI each complete (2 completions, 1 refusal), QR9 written |
| refusing `0x2A` issued during a valid `0x2A` in flight | accepted but lost: 1 completion (the valid one), no refusal |
| refusing `0x2A` 3 cycles before the valid result (result at cycle 556) | accepted but lost: no refusal, 1 completion |
| refusing `0x2A` 2 cycles before the valid result | **not refused**: the guard sampled the first instruction's lane (5, not 3); the second run launched with lane 5's data and completed with a result (2 launches, 2 results) |
| refusing `0x2A` 1 to −3 cycles around/after the result | refused once, ordered after the first completion |

The offset −2 case is the B1 review's finding made concrete: a second accepted instruction whose lane selection is skipped by the shared priority chain leaves `rote_src_lane` pointing at the previous operand, so an out-of-domain operand is never examined.

## 4. Full regression

* **Contaminated checkout run (failed, not accepted).** `build/rtl/num_som_4_phaseB/gate-20261028-144958` in the shared checkout: terminal marker `FAILED`, exit 1, 958 s; Verilog 186 tests (185 passed, 1 failed), C++ and Python passed, total 261 passed and 1 failed. The failing test, `rotc_round_witness_tb.v` (ROTC angle-1 thirds witness, 16 mismatches), exists only as an untracked file under `spu_strategy/evidence/rotc_2026-10-28/` belonging to separate research, and `run_all_tests.py` discovers any `*tb*.v` in the working tree. By source inspection it is unrelated to Phase B (it checks the known ROTC divide-by-three behavior); that was not independently established. Not a Phase B defect, and the witness was not changed.
* **Clean isolated-checkout run (accepted).** Clone of `6556d22` at `~/.local/gate/spu-6556d22-phaseB` with exactly the Phase B `spu13_core.v` diff (applied-diff and resulting-file hashes above) and the five fixture files (hashes verified before and after transfer; the shared checkout's files are byte-identical): discovery 177 test files plus 8 parameter variants = 185, no untracked test present. Terminal marker `COMPLETE`, exit 0, 1008 s, evidence `build/rtl/num_som_4_phaseB/gate-clean-20261028-151336` in that clone. **Verilog 185/185 passed, C++ 12/12, Python 2/2, all other suites passed; grand total 261 passed, 0 failed**, no skips. `spu13_jet_mac_tb` and `spu13_phslk_core_tb` fell back from Icarus to Verilator 5.053 and passed (as in the Phase A run); every other test ran under Icarus.
* The Phase B targeted runner was rerun in the clean clone on the same source and fixtures: all components `PASS`, `RESULT: PASS` (log `phaseB_targeted_rerun.log` in the evidence directory).
* **Limitation of the gate:** test discovery depends on the contents of the working checkout, including untracked files; a frozen or tracked-only manifest would avoid this class of contamination. Not addressed here.

## 5. Not claimed; remaining dependencies

Not claimed: SPI-visible refusal; any reason encoding; safety under overlapping instructions; sidecar coverage; SOM/BTU/Padé or A₃₁ refusal correctness; synthesis, timing or hardware behavior. H0-C1 dependencies: a transaction controller that owns a single outstanding instruction from acceptance through terminal event; atomic capture of `inst_done` and `rplu2_domain_refused` with transaction identity; a host-visible outcome and reason; reset, clock-domain and sidecar arbitration behavior; A₃₁ validity and refusal propagation; integrity-fault classification (D7).
