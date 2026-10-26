# SSM-3 proposal: bounded proof-carrying relational messages

Date: 2026-10-18
Status: ACTIVE — owner approved implementation and the verification amendment
Roles: current agent performs specification, implementation and audit sequentially.

## 1. Scope and preserved predecessor

Preserve the SSM-2 baseline `research/ssm2_baseline_20261018/`, all predecessor
implementations and serialization contracts. Future code is restricted to
`research/ssm3/` and this contract. GPU W1-C, C++ SIM-G1 and FPGA qualification
remain independent; do not launch or modify their campaigns here.

Retain SSM-2's three scalar rational variables A,B,C, at most three binary edges
and three observations, including its exact input validation and seven controls.
No full Q4 nodes, graph discovery, nonlinear equations, learning, Soul or ISA/RTL
changes. Use arbitrary-precision Fraction with the existing 4096-bit completed
coefficient guard.

The execution model is a shared, centrally scheduled relational-message pool.
It is not autonomous distributed message passing or a claim that unary local
propagation became complete. Explicitly compare these different representations.
The mathematics is bounded rational elimination, not novel linear algebra.

## 2. Persistent message and certificate representation

An immutable message contains:

- Sparse ordered coefficient pairs `(node_id, rational)` with no stored zeros,
  unique node IDs 0..2, and an exact rational right-hand side c.
- A certificate vector of length m, where m<=6 is the number of original edge
  and observation rows, including repeated observations.
- A deterministic message ID and operation/parent IDs. Parent IDs must refer
  strictly backward, preventing circular proof dependencies.

Message semantics: sum(a_j*x_j)=c. All-zero coefficients are legal derived
relations. Distinguish 0=0 (redundancy) from 0=c, c!=0 (contradiction).
The original input rows are immutable and never replaced by derived messages.
Their certificate vectors are unit vectors in canonical SSM-2 input order:
endpoint-sorted edges followed by sorted observations.

For original augmented rows r_i=(a_iA,a_iB,a_iC,c_i), every message must satisfy

```
r_message = sum(lambda_i * r_i)
```

Check all four rational entries exactly. A contradiction normalized to 0=1
therefore carries a checkable no-solution certificate. A derived singleton row
must carry its proof rather than merely presenting a numerical answer.

## 3. Explicit bounded instruction semantics

Expose software operations over message IDs, not binary processor opcodes:

1. `input(row,unit_certificate)`: publish an original relation after validation.
2. `scale(parent,q)`: q!=0, scale row and certificate by q.
3. `eliminate(target,pivot,column)`: pivot entry must be nonzero; derive
   target - (target[column]/pivot[column])*pivot, updating its certificate.
   Target and pivot must be distinct active row positions; retain the pivot.
4. `verify(message)`: check the operation/parents and original-row certificate.
5. `resolve(active_rows)`: classify the certified reduced system and construct
   its exact joint affine result, or return an explicit unfinished outcome.

Never turn arbitrary assertions into verified facts. Validate parents, IDs,
coefficients, certificate lengths, input rows and budgets before publication.
Failed operations leave all prior messages and active references unchanged.
Immutable old messages remain readable after a new derivation.

## 4. Frozen deterministic relational schedule

Keep at most six active row references, initially the original messages. For
columns A,B,C in order:

- Choose the first active row at or below the current pivot position with a
  nonzero coefficient; swap row references only.
- Scale that pivot to coefficient one.
- Eliminate that column from every other active row in row order, skipping
  zero coefficients. Publish each nontrivial result as a new immutable message.
- Advance the pivot position; retain every prior row and its derivation.

After the three coefficient columns, normalize the first contradiction row to 0=1.
Do not pivot on the constant column as though it were a fourth variable.
This is deterministic Gauss-Jordan elimination expressed as persistent relational
operations. Do not claim network-local routing or a performance advantage.
No enumeration of assignments is allowed.

