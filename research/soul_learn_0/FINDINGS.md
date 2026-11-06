# SOUL-LEARN-0 findings

**Disposition: BOUNDED PASS.** In one deterministic two-feature world, a
finite-hypothesis learner selected a provisional rule from examples, predicted
a counterexample incorrectly, rejected that candidate after feedback, and
retained a revised candidate through serialization. This is preliminary
exploratory software evidence, not independent verification or qualification.

| Measurement | Registered result |
|---|---|
| Training example recall | 2/2 |
| New-entity predictions before counterexample | 2/2 correct |
| Prediction of linked detachable counterexample before feedback | wrong |
| Hypothesis revision | `linked` rejected by the counterexample; `linked_and_fixed` selected |
| New-entity predictions after feedback | 3/3 correct |
| Revision retention | serialized state and later predictions exactly reproduced |
| Exact-ID memorization baseline on post-feedback cases | abstained on all 3 new IDs |

The first two observations are consistent with both `linked` and
`linked_and_fixed`, so the learner marks its state **unresolved** while using
its predeclared simplicity ordering to make provisional predictions. It is not
justified in treating that provisional rule as uniquely established. When the
detachable example contradicts `linked`, the state records the rejecting
observation and retains the surviving candidate. A rejection means inconsistency
with the supplied trusted evidence and candidate language; it is not a proof of
the rule's logical negation.

All six controls passed: initial unknown; ambiguity explicitly unresolved;
rejection linked to its counterexample; no revision without that feedback;
inconsistent evidence leaving no prediction; and a memorizer abstaining on
unseen IDs. Three focused tests passed. Two complete runs produced byte-identical
outputs; this does not constitute independent implementation verification.

## Interpretation

**Established in this fixture:** elimination of explicit candidate rules based
on observations, a falsifiable provisional prediction, evidence-linked
rejection, a changed subsequent prediction for new IDs, and same-implementation
serialization and reload.

**Observed:** the fixed simplicity preference made the initial counterexample
prediction wrong, and the remaining candidate predicted the registered later
cases. The exact-ID memorizer could not answer these new IDs.

**Assumed:** noiseless labels, correct feature extraction, trusted examples and
an environment expressible in the four predefined candidates. The target rule
was not passed to the learner, but it was included in its finite hypothesis
language. These conditions make the task deliberately small.

**Unknown:** discovery outside the supplied language, noisy or adversarial
feedback, new predicates, broad out-of-distribution generalization, richer
relational reasoning, and whether a different engine can interpret the acquired
revision. Distinct test IDs exercise new objects but the feature domain contains
only four combinations; this is not general reasoning from arbitrary experiences.

**Excluded:** consciousness, subjective identity, transformers, network access,
physical systems, production integration and publication. The second-engine
continuation and independent evidence-verification questions remain future work.

## Reproduction

Python 3.10.12; base repository revision
`e818108fc9addc64b67bbe60b7ad132aa4f8c531`, with unrelated workspace changes.
The contract, sources, fixtures, tests and reproduction instructions were hashed
before the two registered runs. No registered repair or criterion change was
made. The [README](README.md) contains commands, limits and policy details;
`evidence/results.json` preserves the full observations, state, predictions,
controls and metrics. Prior Soul experiment files and the earlier consolidation
note were not changed.
