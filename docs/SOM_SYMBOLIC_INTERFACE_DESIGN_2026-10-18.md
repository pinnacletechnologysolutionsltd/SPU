# SOM–symbolic interface: candidate ranking with independent exact verification

Status: DESIGN ONLY, 2026-10-18. No bridge implementation, training run, firmware
change or campaign is authorized here. Preserve qualified SSM-0 through SSM-3 and
the existing SOM path. This document specifies a small next interface to review,
not a neural S3 experiment or SSM-4. The current sequence places
[SG-0](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md) and the resulting
[SSM-4 geometric-state work](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md)
before SOM–SSM implementation; this interface remains follow-on design.

## Responsibility boundary

SOM may organize patterns, rank candidates or prioritize work. SSM admits only
supported exact operations and independently checks their consequences. A SOM
winner, similarity score, label or confidence gap is not a mathematical proof.
The system must preserve that distinction in storage and logs.

| Object | Authority |
|---|---|
| Frozen original rational equations | Declared assumptions for this task; not established physical facts |
| Candidate row operation | Proposal only until exact validation |
| SOM winner/ranking/ambiguity | Adaptive ordering evidence, never proof validity |
| Accepted scale/elimination | Exact operation over admitted immutable inputs |
| Derived certificate | Checkable consequence relative to those original inputs |
| Complete row-operation replay | Evidence of equivalent final system and supported classification |

The current SOM oracle is [rational_som.py](../software/lib/rational_som.py);
the [SOM v1 contract](SOM_V1_PRODUCT_CONTRACT.md) specifies weighted quadrance,
stable ties, runner-up and ambiguity. Existing classification hardware evidence
is recorded separately in [hardware evidence §§3.2g.5–3.2g.6](hardware_evidence.md#32g5-som1-full-decision-evidence-silicon-proof).
That classifier evidence establishes no SOM–SSM integration or inference benefit.
The first proposed bridge is host software only.

## Smallest bounded candidate-selection design

Use the frozen SSM-3 three-variable tasks. A trusted enumerator forms a finite
catalog of currently supported row operations from the active snapshot. SSM-3's
qualified deterministic schedule remains the unchanged baseline. The bridge
would be a separate adapter with its own contract, not a change to SSM-3.

Start with ranking certified-operation candidates, not inventing equations:

1. Identify the original-input digest, ledger snapshot and active references.
2. Enumerate eligible nonzero scale/pivot/elimination actions, retaining distinct
   target and pivot positions and every original active row.
3. Build a frozen feature vector per candidate and query a frozen SOM map.
4. Order candidates with an explicitly declared node-priority mapping, stable
   candidate-ID tie-break and deterministic fallback on ambiguity or rejection.
5. Revalidate the selected candidate against the exact current snapshot.
6. Execute through the narrow certified row-operation interface; retain the
   original-row certificate and complete equivalence-preserving history.
7. Independently replay the emitted proof before publishing a mathematical result.

A different operation order may alter fill and intermediate coefficient sizes.
It cannot change the original task or the meaning of a verified final result.
Repeated stale or unproductive choices may exhaust a budget; that outcome must
remain separate from empty/unique/family. Verification does not guarantee that
an adaptive scheduler finds a useful or terminating sequence.

## Proposed messages, features and provenance

`Candidate` contains task digest, snapshot digest, candidate ID, operation name,
active target/pivot positions, coefficient column or exact scaling factor,
and expected supported domain. It carries no authority to insert new assumptions.
`Ranking` contains candidate IDs, SOM map/model identity, feature schema/version,
feature values, winner/runner-up data, ambiguity and ordering policy identity.

`Admission` records accepted/rejected, exact reason, revalidated parent IDs and
whether the snapshot was current. `CertifiedResult` records proof artifact digest,
verification outcome and explicit empty/unique/family/resource status. Mathematical
and adaptive records stay separate but share stable task/snapshot identities.
Store proofs and enough original inputs to replay them, not only model scores.

A first four-feature sketch uses exact nonnegative integers:

- Pivot magnitude numerator bit length.
- Pivot denominator bit length.
- Current target-row nonzero coefficient count.
- Upper bound on fill in the proposed resulting row's coefficient support.

This schema is provisional. Require an explicit definition for scale candidates,
normalization, feature range, clipping/rejection and map feature order before any
experiment. Integer features can embed as (p,0) in the existing surd-pair oracle;
that is an explicit bridge, not an assumption that SSM is using surd coordinates.
Freeze feature weights and prototypes. No online map mutation occurs during an
inference trial. A SOM cluster ID alone has no inherent scheduling priority;
the node-priority rule needs its own declared or trained provenance.

## Proposed equations remain hypotheses

A later proposal may suggest a new relation, but it must be tagged
UNTRUSTED_HYPOTHESIS. Without a valid derivation from the fixed original rows,
it cannot be admitted as a certified conclusion. If an owner intentionally adds
it as an assumption, that creates a different task and conditional conclusions;
it does not validate the hypothesis against the physical world.

The first pilot excludes admission of new axioms, learned changes to proof rules,
new algebraic domains and probabilistic treatment of exact observations. It also
excludes Soul integration, neural training, RTL/opcodes and FPGA SOM changes.

## Required future controls and measurements

Compare frozen deterministic scheduling, a fixed nonlearned candidate ordering,
and the SOM-ranked adapter on identical tasks and resource budgets. Keep evaluation
cases separate from map fitting; equivalent rescalings/edge order changes must not
leak task identity into training labels. Training/evaluation splits and candidate
budgets require a future frozen contract; no learning result is claimed now.

Acceptance should require:

- Every published conclusion passes original-row and active-system replay.
- No invalid or stale candidate is executed; reject wrong IDs, domains, zero
  scales/pivots, self-elimination, dropped rows and fabricated certificates.
- A malicious high-confidence ranking cannot alter proof acceptance.
- The two SSM-2 cycle controls remain decisive: relational proofs distinguish
  them; no classifier label may substitute for those proofs.
- Where all schedulers finish, exact joint families agree with the frozen global
  baseline. Budget exhaustion is reported, never converted into an inferred answer.
- Replaying fixed map/features and proposals reproduces the same ordering and proof.

Report completed tasks, verified/rejected proposals, rejection reasons, operation
counts, peak coefficient/certificate bit lengths, message use and total feature/
SOM/proof-check costs separately. Performance or generalization improvement is an
open question, not an acceptance assumption. Classification accuracy alone would
not establish better symbolic reasoning or proof correctness.

The [consolidated SSM architecture](SSM_ARCHITECTURE_2026-10-18.md) is the qualified
software baseline. This interface remains a design artifact pending its own
implementation scope, executable semantics, budget and authorization.
