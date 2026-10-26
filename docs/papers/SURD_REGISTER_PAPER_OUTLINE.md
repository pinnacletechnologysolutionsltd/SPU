# ISA-Visible Exact Quadratic-Surd Registers

[Working manuscript](SURD_REGISTER_PAPER_DRAFT.md) drafted October 10;
results/conclusions remain provisional pending qualification and evidence review.

Working subtitle: Semantics, Processor Integration, and FPGA Cost.
Date: 2026-10-08. Outline for a focused architecture paper, not a completed
qualification report or novelty certification.

## Research question and contribution

Can an ISA-visible bounded Q(sqrt(3)) register file provide exact arithmetic
with deterministic failure semantics, alias-safe atomic retirement and recovery,
and what FPGA resource and latency costs follow from that contract?

Cost is an evaluation question, not an assumed claim of practicality. Answer
correctness and integration from the frozen simulation evidence, characterize
latency from retained traces, and identify which cost questions remain open
until integrated routing and board measurements are available.

### Proposed Section 1 contribution paragraph

We present an ISA-visible bounded Q(sqrt(3)) register architecture that combines
an explicit normalization policy, exact overflow rescue, alias-safe retirement
and full-bank preservation on failed arithmetic retirement. The architecture is
implemented in the SPU CPU datapath and evaluated through focused RTL simulation,
an independent arithmetic oracle and reproducible kernel traces. Standalone FPGA
routing estimates characterize selected component costs; integrated fit, routed
resource utilization, timing and board performance remain unresolved. The
contribution is this processor-visible contract and its implemented integration.
Its novelty relative to prior arithmetic processors requires full-text comparison.

### Representation and claim boundaries

A processor-visible finite-width tuple represents `(a + b sqrt(3)) / D` with
integer coefficients and positive denominator. The contribution is the complete
architectural contract: tuple transfers, arithmetic, deliberate normalization,
alias-safe retirement, exact overflow rescue and preservation on failure.
The current implementation fixes the radicand at 3. Generic `sqrt(r)` support
belongs in discussion unless separately specified and implemented.

Successful operations preserve the represented value exactly. Finite capacity
can cause failure; these registers are not closed over all of Q(sqrt(3)).
Deterministic results do not imply constant execution time: alignment and
normalization consume data-dependent work. Exactness and latency are separate
claims. Avoid claiming a general division instruction from the bounded exact
quotient machinery used internally by normalization/alignment.

## Proposed paper structure

1. **Problem and contribution.** Explain the spatial closure workload and why
   exact algebraic structure matters. Lead with the research question and narrowed
   contribution paragraph above. State the implemented processor interface and
   distinguish supported conclusions from the still-open integrated cost question.
2. **Related work.** Compare rational arithmetic processors, exact geometric
   number types, quadratic-extension hardware, and processor custom arithmetic
   interfaces. Establish differences in arithmetic domain, bounded representation,
   normalization policy and visible failure/retirement semantics.
3. **Representation and ISA.** Specify widths, positive-denominator constraints,
   invalid/uninitialized tuples, load/read slice order, register validity, operation
   formulas, status, busy behavior, reset and source/destination aliases. Distinguish
   value equality from tuple identity. Fitting raw zero retains its denominator;
   explicit normalization or rescue has its own canonical-zero rule.
4. **Microarchitecture.** Show dispatch, register bank, captured operands,
   arithmetic engine, alignment, normalizer and retirement. Explain wide
   intermediates, exact remainder checks, resource sharing and commit gating.
   Derive a successful write and a failed operation preserving the full bank.
5. **Verification.** Freeze source hashes, independent oracle and executable
   tests. Include destination-right/all-equal aliases, full bank/validity failure
   preservation, injected terminal engine failures and recovery without reset.
   Separate directed simulation coverage from universal/formal claims.
6. **Kernel evaluation.** Define forward/inverse/closure schedules and reductions.
   Report instructions, transfers, cycles, alignment, rescue requests and normalizer
   starts. The retained 128-group cohort has rational joint coefficients (`b=0`);
   directed radical tests do not establish a radical-heavy throughput result.
   Describe the issuer/host work so end-to-end scope is reproducible. Retain this
   cohort as the primary workload; report any future radical-heavy microbenchmarks
   separately, using the criteria below.
7. **FPGA evaluation.** Present standalone block routing estimates separately
   from integrated synthesis and completed routing. Use matched clocks/devices,
   parameter widths and workload contracts. Publish unsuccessful bounded attempts
   where they explain integration limits. Board measurements require their own
   frozen image and [hardware evidence ledger](../hardware_evidence.md) entry.
8. **Limits and conclusion.** Discuss representation bounds, variable latency,
   unsupported baseline capabilities and compiler/runtime scope. Vector registers,
   larger devices and heterogeneous GPU integration are future work.

## Evaluation mapped to the research question

| Question | Evaluation section | Required distinction |
| --- | --- | --- |
| Are represented values exact on success? | Representation/ISA and verification | Value equality versus tuple identity; raw versus normalized zero |
| Are failures deterministic and atomic? | Microarchitecture and verification | Status, one retirement, no writes, full bank/validity preservation |
| Do aliases and recovery preserve integration behavior? | Verification | Source capture, destination-right/all-equal cases, recovery without reset |
| What latency follows from the policy? | Kernel evaluation | Transfers, alignment, rescue and scheduled reductions; deterministic is not constant-time |
| What FPGA cost follows from the contract? | FPGA evaluation | Standalone estimates versus integrated synthesis, completed routing and physical measurements |

## Proposed radical-heavy microbenchmark cohort

