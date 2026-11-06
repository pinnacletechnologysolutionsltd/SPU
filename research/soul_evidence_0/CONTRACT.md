# SOUL-EVIDENCE-0: bounded evidence checking

**Status:** PROPOSED — not an execution authorization
**Predecessors:** SOUL-MEM-2 (PARTIAL), SOUL-LEARN-0 (BOUNDED PASS)
**Scope:** deterministic, software-only research
**Production integration and publication:** HOLD

## Question

Can a separately implemented checker distinguish a supported deduction from a
hypothesis merely consistent with observed examples, and detect whether a cited
counterexample really contradicts a hypothesis?

The checker operates over a small, declared vocabulary and trusted fixture
observations. It checks whether evidence supports a claim *under those rules*;
it does not establish source truth, prove a universal empirical hypothesis, or
validate arbitrary reasoning. A correct prediction alone is not evidence that a
hypothesis is uniquely established.

## Proposed interface and semantics

Input: a typed claim, explicit evidence IDs, a finite evidence registry, and a
declared set of inference rules. Record source IDs, relevant entity identities,
epochs and the evidence used. The checker must not receive the expected verdict
or evaluator ground truth. Define the supported syntax and rule semantics before
registration; do not silently infer unlisted rules.

Use exactly these five top-level verdicts, with a reason:

- **SUPPORTED:** the claimed derivation or bounded consistency statement is
  established under validated premises and declared semantics.
- **UNSUPPORTED:** complete applicable evidence and rules establish that the
  claimed derivation or consistency statement is invalid.
- **UNKNOWN:** required evidence or trusted context is absent or incomplete.
- **INVALID_EVIDENCE:** evidence or trusted-anchor validation fails.
- **UNVERIFIED:** complete inputs are present, but the requested interpretation
  or inference lies outside supported semantics.

Use CONSISTENT, CONTRADICTED and
`UNIQUE_WITHIN_DECLARED_HYPOTHESIS_AND_EVIDENCE_BOUNDARY` only as typed findings,
not top-level verdicts. Apply precedence in this order: INVALID_EVIDENCE,
UNKNOWN, UNVERIFIED, then SUPPORTED or UNSUPPORTED after semantic checking.
Malformed, inconsistent or anchor-invalid records are INVALID_EVIDENCE. An
absent trusted anchor is UNKNOWN; a present invalid anchor is INVALID_EVIDENCE.
Register exact conflict, stale, revoked, duplicate and missing-record handling
before execution. A failed justification is not proof that its proposition is
false, and missing evidence does not establish a conclusion.

## Bounded fixtures

1. A direct proposition supported by its exact observation.
2. A declared transitive relation: A relates to B and B to C supports A to C;
   absent the rule or a premise, return UNKNOWN. A source merely mentioning A
   and C must not by itself validate the deduction.
3. A broken or reversed inference chain, a mismatched entity or epoch, and a
   misleading but relevant reference: none may be counted as support.
4. Two examples consistent with multiple candidate hypotheses: report a CONSISTENT typed finding, not unique establishment. An unseen prediction remains a
   prediction until feedback is supplied.
5. A genuine labelled counterexample to the provisional `linked` hypothesis;
   validate both its applicability and its conflicting outcome. The revised
   candidate can be consistent with the available examples without being
   universally proved.
6. A cited revision whose supposed counterexample instead supports the rejected
   candidate; detect the invalid attribution. Also test missing, revoked or
   corrupted references and conflicting observations.

Register exact cases and independently specified expected verdicts before
running them. Include controls that show valid evidence remains usable, plus
mutations to premises, rule identity and counterexample labels that change the
expected verdict. A crash or blanket refusal is not a successful control.

## Execution and evaluation, if authorized

Use an independently coded checker rather than the same reasoning function that
produces claims. The small [SOUL-MEM-2 checker](soul_mem_2/support.py) may inform
the design; identify any actual reuse. The
[SOUL-LEARN-0 findings](soul_learn_0/FINDINGS.md) supply a bounded learning
example, not proof of open-ended learning or engine migration.

