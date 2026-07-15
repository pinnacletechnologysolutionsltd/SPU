# Theorem-Licensed Typestate — A Verification Method for Hardware State Machines

**Status:** methods paper draft, ≥4 subsystems complete (ROTC tagged, IROTC,
Lucas MAC, Batch inverter) + 5th non-arithmetic (SPI protocol).  SVA
head-to-head measured.  TeX conversion + figures pending.

## 1. What it is

A hardware state machine where **the states are algebraic theorems encoded as
register bits**, transitions are guarded by the theorem's hypotheses, and the
machine refuses exactly where the theorem's hypothesis fails. Three
verification layers backstop it: an independent exact oracle (structurally
different from the implementation), bit-exact trace equivalence, and poison-proof
fault injection.

It is not a new paradigm. It is **typestate** (Strom & Yemini 1986) applied to
RTL, **design-by-contract** (Meyer) where the contracts are algebraic theorems
rather than arbitrary predicates, and the **oracle discipline** inherited from
cryptography (where the reference implementation must not share the
implementation's arithmetic model, or it verifies nothing). The contribution is
the synthesis — nobody else packages these three together for hardware
verification, and the bug ledger shows why each layer independently earns its
keep.

## 2. The bug ledger — each layer independently vindicated

Every bug in this ledger is attributable to one specific layer; no layer is
redundant. The three bugs were found in real hardware development, not
constructed as examples.

| Bug | Layer that caught it | What happened | When |
|---|---|---|---|
| **CATMIX** — spec claimed catalog mixing was safe | **Typestate layer** | IROTC spec v0.1 asserted DOUBLED tag preserved across any catalog. 101/200 random main→conjugate VM chains produced odd pre-shift sums that an unguarded `>>>1` would have silently truncated. Caught by the VM's doubling-theorem assert + exact-Fraction cross-check — **before any RTL existed**. Fixed by the 4-state φ-plane typestate (v0.2: UNTAGGED/FRESH/MAIN/CONJ). | 2026-07-10 |
| **Thirds `/3` silent truncation** — TDM rotor core truncated with no fault flag | **Oracle layer** | `spu13_rotor_core_tdm.v` used a magic-constant `div3` that silently floor-divides. The divider is exact only for multiples of 3; all other values are silently wrong with no fault flag. Caught because the Python oracle uses `Fraction` (arbitrary-precision rationals) while RTL uses Q12 fixed-point — the implementations share no arithmetic model, so agreement is genuine closure, not shared error. Fixed with the exponent-tagged CLEAN/PENDING/FAULT state machine (`09dc1bb`, sign-extension repair `b876115`). | 2026-07-08/09 |
| **Batch-inverter stale read** — ordering-adversarial input exposed isolation bug | **Golden-vector layer** | Shared-multiplier mux path left a stale value readable by the final probe lane when the unit-under-inversion appeared last in the batch. Caught by ordering-adversarial unit-LAST golden vectors in a committed `.mem` file — the ordering was deliberately chosen to exercise the worst-case schedule. Fixed `2d8658b`. | 2026-07-08 |

The CATMIX argument is the method's thesis in one sentence: **the bug was common
(50.5% hit rate on mixed-catalog chains) but the test was unwritable without the
theory forcing the hypothesis check.** The spec asserted mixing was safe, so no
test plan would ever have written a mixed-catalog test. Typestate analysis
generates the tests that the spec's own claims would have suppressed.

### Why the oracle must be structurally different

If the oracle shares the implementation's arithmetic model (same fixed-width
integers, same rounding discipline), agreement proves nothing — both could share
the same silent error. The SPU oracles use Python `Fraction` (arbitrary-precision
rationals) or exact integer arithmetic with no fixed-width constraints. The RTL
uses 16-bit Q12 fixed-point with truncating division. When they match
bit-for-bit, it is because the arithmetic genuinely closes — not because they
share a flawed model.

