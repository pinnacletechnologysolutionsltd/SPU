# ISA-V02-A31-R3 — Core RPLU2 arithmetic refusal propagation

**Status:** implemented in `rplu_pipeline.v` and `spu13_core.v` and verified at **core-level RTL simulation** scope. A zero-norm A₃₁ refusal in the Padé evaluator no longer publishes a stale or undefined result as fresh telemetry in the SPU-13 core. It is **not** SPI-visible, not H0-C1-compliant, not synthesized or timed, and not hardware-qualified. The live-evaluator sidecar and other consumers of `rplu_pipeline` are **not** repaired (see §5).
**Source identity:** tested on `dev/next` at `71c8a5a46ce920f46b6e4185c21b84ba1c610fb5` plus the diff below. The later commit `0e72c6e` is documentation only (no `hardware/`, runner or tool differences). Preserved evidence is added by the commit containing this file (`git log -1 -- docs/isa/ISA_V02_A31R3_FINDINGS.md`).
**Toolchain:** isolated OSS CAD Suite release 2026-10-27 (archive SHA-256 `9fa347adb4a86e45472c55ee6fb286a91243228e856ccb408ff1bf0cfeef58ae`): Icarus Verilog 14.0 (devel) `s20260301-739-gd95f2401b-dirty`, Verilator 5.053 devel, system Python 3.10.12 and g++ 11.4.0.
**Evidence classes:** *RTL observation* = simulation of the preserved probes; *oracle* = `software/lib/a31_field.py` used as an independent expectation for success limbs and for the refusal witness. Nothing here is a physical-hardware result.

## 1. Repair location (determined before editing)

Source tracing and the A31-R2 timelines establish the following:

* `rplu_thimble_pade.v` sets `flags_v` on the same edge as `done` when the inverter reports a zero norm, and clears it at the next `start`; on a normal completion `flags_v` is 0. `pade_done && flags_v` therefore identifies the characterized refusal, and `rns_error` (separate signal) is not conflated with it.
* `rplu_pipeline.v` latched `pade_done` into `phi4_valid` (= `thimble_valid`) with no reference to `pade_flags_v`, so a refused completion looked like a result.
* The core bridge turned `thimble_valid` into `rplu2_result_valid`, which sets `inst_done` and the commit telemetry. Timeline from A31-R2: `pade_done` at cycle *t*, `thimble_valid` at *t+1*, commit and `inst_done` at *t+2*.
* The standalone sidecar already gated by its own `error` path, and `spu13_rplu2_sidecar` consumes `thimble_valid` as its completion event.

Chosen repair (smallest, single point of discrimination): `rplu_pipeline` exports the refusal flag aligned with `thimble_valid` and **keeps `thimble_valid` as a completion signal** (so other consumers cannot hang); the core gates result-valid on it and ends the instruction through a distinct refusal pulse.

## 2. Implementation

Two files changed (applied diff SHA-256 `15e2fdfeb9977f3f6be0e4dca861028db610dc01432942621d0f38ca6701d9bc`, 129 lines):

* `rplu_pipeline.v` (SHA-256 `a34ce8843087ec15f90fa6ec37ca3ba5416b33471ce01073900e9312356eb02e`): new output `thimble_refused`, a registered flag loaded with `pade_flags_v` when `pade_done` latches the result, high on the same cycle as `thimble_valid`.
* `spu13_core.v` (SHA-256 `27559099e59143f2ca65d203b97945fa4e45c9fd498cc80f79ece99c6a39ed19`): `rplu2_result_valid = rplu2_thimble_valid && !rplu2_thimble_refused`; a registered one-core-clock pulse `rplu2_arith_refused` (new output port, tied low in the config-only and disabled RPLU2 branches) loaded from `thimble_valid && thimble_refused`; and `inst_done = inst_done_r | rplu2_domain_refused | rplu2_arith_refused`, so the refusal pulse is aligned with `inst_done` exactly as success is (same *t+2* timing). `inst_done` remains a generic handshake release.

Not changed: numeric-domain guard, comparator, SOM, BTU, Padé arithmetic, coefficients, SPI, `0xAE`, sidecars, ISA encodings.

## 3. Verification (`hardware/tests/spu13/a31_r3/`)

| File | Role |
|---|---|
| `a31r3_core_probe.v` | core-level directed probe (H0 configuration; `INV` selects the reference or structured inverter); `$fatal` on any failed check |
| `a31r3_lock.v` | lockstep probe: previous `spu13_core` (extracted from git at `71c8a5a`, renamed) versus the current core |
| `run_a31_r3.py`, `expected/probe_ref.txt`, `expected/probe_str.txt`, `expected/lock.txt` | runner and fixed expectations; no regenerate option; requires simulator exit status 0 |

SHA-256: `a31r3_core_probe.v` `68a334cef34ede4c42828b28de6be5e88f490af5a4da08c90941ba0dc28811d4`; `a31r3_lock.v` `1437b058a94fddd26d99a687738fc347f1800eb96eac4a842028c0eb3e9486d6`; `run_a31_r3.py` `4c41acb8db02ba6291e3af7499add9d2ca17fab645904546c48a759e7f6d76bb`; `expected/probe_ref.txt` and `expected/probe_str.txt` `98867655a1a30c7142ffec84e77bd173aea01f07b6c617041556b17b5dbb9863` (identical files); `expected/lock.txt` `a67015d6a167d764779747134fb595971dda72501160d886da16cf33e5a47324`.

