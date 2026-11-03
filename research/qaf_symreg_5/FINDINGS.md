# SYMREG-5 — trusted mathematical contexts

**REVISE.** Within one trusted, continuously existing in-memory authority,
the experiment distinguishes proof validity, immutable identity consistency,
and authorization for the current context revision. It rejects stale revisions,
expired epochs, unauthorized premises and missing branch witnesses in the
tested cases. It does **not** establish replay protection across authority
restart: two newly constructed authorities with the same name, allocation
history and supplied data create identical views, and the old certificate is
accepted by the second. This is a reproduced counterexample, not a solver
timeout. Durable non-reuse or another independently supplied freshness anchor
would require a separately specified trust boundary; neither is implemented.

The authority's view is supplied separately from the certificate producer.
The independent checker imports the unchanged SYMREG-4 checker, not the
producer or inference engine. Its three outputs distinguish mathematical proof,
identity matching and authorization. `AUTHORIZED_HISTORICAL` permits a claim
about identities, not a current-register claim. After a register overwrite,
the original certificate still verifies mathematically but is no longer
authorized; a new historical certificate can refer to the old immutable values.
Context-label reuse requires an explicit call and creates a new epoch. Within
one authority lifetime counters do not wrap; exhaustion is refused. A modified
branch set creates a new revision, and universal claims require witnesses for
each branch the authority declares feasible.

## Verification and limitations

Eleven test groups passed, including 49 systematically enumerated conjugation
values against an independent `Fraction` oracle. Tests cover expiry, reuse,
identity collision requests, current bindings, context substitution, missing
branch witnesses, untrusted premises, false concrete premises and allocation
exhaustion. They also preserve the restart replay counterexample. This is
bounded evidence, not exhaustive proof of Python behavior. The present producer
demonstrates premise-based proofs, while the unchanged SYMREG-4 checker also
supports composition and norm projection. The mathematical domain and exact
concrete checks are not a model of the full SPU ISA, overflow or RTL.

Authority state and the data it provides are trusted; no signatures,
authentication, durable storage, cross-process coordination or external
identity infrastructure are provided. A SHA-256 digest detects a changed
snapshot but does not authenticate its source. Branch feasibility is assumed,
not inferred. An attacker able to replace the trusted authority view is outside
the model. A current authorization is a local model decision, not permission
to execute a program. The view includes historical snapshots and is itself
subject to the predecessor's 65,536-byte input limit; the nominal per-epoch
count bounds do not guarantee the serialized view fits that limit. Resource
exhaustion is a refusal, not eviction or proof of falsehood.

## Solver record

Z3 4.15.5, QF_BV, with two-bit old/new epoch and identity variables, and
Boolean branch-witness and premise-authorization variables. The file encodes
four counterexample searches: equality despite assumed distinct epochs;
equality despite assumed distinct identities; a missing witness despite both
being required; and an unauthorized premise despite requiring authorization.
Each is UNSAT under its stated assumptions. Four deliberate mutants omit the
respective requirement and are SAT: example witnesses are epoch `11` vs `00`,
identity `11` vs `00`, A true/B false, and authorization false. This includes
wrap-shaped values but assumes distinction; it does not prove allocation,
non-wrap, authority persistence, branch feasibility or the Python code.
External timeout 30 s, solver timeout 25 s, address-space limit 1 GiB.

## Observed cost

On Python 3.10.12, one two-branch fixture produced a 693-byte envelope and
504-byte authority view; the proof used two premises, two steps and depth one.
One run took 0.000730 s for setup and a 30-check median of 0.000760 s per
verification; traced peak Python allocation during one check was 18,413 bytes.
These small observations include checking and JSON parsing, are not total
process memory and make no hardware speed, area or power claim. Costs grow as
historical snapshots accumulate; no asymptotic conclusion was measured.

## Reproduction

From the repository root, on baseline `a974cbc`, with SYMREG-5 untracked:

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_5.test_context -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_5.measure)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_5/verification.smt2)
```

Expected solver outcomes: `unsat, sat, unsat, sat, unsat, sat, unsat, sat`.
No random seeds are used. The checker can also be invoked with
`python3 -m research.qaf_symreg_5.checker ENVELOPE TRUSTED_VIEW`.

## Next experiment

The existing proof checker is a useful starting point for a **software-only**
SYMREG-GEOM-0, provided its trusted-context and restart limits remain explicit.
Start with a single exact quadratic-form structure and a symmetry claim such
as `Q(A,B)=Q(B,A)`, with an independent exact oracle and bounded solver control.
The current vocabulary does not encode point subtraction or geometric rules;
their minimal certificate semantics must be specified and checked in the
future experiment. It is not evidence of geometric correctness today. No
geometry implementation or v0.2 qualification change was performed here.
