# SPU-FABRIC-0 Phase 1B Timing-Policy Addendum

**Date:** 2026-10-15
**Status:** OWNER-ACCEPTED TIMING POLICY — TIMING QUALIFICATION PENDING
**Parent:** `contract_spu_fabric_0_2026-10-15.md`
**Frozen inputs:** `fixtures/spu_fabric_0/manifest.json` and its three hashed traces

## 1. Preservation

Do not modify the Phase 0/Phase 1A contracts, source-lock files, manifest, or
trace fixtures. This addendum governs Phase 1B timing interpretation and does
not alter the frozen inputs or their hashes.

## 2. Replacement Timing Rule

For Phase 1B only, replace the parent contract's prohibition on data-dependent
variable latency with this rule:

> **Bounded deterministic service latency.** Each operator must have a finite,
> reproducible service-cycle count under its specified RTL semantics.
> Operand-dependent latency is permitted where the underlying implementation
> requires it, provided the exact count is independently derived from frozen
> operands and operator semantics, recorded in the Phase 1B input manifest,
> and frozen before any candidate scheduler runs. No candidate may estimate,
> modify, or select service-cycle counts during evaluation. Unbounded
> execution, nondeterministic scheduling, and undocumented latency variation
> remain prohibited.

Exact arithmetic, reproducible latency, finite worst-case latency, frozen
timing inputs, and bounded deterministic scheduling are mandatory. Identical
latency for every operand is not required.

## 3. Timing Qualification Requirements

Before scheduler evaluation, prepare and review a timing table keyed by frozen
operation ID. It must distinguish:

1. **Intrinsic operator timing:** accepted-start-to-completion cycles from the
   applicable operator's RTL semantics, including normalization, handshakes,
   and early invalid/error completion.
2. **Candidate execution timing:** additional cycles from the declared
   candidate's product-lane count, operation mapping, issue schedule,
   accumulation resources, and completion protocol.

Do not add overlapping stages twice. Do not assign Candidate A latency to B or
C when their resource schedules differ. Freeze each candidate's service
schedule before measuring contention.

The timing derivation must be independent of the scheduler evaluator. Include
representative zero/unit, signed-extreme, fast/slow GCD, normalized,
non-normalized, and invalid-denominator cases. Validate the finite worst-case
bound. Report these separately:

- A proved or derived upper bound over the complete supported operand-width
  domain.
- The maximum latency observed among the frozen Phase 1A fixtures.

The fixture maximum is evidence about those fixtures only; it does not
establish the general operand-domain upper bound. If the upper bound or exact
accepted-start-to-completion timing cannot be established for an operation,
mark its timing unqualified and halt the affected comparison.

Keep three latency quantities distinct:

\[
L_{\mathrm{operator}}(x),\qquad
L_{\mathrm{candidate}}(x),\qquad
L_{\mathrm{response}}(x).
\]

`L_operator` is intrinsic accepted-start-to-completion latency.
`L_candidate` includes the candidate's fixed resource mapping and issue
schedule, but excludes contention-dependent queueing. The scheduler computes
`L_response`, which includes queueing, arbitration, and backpressure. Do not
freeze `L_response` in the timing table or count contention in both candidate
service and scheduler response time.

Phase 1B must not claim constant-time execution. The permitted guarantee is
bounded deterministic service latency for the frozen input set and declared
operator model.

## 4. Remaining Phase 1B Gate

The scheduler remains held until a separate Phase 1B execution contract:

- Specifies complete A/B/C micro-operation schedules and resource mappings.
- Records the reviewed intrinsic and candidate-specific timing table hashes.
- Names the exact command and output directory.
- Freezes maximum attempts, per-attempt timeout, cumulative budget, and retry
  policy.
- Confirms that only the reviewed Phase 1A fixtures are consumed and that no
  RTL, synthesis, P&R, FPGA, or hardware operation is included.

Owner authorization of Phase 1B does not permit launching before these items
are frozen and timing qualification passes.