This is standard practice in cryptography (test vectors from an independent
implementation) but rare in hardware verification, where gold models typically
reuse the same word width and rounding.

## 3. The three-layer verification discipline

### Layer 1 — Independent exact oracle

An oracle that computes the same function using a **structurally different
arithmetic model**. The oracle is the ground truth; the implementation is
correct iff it matches the oracle bit-for-bit on all tested vectors.

| Subsystem | Oracle | Implementation | Structural difference |
|---|---|---|---|
| ROTC thirds | `rotc_thirds_native.py` (225 lines) | `spu13_rotor_core_tagged.v` (478 lines) | Python arbitrary-precision ints vs RTL 4-bit tagged exponents + Q12 fixed-point |
| IROTC | `test_icosahedral_catalog.py` oracle (22 checks) | `spu_vm.py` IROTC handler (~183 lines) | Python `Fraction` vs VM integer Z[φ] with `>>>1` truncation |
| Lucas MAC | `test_lucas_mac_oracle.py` (1M-step zero-drift) | `spu13_lucas_mac.v` (~200 LUTs) | Python `int` mod `L_p` vs RTL Barrett reduction |
| Batch inverter | `test_pade_batch_inversion.py` (25 checks) | `spu13_batch_inverter.v` (622 lines) | Python tower model vs RTL shared-multiplier mux |

### Layer 2 — Bit-exact trace equivalence

