# A theorem-licensed typestate machine for exact rotation algebra

**Author:** John Curley
**Affiliation:** Independent Researcher, SPU-13 Project
**Location:** Wellington, New Zealand
**Date:** 13 August 2026 (Version 1.2)
**AI disclosure:** AI tools assisted with drafting, repository evidence
synthesis, and editorial revision. The human author reviewed the manuscript,
selected its claims and scope, and is responsible for the submitted record.

## Abstract

[THEOREM] This paper presents a typestate construction for exact rotation
algebra whose transitions are licensed by a doubling theorem. The construction
separates fresh values from values known to remain in one catalog domain, and
rejects transitions when the theorem's validity domain is not established.
[RTL] The construction is instantiated in the ROTC and IROTC paths and is
connected to a bounded tensegrity admission guard. [SILICON] Selected ROTC,
IROTC, and tensegrity paths have board evidence, while the complete catalog
surfaces remain a mixture of RTL and board-scoped results. The contribution is
the correspondence between an algebraic domain and an enforced transition
relation; it is not a claim about project-wide evidence or arbitrary arithmetic
values.

## SPU-13 context

[RTL] SPU-13 is the engineering host for these case studies: ROTC supplies
integer-coordinate rotation paths, IROTC supplies catalog rotations whose
stored doubled numerators are exact Z[φ] values,
and the tensegrity guard supplies a bounded admission state machine. They share
an exact-arithmetic hardware setting, but the paper does not claim that the
project as a whole is covered by the typestate result. The examples are chosen
to show the same transition discipline at arithmetic, catalog, and system
boundaries.

## 1. Scope and contribution

[THEOREM] The central result is a four-state typestate lattice for registers
holding Z[φ] pairs: `UNTAGGED`, `FRESH`, `MAIN`, and `CONJ`. `MAIN` and `CONJ`
mean that the register is known to lie in one of two catalog domains; they do
not mean that an arbitrary value has been proved to be a desired application
result.

[THEOREM] Within one A₅ catalog, the doubling theorem licenses the transition
from `FRESH` to the catalog's typed state and licenses subsequent operations
that preserve that domain. The conjugate catalog carries the Galois-dual
domain. A mixed main/conjugate product is outside the theorem's domain and is
therefore rejected rather than silently truncated.

[THEOREM] The premise of this license is that the icosahedral catalog matrices
live in `½Z[φ]`, not in `Z[φ]`. The generated catalog stores the doubled
matrices `2M`, whose entries lie in `Z[φ]`; `LOAD2X` or `SCALE2` doubles the
operand once so that the registered representation remains integral. Within
one catalog, the doubling theorem guarantees that the subsequent half-valued
matrix compositions return an exact `Z[φ]` result. That guarantee does not
compose across the main and conjugate catalogs: a mixed product can leave
`½Z[φ]` with a non-integral stored result, so the typestate machine rejects it
as `CATMIX` rather than truncating it.

[THEOREM] `PCHIRAL` carries the ring automorphism between the two catalog
domains. `SCALE2` reconditions a register to `FRESH`. Operations outside the
A₅ theorem domain, including the integer-matrix ROTC classes, either preserve
only the state they are specified to preserve or demote the tag to
`UNTAGGED`.

[RTL] The state machine is represented in the IROTC integration as a two-bit
tag per QR register, with dispatch faults for untagged use, bad catalog index,
and catalog mixing. Faulting operations hold the destination and its tag.

[THEOREM] The result is a transition-soundness statement: every accepted
transition is licensed by the stated precondition and theorem domain. It does
not imply that the datapath computes the intended value, that a testbench
exhausts all values, or that a document claim is supported.

## 2. Formal model

### 2.1 State space

[THEOREM] Let the register typestate be

\[
  \tau \in \{U,F,M,C\}
\]

for `UNTAGGED`, `FRESH`, `MAIN`, and `CONJ`. Let `D_M` and `D_C` denote the
two catalog domains and let `φ` denote the ring automorphism used by the
conjugate construction. The state invariant is a judgment of the form
`Γ ⊢ (r, τ)`, where `M` and `C` carry a domain witness and `U` carries none.