Preserve the exact fixture data, claim and evidence inputs, expected and actual
verdicts, source hashes, negative-control outcomes, commands and limitations.
Measure verdicts separately for deductions, predictions, hypothesis
consistency and counterexample/revision attribution. Run focused tests and two
deterministic reproductions within the repository's Class A resource limits.
A bounded pass requires the registered positive cases and targeted negative
controls to behave as specified, with reproducible outputs and no hidden access
to expected verdicts. If a semantic check is absent, report PARTIAL or
INCONCLUSIVE rather than treating relevance as proof.

No transformer, generalized theorem prover, network, physical hardware,
production integration or publication is authorized. Migration of learned
state into a different engine belongs to a later SOUL-CONTINUE-1 proposal;
history-dependent perception belongs to a separate SOUL-PERCEPT-0 proposal.
Prior experimental results remain unchanged.

## Amendment A1 — evidence-set completeness and bounded uniqueness

**Status: approved for contract inclusion; execution remains proposed.** A
hypothesis-uniqueness claim must identify the finite hypothesis language and
version, the complete trusted evidence set, the declared interpretation rules,
and the evidence-set anchor or equivalent trusted identifier.

Before evaluating uniqueness, the checker must validate set membership and
contents against the supplied trusted anchor and distinguish a complete set
from an incomplete or unverified subset. Missing required records yield UNKNOWN
or INVALID_EVIDENCE under the registered failure classification; consistency
with a subset does not establish consistency with the declared complete set.
A hash checks consistency against its trusted anchor, not authorship or source
truth, and cannot protect against replacement of both data and anchor.

Only exactly one candidate surviving independent checking against **every**
observation in the validated set qualifies for the label
`UNIQUE_WITHIN_DECLARED_HYPOTHESIS_AND_EVIDENCE_BOUNDARY`. This does not establish
truth beyond the supplied evidence, uniqueness among unrepresented hypotheses,
source reliability, generalization, subjective certainty or consciousness.

Register controls for a complete set with exactly one survivor, a complete set
with multiple survivors, a complete set with none, an incomplete set that would
falsely appear to establish uniqueness, altered set membership, and a complete
valid set containing a counterexample to the claimed unique candidate. At least
one mutation must preserve structurally valid records while invalidating the
claimed semantic conclusion. Freeze the evidence-set definition, hypothesis
language, inference rules, expected outcomes and trusted-anchor format before
registered evaluation; preserve negative results and record repairs as distinct
attempts. No changes to prior Soul experiments are authorized by this amendment.


## Amendment A2 — checker independence, anchor and verdicts

**Status: approved for contract incorporation; implementation is not authorized.**
The checker independently reconstructs the complete surviving hypothesis set
from the declared language and validated evidence. It does not trust the
learner's reported survivors, eliminations or uniqueness claims. Register a
correct survivor set, incorrect elimination of a consistent candidate,
incorrect retention of a contradicted candidate, and forged uniqueness despite
multiple survivors. Detect discrepancies through independent evaluation.

The trusted anchor binds all three components: complete evidence-set membership
and record contents; hypothesis candidate definitions, identifiers and language
version; and predicate meanings, inference rules and their versions. Validate all
three bindings before reporting bounded uniqueness. A substituted language or
rule set must not pass solely because the evidence digest remains valid. The
anchor arrives through an explicitly trusted channel; a digest neither
authenticates that channel nor protects against replacement of data and anchor.

Apply the five top-level verdicts and precedence defined above. CONSISTENT,
CONTRADICTED and the exact A1 bounded-uniqueness label are typed findings only.
Emit bounded uniqueness only for exactly one survivor after complete validated
evidence, language and rule bindings and supported semantics. The finding does
not establish truth outside that declared boundary.

In addition to A1 controls, register correct evidence with substituted language;
correct evidence and language with substituted rules; complete valid evidence
with an incorrect learner survivor set; complete valid evidence with forged
bounded uniqueness; missing required evidence; a present invalid anchor; and
complete valid evidence with an unsupported inference rule. At least one
mutation must preserve structurally valid records while violating a semantic
claim. The precedence for missing and invalid anchors is fixed above.

This amendment authorizes no implementation, registered evaluation, changes to
completed Soul experiments, QAF, SPU RTL or ISA, general proof-system work,
production integration or publication. Execution remains PROPOSED.
