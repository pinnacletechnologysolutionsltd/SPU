# SYMREG-3 bounded semantic branch join

Experimental software model only. It reuses, without changing, the local
[SYMREG-1](../qaf_symreg_1/SPECIFICATION.md) value identities and facts and the
[SYMREG-2](../qaf_symreg_2/SPECIFICATION.md) sparse proof search and verifier.
The values are integer-coefficient Q(√3); algebraic norm is not the ISA's
tuple-normalizing `SNORM`. Base admissions are predecessor-concretely-checked
facts. Python internals and the external declaration of feasible paths are
trusted assumptions, not a security boundary or branch-feasibility proof.

## Propositions and join

The configured finite query set contains exact predecessor `Key` propositions:
`target=k·conj^f(source)`, with `k∈{-2,-1,0,1,2}`, or
`N(target)=k·N(source)`, with `k∈{-4,-2,-1,0,1,2,4}`. For zero value scale,
`f` is false. Endpoints are immutable identities shared across the branch
domain, not register numbers. Unsupported or unconfigured queries yield
`UNKNOWN` and are not silently discovered.

`BranchRoster` holds one to three uniquely named, declared-feasible branches
with a shared domain and width. It has an explicit revision incremented on
membership changes. `Join` fixes the roster, each branch's current bindings,
known identities, fact objects and status, and at most 16 query keys. It is
sequential and not thread-safe. Changes to the roster or these branch snapshots
invalidate the context and its proofs; make a fresh context after a change.
Adding new identities elsewhere in the shared predecessor domain does not alter
existing immutable identities. Direct mutation of predecessor internals is not
within the trust model.

The syntactic comparator invokes the predecessor intersection join and then
the sparse query. The semantic comparator independently searches every named
branch for the *same* configured key. It returns `PROVEN` only when each
search returns a separately validated proof; `RESOURCE_LIMIT` propagates;
missing facts, unsupported inference or changed context return `UNKNOWN`.
The semantic join **does not emit `DISPROVEN`**: absence of a common proof is
not a counterexample. A caller may separately use the predecessor's concrete
counterexample rule for an identified binding; this model does not interpret
that result as false on every branch.

For a current-register query the optional pair of register numbers must resolve
to the proposition's same source and target identities in every branch.
Historical identity queries do not require those current bindings, but each
branch must still know the endpoints and prove the proposition. A different
binding on even one branch makes the current-register query `UNKNOWN`.

## Proof and limits

Each issued `JoinProof` contains the normalized key, rule `ALL_FEASIBLE_PATHS`,
ordered branch IDs, one predecessor proof per branch, optional current-register
bindings, roster revision, branch snapshots and fixed query-set reference. It
also carries an in-process context token. Validation checks the context is
unchanged, the proof was issued by this context, full exact branch coverage,
current bindings if requested, and replays each witness against its own
branch's trusted facts. A proof made from another branch's unique facts, a
missing branch or a fabricated or stale object is rejected. The token and
object-identity checks mean these are **not portable serialized certificates**;
independent replay here means a separate validation call in the same context.

Predecessor limits remain 64 identities, 256 facts per path, search depth 32,
and bounded predecessor provenance. This experiment adds at most 3 branches,
16 candidate keys, 4,096 aggregate edge inspections per query, 96 proof-path
edges and 256 unique provenance nodes per bundle, and 16 retained issued
proofs per context. Work, edge, node or retained-proof exhaustion returns
`RESOURCE_LIMIT`; no branch is silently omitted and no issued proof is evicted.
Depth or unsupported inference can return `UNKNOWN`. The optional canonical
semantic comparator was not implemented; the question-directed comparator is
the sole new join and does not expand the arithmetic vocabulary.