A certificate establishes a consequence, not equivalence of an arbitrary
selected row set. The resolver must also replay active-row swaps, nonzero scales
and distinct-target eliminations starting with every original row. Replace
exactly one active reference per scale/elimination; never drop rows or replace
the retained pivot. These invertible row operations certify that the final
active system is equivalent to the original system. Reject valid-but-incomplete
collections of consequences as input to resolution.

Inspect this verified active system to classify empty, unique or family. For a consistent
rank-deficient system, construct the particular solution/nullspace parameterization
from these rows and use the qualified Family constructor for canonical output.
Do not call SSM-2's global baseline to obtain the message engine's answer.
Keep the unchanged global solve as a separate comparison path. It shares exact
representation code, so it is not an independent mathematical oracle.

## 5. Required controls and replayable proof artifacts

Reuse all seven SSM-2 cases, with exact agreement against its global baseline.
In particular:

- Inconsistent cycle B-A=0,C-B=0,C-A=1: derive normalized 0=1, with original-row
  linear-combination certificate. The unchanged unary solver stays UNRESOLVED.
- Unique cycle A+B=0,B+C=0,C+A=1: derive A=1/2,B=-1/2,C=1/2 with certificates.
  The unchanged unary solver stays UNRESOLVED.
- Unanchored chain: retain a dimension-one correlated family; do not collapse it
  to three independent unrestricted domains or choose an arbitrary witness.
- Anchored cases, contradictions and repeated contradictory observations:
  reproduce the frozen results, preserving their original input rows.

Add a redundant consistent cycle yielding at least one certified 0=0 row,
and nonunit rational coefficients with frozen exact solutions. Include an
empty-edge/empty-observation case denoting all Q3, with no fabricated proof rows.

Replay every scale/elimination operation independently from its parents. Also
verify each certificate directly against the original augmented matrix; do not
verify solely against the same derivation function that produced it. For a
reported solution, check all original residuals; for a family, check the origin
residuals and homogeneous residuals of every basis direction.

Tamper controls must reject a changed coefficient/RHS, changed certificate,
missing/forward parent, forged message ID, wrong certificate length, unsupported
node, zero scaling factor, zero pivot and budget overflow. Demonstrate that a
false conclusion cannot pass the proof checker just because its parent IDs exist.
Also reject dropping an original active row, eliminating a pivot against itself,
and resolving from fewer valid consequence rows that omit an original constraint.

Persist original inputs, message sequence, active references, final family,
classification, all certificates and proof-check outcomes in durable JSON
artifacts. Include unchanged unary-local and global results side by side.
Canonical ordering, decimal-string rational pairs, sorted JSON keys, compact
separators and one trailing newline must reproduce byte-for-byte under different
hash seeds and reversed initial edge input order. This is a research trace schema;
do not change SSM0_V1 or earlier report schemas.

## 6. Budgets and outcome semantics

Freeze three variables, six original rows, six-entry certificates, 64 messages
including originals, and 64 derivation operations. The deterministic schedule
uses at most three pivot normalizations, fifteen nontrivial eliminations and
one contradiction normalization: at most 19 derived rows plus six originals.
The frozen controls must finish under the cap. Resource limits apply to message
coefficients, certificate entries and completed arithmetic results.

Report `BUDGET_EXHAUSTED` separately from mathematical empty/unique/family.
Never infer consistency from an unfinished reduction. Validation/overflow is an
explicit failure, not a contradiction certificate. Parent-reference swaps must
not commit if the associated requested operation fails.

Use ordinary immutable messages and a bounded ledger; do not build a second
unbounded expression store. This ledger is a specialized research object pool,
not an extension of SSM-0's eight-register/128-object API. If those handles are
used in demos, their existing limits continue to apply independently. Arithmetic
temporaries and input conversion remain host-managed, not hard memory isolation.

## 7. Future command-first implementation and verification

