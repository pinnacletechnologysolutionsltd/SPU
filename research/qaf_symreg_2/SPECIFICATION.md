# SYMREG-2 bounded representation specification

Software-only experiment; this is not an ISA, VM or hardware contract. The
unmodified [SYMREG-1 model](../qaf_symreg_1/SPECIFICATION.md) supplies exact
integer-coefficient Q(√3) values, immutable identities, concretely checked base
facts, register bindings and declared-feasible branch joins. Its algebraic
norm is distinct from the ISA's tuple-normalizing `SNORM` instruction.

## Vocabulary and trust

`value(source,target,k,f)` means `target=k·conj^f(source)`, for
`k∈{-2,-1,0,1,2}` and Boolean `f`. The flip flag is canonicalized to false
when `k=0`. `norm(source,target,k)` means `N(target)=k·N(source)`, for
`k∈{-4,-2,-1,0,1,2,4}`. Norm equality does not imply value equality.

`admit_checked` delegates to predecessor admission: checked concrete truth is
`PROVEN`, a checked concrete contradiction is `DISPROVEN`, and unsupported or
unavailable inputs yield `UNKNOWN`. It does not promote arbitrary assertions or
prove trust in a malicious caller; Python internals are not a security boundary.
The predecessor's trusted-fact store and branch feasibility inputs remain
assumptions. Fact admission reads values; later derivation need not.

## Three representations

1. **Explicit reference:** SYMREG-1 facts, including materialized derived
   facts where explicitly requested. Its implementation is unchanged.
2. **Sparse graph:** store only admitted facts. Directed breadth-first search
   composes value edges by multiplying scales and XORing conjugation. For a
   norm query, a value edge contributes the square of its scale and a norm
   edge contributes its own scale. No derived closure is stored by a query.
3. **Rooted canonical tree:** each node retains a canonical root-to-node
   `(scale,flip)` descriptor and a link to its parent proof edge. A query from
   that root reconstructs the path. Norm-only paths can use the same bounded
   sparse search. Other sources, cycles, alternative tree paths, reverse
   relations and unsupported scales return `UNKNOWN` rather than guessed facts.

Both representations return a `Proof` with endpoint identities, descriptor and
the ordered predecessor facts. `validate` replays the path and supported
provenance rules without rereading concrete values. It requires each top-level
fact to be the actual object present in the current path's trusted store;
fabricated or stale proofs are rejected. Historical facts remain valid for
their immutable identities, but current-register queries resolve the current
bindings. Joins use the predecessor's intersection of facts from every
declared feasible branch. A fact separately derivable through different paths
can therefore be lost at the join: this is safe incompleteness, not a false
conclusion. Branch feasibility is supplied, not inferred.

## Bounds and interpretation

The predecessor limits each domain to 64 identities and each path to 256
stored facts; additions fail explicitly without eviction. Graph queries allow
at most 4,096 edge inspections and depth 32. Canonical paths have depth at most
32 and at most 64 identity nodes. Proof validation permits depth 32 and at most
256 unique provenance nodes. Work exhaustion returns `RESOURCE_LIMIT`; a depth,
vocabulary, stale-proof or provenance limitation returns `UNKNOWN`. Proof
checking trusts the predecessor's `concrete_checked` admissions and verifies
derivation structure; it is not a solver or a proof of predecessor code.

An intermediate scale outside the vocabulary is not represented even if a
later zero scale would make the final expression representable. No facts are
silently evicted; a tree simply declines extra paths and the graph does not
materialize derived facts. `PROVEN` only means a checked path exists under
these rules, not that all true mathematical relationships are discoverable.