Status: offline evaluation proposal, not an executed cohort or authorization to
launch tests, synthesis or hardware. Preserve the 128-group results unchanged.

Use a small frozen set with nonzero radical coefficients in both operands.
Include multiply cases where both `3*b1*b2` and the cross terms contribute to
the result, unequal-denominator ADD/SUB, fitting operations, successful rescue
and unrepresentable results. Include a conjugate product as an interpretable
check, but also retain results whose radical coefficient stays nonzero.
Exercise destination aliases under the same frozen ISA contract.

Before execution, specify exact input tuples, expected raw/canonical tuples,
status, rescue path, register effects and source hashes. Use the independent
oracle and existing CPU issue/readback path. Freeze the schedule and campaign
budget before launching any long-running evaluation. Report cycles, instruction
and transfer counts, alignment work, rescue requests and normalizer starts.
Keep correctness and latency results separate from throughput claims; a small
directed cohort would establish exercised surd behavior, not representative
application performance or a measured hardware speedup.

## Drafting order

Lock Section 1's question and contribution paragraph first. Write Representation/
ISA and Verification against the frozen interface and evidence next. Then write
Microarchitecture and the evaluation sections to answer the questions above.
Keep pending measurement tables explicit rather than filling them with estimates
from different configurations. Related-work comparison can proceed alongside
drafting without asserting a priority claim.

## Evidence available and missing

| Claim | Evidence now | Limit or next gate |
| --- | --- | --- |
| Arithmetic contract | [Oracle review](../SURD_CPU_ORACLE_REVIEW_2026-10-07.md) and frozen interface | Checked cases; no universal proof |
| CPU integration and retained kernels | Frozen `focused_01` simulation PASS | Host/issuer scope must be described; no board throughput |
| Failure preservation and aliases | [Verification update](../../spu_strategy/contract_surd_cpu_verification_update_2026-10-07.md): 39 failed retirements, 17 aliases, 6 terminal fault injections | Directed subset; broader required gates not rerun for the update |
| Trace extraction | [Analyzer](../SURD_CPU_KERNEL_ANALYSIS_2026-10-07.md): 128 groups agree with retained counters | Counter agreement alone does not prove arithmetic |
| Resource trade-offs | [Progress article](../blog/exact_surd_progress_2026-10-07.md): standalone routing estimates | Review original reports and source identity before publication |
| Integrated FPGA fit/timing (historical campaign) | [Campaign closeout](../../build/spu_surd_register/main_cpu_integration_20261007/campaign_closeout_01.json): CLOSED_TIMEOUT, zero remaining attempts | Fit unresolved; timing, critical paths and board performance unmeasured |
| Historical corrected integrated mapping candidate | [Attempt result](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/result.json): TIMEOUT, exit 124, 7,200 seconds in analytical placement; synthesis/packing confirmed 234/240 DSPs, including 24 selected REGEN and 80 incremental Surd DSPs | 81% packed LUT-slot occupancy; legal routing and complete required timing coverage/PASS at 25 MHz unavailable; no board result |
| Packet 06 routed CPU | [Independent route audit](../../build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_all_net_audit_20261015.json): route-integrity PASS, 51,197 preserved cells, 192,229 connected physical sinks | Timing HOLD: 40.886 MHz remains an unqualified tool estimate; active FF/DSP arcs and corners remain incomplete; 25 MHz and board operation unqualified |
| Native integer comparison | [Capability specification](../../spu_strategy/spec_surd_integer_baseline_capabilities_2026-10-07.md) | Baseline unsupported; specification remains owner-unreviewed |
| CPU speedup and energy | No established result | Do not report either as measured |

Use separate tables for simulator cycles, synthesis counts, completed routing
estimates and physical observations. Mapped cell counts are not routed LUT
utilization; estimated Fmax is not measured board clock behavior. Existing
physical observations of other Surd/ROTC blocks do not qualify this register bank.

For comparison, an exact software/reference baseline must meet the same success
and failure contract. Floating/fixed-point comparisons can report cost and error
or closure drift, but they compute a different correctness contract. Do not
expand the ISA merely to manufacture a comparison. A larger FPGA may enable a
later evaluation; it is not a prerequisite for drafting this focused paper.

## Initial primary-source related work

This is a starting set, not an exhaustive novelty search. Do not use “first ever”
or “to our knowledge” as a substitute for full-text comparison and citation tracing.

* Irwin and Smith, **Rational Arithmetic Processor** (1981), describes rational
  representation, GCD-driven reduction and hardware arithmetic. This is direct
  prior work for reduction architecture, though it does not by itself establish
  the same quadratic-surd ISA contract. [Institutional publication record](https://pure.psu.edu/en/publications/rational-arithmetic-processor).
* **CGAL Sqrt_extension** documents exact number-type extensions by a square root
  and restrictions on mixing extensions. The mathematical tuple representation
  is established software practice. [Official reference](https://doc.cgal.org/latest/Number_types/classCGAL_1_1Sqrt__extension.html).
* **Constant-time hardware computation of elliptic curve scalar multiplication
  around the 128 bit security level**, Microprocessors and Microsystems (2018),
  DOI `10.1016/j.micpro.2018.05.005`, is a quadratic finite-field hardware lead.
  Finite-field cryptographic arithmetic differs from ordered Q(sqrt(3)) tuples.
  Review the full paper before making architectural absence claims.
  [Publisher record](https://doi.org/10.1016/j.micpro.2018.05.005).

Before submission, complete the processor-interface literature search, review
the frozen source/test packet, reconcile every result with its raw evidence,
and close the applicable implementation gates within an owner-authorized budget.
Drafting this outline launches no synthesis or hardware work.