```bash
python3 -I hardware/tests/spu13/a31_r3/run_a31_r3.py     # about 2-3 minutes; needs iverilog >= 12
```

The file names avoid the substring `tb`, so `run_all_tests.py` does not discover the probes.

**Probe, 36 checks per inverter variant, 0 failures** (reference and structured inverter produce identical observable results):

| Transaction | Observed |
|---|---|
| S1 success (num0 = 2, den0 = 1) | one completion, one result, one commit, `A = 2` (oracle: 2) |
| R1 zero-divisor refusal after success | one completion and one refusal pulse on the same cycle, no result-valid, no commit, commit telemetry unchanged (historical), no QR write |
| S1b success after refusal | normal success, `A = 2` |
| S2 success (3 / 2) | `A = 1073741825` (oracle: 1073741825) |
| R0 refusal as the first transaction after reset | refusal, no commit |
| numeric-domain refusal (out-of-domain operand) | `rplu2_domain_refused` only, no arithmetic refusal, nothing launched (unchanged from Phase B) |
| reset mid-Padé; at the `pade_done` cycle; at the `thimble_refused` cycle | no completion, refusal or result afterwards; normal success and refusal recovered each time |

Each transaction is observed for 1400 cycles: exactly one completion, no duplicate or late event.

**Lockstep, 0 mismatches in all five configurations** (160 operations each; same configurations as NUM-SOM-4 Phase B): H0 with QLDI/QSUB/ROTC only, H0 with in-domain `0x2A`, RPLU2 config-only, legacy core SOM, no RPLU2 and no SOM. The streams contain no arithmetic refusal, so they show that nothing else changed.

**Controls.** A built-in negative control (matching output, then `$fatal`) is rejected. Two mutated cores are each detected: refused completions published as results again; refusal pulse never produced. Success limbs are cross-checked against the independent oracle `software/lib/a31_field.py`, and the witness denominator `2CEE24B2, 0, 0, 1` is confirmed there as a `flags_v` refusal.

**Related runners.** The NUM-SOM-4 Phase B runner passes unchanged against the new core. The A31-R2 runner (historical evidence of the defect, expected files untouched) now reports `FAIL` for the three core variants (`core_ref`, `core_ref_first`, `core_str`) **by design**; for `core_ref` the only difference from the preserved output is the removal of the spurious `qr_commit_valid` during the refused transaction (`inst_done` still pulses once). Its pipeline, sidecar and SPI variants still pass. The A31-R2 expectations were not edited.

## 4. Full regression

Clean isolated checkout (clone of `71c8a5a` at `~/.local/gate/spu-a31r3-clean`) with exactly the applied diff and the six fixture files (hashes verified before and after transfer and against the shared checkout); discovery 177 test files plus 8 parameter variants = 185, none from A31-R3, no ROTC research files. Evidence: `build/rtl/a31_r3/gate-clean-20261028-163227` in that clone (including `applied_a31r3.diff`, fixture hashes and `toolchain_record.txt`).

* Terminal marker `COMPLETE`, exit 0, 995 s.
* **Verilog 185/185 passed, C++ 12/12, Python 2/2, all other suites passed; grand total 261 passed, 0 failed**, no skips.
* `spu13_jet_mac_tb` and `spu13_phslk_core_tb` fell back from Icarus to Verilator 5.053 and passed (unchanged from the Phase A and Phase B runs).

## 5. Not claimed; limitations and remaining dependencies

* **Other consumers of `rplu_pipeline`.** `spu13_rplu2_sidecar.v` still treats `thimble_valid` as a result (it commits on it) and was not changed or simulated; the same stale-publication exposure remains there, and the Artix-7 sidecar spins are unaffected by this repair. `thimble_refused` is available to them.
* **Host visibility.** No SPI or `0xAE` change: a refusal produces no fresh commit, so the SPI sticky valid keeps the previous result, which remains historical. Host-visible refusal, reason and freshness belong to the H0-C1 transaction controller.
* **Coverage of the refusal itself.** `flags_v` is the zero-norm check of the tower inverter; the inverter's norm check is not claimed to detect every zero divisor of A₃₁, and integrity events (`rns_error`, ECC, coherence faults) are separate and unclassified (H0-C1 D7). One zero-divisor witness was exercised.
* **First-after-reset.** In this simulation the commit registers hold earlier values after reset (not `x`), so the A31-R2 "undefined data published" symptom is eliminated by the absence of any commit on refusal, not by resetting the Padé result registers.
* **Overlap.** The single-outstanding assumption is unchanged and unenforced by the core; overlapping instructions are unsupported (see the NUM-SOM-4 Phase B findings).
* No synthesis, timing, FPGA or Vivado work was done; no SPI protocol, algorithm or coefficient change.