[THEOREM] The principal transition rules are:

| Operation | Precondition | Result |
|---|---|---|
| raw load | none | `U` |
| `SCALE2` | `U`, `M`, or `C` | `F` |
| main-catalog IROTC | `F` or `M` | `M` |
| conjugate-catalog IROTC | `F` or `C` | `C` |
| `PCHIRAL` | `M` or `C` | the opposite typed domain |
| mixed catalog operation | `M` and `C` | reject with `CATMIX` |
| octahedral/integer ROTC | operation-specific | preserve or demote as specified |

[THEOREM] The induction argument is by transition cases. Raw writes establish
no catalog fact; reconditioning establishes the `FRESH` precondition; a
same-catalog step consumes and returns the same domain witness; `PCHIRAL`
applies the automorphism; and a mixed step has no licensed conclusion. Thus a
rejected transition is evidence that the machine has reached the boundary of
the theorem's stated domain, not evidence that the underlying value is
invalid.

### 2.2 What the theorem does not establish

[THEOREM] The judgment is deliberately narrower than a value proof. It does
not establish bounds, expected test-vector outputs, transport framing, clock
configuration, placement quality, or the absence of faults outside the
transition relation.

## 3. Case studies

### 3.1 ROTC

[RTL] The tagged ROTC path models `CLEAN`, `PENDING`, and explicit
`MISALIGNED`, `OVERFLOW`, and `INEXACT` fault states. Its acceptance harness
provides 9/9 acceptance tests in `spu13_rotor_core_tagged_tb.v`, and the tagged
core is distinct from the original TDM baseline.

[SILICON] ROTC angles 0–5 have board evidence in
[hardware_evidence.md §3.2g (ROTC 0–5)](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32g-rotc-0-5-silicon-probe).

[RTL] ROTC angles 6–35 are covered by RTL/trace evidence only; they are not
reported here as board results. The integer permutation classes are therefore
an example of a transition surface whose algebraic classification and board
status must remain separate.

### 3.2 IROTC

[THEOREM] IROTC is the direct case study for the lattice: main-catalog chains
remain in `MAIN`, conjugate chains remain in `CONJ`, `PCHIRAL` changes the
catalog witness, and mixed chains have no theorem-licensed result.

[RTL] The RTL engine covers the generated 60-entry main catalog and its
conjugate catalog, including the typestate dispatch and poison-hold behavior.
The full 60×2 catalog is reported as RTL-only in this paper.

[SILICON] The IROTC probe vectors and the `BADIDX`/`UNTAGGED`/`CATMIX` fault
matrix are supported by [hardware_evidence.md §3.2k](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32k-irotc-icosahedral-rotation-engine-silicon-probe).

[SILICON] SPI core integration and the conjugate-catalog cases are supported
by [hardware_evidence.md §3.2k.1](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32k1-irotc-spi-core-integration--conjugate-catalog-silicon-proof).

### 3.3 Tensegrity admission

[RTL] The tensegrity guard demonstrates the same separation at a system
boundary: a bounded admission decision carries explicit state, fault, and
recovery transitions, while its geometry and equilibrium predicates remain
separate computations.

[SILICON] The seven frozen admission fixtures, including the equilibrium
fixture, are supported by [hardware_evidence.md §3.2l — V:7 final admission tranche](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32l-wukong-tensegrity-admission-guard-silicon-probe).

[SILICON] The four-act transport and recovery sequence is supported by
[hardware_evidence.md §3.2l.1](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32l1-tensegritylink-four-act-proof-on-the-karatsuba-candidate).

## 4. Harness and coverage boundary

[RTL] The repository's state-machine document lists typestate or explicit
state descriptions for ROTC, SOM/BMU, BTU, Padé evaluation, Lucas MAC, and
batch inversion. Its completed formal typestate harness is the ROTC item; the
other entries describe planned or partial harness work and must not be counted
as completed formal coverage.