After owner authorization, create a narrow message ledger/executor, independent
proof replayer/checker, frozen examples, focused tests, demo and artifact capture
under `research/ssm3/`. Reuse validated SSM-2 Problems and exact arithmetic; do not
rewrite predecessors. Keep the global solve outside the relational engine.

Future commands, not runnable until that package exists:

```bash
python3 -m unittest discover -s research/ssm3 -p 'test_*.py' -v
python3 -m research.ssm3.demo
```

Capture source hashes/archive before launch, including untracked research code;
verify at gate entry/exit and log manifest/archive digests. Inspect predecessor
terminal evidence and exclude concurrent shared regressions first.
Proposed verification budget: one detached attempt, 1800 seconds, no retries or
extensions. The future check script must run the new tests/demo/proof capture
followed by SSM-2's existing full check script once.

```bash
tools/run_detached_job.sh \
  --output build/ssm3/relational_messages_20261018_01 \
  --timeout 1800 --notify-desktop \
  -- bash research/ssm3/check_repo.sh
```

Refuse existing output. End turn at LAUNCHED. Interpret exactly one terminal
marker later. This draft authorizes no implementation or campaign.

## 8. Stop conditions and interpretation

Halt on an invalid derived certificate, lost original relation, incorrect
contradiction/solution classification, forward/cyclic proof dependency, mutation
on rejection, global-baseline use inside the message engine or scope expansion.
Preserve the failing proof trace and report the discrepancy; do not weaken checks.

A pass would establish that a bounded persistent relational representation can
resolve the frozen systems that unary-domain propagation leaves inconclusive,
with replayable exact derivations. It would not establish new mathematics,
a complete general constraint solver, distributed local completeness, learned
reasoning, hardware realization or a performance advantage.


## 9. Owner ratification and authorized runner amendment

Owner approved bounded software implementation, then explicitly authorized the
verification-only amendment after the halt-and-flag review identified a fixed
SSM-2 artifact path. SSM-2's original check script refuses to replace its existing
trace directory; invoking it unchanged would fail. No predecessor is modified.

Replace the section 7 requirement to invoke SSM-2's existing full script with
this equivalent sequence inside SSM-3's runner:

```bash
sha256sum -c research/ssm2/provenance/artifacts.sha256
sha256sum -c research/ssm2/provenance/sources.sha256
python3 -m unittest discover -s research/ssm2 -p 'test_*.py' -v
python3 -m research.ssm2.demo
python3 -m research.ssm2.capture --output build/ssm3/relational_messages_20261018_01/ssm2_traces
bash research/ssm1/check_repo.sh
sha256sum -c research/ssm2/provenance/sources.sha256
```

The new runner preserves all SSM-2 checks, creates only fresh comparison traces,
and runs the shared repository regression once through SSM-1. The original one
attempt/1800-second budget, frozen mathematical scope and all stop conditions
remain unchanged. This section supersedes proposal-only restrictions in section 7.

## 10. Focused implementation record

Implementation is restricted to `research/ssm3/` and this contract. Fourteen
focused methods pass before source capture; ten control proofs are captured and
reconstructed from durable JSON. The inconsistent cycle has a certified 0=1;
the unique cycle has certified singleton rows. Both retain unchanged unary
UNRESOLVED results. Redundancy, rational coefficients and no-equation controls
also pass.

The row/certificate checker and active-history replayer import no ledger or
executor helpers. They rebuild original equations from the frozen Problem,
check each parent derivation and original-input combination, replay active
references from all original rows and reject differences from the final claim.
Outcome checking independently validates reduced pivot structure, affine
dimension and all original residuals. The artifact loader reconstructs records
from JSON and invokes this verifier; stored proof-pass flags are not authoritative.

Prelaunch source hashes/archive cover the research sources and named gate entry
points, with entry/exit checks and logged manifest/archive digests. External tools
and all full-regression inputs are outside that declared source scope. Full
repository qualification remains pending the one authorized detached attempt.
