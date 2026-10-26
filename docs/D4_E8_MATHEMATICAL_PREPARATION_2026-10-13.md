# D4/E8 mathematical preparation and AOR-S1 integration audit

Date: 2026-10-13. Status: PREPARATION CHECKS PASS; qualification NOT RUN.
The [implementation contract](../spu_strategy/contract_d4_e8_mathematical_preparation_2026-10-13.md)
defines isolated code, exact mathematics, fixtures, counters, proof obligations
and the remaining implementation plan. Surd CPU backend repair remains primary.
No hardware command, RTL/ISA change or substantial campaign was executed.

## AOR-S1 integration finding

The inspected current CPU/build path does not implement AOR-S1. This conclusion
combines source inspection with source-list and representation evidence; it
does not rely solely on absence of a name. The read-only audit is recorded in
[integration_audit.json](../build/d4_e8_math_20261013/preparation_01/integration_audit.json).
It scanned706 hardware/research source files, found no hardware AOR name match,
and found no `software/research/aor_s1` implementation directory.

| Artifact | Observed semantics |
|---|---|
| [CPU core](../hardware/rtl/core/spu13/spu13_core.v) | Optional `ENABLE_SURD_CPU`, default0, instantiates `spu13_surd_exec`; separate legacy Pell path |
| [Surd bank](../hardware/rtl/core/spu13/spu13_surd_bank.v) | Eight192-bit explicit-denominator `(A,B,D)` tuples |
| [Surd arithmetic](../hardware/rtl/core/spu13/spu13_surd_arith.v) | Exact coefficient/denominator arithmetic and GCD normalization; no balanced mantissa/exponent descriptor |
| [Pell vault](../hardware/rtl/core/shared/spu_rotor_vault.v) | Eight-entry unit orbit with step/octave state; not general AOR-S1 product-fragment semantics |
| [CPU bench wrapper](../hardware/boards/artix7/spu_a7_surd_cpu_bench_top.v) | Selects enabled Surd configuration; legacy lattice/math functionality disabled in this bench configuration |
| [CPU build script](../tools/build_surd_cpu_a7.sh) | Uses the retained CPU RTL source list and wrapper; toggles `ENABLE_SURD_CPU`; inspected, never run |
| [AOR-S1 draft](../spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md) | Proposed balanced `(a,b,k)` for `(a+b*sqrt(3))*U^k`, U=2+sqrt(3), with separate bounds/canonicality/work semantics |

Existing `software/research/aor1` is earlier software evidence. Pell arithmetic,
Surd arithmetic, octave counters and AOR-S1 share mathematical ingredients but
do not establish the same architecture or integration. No mapped-build inspection,
elaboration, synthesis, timing or silicon qualification is claimed in this audit.
The protected-input manifest covers665 existing source/build-list files, whose
hashes are checked again after preparation. Dirty repository state is not reset.

## Exact preparation results

| Check | D4 | E8 |
|---|---:|---:|
| Independent agreed root count | 24 | 240 |
| Exact rank | 4 | 8 |
| Physical squared root length | 2 | 2 |
| Root/reflection closure and involution pairs | 576 | 57,600 |
| Independent rational/matrix reflection pairs | 16 | 16 |

Physical inner products are exactly{-2,-1,0,1,2}. Ordered-pair distributions
are D4:(24,192,144,192,24) and E8:(240,13440,30240,13440,240), in that order.
Simple generators belong to the root sets, have full rank, and generate the
full root orbit. These are finite preparation checks, not formal universal proofs.
The independent reference enumerates rational norm shells; candidate roots
are doubled integers. Neither imports an SPU representation or legacy D4 oracle.

The [latest preparation result](../build/d4_e8_math_20261013/preparation_01/checks_03/math_preparation.json)
records15 named negative controls with exact counterexamples,264 mapping-root
round trips, rank6 for constrained Quadray blocks and rank8 for the extended
encoding. Four focused literal/accounting tests pass separately.

The first preparation run stopped during JSON encoding of a Fraction diagnostic.
The report encoder was corrected to retain numerator/denominator pairs. Later
refinements expose schoolbook cancellation temporaries, reject invalid generator
IDs and ensure integer arguments to the rational reference cannot produce floats.
Earlier successful preparation reports and matching source snapshots are retained
under `checks`, `checks_02`, `checks_source_01` and `checks_source_02`. These are
preparation iterations, not qualification attempts or repairs to prior evidence.

## Representation findings

Two zero-sum Quadray blocks retain six independent coordinates. The new bridge
retains two additional block sums: q_i=4X_i-t and X_i=(q_i+t)/4. Exact rank8 and
root round trips pass, but ten stored coefficients and conversion/divisibility
work must be charged. This proves a reversible software encoding, not superior
storage or native E8 network execution. D4 needs its own fourth independent state.

The Surd bridge uses rational coordinates embedded in `(A+0*sqrt(3))/D`.
It matches exact reflection values on the small comparison fixtures and is
independent of production modules. General Surd packaging would require a
separate metric: `a*a-3*b*b` is not the E8 Euclidean squared norm. No canonical
AOR-S1 descriptor for E8 actions is established by this bridge.

## Comparative preparation and remaining questions

[workload_plan.json](../build/d4_e8_math_20261013/preparation_01/checks_03/workload_plan.json)
contains120 deterministic proposed cases. Four small cases agree across
coordinate, rational-matrix, ordinary generator-word and software Surd arms.
The remaining cases are NOT RUN. No host-speed or architecture advantage is claimed.

Current counters report logical arithmetic, normalization calls, exact quotients,
word construction and conversion events, modeled schoolbook intermediates and
observed array storage. They exclude complete validation/allocation schedules,
Python objects and GCD internals; they do not form a fully qualified cost model.
Matrix table setup and deferred materialization must remain visible in comparisons.

Resolve before substantial execution: complete cost instrumentation; conventional
D4 signed-permutation baselines; finite resource/refusal limits; serialized state
schema; general Surd/E8 metric compatibility; useful application workloads; and
whether any descriptor improves on ordinary words/matrices after all costs.
The contract gives the staged implementation plan. An isolated qualification
driver, frozen commands and explicit owner attempt/time limits remain required.

Full repository regression is NOT RUN for this preparation, and no hardware
gates are run. Scoped checks and preservation hashes are reported separately.
Existing unrelated documentation-audit findings remain; no repository-wide
documentation or hardware PASS is implied. SGN Phase B remains deferred until
the Surd CPU implementation path meets its separately recorded physical gates.
