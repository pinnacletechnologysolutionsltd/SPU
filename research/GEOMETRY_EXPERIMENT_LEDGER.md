# SPU Geometry Experiment Ledger (frozen framing)

Status: framing only. No experiment, benchmark, ISA, RTL or candidate implementation is authorized or implied by this file.
Evidence labels follow `docs/hardware_evidence.md`; nothing here is "silicon-verified".

## Hypothesis

For geometry tasks whose natural quantities are intrinsic to the SPU representation, computing in that representation
costs fewer exact operations, narrower intermediate widths, or fewer refusal-prone steps than the strongest relevant
conventional method with equivalent mathematical optimizations, and the benefit separates into representation effects
and SPU-architecture effects.

## Mandatory pre-execution falsification condition

Before any run, each task fixes: the metric, the conventional baseline, the input set and the pass/fail threshold.
The hypothesis is falsified for a task if the conventional baseline (Variant C) is equal to or better than the
intrinsic-representation variants (A, D) on the pre-registered metric. A threshold chosen or changed after seeing
results is invalid. Negative results are committed.

## Comparison roles

A-D are comparison roles, not distinct code bases; one implementation may fill several roles when it is equivalent.

| Role | Meaning |
|---|---|
| A | Intrinsic representation on the SPU architecture. |
| B | Cartesian conversion reference: optional conversion-cost reference only; not a mandatory conventional baseline. |
| C | Strongest relevant conventional method with equivalent mathematical optimizations (the baseline). |
| D | The same intrinsic representation on conventional hardware; isolates representation benefits from SPU-specific benefits. |

Reading: D vs C = representation effect; A vs D = SPU-architecture effect; A vs C = combined effect.

## Evidence table

| Class | What it can establish | Required support | Current status |
|---|---|---|---|
| Proven width-bound improvement | A proven bound on operand/intermediate width, with a stated theorem or exhaustive check | Proof or exact-arithmetic enumeration | none registered in this ledger |
| Algorithmic saving | Fewer exact operations of a counted kind versus C | Operation counts against an independent oracle | none registered in this ledger |
| Architectural advantage | A benefit that exists only given SPU hardware structure (A vs D) | RTL simulation evidence, reported separately | none registered in this ledger |
| Physically measured benefit | Timing, resource or board behavior | Entry in `docs/hardware_evidence.md` | none registered in this ledger |
| Power / energy | Not claimed | Credible measurement only | **unmeasured** |

Rows are added only with citations to the supporting artifact; the four classes are reported separately and never merged.
Software conformance, RTL functional evidence, synthesis/timing and physical qualification stay separate (AGENTS.md 4.4).

---

## Amendment 1 (2026-10-23, parent c261820): Variant E and the compiler-analysis level

The text above is unchanged. This amendment adds one role and one rule; it removes or weakens nothing.

### Role E (form-based lowering)

| Role | Meaning |
|---|---|
| E | Form-based compiler lowering: the intrinsic representation expressed as small forms (Gram/quadratic/bilinear) and lowered by a compiler. Tests whether the uniform form representation improves specialization, width inference or arithmetic reuse over individually written expressions. |

Hypothesis for E: a uniform representation of small geometric forms yields better width inference or
reusable arithmetic across multiple operations than individually optimized expressions, without prohibitive
added state, conversions or width growth.

Falsification for E (pre-registered metric and threshold per task, as above): E is falsified for a task if it does
not beat the better of A and C on the pre-registered metric, where both A and C have received competent
compiler common-subexpression elimination across their separate functions. A threshold chosen or changed after
seeing results is invalid. Negative results are committed.

### Compiler-CSE rule

A, C and D baselines must be given the common-subexpression elimination a competent optimizing compiler
would apply across specialized functions before E is compared. A shared-partial-product saving measured against a
baseline without that elimination is an optimizer deficiency, not an architectural result, and is invalid.

### Compiler-analysis level (added row to the evidence table)

| Class | What it can establish | Required support | Current status |
|---|---|---|---|
| Compiler-analysis benefit | A bound or sharing that a compiler can derive mechanically from E (e.g. per-stage width bounds, detected common products) **without reducing the counted operation count** | Mechanical derivation shown, checked against an independent oracle | none registered in this ledger |

A failed algorithmic claim must not be relabelled as a compiler-analysis benefit. If operation count or live
state falls, report it as an algorithmic saving against C; if neither falls, a compiler-analysis result is
reported as such and is not a hardware saving until measured.

### Cross-reference

Cartesian conversion cost is reported via role B; no separate rule is added here.