[RTL] A separate strict case-study bar was completed after the published v1.1
artifact: independent oracle, RTL trace equivalence, and poison proofs. Five
subsystems now meet that bar—ROTC, IROTC, SPI protocol, Lucas MAC, and batch
inversion—but this does not turn their output benches into formal typestate
harnesses. SOM/BMU has an oracle, trace material, and a gatekeeper positive
control, but still lacks a complete poison proof and independent fault oracle.

| Subsystem | State-machine material | Coverage represented here |
|---|---|---|
| ROTC | Completed tagged-state harness | RTL harness; angles 0–5 additionally have SILICON evidence |
| SOM/BMU | State description and planned harness | Testbench/oracle material only; no completed typestate harness claimed |
| BTU | State description and planned harness | Testbench/oracle material only; no completed typestate harness claimed |
| Padé evaluator | State description and planned harness | Testbench/oracle material only; no completed typestate harness claimed |
| Lucas MAC | State description and strict case-study checks | Oracle + 59-vector RTL trace + poison proof; no completed typestate harness claimed |
| Batch inversion | State description and strict case-study checks | Oracle + 10-case RTL trace + poison/collision proofs; no completed typestate harness claimed |
| SPI protocol | Explicit protocol state machine and strict case-study checks | Oracle + RTL trace + poison proof; no completed typestate harness claimed |
| IROTC | Integrated typestate tags and fault transitions | RTL engine/integration; selected cases SILICON, full catalog RTL-only |
| Tensegrity guard | Explicit admission/fault/recovery states | RTL guard; seven fixtures and transport also SILICON |

[RTL] The distinction in this table is intentional: a bench that checks
outputs or protocol frames is not counted as a typestate harness, and a
state-machine description is not counted as an executed proof artifact.

## 5. Negative results

[RTL] The planned SOM/BMU, BTU, Padé, Lucas MAC, batch-inversion, and SPI
protocol harnesses are specified in the state-machine document but are not
presented as built formal typestate harnesses here. The strict case-study
results for Lucas MAC, batch inversion, and SPI are deliberately reported as
separate evidence layers. This is a negative result about the scope of the
current artifact.

[THEOREM] Several fault classes cannot be expressed by this machine: a wrong
arithmetic value produced while all tags are valid, an omitted clock divider,
a placement-dependent timing failure, a malformed evidence statement, and a
transport or physical failure outside the modeled transition relation. Those
failures require independent value checks, build evidence, or bench evidence.

[THEOREM] The theorem domain and RTL enforcement are also different claims.
The theorem licenses one A₅ domain and its conjugate transformation; RTL can
store and check tags, but that alone does not prove every theorem assumption or
every datapath result. The full generated 60×2 catalog therefore remains an
RTL claim in this paper, not a blanket board claim.

## 6. Limitations

[THEOREM] Typestate constrains transitions, not values. A well-typed execution
may still compute the wrong value, and the machine does not police claims,
documentation, papers, or status reports.

[OBSERVED] The audit of this paper is deliberately separate from the draft.
The five defects found on 2026-08-09/10 were: the aliased loop variable that ran one
vector instead of six; the coverage report that read as complete; the critical-
path misattribution; the RPLU2PADE clock omission; and the seven unbacked
bullets. The typestate machine would have caught none of them.

[THEOREM] The formal result is therefore a bounded transition result. It is
not a substitute for independent vector coverage, synthesis and timing
inspection, configuration accounting, or a claim-by-claim evidence audit.

## 7. Evidence ledger for this draft

Every technical claim in the paper is assigned one tier. The tier is about the
kind of support available for that claim, not a ranking of the theorem.

