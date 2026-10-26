# AOR-1 — Phase A software implementation contract

**Contract ID:** `contract_spu13_aor1_phase_a_2026-10-11.md`

**Status:** PROPOSED — review only; implementation and execution not authorized.

**Date:** 2026-10-11

**Review amendment:** 2026-10-12 — numerical limits recorded; execution remains gated.

Read the review before ratifying numerical parameters or execution:

```bash
sed -n '1,200p' docs/AOR1_PHASE_A_DRAFT_REVIEW_2026-10-11.md
```

## 1. Scope and authority

Define a mathematical oracle, bounded reference and independent negative-control
suite, separate from all current CPU/GPU implementations. No software code,
RTL modification, ISA encoding, register allocation, synthesis or routing is
authorized. The active Artix-7 timing campaign is independent.

The parent [AOR-1 proposal](contract_spu13_algebraic_octave_aor1_2026-10-11.md)
remains PROPOSED. Freezing this review draft does not ratify implementation.

## 2. Mathematical representation

z = (a+b sqrt(3))(2+sqrt(3))^k, with a,b,k in Z.
Phase A supports no rational-denominator mantissa. The mathematical oracle uses
arbitrary-precision integers; practical expansion still requires effort limits.

## 3. Special values

| Value | Required/preferred tuple (a,b,k) |
|---|---|
| Canonical zero | (0,0,0) |
| Preferred identity | (1,0,0) |
| Pell unit | (1,0,1) |
| Inverse Pell unit | (1,0,-1) |

step(0,n)=0 for a valid increment. Invalid operand validation precedes this rule.
Every zero-producing operation returns canonical zero. Equivalent nonzero
identity factorizations are permitted; general canonicalization is deferred.
Raw tuple equality is representation equality, not general value equality.

## 4. Bounded reference profile — owner-approved numerical direction

| Parameter | Agreed numerical limit / remaining implementation detail |
|---|---|
| Residual a,b | Signed64 integers |
| Stored k | Signed32 integer |
| Multiplication intermediates | Sufficiently wide exact temporaries; final-result checks |
| Norm output | Exact signed128 if representable |
| Overflow behavior | Defined status, full destination preservation |
| Oracle expanded coefficients | At most 1,000,000 magnitude bits each |
| Oracle per-case arithmetic budget | At most 100,000 counted operations; accounting pending review |
| Bounded expansion loop | At most 128 exponentiation-loop iterations |
| Bounded expansion output | Both coefficients must fit signed64 |
| Expansion effort | Separate bit-size guards; detailed accounting/prechecks pending review |

Evaluate mathematical expected results with arbitrary precision, independently
of bounded representability checks. Signed128 intermediates cannot cover every
signed64 Surd multiplication: ac+3bd and ad+bc may exceed that width. Use sufficient
temporary width rather than rejecting a fitting final result because of an
artificial signed128 intermediate limit. Signed130 suffices for these two product
accumulators; signed129 suffices for the residual norm calculation. These are
software width bounds, not a hardware allocation. Norm output remains signed128.

Conjugation independently checks negation of b and k, including signed minima.
Input increment width/domain, norm overflow status, and encoding validation
interface remain to be ratified. No binary encoding is allocated by this draft.

## 5. Expansion resource limits

EXPANSION_OVERFLOW means at least one destination coefficient is proven out of
range. EXPANSION_RESOURCE_LIMIT means permitted computational effort is exceeded
without necessarily establishing numerical overflow. No timeout implies overflow.

Use exponentiation by squaring and mathematically justified checks before large
allocations. The 128-iteration bound alone is not a computational-cost guarantee.
Freeze operation counting, temporary-size bounds and prechecks before execution.
A large |k| alone does not prove overflow: a residual can contain a cancelling
unit factor. The [accounting/precheck review proposal](contract_spu13_aor1_accounting_review_2026-10-12.md)
records precise candidate rules; they are not yet ratified.

Requested sequence: validate inputs/operation; check applicable exponent
arithmetic; attempt exact bounded-cost overflow proofs; enforce explicit resource
budgets; expand exactly and check signed64 results; commit atomically on success.
Prechecks themselves consume a declared budget. An unestablished numerical
overflow must be reported as a resource limit when that budget is exhausted.

For negative k use U^-1=2-sqrt(3), preserving integer exactness. Do not require
full expansion for stepping, multiplication, conjugation or residual norm.

## 6. Norm and representation

N(m)=a^2-3b^2 and N(m U^k)=N(m). The oracle calculates the exact norm. The bounded
reference returns it only if it fits the declared output range; otherwise it
reports a checked range failure. IS_UNIT may use an exact predicate independently
of whether a norm value can be returned, subject to final operation ratification.

## 7. Reversibility

I3: step(step(z,n),-n)=z as a representation when both operations succeed, for
valid normalized inputs. Here normalized means canonical zero or a valid nonzero
tuple; it does not mean a general canonical mantissa/exponent factorization.

I4: U^n U^-n is mathematical identity for all supported representations. For the
mantissa-one workload the tuple must be (1,0,0). General equivalent factorizations
need not canonicalize. Zero stepping remains reversible under its special rule.

## 8. Proposed deterministic failure precedence

1. Invalid encoding or malformed operands.
2. Unsupported operation or operand domain.
3. Exponent overflow.
4. Mantissa/result overflow.
5. Expansion-specific overflow or resource limit.

For expansion, proven destination overflow takes precedence when established
within the frozen computational budget; otherwise report its resource limit.
Every failure preserves destination. Resolve status names, zero-result exponent
checking, and simultaneous-fault cases before ratification. Proposed precedence
is not an implementation license to discard an overflow through normalization.

## 9. Eventual Phase A acceptance

- Exact coefficient/exponent results against an independent oracle.
- Pell recurrence and literal fixtures, positive/negative exponents.
- Canonical zero, preferred identity, conjugation and equivalent representations.
- Norm preservation/multiplicativity and bounded norm-output faults.
- Reversible steps, unit cancellation and bounded associativity behavior.
- Successful exact expansion, proven overflow and deterministic resource limits.
- Malformed operands, exponent/coefficient boundaries and simultaneous faults.
- Atomic destination preservation for every supported failure category.
- Injected incorrect coefficients, exponents and norms rejected by the checker.
- Mixed mantissa example: multiply (5,2,1000) by its conjugate (5,-2,-1000)
  and obtain (13,0,0) without coefficient expansion.
- Compare the same semantics against an ordinary Surd mantissa plus a signed
  exponent counter. Report practical handling, correctness, cost and integration
  differences; renaming the same tuple is not an architectural advantage.

Oracle, bounded reference and checker must not share arithmetic kernels as their
sole basis for expected results. Compare independent algorithms and literal
fixtures; agreement alone cannot establish correctness.

## 10. Authorization and stop conditions

Hold implementation until domain, widths, norm representation/status, arithmetic
policy, precedence and exact expansion effort limits are ratified. A subsequent
execution contract must provide exact commands, scoped files, required gates and
authorized budgets for deterministic jobs expected to exceed 60 seconds.

Do not implement unresolved semantics, assign opcodes, modify existing Surd
behavior or integrate AOR into the active physical campaign. The software-object
versus architectural-register decision remains open. No implementation,
qualification, routing, timing or silicon evidence is claimed by this draft.