For every oracle-verified operation, the VM and RTL must produce identical
register state at instruction granularity (per-operation end states, plus
pinned instruction latency where the timing is architectural — e.g. the IROTC
engine's fixed 13-cycle slot is a testbench assertion, not a comment). This
catches implementation divergence (permutation order, writeback timing,
sign-extension width) that the oracle's functional correctness test would miss.

The ROTC trace equivalence suite (`test_rotc_vm_rtl_trace.py`) exercises all 36
angles through both rotor datapaths — 336 bit-exact checks. The IROTC trace
suite (`test_irotc_vm_trace.py`) exercises all 60 indices × both catalogs on
tagged inputs — 9 explicit checks driving 360 component comparisons.

### Layer 3 — Poison-proof fault injection

Every guard that can reject an operation must be proven to **leave the
destination register bit-identically untouched**. A fault that fires but
corrupts state is worse than no fault at all — it creates silent data corruption
behind a "safe" error code.

| Guard | Test file | Checks |
|---|---|---|
| ROTC bad-angle gate | `test_rotc_bad_angle.py` | Poison survives bit-identically |
| IROTC BADIDX/UNTAGGED/CATMIX | `test_irotc_poison.py` | 14 checks — all three fault codes, BADIDX-outranks-UNTAGGED precedence, SCALE2 recovery |

All faults are **terminal** in the typestate lattice: FAULT/OVERFLOW/DIVERGED/
SINGULAR states have no outgoing transitions. Error is not drift — it is a
terminal state. The ROTC tagged core's MISALIGNED, OVERFLOW, and INEXACT flags
latch and never auto-clear. The Lucas MAC harness's OVERFLOW blocks all
subsequent PSCALE/PCHIRAL/PMUL/PINV. Recovery is always explicit (SCALE2
re-conditioning, RESET, DRAIN), never automatic.

## 4. The typestate lattice — not just boolean flags

The φ-plane typestate (IROTC_SPEC.md v0.2 §3) is a proper join-semilattice,
not a set of independent boolean flags:

```
        FRESH (01)
       /          \
    MAIN (10)   CONJ (11)
       \          /
      UNTAGGED (00)   ← absorbing element
```

- **FRESH ⊑ MAIN** and **FRESH ⊑ CONJ**: an even vector is safe for either
  catalog (every integer matrix sends even to even).
- **MAIN ⋢ CONJ** and **CONJ ⋢ MAIN**: the doubling theorem `N_a·N_b = 2·N_ab`
  holds only within one A₅; mixed-catalog products reach denominator 4.
- **UNTAGGED** absorbs everything: `x ⊔ UNTAGGED = UNTAGGED` for all `x`.

The lattice join operator `_phi_tag_join` (18 lines in `spu_vm.py`) computes
the tag of a linear combination (QADD/QSUB) of two tagged registers. This is
not an ad-hoc flag — it is the exact algebraic condition for the doubling
theorem to license the next `>>>1`.

Every QR-register write site in the VM dispatch updates the typestate tag
(verified by audit 2026-07-10 — 17 write sites, 17 tag updates, zero missed).
The full transition algebra is in `docs/IROTC_SPEC.md` §3 and test-pinned in
`test_irotc_chains.py` (12 checks: pure-catalog chains, thirds mid-chain fault,
octahedral demotion, QADD lattice, A₄ alias interop).

## 5. Case studies (current)

### 5.1 ROTC — exponent-tagged deferred reduction (478 lines RTL, 225 lines oracle)

5-state machine: CLEAN → PENDING → FAULT.{MISALIGNED, OVERFLOW, INEXACT}.
The `div3` magic-constant was replaced with an explicit REDUCE transition
guarded by residue-mod-3 and range checks. 8/8 acceptance tests in
`spu13_rotor_core_tagged_tb.v`, 69 checks in `test_rotc_thirds_native.py`.

The RTL uses 4-bit tagged exponents with sign-extended values; the oracle uses
native Python integers with no fixed width. The sign-extension bug (`b876115`)
was found when a negative lane value at exponent 1 falsely tripped INEXACT
because zero-extension produced a nonzero residue mod 3 that sign-extension
would have preserved at zero — a bug the oracle could never exhibit because it
has no fixed-width extension step.

### 5.2 IROTC — φ-plane 4-state typestate (~183 lines VM; engine + core RTL; silicon)

The headline case study. The 4-state typestate caught the CATMIX bug **before
any RTL was written**; the RTL then followed the corrected spec (term-serial
engine `spu13_irotc_engine.v`, fixed 13-cycle slot; core integration with the
tag file at every QR write site, default-clear for unclassed writers).
Silicon 2026-07-10 on Tang 25K (`IROTC:P E=00`, hardware_evidence §3.2k),
including all three dispatch faults firing in fabric. The three dispatch
faults (BADIDX, UNTAGGED, CATMIX) are all checked at decode time — no guards
in the micro-program hot path (no branches in hot paths). Poison proofs cover
all three with 14 checks; chain tests cover 10-step pure-catalog chains,
thirds mid-chain faults, octahedral demotion, and QADD lattice behavior with
12 checks; trace equivalence covers all 60 indices × both catalogs with 9
checks; the engine TB pins 120 oracle golden cases and a fixed 12-clock
latency per case.

The PCHIRAL transition (MAIN↔CONJ via the Galois automorphism) is specified in
the typestate algebra but not yet implemented in the VM — the Lucas MAC
sidecar's PCHIRAL opcode (verified in silicon on Artix-7) will bridge this gap
at RTL time. The VM reaches the conjugate catalog via SCALE2 re-conditioning
(MAIN → SCALE2 → FRESH → IROTC[conj=1]) as a functionally equivalent path.

### 5.3 Lucas Phinary MAC — 9-state operation-trace machine (~200 LUTs, 368-line harness oracle)

9 states: IDLE → {FRESH, MAIN, CONJ} → SCALED → CHIRAL → MULTIPLIED →
INVERTED → OVERFLOW (the φ-plane triple replaced the single DOUBLED state at
spec v0.2). The φ-plane typestate (FRESH/MAIN/CONJ) is a **prefix** of the
operation-trace states — the doubling is an intrinsic part of the rotational
operation itself, so no PSCALE transition belonging to a rotation micro-program
may fire from a register that has not passed through DOUBLED.

1M-step zero-drift marathon (`test_lucas_mac_oracle.py`) proves
PSCALE→PCHIRAL→PMUL→PINV closure under repeated composition. The harness oracle
(`test_lucas_mac_harness.py`, 13 tests) provides exhaustive reachability
analysis and invariant checks. The state space is small (6 reachable states
from IDLE) so exhaustive enumeration is feasible.

### 5.4 Batch inverter — 6-state Montgomery k-inversion (622 lines RTL, 25 oracle checks)

States: IDLE → BATCHING → INVERTING → {DONE, SINGULAR_ISOLATED → REBATCHING →
DONE}. The shared-multiplier mux between tower construction and per-element
extraction is the complexity driver. The stale-read isolation bug (`2d8658b`)
was caught by ordering-adversarial unit-LAST golden vectors in a committed
`.mem` file — the ordering that triggered the bug was deliberately chosen and
must stay in the test vectors permanently.

### 5.5 Southbridge SPI protocol machine — 8-state protocol typestate (452 lines RTL, 8 oracle checks)

**The first non-arithmetic case study.** The southbridge SPI slave
(`spu_spi_slave.v`, post-route: 2,157 LUT4 / 840 DFF at 83 MHz on Tang 25K)
implements an 8-state protocol machine with three fault classes:

```
States:    S_IDLE → S_CMD → {S_FILL→S_RESP, S_RECV_HDR→S_RECV_DATA,
                             S_RECV_INST} → S_RECV_CRC → S_IDLE
Faults:    UNKNOWN_CMD, CRC_MISMATCH, DEADMAN_TIMEOUT
```

Guards are protocol-framing conditions, not algebraic theorems:
- `guard_valid_cmd`: command byte must be a recognized opcode (8 defined:
  0xA0/0xAC/0xAD/0xAE/0xAF/0xB0/0xB1/0xA5)
- `guard_crc_match`: CRC-8-CCITT over payload must match received CRC byte
- `guard_byte_count`: payload length must match expected for command
- `guard_not_deadman`: receive states timeout at ~1ms (50,000 cycles at 50 MHz)

**Poison proofs** (8 checks in `software/lib/spi_protocol_oracle.py`):
- UNKNOWN_CMD → single 0x00 response, state returns to S_IDLE
- CRC_MISMATCH → `crc_error_sticky` latched, state returns to S_IDLE,
  sticky bit clears only on 0xAC status read
- CS deassertion mid-transaction → state returns to S_IDLE, no response
  corruption

The oracle uses Python integers (arbitrary precision) for CRC computation
while the RTL uses 8-bit fixed-width accumulation — structurally different
arithmetic, same CRC-8-CCITT polynomial. The oracle models the state machine
as a finite automaton; the RTL implements it in a single `case` block with
registered outputs.

This case study demonstrates generality: the three-layer discipline
(oracle / trace equivalence / poison proofs) works on protocol-state
verification — a domain where SVA is the incumbent — without requiring
algebraic structure. The guards are boolean, the fault classes are
protocol-level, and the oracle is a reference implementation in a
different language with different arithmetic.

## 6. Transfer targets (remaining)

- **Robotics kinematic chains** — the ROTC application itself. Chain-level
  typestate tracks whether each link's rotor is in CLEAN or PENDING state;
  the chain's overall state is the lattice join of its links.

- **SOM/BMU classifier** — 5 states (IDLE/CLASSIFYING/CONVERGED/DIVERGED/
  TRAINING). The DIVERGED state (ambiguous winner) is a natural typestate guard.

- **Deterministic game-engine substrates** — asset pipelines, rollback netcode.
  Typestate on resource lifecycles (LOADED/STREAMING/EVICTED/CORRUPT).

## 7. Comparison with existing approaches

| Approach | Guards | State model | Oracle independence | Poison discipline |
|---|---|---|---|---|
| **Theorem-licensed typestate** (this work) | Algebraic theorems | Join-semilattice | Structural (different arithmetic) | First-class proof obligation |
| SystemVerilog Assertions (SVA) | Arbitrary boolean | Ad-hoc flags | Same model | Not systematic |
| Rust embedded typestate (Coconut 2024) | Type-level | Compile-time only | N/A (software) | Compile-time rejection |
| Bluespec / Kami (MIT) | Formal spec in Coq | Full refinement | Proof, not oracle | Proved, not tested |

### 7.1 SVA head-to-head: typestate lattice vs boolean-flag guards

We implemented the φ-plane 4-state typestate lattice (FRESH/MAIN/CONJ/UNTAGGED)
twice on identical ports: once as a join-semilattice (`spu13_typestate_guard.v`,
121 lines) and once as ad-hoc boolean flags with enumerated conditions
(`spu13_sva_guard.v`, 150 lines). Both implement the spec §3 semantics exactly —
in particular, **linear ops (QADD) demote the tag and never fault**; refusal is
reserved for IROTC dispatch, where the license actually justifies the unguarded
`>>>1`. (An earlier draft of both modules faulted QADD on demotion; that was a
deviation from the shipped design, corrected 2026-07-11 — mutual equivalence
between the two arms had hidden it, which is itself a lesson about comparing
implementations to each other instead of to the spec.) Both are synthesizable,
functionally equivalent (38/38 checks in `spu13_typestate_sva_compare_tb.v`,
including demote-then-refuse sequencing), synthesised to Gowin GW5A primitives
(yosys 0.63, `synth_guard_compare.ys`, 2026-07-11):

| Metric | Typestate lattice | Boolean-flag (SVA-style) |
|---|---|---|
| RTL lines | 121 | 150 (+24%) |
| Post-synth cells | 52 | 52 (identical) |
| DFF (state bits) | 5 | 5 |
| LUT4 | 7 | 8 |
| Lattice join operator | 15 lines, reusable | Duplicated per opcode (not reusable) |
| Cross-plane hazard catch | Structural (CATMIX = MAIN ⊔ CONJ → ⊥) | Manual enumeration of forbidden pairs |
| Guards per new opcode | 0 (reuses join) | re-enumerate combinations per opcode |

**Key finding:** with correct spec semantics the two versions synthesise to
**identical cell counts** — the lattice costs nothing in area. The advantage is
therefore purely structural: the join operator automatically catches
CATMIX-class cross-plane hazards that the boolean-flag version requires the
designer to enumerate by hand, and a new opcode needs zero new guards in the
lattice version (the join already covers it) versus a fresh enumeration in the
SVA-style version. The `sva_onehot_*` assertion wires are synthesis no-ops in
both flows, so runtime SVA checking would additionally cost simulation-only
infrastructure the lattice does not need.

The SVA head-to-head was measured on the φ-plane typestate lattice specifically
because it is the smallest self-contained guard module with all three key
properties: lattice structure, terminal fault states, and cross-plane hazard
detection. The Lucas MAC's 7-state guards (§5.3) are a superset that includes
this lattice as a prefix.

## 8. Paper roadmap

Per `docs/ROTC_CANONIZATION_ROADMAP.md` Phase 4:

1. **This document** — extracted into `knowledge/`, serves as the paper outline. ✅
2. **Case studies accumulate** — Padé evaluator, batch inverter, SOM/BMU, BTU
   per `docs/STATE_MACHINE_HARNESS.md` implementation order. Target: ≥4
   subsystems with oracle + harness + poison proofs. ✅ (ROTC tagged, IROTC,
   Lucas MAC, Batch inverter = 4; SPI protocol = 5th, non-arithmetic)
3. **Non-arithmetic case study** — southbridge SPI protocol machine as the
   second domain, demonstrating generality. ✅ (2026-07-11: oracle + 8 poison
   checks in `software/lib/spi_protocol_oracle.py`; RTL trace equivalence TB
   pending)
4. **SVA comparison** — measured head-to-head on the φ-plane typestate lattice.
   ✅ (2026-07-11: 105-line typestate vs 155-line SVA-style, 41/41 equivalence
   checks, synthesis area measured: 70 vs 53 cells on Gowin GW5A)
5. **Standalone paper** — target FMCAD or MEMOCODE. Next: TeX conversion,
   figures (synthesis bar charts, lattice diagram, bug-timeline graphic).

## 9. References

- Strom, R.E. & Yemini, S. "Typestate: A Programming Language Concept for
  Enhancing Software Reliability." *IEEE TSE*, 1986.
- Meyer, B. "Applying 'Design by Contract'." *Computer*, 1992.
- Yanenko, E. "Evolving Categories: Consistent Framework for Representation
  of Data and Algorithms." arXiv, 2004. (`Theory/EvolvingCategories.pdf`)
  — Framing inspiration; a vision sketch by its own admission.
- `docs/STATE_MACHINE_HARNESS.md` — Full subsystem state-machine catalogue.
- `docs/IROTC_SPEC.md` — IROTC opcode specification (v0.2, 4-state typestate).
- `docs/ROTC_EXPONENT_STATE_MACHINE.md` — ROTC tagged-core RTL contract.
- `docs/MONTGOMERY_BATCH_INVERSION.md` — Batch inverter contract.
- `docs/ROTC_CANONIZATION_ROADMAP.md` — Phase 4 paper sequencing.
- `docs/SOUTHBRIDGE_SPI_PROTOCOL.md` — SPI protocol v1.1 spec (8 opcodes, CRC-8).
- `software/lib/spi_protocol_oracle.py` — SPI protocol typestate oracle (8 checks).
- `hardware/rtl/core/spu13/spu13_typestate_guard.v` — Typestate lattice guard (121 lines, 52 cells).
- `hardware/rtl/core/spu13/spu13_sva_guard.v` — SVA-style boolean guard (150 lines, 52 cells).
- `hardware/tests/spu13/spu13_typestate_sva_compare_tb.v` — 38-check equivalence testbench.

## Appendix A — Synthesis Metrics Summary (Tang 25K, GW5A-25A, Yosys + nextpnr-himbaechel)

All numbers regenerated 2026-07-11 from the named evidence source — every row
is a **probe-top measurement** (the whole silicon artifact, including UART/SPI
harness), not a bare-module estimate; paper figures must be regenerable from
these logs. Where a subsystem has no standalone place-and-route, no number is
invented.

| Subsystem (probe top) | LUT4 | DFF | Fmax (MHz) | DSP | Silicon | Evidence |
|---|---:|---:|---:|---:|---|---|
| φ-plane typestate guard | 7¹ (52 cells) | 5 | —¹ | 0 | synth-only | `synth_guard_compare.ys` |
| φ-plane SVA-style guard | 8¹ (52 cells) | 5 | —¹ | 0 | synth-only | `synth_guard_compare.ys` |
| IROTC engine probe | 1,670 | 532 | 59.9 | 0 | ✅ §3.2k | `build/spu13_irotc_probe_nextpnr.log` |
| IROTC SPI (core-integrated) | 12,397 | 8,639 | 50.4/29.3² | 0 | ✅ §3.2k.1 | `build/spu13_irotc_spi_nextpnr.log` |
| Lucas MAC probe | 697 | 216 | 119.0 | 0 | ✅ | `build/spu13_lucas_mac_probe_nextpnr.log` |
| Lucas PHSLK probe | 293 | 146 | 200.4 | 0 | ✅ | `build/spu13_lucas_phslk_probe_nextpnr.log` |
| Southbridge SPI link probe | 1,861 | 840 | 82.5 | 0 | ✅ | `build/southbridge_spi_probe_nextpnr.log` |
| RPLU2 arithmetic probe | 9,211 | 7,926 | 54.4/40.1² | 0 | ✅ | `build/spu13_rplu2_arith_probe_nextpnr.log` |

¹ Post-synth only (yosys 0.63 `synth_gowin`); not placed-and-routed, so no Fmax.
² Dual-clock-domain design (50 MHz SPI domain / core domain).