| ID | Claim summary | Tier | Source | Body mapping |
|---|---|---|---|---|
| T1 | Four-state lattice and domain witnesses | THEOREM | §2.1 | §1 lines 37–41; §2.1 lines 68–77 |
| T2 | Same-catalog doubling transition | THEOREM | §2.1 | §1 lines 43–47; §2.1 lines 79–97 |
| T3 | `PCHIRAL`, `SCALE2`, and integer-ROTC boundary rules | THEOREM | §2.1 | §1 lines 49–53; §2.1 lines 79–97 |
| T4 | Transition soundness is narrower than value proof | THEOREM | §1, §2.2 | §1 lines 59–62; §2.2 lines 101–104 |
| T5 | IROTC main/conjugate transition interpretation | THEOREM | §3.2 | §3.2 lines 125–127 |
| T6 | Unexpressible fault classes and theorem/RTL gap | THEOREM | §5 | §5 lines 182–192 |
| R1 | Tagged ROTC states and tagged-state harness | RTL | `spu13_rotor_core_tagged_tb.v` (9/9 acceptance tests, plus 2000 randomized REDUCE cases) | §3.1 lines 110–113 |
| R2 | ROTC angles 6–35 are RTL/trace-only here | RTL | `test_rotc_vm_rtl_trace.py` (336 checks over 42 generated cases) | §3.1 lines 118–121 |
| R3 | IROTC generated 60×2 surface and fault transitions | RTL | `spu13_irotc_engine_tb.v` (120 oracle golden cases; fixed 12-clock latency) | §3.2 lines 129–131 |
| R4 | Tensegrity bounded state/fault/recovery model | RTL | `spu13_tensegrity_guard_tb.v` (9/9 cases); tensegrity suite total 50 PASS (suite total, not a check count) | §3.3 lines 141–144 |
| R5 | Harness-versus-bench coverage boundary | RTL | `STATE_MACHINE_HARNESS.md` §3 (8 subsystem entries; 1 completed harness) | §4 lines 154–173 |
| R6 | SPU-13 case-study context | RTL | `spu13_core_rotc_opcode_tb.v` (41 lane checks + 2 poison faults) and `spu13_core_irotc_opcode_tb.v` (25 checks) | §SPU-13 context lines 27–33 |
| R7 | Lucas MAC strict case study | RTL | `test_lucas_mac_rtl_trace.py` (59 vectors) + `spu13_lucas_mac_poison_tb.v`; oracle harness 30 checks | §4 lines 171–186 |
| R8 | Batch-inverter strict case study | RTL | `test_batch_inverter_rtl_trace.py` (10 regenerated cases) + `spu13_batch_inverter_poison_tb.v`; oracle 25 checks | §4 lines 171–186 |
| R9 | SPI protocol strict case study | RTL | `spu_spi_protocol_trace_tb.v` (26 comparisons) + protocol poison checks | §4 lines 171–186 |
| S1 | ROTC angles 0–5 | SILICON | `hardware_evidence.md` §3.2g (ROTC 0–5) | §3.1 lines 115–116 |
| S2 | IROTC probe and fault matrix | SILICON | `hardware_evidence.md` §3.2k | §3.2 lines 133–134 |
| S3 | IROTC SPI integration and conjugate catalog | SILICON | `hardware_evidence.md` §3.2k.1 | §3.2 lines 136–137 |
| S4 | Tensegrity seven admission fixtures | SILICON | `hardware_evidence.md` §3.2l | §3.3 lines 146–147 |
| S5 | Tensegrity four-act transport and recovery | SILICON | `hardware_evidence.md` §3.2l.1 | §3.3 lines 149–150 |
| O1 | Five repository defects observed 2026-08-09/10; typestate caught none | OBSERVED | §6 | §6 lines 200–204 |

The repository sections `§3.1–§3.2c` are only partial backing for the broader
project context: they do not supply the date and SHA-256 shape required for a
silicon claim in this paper, so none of them is used as a SILICON source here.

## References

All repository citations below are pinned to the `v1.2-typestate` release tag.

1. [STATE_MACHINE_HARNESS.md §3](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/STATE_MACHINE_HARNESS.md#3-subsystem-state-machines).
2. [IROTC_SPEC.md](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/IROTC_SPEC.md).
3. [hardware_evidence.md §3.2g (ROTC 0–5)](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32g-rotc-0-5-silicon-probe), [§§3.2k, 3.2k.1, 3.2l, 3.2l.1](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/hardware_evidence.md#32k-irotc-icosahedral-rotation-engine-silicon-probe).
4. [ROTC_EXPONENT_STATE_MACHINE.md](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/v1.2-typestate/docs/ROTC_EXPONENT_STATE_MACHINE.md).
